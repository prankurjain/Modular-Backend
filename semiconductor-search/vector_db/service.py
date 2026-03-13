"""Vector search service with external Vector DB support.

- Primary mode: Qdrant (production-like external vector DB)
- Fallback mode: Oracle embedding scan (local/dev)
"""

from __future__ import annotations

import hashlib
from typing import Any

from config.settings import (
    VECTOR_DB_PROVIDER,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION_PREFIX,
)
from database.db_client import (
    get_products_with_embeddings_by_category,
)
from search.vector_search import find_similar_by_vector

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except Exception:  # optional dependency in environments that don't install qdrant
    QdrantClient = None
    qmodels = None


def search_similar_products(*, base_product: dict, category: str, top_n: int) -> list[dict]:
    base_embedding = base_product.get("embedding_vector")
    if not base_embedding or not isinstance(base_embedding, list):
        return []

    if _use_qdrant():
        results = _search_qdrant(base_product=base_product, category=category, top_n=top_n)
        if results:
            return results

    # fallback to oracle-backed vector scan
    lookup_key = base_product.get("part_number") or base_product.get("product_name")
    indexed_products = get_products_with_embeddings_by_category(
        category=category,
        exclude_lookup_key=lookup_key,
    )
    if not indexed_products:
        return []
    return find_similar_by_vector(base_product, indexed_products, top_n=top_n)


def upsert_product_vector(product: dict):
    """Upsert a product embedding into external vector DB (if enabled)."""
    if not _use_qdrant():
        return

    embedding = product.get("embedding_vector")
    category = product.get("category")
    if not embedding or not isinstance(embedding, list) or not category:
        return

    client = _get_qdrant_client()
    collection_name = _collection_name(category)
    _ensure_collection(client, collection_name, len(embedding))

    point_id = _product_point_id(product)
    payload = {
        "product_id": product.get("id"),
        "product_name": product.get("product_name"),
        "part_number": product.get("part_number"),
        "category": category,
        "manufacturer": product.get("manufacturer"),
        "datasheet_url": product.get("datasheet_url"),
        "package_type": product.get("package_type"),
    }

    client.upsert(
        collection_name=collection_name,
        points=[
            qmodels.PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )
        ],
        wait=True,
    )


def _search_qdrant(*, base_product: dict, category: str, top_n: int) -> list[dict]:
    client = _get_qdrant_client()
    collection_name = _collection_name(category)

    try:
        response = client.query_points(
            collection_name=collection_name,
            query=base_product["embedding_vector"],
            limit=top_n + 3,
            with_payload=True,
        )
    except Exception:
        return []

    base_lookup = (base_product.get("part_number") or base_product.get("product_name") or "").lower()
    results: list[dict] = []
    for point in (response.points or []):
        payload = dict(point.payload or {})
        lookup = str(payload.get("part_number") or payload.get("product_name") or "").lower()
        if lookup == base_lookup:
            continue

        item = {
            "id": payload.get("product_id"),
            "product_name": payload.get("product_name"),
            "part_number": payload.get("part_number"),
            "category": payload.get("category"),
            "manufacturer": payload.get("manufacturer"),
            "datasheet_url": payload.get("datasheet_url"),
            "package_type": payload.get("package_type"),
            "similarity_score": round(float(point.score or 0.0), 6),
        }
        results.append(item)
        if len(results) >= top_n:
            break

    return results


def _use_qdrant() -> bool:
    return VECTOR_DB_PROVIDER == "qdrant" and bool(QDRANT_URL) and QdrantClient is not None and qmodels is not None


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)


def _collection_name(category: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in category.lower())
    return f"{QDRANT_COLLECTION_PREFIX}_{safe}"


def _ensure_collection(client: QdrantClient, collection_name: str, vector_size: int):
    try:
        client.get_collection(collection_name)
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )


def _product_point_id(product: dict) -> int:
    if product.get("id") is not None:
        return int(product["id"])
    key = str(product.get("part_number") or product.get("product_name") or "unknown")
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:15]
    return int(digest, 16)
