import logging
from typing import List, Mapping, Sequence

import requests

from .config import (
    HF_API_BASE_URL,
    HF_API_TOKEN,
    HF_CHAT_MAX_OUTPUT_TOKENS,
    HF_CHAT_MODEL,
    HF_CHAT_TEMPERATURE,
    HF_EMBEDDING_MODEL,
    HF_RERANK_MODEL,
    HF_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _ensure_messages(messages: Sequence[Mapping[str, str]]) -> List[Mapping[str, str]]:
    normalized: List[Mapping[str, str]] = []
    for entry in messages:
        if "role" not in entry or "content" not in entry:
            raise ValueError(f"Invalid message payload: {entry}")
        normalized.append({"role": entry["role"], "content": entry["content"]})
    return normalized


def _base_api_url() -> str:
    return HF_API_BASE_URL.rstrip("/") if HF_API_BASE_URL else "https://router.huggingface.co"


def LLM_call(messages: List[Mapping[str, str]]) -> str:
    """Call the Hugging Face chat completion endpoint and return the reply text."""
    print("Я LLM тут\nЯ LLM тут\nЯ LLM тут\nЯ LLM тут\n")
    if not HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not configured.")

    normalized_messages = _ensure_messages(messages)
    url = f"{_base_api_url()}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_CHAT_MODEL,
        "messages": normalized_messages,
        "temperature": HF_CHAT_TEMPERATURE,
    }
    if HF_CHAT_MAX_OUTPUT_TOKENS is not None:
        payload["max_tokens"] = HF_CHAT_MAX_OUTPUT_TOKENS

    logger.debug("Posting chat completion request to %s", url)
    response = requests.post(url, headers=headers, json=payload, timeout=HF_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    try:
        assistant_message = data["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, AttributeError) as exc:
        raise RuntimeError(f"Invalid response from chat completion endpoint: {data!r}") from exc

    logger.info("Received assistant message from Hugging Face provider.")
    print("Я LLM отработал")
    return assistant_message


def _embedding_request(texts: List[str], model_id: str) -> List[List[float]]:
    print("Я эмбеддер тут\nЯ тут\nЯ тут\nЯ тут\nЯ тут\n")
    print(texts)
    if not texts:
        return []

    if not HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not configured.")

    base_url = _base_api_url()
    url = f"{base_url}/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    embeddings: List[List[float]] = []
    for query in texts:
        payload = {"inputs": {"source_sentence": query, "sentences": [query]}}
        logger.debug("Posting embedding request to %s", url)
        response = requests.post(url, headers=headers, json=payload, timeout=HF_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or not data:
            raise RuntimeError(f"Unexpected embedding response payload: {data!r}")
        try:
            vectors = [float(value) for value in data]
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Could not parse embedding response: {data!r}") from exc
        embeddings.append(vectors)
    print("Я эмбеддер отработал")
    return embeddings


def embedding_call(texts: List[str]) -> List[List[float]]:
    """Return embeddings for each text using the configured Hugging Face model."""
    embeddings = _embedding_request(texts, HF_EMBEDDING_MODEL)

    if embeddings and len(embeddings) != len(texts):
        logger.warning(
            "Embedding count mismatch; requested=%d received=%d",
            len(texts),
            len(embeddings),
        )
    return embeddings


def reranker_call(query: str, documents: List[str]) -> List[float]:
    """Return similarity scores between the query and documents using the HF reranker model."""
    if not documents:
        return []
    if not HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not configured.")

    url = f"{_base_api_url()}/models/{HF_RERANK_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"inputs": {"source_sentence": query, "sentences": documents}}

    logger.debug("Posting reranker request to %s", url)
    response = requests.post(url, headers=headers, json=payload, timeout=HF_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected reranker response payload: {data!r}")
    try:
        return [float(score) for score in data]
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Could not parse reranker response: {data!r}") from exc
