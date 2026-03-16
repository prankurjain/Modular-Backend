"""LLM helpers for datasheet extraction and alternative analysis."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from config.settings import OPENAI_API_KEY

LLM_MODEL = "gpt-4o-mini"

_client: OpenAI | None = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _json_response(messages: list[dict[str, str]]) -> dict[str, Any]:
    if not _client:
        return {}

    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            temperature=0.2,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as exc:
        print(f"[LLM] request failed: {exc}")
        return {}


def extract_datasheet_attributes(part_number: str, category: str, datasheet_text: str) -> list[str]:
    """Extract concise semiconductor-relevant attributes from datasheet text."""
    if not datasheet_text.strip():
        return []

    text_excerpt = datasheet_text[:12000]
    payload = _json_response(
        [
            {
                "role": "system",
                "content": (
                    "You are a senior electronics engineer with 20+ years of experience in "
                    "semiconductors, ICs, and sensors. Extract the most important product "
                    "attributes useful for component comparison and sourcing."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return strict JSON with key 'attributes' as an array of short bullet strings. "
                    f"Part number: {part_number}. Category hint: {category}. "
                    "Focus on key electrical and package properties such as voltage/current limits, "
                    "frequency, power, thermal range, accuracy, interface, package, reliability, and "
                    "what makes the part important. Keep max 12 bullets. Datasheet text:\n"
                    f"{text_excerpt}"
                ),
            },
        ]
    )

    attributes = payload.get("attributes", []) if isinstance(payload, dict) else []
    if not isinstance(attributes, list):
        return []

    cleaned = [str(item).strip() for item in attributes if str(item).strip()]
    return cleaned[:12]


def generate_alternative_pros_cons(base_product: dict, candidate_product: dict) -> dict[str, Any]:
    """Generate pros/cons and matrix highlights for a candidate alternative."""
    payload = _json_response(
        [
            {
                "role": "system",
                "content": (
                    "You are a principal component selection engineer. Compare a base semiconductor "
                    "product and an alternative candidate."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return strict JSON with keys: 'pros' (array), 'cons' (array), "
                    "'summary' (string), and 'matrix_attributes' (object mapping attribute->comparison text). "
                    "Keep each item short and technical.\n"
                    f"Base product: {json.dumps(base_product, default=str)}\n"
                    f"Candidate product: {json.dumps(candidate_product, default=str)}"
                ),
            },
        ]
    )

    if not isinstance(payload, dict):
        return {"pros": [], "cons": [], "summary": "", "matrix_attributes": {}}

    pros = payload.get("pros", [])
    cons = payload.get("cons", [])
    matrix_attributes = payload.get("matrix_attributes", {})
    summary = str(payload.get("summary", "")).strip()

    return {
        "pros": pros if isinstance(pros, list) else [],
        "cons": cons if isinstance(cons, list) else [],
        "summary": summary,
        "matrix_attributes": matrix_attributes if isinstance(matrix_attributes, dict) else {},
    }
