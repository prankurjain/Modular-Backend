"""Hybrid search orchestration.

Flow:
1) Fetch base product from Oracle DB.
2) Pull structured candidates from Oracle DB.
3) Pull vector neighbors from Vector DB service.
4) Merge candidates.
5) Run comparison engine for rule filtering + weighted ranking.
"""

from config.settings import TOP_N_RESULTS
from database.db_client import get_product_by_part_number
from search.comparison_engine import apply_rules_and_rank
from search.structured_filter import find_structured_candidates
from vector_db.service import search_similar_products


def find_alternatives(part_number: str, top_n: int = TOP_N_RESULTS) -> dict:
    base = get_product_by_part_number(part_number)
    if not base:
        return {
            "error": (
                f"Product '{part_number}' not found in database. "
                "In this demo flow, ingest demo data first before searching."
            ),
            "base_product": None,
            "alternatives": [],
        }

    category = base.get("category")
    structured_candidates = find_structured_candidates(base, top_n=top_n * 5)

    vector_candidates = []
    if category:
        vector_candidates = search_similar_products(
            base_product=base,
            category=category,
            top_n=top_n * 5,
        )

    merged_candidates = _merge_candidates(structured_candidates, vector_candidates)
    if not merged_candidates:
        return {
            "base_product": _clean(base),
            "alternatives": [],
            "search_mode": "none",
            "message": "No candidates found from Oracle structured search or vector search.",
        }

    ranked = apply_rules_and_rank(base, merged_candidates, top_n=top_n)

    return {
        "base_product": _clean(base),
        "alternatives": [_clean(x) for x in ranked],
        "search_mode": _resolve_search_mode(structured_candidates, vector_candidates),
        "total_candidates": len(merged_candidates),
        "sources": {
            "oracle_structured": len(structured_candidates),
            "vector_db": len(vector_candidates),
        },
    }


def _merge_candidates(structured: list[dict], vector: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}

    for candidate in structured + vector:
        key = str(candidate.get("id") or candidate.get("part_number") or candidate.get("product_name"))
        if key not in merged:
            merged[key] = dict(candidate)
        else:
            merged[key].update({k: v for k, v in candidate.items() if v is not None})

    return list(merged.values())


def _resolve_search_mode(structured: list[dict], vector: list[dict]) -> str:
    if structured and vector:
        return "oracle_plus_vector"
    if vector:
        return "vector_only"
    if structured:
        return "structured_only"
    return "none"


def _clean(product: dict) -> dict:
    cleaned = {k: v for k, v in product.items() if k != "embedding_vector"}
    for key in ("created_at", "updated_at"):
        if cleaned.get(key) and hasattr(cleaned[key], "isoformat"):
            cleaned[key] = cleaned[key].isoformat()
    return cleaned
