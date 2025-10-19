"""Utility tools for the agent workflow: retrieval helpers and knowledge surfacing."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .local_calls import LLM_call, reranker_call  # type: ignore
except Exception:  # pragma: no cover - allow flat layout imports
    try:
        from local_calls import LLM_call, reranker_call  # type: ignore
    except Exception:
        LLM_call = None  # type: ignore
        reranker_call = None  # type: ignore

try:
    from .raptor.raptorRag import RaptorRagPipeline  # type: ignore
except Exception:  # pragma: no cover - fallback when running as flat package
    from raptor.raptorRag import RaptorRagPipeline  # type: ignore

try:
    from .State import EvidenceItem
except Exception:  # pragma: no cover - fallback
    from State import EvidenceItem  # type: ignore

try:
    from .prompts import get_rag_rephrase_prompt
except Exception:  # pragma: no cover - fallback
    from prompts import get_rag_rephrase_prompt  # type: ignore

logger = logging.getLogger(__name__)

_RAPTOR_PIPELINE: Optional[RaptorRagPipeline] = None
_RAPTOR_INDEX_PATH: Optional[Path] = None
_MAX_VARIANTS = 3  # original + two rewrites


def _load_raptor_pipeline(top_k: int) -> RaptorRagPipeline:
    """Load (or cache) the Raptor pipeline from the persisted knowledge base."""
    global _RAPTOR_PIPELINE, _RAPTOR_INDEX_PATH
    base_dir = Path(__file__).resolve().parent
    index_path = (base_dir / "raptorkb.pickle").resolve()

    if not index_path.exists():
        raise FileNotFoundError(
            f"Raptor knowledge base missing at {index_path}. "
            "Ensure build_kb has generated the pickle before using RAG tools."
        )

    if (_RAPTOR_PIPELINE is None) or (_RAPTOR_INDEX_PATH != index_path):
        _RAPTOR_PIPELINE = RaptorRagPipeline(index_path=index_path, retriever_top_k=top_k)
        _RAPTOR_INDEX_PATH = index_path
    return _RAPTOR_PIPELINE


def _retrieve_with_raptor(pipeline: RaptorRagPipeline, query: str, top_k: int) -> List[Dict[str, Any]]:
    """Run retrieval with the active pipeline and return chunk metadata without scoring."""
    _, layer_info = pipeline.retrieve(query, top_k=top_k, collapse_tree=True)

    results: List[Dict[str, Any]] = []
    for meta in layer_info[:top_k]:
        node_index = int(meta["node_index"])
        entry: Dict[str, Any] = {
            "text": pipeline.node_text(node_index),
            "chunk_id": node_index,
            "layer": int(meta.get("layer_number", -1)),
        }
        extra_meta = {
            key: value
            for key, value in meta.items()
            if key not in {"node_index", "layer_number"}
        }
        if extra_meta:
            entry["metadata"] = extra_meta
        results.append(entry)
    return results


def RAG_call(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Low-level retrieval call returning raw chunk metadata for downstream tooling."""
    pipeline = _load_raptor_pipeline(top_k)
    return _retrieve_with_raptor(pipeline, query, top_k)


def _coerce_doc_id(entry: Dict[str, Any]) -> str:
    metadata = entry.get("metadata")
    if isinstance(metadata, dict):
        doc_id = metadata.get("doc_id")
        if isinstance(doc_id, str) and doc_id.strip():
            return doc_id
    return f"kb-chunk-{entry['chunk_id']}"


def RAG_tool(query: str, top_k: int = 3) -> List[EvidenceItem]:
    """Convert retrieval results into EvidenceItems ranked via the reranker."""
    queries = _generate_query_variants(query)
    deduped_entries: Dict[Any, Dict[str, Any]] = {}

    for variant in queries:
        try:
            raw_results = RAG_call(variant, top_k=top_k)
        except Exception as exc:
            logger.warning("RAG_call failed for variant '%s': %s", variant, exc)
            continue

        for entry in raw_results:
            chunk_id = entry.get("chunk_id")
            if chunk_id is None:
                continue

            if chunk_id not in deduped_entries:
                deduped_entries[chunk_id] = entry
            else:
                existing = deduped_entries[chunk_id]
                if "metadata" in entry and isinstance(entry["metadata"], dict):
                    metadata = existing.setdefault("metadata", {})
                    if isinstance(metadata, dict):
                        metadata.update(entry["metadata"])

    if not deduped_entries:
        return []

    pooled_entries = list(deduped_entries.values())
    documents = [str(entry["text"]) for entry in pooled_entries]
    scores = reranker_call(query, documents)

    if len(scores) != len(pooled_entries):
        logger.warning(
            "Reranker returned %d scores for %d documents; missing entries default to 0.0",
            len(scores),
            len(pooled_entries),
        )

    ranked_entries: List[Tuple[Dict[str, Any], float]] = []
    for idx, entry in enumerate(pooled_entries):
        score = float(scores[idx]) if idx < len(scores) else 0.0
        ranked_entries.append((entry, score))

    ranked_entries.sort(key=lambda item: item[1], reverse=True)
    ranked_entries = ranked_entries[:top_k]

    evidence_items: List[EvidenceItem] = []
    for entry, score in ranked_entries:
        evidence_items.append(
            EvidenceItem(
                doc_id=_coerce_doc_id(entry),
                chunk_id=str(entry["chunk_id"]),
                text=str(entry["text"]),
                score=score,
            )
        )

    return evidence_items


def _generate_query_variants(query: str) -> List[str]:
    """Create a list containing the original query and up to two LLM-generated rewrites."""
    cleaned_query = (query or "").strip()
    variants: List[str] = [cleaned_query] if cleaned_query else []

    if not cleaned_query:
        return variants

    try:
        messages = get_rag_rephrase_prompt(cleaned_query)
        raw_response = LLM_call(messages)
        parsed = json.loads(raw_response)
        candidate_variants = parsed.get("variants", [])
    except Exception as exc:
        logger.warning("Failed to obtain query rephrasings: %s", exc)
        candidate_variants = []

    for candidate in candidate_variants:
        if len(variants) >= _MAX_VARIANTS:
            break
        if not isinstance(candidate, str):
            continue
        normalized = candidate.strip()
        if not normalized:
            continue
        if any(normalized.lower() == existing.lower() for existing in variants):
            continue
        variants.append(normalized)

    return variants or [cleaned_query]
