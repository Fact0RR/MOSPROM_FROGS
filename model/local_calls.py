import logging
from threading import Lock
from typing import List, Mapping, Optional, Sequence

import requests

try:
    import torch
    import torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
except ImportError as exc:  # pragma: no cover - optional dependency
    torch = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    AutoModel = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]
    _embedding_import_error: Optional[Exception] = exc
else:
    _embedding_import_error = None

from .config import (
    HF_API_BASE_URL,
    HF_API_TOKEN,
    HF_CHAT_MAX_OUTPUT_TOKENS,
    HF_CHAT_MODEL,
    HF_CHAT_TEMPERATURE,
    HF_RERANK_MODEL,
    HF_TIMEOUT,
    HF_MAX_RETRIES,
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
    attempts = max(1, HF_MAX_RETRIES)
    response = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=HF_TIMEOUT,
            )
            response.raise_for_status()
            break
        except requests.Timeout as exc:
            logger.warning(
                "LLM_call timed out after %.1fs on attempt %d/%d",
                HF_TIMEOUT,
                attempt,
                attempts,
            )
            if attempt == attempts:
                raise RuntimeError(
                    f"LLM_call timed out after {attempts} attempts (timeout={HF_TIMEOUT}s)"
                ) from exc
        except requests.HTTPError:
            body_preview = response.text[:1000] if response is not None and response.text else "<empty body>"
            status = response.status_code if response is not None else "unknown"
            logger.error(
                "LLM_call HTTP %s at %s; body preview=%s",
                status,
                url,
                body_preview,
            )
            raise
        except requests.RequestException as exc:
            logger.exception("LLM_call request failed on attempt %d/%d", attempt, attempts)
            raise

    if response is None:
        raise RuntimeError("LLM_call failed: no response received after retries.")

    try:
        data = response.json()
    except ValueError as exc:
        body_preview = response.text[:1000] if response.text else "<empty body>"
        logger.exception("Failed to decode chat response: %s", body_preview)
        raise RuntimeError("Invalid response from chat completion endpoint") from exc

    try:
        assistant_message = data["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, AttributeError) as exc:
        raise RuntimeError(f"Invalid response from chat completion endpoint: {data!r}") from exc

    logger.info("Received assistant message from Hugging Face provider.")
    return assistant_message


def embedding_call(texts: List[str]) -> List[List[float]]:
    """Return embeddings for each text using the local Qwen embedding model."""
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
    if (
        _embedding_import_error is not None
        or torch is None
        or AutoTokenizer is None
        or AutoModel is None
        or F is None
    ):
        raise RuntimeError(
            "Local embedding model requires the `torch` and `transformers` packages. "
            "Install them to enable embeddings."
        ) from _embedding_import_error

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
