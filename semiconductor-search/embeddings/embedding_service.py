"""
Generates vector embeddings for product feature texts using ST AI Bridge.

When API_KEY is not set, embedding generation is skipped gracefully.
The rest of the system (ingestion, structured search) remains fully functional.
"""

from __future__ import annotations

import hashlib
import random
import time
import ast
from typing import List, Optional

import requests
import urllib3

from config.settings import (
    API_KEY,
    CLIENT_APP_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_SERVICE_NAME,
    EMBEDDING_URL,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _generate_token(api_key: str, client_app_name: str, service_name: str) -> tuple[str, int, int]:
    """
    Generate ST AI Bridge authentication token, timestamp, and nonce.

    Token string is SHA1 of: "<clientAppName>_<serviceName>_<apiKey>_<timestamp>_<nonce>"
    """
    timestamp = int(time.time())
    nonce = random.randint(0, 1_000_000)

    data = f"{client_app_name}_{service_name}_{api_key}_{timestamp}_{nonce}"
    hash_object = hashlib.sha1(data.encode())
    token = hash_object.hexdigest()

    return token, timestamp, nonce


def _call_embedding_api(inputs: List[str]) -> Optional[List[List[float]]]:
    """
    Low-level call to the embedding service through ST AI Bridge.

    Returns:
        List of embedding vectors in the same order as `inputs`,
        or None if an error occurs.
    """
    def _normalize_config_string(value: object) -> str:
        """Normalize possibly malformed env/config values into a plain string."""
        if isinstance(value, str):
            text = value.strip()

            # Handle tuple/list string forms such as "('chat',)" or "['embeddings']"
            if (text.startswith("(") and text.endswith(")")) or (
                text.startswith("[") and text.endswith("]")
            ):
                try:
                    parsed = ast.literal_eval(text)
                    if isinstance(parsed, (list, tuple)) and parsed:
                        return str(parsed[0]).strip()
                except (ValueError, SyntaxError):
                    pass

            return text

        if isinstance(value, (list, tuple)) and value:
            return str(value[0]).strip()

        if value is None:
            return ""

        return str(value).strip()

    def _looks_like_embedding_service(service_name: str) -> bool:
        lowered = service_name.lower()
        return "embed" in lowered

    api_key = _normalize_config_string(API_KEY)
    client_app_name = _normalize_config_string(CLIENT_APP_NAME)

    if not api_key or not client_app_name:
        # No credentials configured: behave gracefully
        return None

    url = EMBEDDING_URL  # e.g. "https://.../embeddings/api/client-apps"

    def _post_with_service(service_name: str) -> dict:
        token, timestamp, nonce = _generate_token(api_key, client_app_name, service_name)

        # Request body format – this MUST match what your embedding service expects.
        # Example payload; adjust if your backend uses a different schema.
        request_body = {
            "version": 1,
            "clientAppName": client_app_name,
            "service": service_name,
            "timestamp": timestamp,
            "model": EMBEDDING_MODEL,
            "inputs": inputs,  # list of strings
        }

        response = requests.post(
            url,
            json=request_body,
            headers={
                "stchatgpt-auth-token": token,
                "stchatgpt-auth-nonce": str(nonce),
            },
            # NOTE: set verify=True in production with proper CA config
            verify=False,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    try:
        service_name = _normalize_config_string(EMBEDDING_SERVICE_NAME)  # e.g. "embeddings"
        payload = _post_with_service(service_name)

        if payload.get("errorCode"):
            suggested_services = payload.get("service")
            if (
                payload.get("message") == "Invalid service type"
                and isinstance(suggested_services, list)
                and suggested_services
            ):
                fallback_service = _normalize_config_string(suggested_services[0])
                if (
                    fallback_service != service_name
                    and _looks_like_embedding_service(fallback_service)
                ):
                    print(
                        "[Embedding] Invalid service type for "
                        f"'{service_name}'. Retrying with '{fallback_service}'."
                    )
                    payload = _post_with_service(fallback_service)
                else:
                    print(
                        "[Embedding] Invalid service type and no embedding-compatible "
                        f"fallback provided. configured='{service_name}', "
                        f"suggested={suggested_services}"
                    )

            if payload.get("errorCode"):
                print(f"[Embedding] API error: {payload}")
                return None

        # Expected response shape example:
        # {
        #   "embeddings": [
        #       {"index": 0, "vector": [...]},
        #       {"index": 1, "vector": [...]},
        #       ...
        #   ]
        # }
        if "embeddings" not in payload or not isinstance(payload["embeddings"], list):
            print("[Embedding] Unexpected response format:", payload)
            return None

        # Initialize result array
        result: List[Optional[List[float]]] = [None] * len(inputs)

        for item in payload["embeddings"]:
            try:
                idx = item["index"]
                vec = item["vector"]
                if 0 <= idx < len(result):
                    result[idx] = vec
            except (KeyError, TypeError):
                continue

        # If any None remains, treat as failure:
        if any(r is None for r in result):
            print("[Embedding] Some embeddings missing in response:", payload)
            return None

        # Type narrowing: we now know all are non-None
        return result  # type: ignore[return-value]

    except requests.exceptions.RequestException as error:
        try:
            err_payload = error.response.json() if error.response else str(error)
        except Exception:
            err_payload = str(error)
        print(f"[Embedding] HTTP error: {err_payload}")
        return None
    except Exception as e:
        print(f"[Embedding] Unexpected error: {e}")
        return None


def get_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a single embedding vector for the given text using ST AI Bridge.

    Returns:
        List of floats (the embedding vector), or None if credentials are missing
        or an error occurs.
    """
    if not text:
        return None

    vectors = _call_embedding_api([text])
    if not vectors:
        return None
    return vectors[0]


def get_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embeddings for a list of texts in a single API call.

    Returns:
        List of embedding vectors (or None values where generation failed).
    """
    if not texts:
        return []

    vectors = _call_embedding_api(texts)
    if vectors is None:
        # Preserve API contract: same length, all None on failure
        return [None] * len(texts)

    # `vectors` is guaranteed same length as `texts`
    return vectors
