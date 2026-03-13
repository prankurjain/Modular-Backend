"""
Generates vector embeddings for product feature texts using ST AI Bridge.

When API_KEY is not set, embedding generation is skipped gracefully.
The rest of the system (ingestion, structured search) remains fully functional.
"""

from __future__ import annotations

import hashlib
import random
import time
from typing import List, Optional

import requests
import urllib3

from config.settings import (
    API_KEY,
    CLIENT_APP_NAME,
    #EMBEDDING_MODEL,
    EMBEDDING_SERVICE_NAME,
    EMBEDDING_URL,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# -----------------------------------------------------------
# Token Generation
# -----------------------------------------------------------

def _generate_token(api_key: str, client_app_name: str, service_name: str):

    timestamp = int(time.time())
    nonce = random.randint(0, 1_000_000)

    data = f"{client_app_name}_{service_name}_{api_key}_{timestamp}_{nonce}"
    token = hashlib.sha1(data.encode()).hexdigest()

    return token, timestamp, nonce


# -----------------------------------------------------------
# API Call
# -----------------------------------------------------------

def _call_embedding_api(inputs: List[str]) -> Optional[List[List[float]]]:

    if not API_KEY or not CLIENT_APP_NAME:
        print("[Embedding] API key or client name missing — skipping embeddings")
        return None

    token, timestamp, nonce = _generate_token(
        API_KEY,
        CLIENT_APP_NAME,
        EMBEDDING_SERVICE_NAME
    )

    request_body = {
        "version": 1,
        "clientAppName": CLIENT_APP_NAME,
        "service": EMBEDDING_SERVICE_NAME,
        "timestamp": timestamp,
        # "model": EMBEDDING_MODEL,
        "contents": inputs,
    }

    try:

        response = requests.post(
            EMBEDDING_URL,
            json=request_body,
            headers={
                "stchatgpt-auth-token": token,
                "stchatgpt-auth-nonce": str(nonce),
                "Content-Type": "application/json"
            },
            verify=False,
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()
 
        if "embedding" not in payload:

            print("[Embedding] Unexpected response:", payload)

            return None
 
        vectors: List[List[float]] = payload["embedding"]  # list of lists of floats
 
        if len(vectors) != len(inputs):

            print("[Embedding] Missing vectors in response:", payload)

            return None
 
        return vectors
 

    except requests.exceptions.RequestException as error:

        try:
            err_payload = error.response.json() if error.response else str(error)
        except Exception:
            err_payload = str(error)

        print("[Embedding] HTTP error:", err_payload)
        return None

    except Exception as e:
        print("[Embedding] Unexpected error:", e)
        return None


# -----------------------------------------------------------
# Public Functions
# -----------------------------------------------------------

# def get_embedding(text: str) -> Optional[List[float]]:

#     if not text:
#         return None

#     vectors = _call_embedding_api([text])

#     if not vectors:
#         return None

#     return vectors[0]
def get_embedding(text: str) -> Optional[List[float]]:

    if not text:
        return None

    vectors = _call_embedding_api([text])

    if not vectors:
        print("[Embedding] No vectors returned")
        return None

    print("[Embedding] Got vector of length:", len(vectors[0]))
    return vectors[0]


def get_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:

    if not texts:
        return []

    vectors = _call_embedding_api(texts)

    if vectors is None:
        return [None] * len(texts)

    return vectors