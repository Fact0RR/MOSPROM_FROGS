"""Centralized configuration for Hugging Face-powered model service."""

from __future__ import annotations

import os
from typing import Optional

# --- Hugging Face Inference settings ----------------------------------------------------------
# All calls now go through Hugging Face-hosted (or compatible) endpoints. Configure credentials
# and model choices via environment variables or a local .env file.

HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
HF_API_BASE_URL: Optional[str] = os.getenv("HF_API_BASE_URL") or None

# Use a lightweight Qwen3 "thinking" model by default for proof-of-concept reasoning flows.
HF_CHAT_MODEL: str = os.getenv("HF_CHAT_MODEL", "Qwen/Qwen3-8B:nscale")
HF_CHAT_TEMPERATURE: float = float(os.getenv("HF_CHAT_TEMPERATURE", "0.7"))

_raw_max_tokens = os.getenv("HF_CHAT_MAX_OUTPUT_TOKENS", "").strip()
HF_CHAT_MAX_OUTPUT_TOKENS: Optional[int] = int(_raw_max_tokens) if _raw_max_tokens else None

HF_EMBEDDING_MODEL: str = os.getenv("HF_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
# Reranking currently relies on cosine similarity over embeddings; allow an override so teams can plug
# in a dedicated reranker model if desired.
HF_RERANK_MODEL: str = os.getenv(
    "HF_RERANK_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

HF_TIMEOUT: float = float(os.getenv("HF_TIMEOUT", "60"))
HF_MAX_RETRIES: int = int(os.getenv("HF_MAX_RETRIES", "3"))
