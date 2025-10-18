import logging
from typing import List, Mapping

import requests

from .config import (
    SG_LANG_API_KEY,
    SG_LANG_CHAT_MODEL,
    SG_LANG_CHAT_URL,
    SG_LANG_EMBEDDINGS_MODEL,
    SG_LANG_EMBEDDINGS_URL,
    SG_LANG_RERANK_MODEL,
    SG_LANG_RERANK_URL,
)

logger = logging.getLogger(__name__)


def LLM_call(messages: List[Mapping[str, str]]) -> str:
    """Call SG_Lang chat completion endpoint using pre-structured messages and return the reply text."""
    logger.info("Sending messages to SG_Lang: %s", messages)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SG_LANG_API_KEY}",
    }
    body = {
        "model": SG_LANG_CHAT_MODEL,
        "messages": messages,
        "stream": False,
    }

    response = requests.post(SG_LANG_CHAT_URL, headers=headers, json=body, timeout=30)
    payload = response.json()
    assistant_message = payload["choices"][0]["message"]["content"]

    logger.info("Received assistant message from SG_Lang: %s", assistant_message)
    return assistant_message


def embedding_call(texts: List[str]) -> List[List[float]]:
    """Call the SGLang embeddings endpoint and return embeddings for each text."""
    logger.info(
        "Requesting embeddings from SG_Lang; count=%d model=%s",
        len(texts),
        SG_LANG_EMBEDDINGS_MODEL,
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SG_LANG_API_KEY}",
    }
    body = {
        "model": SG_LANG_EMBEDDINGS_MODEL,
        "input": texts,
    }

    try:
        response = requests.post(SG_LANG_EMBEDDINGS_URL, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.exception("Embedding request failed: %s", exc)
        raise RuntimeError("Embedding endpoint request failed") from exc

    try:
        embeddings = [item["embedding"] for item in payload["data"]]
    except (KeyError, TypeError) as exc:
        logger.exception("Unexpected embedding payload structure: %s", payload)
        raise RuntimeError("Invalid response from embedding endpoint") from exc

    if len(embeddings) != len(texts):
        logger.warning(
            "Embedding count mismatch; requested=%d received=%d",
            len(texts),
            len(embeddings),
        )

    return embeddings


def reranker_call(query: str, documents: List[str]) -> List[float]:
    """Call the SGLang reranker endpoint and return scores aligned with the input documents."""
    if not documents:
        return []

    logger.info(
        "Requesting rerank scores from SG_Lang; model=%s docs=%d",
        SG_LANG_RERANK_MODEL,
        len(documents),
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SG_LANG_API_KEY}",
    }
    body = {
        "model": SG_LANG_RERANK_MODEL,
        "query": query,
        "documents": documents,
    }

    try:
        response = requests.post(SG_LANG_RERANK_URL, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.exception("Reranker request failed: %s", exc)
        raise RuntimeError("Reranker endpoint request failed") from exc

    try:
        data = payload["data"]
    except (KeyError, TypeError) as exc:
        logger.exception("Unexpected reranker payload structure: %s", payload)
        raise RuntimeError("Invalid response from reranker endpoint") from exc

    scores: List[float]
    # Prefer explicit indices when available so the order matches the original list.
    indexed_scores: List[float] = [0.0] * len(documents)
    found_indices = False
    collected_scores: List[float] = []

    for item in data:
        if not isinstance(item, Mapping):
            logger.error("Reranker response item is not a mapping: %s", item)
            raise RuntimeError("Invalid response from reranker endpoint")

        score = item.get("score", item.get("relevance_score"))
        if score is None:
            logger.error("Reranker response missing score: %s", item)
            raise RuntimeError("Invalid response from reranker endpoint")

        index = item.get("index")
        if index is None:
            collected_scores.append(float(score))
            continue

        found_indices = True
        if not (0 <= index < len(documents)):
            logger.error("Reranker response index out of range: %s", item)
            raise RuntimeError("Invalid response from reranker endpoint")
        indexed_scores[index] = float(score)

    if found_indices:
        scores = indexed_scores
    else:
        scores = [float(s) for s in collected_scores]

    if len(scores) != len(documents):
        logger.warning(
            "Reranker score count mismatch; requested=%d received=%d",
            len(documents),
            len(scores),
        )

    return scores
