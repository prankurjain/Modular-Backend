"""Chat helpers for datasheet extraction and alternative analysis via ST chat API."""

from __future__ import annotations

import hashlib
import json
import random
import time
from typing import Any

import requests
import urllib3

from config.settings import (
    API_KEY,
    CHAT_MAX_RESPONSE_TOKENS,
    CHAT_PERSONA,
    CHAT_SERVICE_NAME,
    CHAT_TEMPERATURE,
    CHAT_URL,
    CLIENT_APP_NAME,
    REMOTE_USER,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _generate_token(api_key: str, client_app_name: str, service_name: str) -> tuple[str, int, int]:
    timestamp = int(time.time() * 1000)
    nonce = random.randint(0, 1_000_000)
    data = f"{client_app_name}_{service_name}_{api_key}_{timestamp}_{nonce}"
    token = hashlib.sha1(data.encode()).hexdigest()
    return token, timestamp, nonce


def _chat_json_response(messages: list[dict[str, Any]]) -> dict[str, Any]:
    if not API_KEY or not CLIENT_APP_NAME:
        return {}

    token, timestamp, nonce = _generate_token(API_KEY, CLIENT_APP_NAME, CHAT_SERVICE_NAME)

    request_body = {
        "version": 1,
        "clientAppName": CLIENT_APP_NAME,
        "timestamp": timestamp,
        "remoteUser": REMOTE_USER,
        "service": CHAT_SERVICE_NAME,
        "temperature": CHAT_TEMPERATURE,
        "maxResponseTokens": CHAT_MAX_RESPONSE_TOKENS,
        "responseFormat": "json_object",
        "persona": CHAT_PERSONA,
        "messages": messages,
    }

    try:
        response = requests.post(
            CHAT_URL,
            json=request_body,
            headers={
                "stchatgpt-auth-token": token,
                "stchatgpt-auth-nonce": str(nonce),
                "Content-Type": "application/json",
            },
            verify=False,
            timeout=40,
        )
        response.raise_for_status()
        payload = response.json()

        # Accept common envelope shapes from chat APIs
        if isinstance(payload, dict) and isinstance(payload.get("content"), dict):
            return payload["content"]
        if isinstance(payload, dict) and isinstance(payload.get("response"), dict):
            return payload["response"]
        if isinstance(payload, dict) and isinstance(payload.get("output"), dict):
            return payload["output"]

        if isinstance(payload, dict):
            return payload
        return {}
    except Exception as exc:
        print(f"[LLM] chat request failed: {exc}")
        return {}


def _text_message(role: str, text: str) -> dict[str, Any]:
    return {
        "role": role,
        "content": [
            {
                "type": "text",
                "content": text,
            }
        ],
    }


def extract_datasheet_attributes(part_number: str, category: str, datasheet_text: str) -> list[str]:
    """Extract concise semiconductor-relevant attributes from datasheet text."""
    if not datasheet_text.strip():
        return []

    text_excerpt = datasheet_text[:12000]

    system_text = (
        "You are a senior electronics engineer with 20+ years of experience in semiconductors, "
        "ICs, and sensors."
    )
    user_text = (
        "Return strict JSON only with key 'attributes' (array of short technical bullets). "
        f"Part number: {part_number}. Category hint: {category}. "
        "Focus on key electrical/package/thermal/performance limits and why the part is important for design. "
        "Max 12 bullets. Datasheet text:\n"
        f"{text_excerpt}"
    )

    payload = _chat_json_response([
        _text_message("system", system_text),
        _text_message("user", user_text),
    ])

    attributes = payload.get("attributes", []) if isinstance(payload, dict) else []
    if not isinstance(attributes, list):
        return []

    cleaned = [str(item).strip() for item in attributes if str(item).strip()]
    return cleaned[:12]


def generate_alternative_pros_cons(base_product: dict, candidate_product: dict) -> dict[str, Any]:
    """Generate pros/cons and matrix highlights for a candidate alternative."""

    user_text = (
        "Compare base and candidate semiconductor products for engineering substitution. "
        "Return strict JSON with keys: 'pros' (array), 'cons' (array), 'summary' (string), "
        "'matrix_attributes' (object mapping attribute->comparison note). Keep concise and technical.\n"
        f"Base product: {json.dumps(base_product, default=str)}\n"
        f"Candidate product: {json.dumps(candidate_product, default=str)}"
    )

    payload = _chat_json_response([
        _text_message("system", "You are a principal component selection engineer."),
        _text_message("user", user_text),
    ])

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
