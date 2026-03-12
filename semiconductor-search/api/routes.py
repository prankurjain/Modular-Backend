"""
FastAPI route definitions for the semiconductor product search API.

Endpoints:
  POST /ingest-data         — read CSV, parse HTML, store specs in DB
  POST /generate-embeddings — generate OpenAI embeddings for stored products
  GET  /find-alternatives   — find alternative products for a given product name
  GET  /products            — list all ingested products
  GET  /health              — health check
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ingestion.csv_loader import load_product_csv
from ingestion.html_loader import load_html
from ingestion.html_parser import parse_product_specs
from ingestion.spec_normalizer import normalize_specs
from database.db_client import (
    upsert_product,
    get_products_without_embeddings,
    update_product_embedding,
    get_all_products,
    get_product_by_name,
)
from embeddings.embedding_service import get_embeddings_batch
from search.hybrid_search import find_alternatives
from config.settings import OPENAI_API_KEY

router = APIRouter()

CSV_PATH = os.environ.get("PRODUCTS_CSV_PATH", "data/products.csv")


# ── Request / Response Models ─────────────────────────────────────────────────

class IngestResponse(BaseModel):
    ingested: int
    skipped: int
    errors: list[str]


class EmbeddingResponse(BaseModel):
    generated: int
    skipped: int
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/ingest-data", response_model=IngestResponse)
def ingest_data(csv_path: str = Query(default=CSV_PATH)):
    """
    Read the products CSV, parse each product's HTML page, normalize specs,
    and store everything in the database.

    Query params:
      csv_path — path to the products.csv file (default: data/products.csv)
    """
    try:
        entries = load_product_csv(csv_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ingested = 0
    skipped = 0
    errors: list[str] = []

    for entry in entries:
        name = entry["product_name"]
        category = entry["category"]
        html_path = entry.get("html_path", "")
        source_url = entry.get("source_url", "")
        html_source = html_path or source_url

        try:
            html = load_html(html_source, csv_dir=str(Path(csv_path).resolve().parent))
        except FileNotFoundError:
            errors.append(f"{name}: HTML file not found at {html_source}")
            skipped += 1
            continue
        except Exception as e:
            errors.append(f"{name}: failed to load source {html_source} — {e}")
            skipped += 1
            continue

        raw_specs = parse_product_specs(html, category)
        product = normalize_specs(name, category, raw_specs)

        try:
            upsert_product(product)
            ingested += 1
        except Exception as e:
            errors.append(f"{name}: DB error — {e}")
            skipped += 1

    return IngestResponse(ingested=ingested, skipped=skipped, errors=errors)


@router.post("/generate-embeddings", response_model=EmbeddingResponse)
def generate_embeddings():
    """
    Generate OpenAI vector embeddings for all products that do not have one yet.
    Requires the OPENAI_API_KEY environment variable to be set.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY is not configured. "
                "Set the secret in your environment and restart the server."
            ),
        )

    pending = get_products_without_embeddings()
    if not pending:
        return EmbeddingResponse(
            generated=0,
            skipped=0,
            message="All products already have embeddings.",
        )

    texts = [p["features_text"] or p["product_name"] for p in pending]
    embeddings = get_embeddings_batch(texts)

    generated = 0
    skipped = 0
    for product, embedding in zip(pending, embeddings):
        if embedding is None:
            skipped += 1
            continue
        try:
            update_product_embedding(product["product_name"], embedding)
            generated += 1
        except Exception as e:
            print(f"[Embed] Failed to store embedding for {product['product_name']}: {e}")
            skipped += 1

    return EmbeddingResponse(
        generated=generated,
        skipped=skipped,
        message=f"Generated embeddings for {generated} products.",
    )


@router.get("/find-alternatives")
def find_alternatives_endpoint(
    product_name: str = Query(..., description="Exact product name to find alternatives for"),
    top_n: int = Query(default=10, ge=1, le=100),
):
    """
    Find alternative semiconductor products for the specified product.

    Returns a ranked list using hybrid search (structured SQL + vector similarity).
    Falls back to heuristic ranking if embeddings are not yet generated.
    """
    result = find_alternatives(product_name, top_n=top_n)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/products")
def list_products(
    category: str | None = Query(default=None, description="Filter by category"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List all ingested products, optionally filtered by category."""
    products = get_all_products()
    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]
    return {"total": len(products), "products": products[:limit]}


@router.get("/products/{product_name}")
def get_product(product_name: str):
    """Get a single product's full spec by name."""
    product = get_product_by_name(product_name)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found.")
    # Don't return the raw embedding vector blob
    product.pop("embedding_vector", None)
    if product.get("created_at") and hasattr(product["created_at"], "isoformat"):
        product["created_at"] = product["created_at"].isoformat()
    if product.get("updated_at") and hasattr(product["updated_at"], "isoformat"):
        product["updated_at"] = product["updated_at"].isoformat()
    return product
