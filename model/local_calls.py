import logging
from threading import Lock
from typing import List, Mapping, Sequence

import requests
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

from .config import (
    HF_API_BASE_URL,
    HF_API_TOKEN,
    HF_CHAT_MAX_OUTPUT_TOKENS,
    HF_CHAT_MODEL,
    HF_CHAT_TEMPERATURE,
    HF_RERANK_MODEL,
    HF_TIMEOUT,
)

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
_embedding_model_lock = Lock()
_embedding_model = None
_embedding_tokenizer = None


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


def embedding_call(texts: List[str]) -> List[List[float]]:
    """Return embeddings for each text using the configured Hugging Face model."""
    print("Я эмбеддер тут\nЯ тут\nЯ тут\nЯ тут\nЯ тут\n")
    print(texts)
    if not texts:
        return []

    embeddings = _local_embedding_request(texts)

    if embeddings and len(embeddings) != len(texts):
        logger.warning(
            "Embedding count mismatch; requested=%d received=%d",
            len(texts),
            len(embeddings),
        )
    return embeddings


def _load_embedding_components():
    """Lazily load the local embedding model and tokenizer once."""
    global _embedding_model, _embedding_tokenizer
    if _embedding_model is not None and _embedding_tokenizer is not None:
        return _embedding_tokenizer, _embedding_model

    with _embedding_model_lock:
        if _embedding_model is None or _embedding_tokenizer is None:
            logger.info("Loading local embedding model %s on CPU.", EMBEDDING_MODEL_ID)
            tokenizer = AutoTokenizer.from_pretrained(
                EMBEDDING_MODEL_ID,
                trust_remote_code=True,
            )
            model = AutoModel.from_pretrained(
                EMBEDDING_MODEL_ID,
                trust_remote_code=True,
            )
            model.to("cpu")
            model.eval()
            _embedding_model = model
            _embedding_tokenizer = tokenizer
    return _embedding_tokenizer, _embedding_model


def _local_embedding_request(texts: List[str]) -> List[List[float]]:
    tokenizer, model = _load_embedding_components()
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        return_tensors="pt",
    )

    with torch.no_grad():
        model_output = model(**encoded)

    token_embeddings = model_output.last_hidden_state
    attention_mask = encoded["attention_mask"].unsqueeze(-1)
    mask = attention_mask.expand_as(token_embeddings).float()
    masked_embeddings = token_embeddings * mask
    summed = masked_embeddings.sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    pooled = summed / counts
    normalized = F.normalize(pooled, p=2, dim=1)
    embeddings = normalized.cpu().tolist()
    print("Я эмбеддер отработал")
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
