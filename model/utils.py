"""Utility helpers for maintaining the local Raptor knowledge base."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

try:
    from .local_calls import embedding_call  # type: ignore
except Exception:  # pragma: no cover - allow flat module usage
    try:
        from local_calls import embedding_call  # type: ignore
    except Exception:  # pragma: no cover - embedding API unavailable
        embedding_call = None  # type: ignore

from .raptor import (
    RetrievalAugmentation,
    RetrievalAugmentationConfig,
)
from .raptor.QAModels import GPT3TurboQAModel
from .raptor.SummarizationModels import GPT3TurboSummarizationModel
from .raptor.EmbeddingModels import BaseEmbeddingModel

logger = logging.getLogger(__name__)


class _HFEmbeddingModel(BaseEmbeddingModel):
    """Adapter that routes embedding requests to the Hugging Face embedding endpoint."""

    def __init__(self) -> None:
        self._call_count = 0

    def create_embedding(self, text: str):
        if embedding_call is None:
            raise RuntimeError("Hugging Face embedding endpoint is not configured.")
        self._call_count += 1
        request_id = self._call_count
        logger.debug(
            "Requesting embedding %d (text length=%d)", request_id, len(text or "")
        )
        try:
            result = embedding_call([text])[0]
        except Exception:
            logger.exception(
                "Embedding request %d failed (text length=%d)",
                request_id,
                len(text or ""),
            )
            raise
        logger.debug("Embedding request %d succeeded", request_id)
        return result


def build_raptor_tree(chunks: Sequence[str], output_path: str | Path) -> Path:
    """Build a Raptor tree from the provided text chunks and persist it to disk."""
    if embedding_call is None:
        raise RuntimeError("Hugging Face embedding endpoint is not configured.")

    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    text = "\n\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())

    logger.info(
        "Starting Raptor tree build with %d text chunks; output=%s",
        sum(1 for chunk in chunks if chunk and chunk.strip()),
        path,
    )
    config = RetrievalAugmentationConfig(
        embedding_model=_HFEmbeddingModel(),
        summarization_model=GPT3TurboSummarizationModel(),
        qa_model=GPT3TurboQAModel(),
    )
    pipeline = RetrievalAugmentation(config=config)
    pipeline.add_documents(text)
    pipeline.save(str(path))
    return path
