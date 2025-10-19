"""Lightweight Raptor pipeline wrapper that relies on the local embedder."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Tuple

try:
    from ..local_calls import embedding_call  # type: ignore
except Exception:  # pragma: no cover - fallback for runtime package usage
    try:
        from local_calls import embedding_call  # type: ignore
    except Exception:  # pragma: no cover - embedding API unavailable
        embedding_call = None  # type: ignore

from .EmbeddingModels import BaseEmbeddingModel
from .QAModels import BaseQAModel
from .RetrievalAugmentation import RetrievalAugmentation, RetrievalAugmentationConfig
from .SummarizationModels import BaseSummarizationModel


class _LocalEmbeddingModel(BaseEmbeddingModel):
    """Adapter that proxies embedding requests to the local embedding endpoint."""

    def create_embedding(self, text: str) -> List[float]:
        if embedding_call is None:
            raise RuntimeError("Local embedding endpoint is not configured.")
        return embedding_call([text])[0]


class _NoOpSummarizationModel(BaseSummarizationModel):
    """Summarizer stub to satisfy the pipeline dependencies."""

    def summarize(self, context, max_tokens: int = 150):  # type: ignore[override]
        return context


class _NoOpQAModel(BaseQAModel):
    """Question-answering stub; we only need retrieval for this pipeline."""

    def answer_question(self, context, question):  # type: ignore[override]
        return ""


class RaptorRagPipeline:
    """Convenience wrapper that loads a pre-built Raptor tree and exposes retrieval helpers."""

    def __init__(
        self,
        *,
        index_path: str | Path,
        retriever_top_k: int = 10,
    ) -> None:
        resolved_path = Path(index_path).expanduser().resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"Raptor index not found: {resolved_path}")

        self._embedding_model = _LocalEmbeddingModel()
        self._config = RetrievalAugmentationConfig(
            embedding_model=self._embedding_model,
            summarization_model=_NoOpSummarizationModel(),
            qa_model=_NoOpQAModel(),
            tr_top_k=retriever_top_k,
        )
        self._ra = RetrievalAugmentation(config=self._config, tree=str(resolved_path))
        if self._ra.retriever is None:
            raise RuntimeError("Failed to initialize Raptor retriever from index.")

        self._retriever = self._ra.retriever
        self._embedding_key = self._retriever.context_embedding_model

    @property
    def embedding_model(self) -> _LocalEmbeddingModel:
        return self._embedding_model

    @property
    def embedding_key(self) -> str:
        return self._embedding_key

    def retrieve(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        max_tokens: int = 3500,
        collapse_tree: bool = True,
    ) -> Tuple[str, List[dict]]:
        """Return concatenated context and layer metadata for the requested query."""
        active_top_k = top_k if top_k is not None else self._retriever.top_k
        return self._retriever.retrieve(
            query,
            top_k=active_top_k,
            max_tokens=max_tokens,
            collapse_tree=collapse_tree,
            return_layer_information=True,
        )

    def node_text(self, node_index: int) -> str:
        return self._retriever.tree.all_nodes[node_index].text

    def node_embedding(self, node_index: int) -> Optional[List[float]]:
        embeddings = self._retriever.tree.all_nodes[node_index].embeddings
        return embeddings.get(self._embedding_key)

    def iter_nodes(self, node_indices: Iterable[int]):
        tree = self._retriever.tree.all_nodes
        for idx in node_indices:
            node = tree[idx]
            yield idx, node
