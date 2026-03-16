"""FastAPI routes."""

import csv
import io
import json
import os
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from config.categories_config import CATEGORIES
from ingestion.csv_loader import load_product_csv
from ingestion.html_loader import load_html
from ingestion.html_parser import parse_product_specs
from ingestion.category_detector import detect_category
from ingestion.spec_normalizer import normalize_specs
from ingestion.datasheet_loader import read_datasheet_text
from database.db_client import (
    upsert_product,
    get_products_without_embeddings,
    update_product_embedding,
    get_all_products,
    get_product_by_name,
    get_product_by_part_number,
    get_products_with_embeddings,
)
from search.hybrid_search import find_alternatives
from llm.product_intelligence import extract_datasheet_attributes, generate_alternative_pros_cons
from vector_db.service import upsert_product_vector
from embeddings.embedding_service import get_embedding

router = APIRouter()
CSV_PATH = os.environ.get("PRODUCTS_CSV_PATH", "data/products.csv")
DEMO_JSON_PATH = os.environ.get("DEMO_PRODUCTS_PATH", "data/demo_products.json")


class IngestResponse(BaseModel):
    ingested: int
    skipped: int
    errors: list[str]


class EmbeddingResponse(BaseModel):
    generated: int
    skipped: int
    message: str


class FindAlternativeRequest(BaseModel):
    part_number: str = Field(..., description="Part number to search alternatives for")
    top_k: int = Field(default=10, ge=1, le=100)


class BomAlternativeItem(BaseModel):
    input_part_number: str
    base_product: dict | None
    valid_attributes: dict
    alternatives: list[dict]
    error: str | None = None


class BomAlternativeResponse(BaseModel):
    total_inputs: int
    processed: int
    failed: int
    results: list[BomAlternativeItem]


def _coerce_embedding_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value).strip()


def _valid_attributes_for_product(product: dict | None) -> dict:
    if not product:
        return {}
    category = str(product.get("category", "")).lower()
    important_attributes = CATEGORIES.get(category, {}).get("important_attributes", [])
    return {
        key: product.get(key)
        for key in important_attributes
        if product.get(key) is not None
    }


def _enrich_alternatives_with_llm(base_product: dict | None, alternatives: list[dict]) -> list[dict]:
    if not base_product:
        return alternatives

    enriched: list[dict] = []
    for candidate in alternatives:
        analysis = generate_alternative_pros_cons(base_product, candidate)
        merged = dict(candidate)
        merged["pros"] = analysis.get("pros", [])
        merged["cons"] = analysis.get("cons", [])
        merged["selection_summary"] = analysis.get("summary", "")
        merged["matrix_attributes"] = analysis.get("matrix_attributes", {})
        enriched.append(merged)
    return enriched


def _parse_bom_part_numbers(csv_bytes: bytes) -> list[str]:
    try:
        decoded = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = csv_bytes.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise ValueError("CSV is missing a header row.")

    normalized = {name.lower().strip(): name for name in reader.fieldnames if name}
    candidate_columns = ["part_number", "product_name", "part", "component", "sku"]
    source_col = next((normalized[col] for col in candidate_columns if col in normalized), None)
    if not source_col:
        raise ValueError(
            "CSV must include one of these columns: part_number, product_name, part, component, sku"
        )

    part_numbers: list[str] = []
    for row in reader:
        value = str(row.get(source_col, "")).strip()
        if value:
            part_numbers.append(value)

    if not part_numbers:
        raise ValueError("CSV contains no usable part numbers.")
    return part_numbers


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/ingest-data", response_model=IngestResponse)
def ingest_data(csv_path: str = Query(default=CSV_PATH)):
    try:
        entries = load_product_csv(csv_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ingested, skipped, errors = 0, 0, []

    for entry in entries:
        name = entry["product_name"]
        category = entry["category"]
        html_source = entry.get("html_path", "") or entry.get("source_url", "")
        datasheet_source = entry.get("datasheet_link", "")

        try:
            html = load_html(html_source, csv_dir=str(Path(csv_path).resolve().parent))
            raw_specs = parse_product_specs(html, category)
            if not raw_specs:
                raw_specs = parse_product_specs(html, None)
            resolved_category = detect_category(raw_specs, hint=category)
            product = normalize_specs(name, resolved_category, raw_specs)

            if datasheet_source:
                datasheet_text = read_datasheet_text(
                    datasheet_source,
                    csv_dir=str(Path(csv_path).resolve().parent),
                )
                datasheet_attributes = extract_datasheet_attributes(
                    part_number=product.get("part_number") or name,
                    category=resolved_category,
                    datasheet_text=datasheet_text,
                )
                if datasheet_attributes:
                    base_features = product.get("features_text") or ""
                    extra_features = " | ".join(datasheet_attributes)
                    product["features_text"] = f"{base_features} | Datasheet insights: {extra_features}".strip(" |")

            upsert_product(product)
            ingested += 1
        except Exception as e:
            errors.append(f"{name}: {e}")
            skipped += 1

    return IngestResponse(ingested=ingested, skipped=skipped, errors=errors)


@router.post("/ingest-demo-data", response_model=IngestResponse)
def ingest_demo_data(path: str = Query(default=DEMO_JSON_PATH)):
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=400, detail=f"Demo file not found: {path}")

    records = json.loads(file_path.read_text())
    ingested, skipped, errors = 0, 0, []

    for record in records:
        try:
            upsert_product(record)
            vector = [
                record.get("vds_max_v") or 0,
                record.get("id_max_a") or 0,
                record.get("rds_on_ohm") or 0,
                record.get("gate_charge_nc") or 0,
                220 if str(record.get("package_type", "")).upper().startswith("TO-220") else 0,
            ]
            update_product_embedding(record["part_number"], vector)
            persisted = get_product_by_part_number(record["part_number"])
            if persisted:
                upsert_product_vector(persisted)
            ingested += 1
        except Exception as e:
            errors.append(f"{record.get('part_number')}: {e}")
            skipped += 1

    return IngestResponse(ingested=ingested, skipped=skipped, errors=errors)


@router.post("/generate-embeddings", response_model=EmbeddingResponse)
def generate_embeddings():
    pending = get_products_without_embeddings()
    if not pending:
        return EmbeddingResponse(
            generated=0,
            skipped=0,
            message="All products already have embeddings."
        )

    generated = 0
    skipped = 0

    for product in pending:
        lookup_key = product.get("part_number") or product.get("product_name")
        display_name = lookup_key or "<unknown>"
        print(f"[INGEST] Processing: {display_name}")

        try:
            raw_text = (
                product.get("features_text")
                or product.get("product_name")
                or product.get("part_number")
            )
            text = _coerce_embedding_text(raw_text)

            if not text:
                print(f"[INGEST] Skipping {display_name}: no text available for embedding")
                skipped += 1
                continue

            embedding = get_embedding(text)
            if not embedding:
                print(f"[INGEST] Skipping {display_name}: embedding is None/empty")
                skipped += 1
                continue

            update_product_embedding(lookup_key, embedding)

            persisted = None
            if product.get("part_number"):
                persisted = get_product_by_part_number(product["part_number"])
            if not persisted and product.get("product_name"):
                persisted = get_product_by_name(product["product_name"])

            if persisted:
                upsert_product_vector(persisted)
            else:
                print(f"[INGEST] Warning: persisted product not found after update: {display_name}")

            generated += 1
            print(f"[INGEST] Completed: {display_name}")

        except Exception as e:
            skipped += 1
            print(f"[ERROR] {display_name}: {e}")

    print("[INGEST] Pipeline completed successfully")

    return EmbeddingResponse(
        generated=generated,
        skipped=skipped,
        message=f"Generated embeddings for {generated} products (skipped {skipped})."
    )


@router.post("/sync-vector-db")
def sync_vector_db():
    """Push all Oracle products with embeddings into the external vector DB."""
    synced = 0
    skipped = 0

    for product in get_products_with_embeddings():
        try:
            upsert_product_vector(product)
            synced += 1
        except Exception:
            skipped += 1

    return {"synced": synced, "skipped": skipped}


@router.post("/find-alternative")
def find_alternatives_endpoint(payload: FindAlternativeRequest):
    result = find_alternatives(payload.part_number, top_n=payload.top_k)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    result["alternatives"] = _enrich_alternatives_with_llm(
        result.get("base_product"),
        result.get("alternatives", []),
    )
    return result


@router.post("/find-alternatives-bom", response_model=BomAlternativeResponse)
async def find_alternatives_bom(file: UploadFile = File(...), top_k: int = Query(default=5, ge=1, le=50)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        part_numbers = _parse_bom_part_numbers(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    results: list[BomAlternativeItem] = []
    failed = 0

    for part_number in part_numbers:
        result = find_alternatives(part_number, top_n=top_k)
        if result.get("error"):
            failed += 1
            results.append(
                BomAlternativeItem(
                    input_part_number=part_number,
                    base_product=None,
                    valid_attributes={},
                    alternatives=[],
                    error=result["error"],
                )
            )
            continue

        base_product = result.get("base_product")
        alternatives = _enrich_alternatives_with_llm(
            base_product,
            result.get("alternatives", []),
        )
        results.append(
            BomAlternativeItem(
                input_part_number=part_number,
                base_product=base_product,
                valid_attributes=_valid_attributes_for_product(base_product),
                alternatives=[
                    {
                        "alternative_for": part_number,
                        "rank": idx,
                        "valid_attributes": _valid_attributes_for_product(candidate),
                        **candidate,
                    }
                    for idx, candidate in enumerate(alternatives, start=1)
                ],
            )
        )

    return BomAlternativeResponse(
        total_inputs=len(part_numbers),
        processed=len(part_numbers) - failed,
        failed=failed,
        results=results,
    )


@router.get("/find-alternatives")
def find_alternatives_legacy(
    product_name: str = Query(..., description="Part number/product name to find alternatives for"),
    top_n: int = Query(default=10, ge=1, le=100),
):
    """Backward-compatible endpoint that maps to part-number search."""
    result = find_alternatives(product_name, top_n=top_n)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    result["alternatives"] = _enrich_alternatives_with_llm(
        result.get("base_product"),
        result.get("alternatives", []),
    )
    return result


@router.get("/products")
def list_products(category: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=1000)):
    products = get_all_products()
    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]
    return {"total": len(products), "products": products[:limit]}


@router.get("/products/{product_name}")
def get_product(product_name: str):
    product = get_product_by_name(product_name)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found.")
    product.pop("embedding_vector", None)
    if product.get("created_at") and hasattr(product["created_at"], "isoformat"):
        product["created_at"] = product["created_at"].isoformat()
    if product.get("updated_at") and hasattr(product["updated_at"], "isoformat"):
        product["updated_at"] = product["updated_at"].isoformat()
    return product
