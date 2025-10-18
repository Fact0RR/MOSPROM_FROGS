"""Utility tools and placeholders for the agent workflow."""


import os
import math
import pickle
import re
from typing import List, Dict, Any, Optional, Union



SBertEmbeddingModel = None
FaissRetriever = None
FaissRetrieverConfig = None
RaptorRagPipeline = None



try:
    # Prefer absolute import when running from the model directory
    from local_calls import embedding_call  # type: ignore
except Exception:
    try:
        # Fallback to package-relative import when used as a module
        from .local_calls import embedding_call  # type: ignore
    except Exception:
        embedding_call = None  # type: ignore

_import_candidates = [
    ("model.raptor.EmbeddingModels", "SBertEmbeddingModel"),
    ("raptor.EmbeddingModels", "SBertEmbeddingModel"),
    ("model.raptor.EmbeddingModel", "SBertEmbeddingModel"),
]
for mod, cls in _import_candidates:
    try:
        m = __import__(mod, fromlist=[cls])
        SBertEmbeddingModel = getattr(m, cls)
        break
    except Exception:
        SBertEmbeddingModel = None

_retriever_candidates = [
    ("model.raptor.FaissRetriever", ("FaissRetriever", "FaissRetrieverConfig")),
    ("raptor.FaissRetriever", ("FaissRetriever", "FaissRetrieverConfig")),
    ("model.raptor.retriever", ("FaissRetriever", "FaissRetrieverConfig")),
]
for mod, names in _retriever_candidates:
    try:
        m = __import__(mod, fromlist=list(names))
        FaissRetriever = getattr(m, names[0])
        FaissRetrieverConfig = getattr(m, names[1])
        break
    except Exception:
        FaissRetriever = None
        FaissRetrieverConfig = None



_pipeline_candidates = [
    ("model.raptor.raptorRag", "RaptorRagPipeline"),
    ("raptor.raptorRag", "RaptorRagPipeline"),
    ("model.raptor.raptor_rag", "RaptorRagPipeline"),
    ("raptor.raptorRag", "RaptorRagPipeline"),
]
for mod, cls in _pipeline_candidates:
    try:
        m = __import__(mod, fromlist=[cls])
        RaptorRagPipeline = getattr(m, cls)
        break
    except Exception:
        RaptorRagPipeline = None



def _smart_chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + 1 + len(p) <= chunk_size:
            current = (current + "\n\n" + p).strip() if current else p
        else:
            if current:
                chunks.append(current)
            if len(p) > chunk_size:
                sents = re.split(r'(?<=[.!?])\s+', p)
                cur2 = ""
                for s in sents:
                    if len(cur2) + 1 + len(s) <= chunk_size:
                        cur2 = (cur2 + " " + s).strip() if cur2 else s
                    else:
                        if cur2:
                            chunks.append(cur2)
                        if len(s) > chunk_size:
                            for i in range(0, len(s), chunk_size - overlap):
                                chunks.append(s[i:i + chunk_size])
                            cur2 = ""
                        else:
                            cur2 = s
                if cur2:
                    chunks.append(cur2)
                current = ""
            else:
                current = p
    if current:
        chunks.append(current)

    
    merged = []
    i = 0
    while i < len(chunks):
        block = chunks[i]
        j = i + 1
        while j < len(chunks) and len(block) < chunk_size:
            if len(block) + 1 + len(chunks[j]) <= chunk_size:
                block = block + "\n\n" + chunks[j]
                j += 1
            else:
                break
        merged.append(block)
        i = j

    if overlap > 0 and len(merged) > 1:
        final = []
        for idx, m in enumerate(merged):
            if idx == 0:
                final.append(m)
            else:
                prev = final[-1]
                tail = prev[-overlap:] if len(prev) >= overlap else prev
                final.append((tail + "\n\n" + m).strip())
        return final
    return merged

def _extract_texts_from_pickle(obj: Any) -> List[str]:
    if obj is None:
        return []
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        for k in ("chunks", "documents", "items", "texts"):
            if k in obj and isinstance(obj[k], (list, tuple)):
                obj_list = obj[k]
                break
        else:
            maybe = []
            for v in obj.values():
                if isinstance(v, str):
                    maybe.append(v)
            return maybe if maybe else [str(obj)]
    elif isinstance(obj, (list, tuple)):
        obj_list = list(obj)
    else:
        return [str(obj)]

    texts = []
    for it in obj_list:
        if isinstance(it, str):
            texts.append(it)
        elif isinstance(it, dict):
            for key in ("text", "content", "chunk", "body"):
                if key in it and isinstance(it[key], str):
                    texts.append(it[key])
                    break
            else:
                texts.append(str(it))
        elif isinstance(it, (list, tuple)):
            candidate = next((x for x in it if isinstance(x, str)), None)
            if candidate:
                texts.append(candidate)
            else:
                texts.append(str(it))
        else:
            texts.append(str(it))
    return texts




from .State import EvidenceItem


def RAG_tool(query: str, top_k: int = 3) -> List[EvidenceItem]:
    """Placeholder for the RAG tool implementation returning evidence items."""
    return [
        EvidenceItem(
            doc_id=f"placeholder-doc-{i + 1}",
            chunk_id=str(i),
            text=f"Placeholder chunk {i + 1} for query: {query}",
            score=1.0,
        )
        for i in range(top_k)
    ]


def RAG_call(query: str,
             data: Optional[Union[str, List[str], Dict[str, str]]] = None,
             top_k: int = 5,
             sbert_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
             chunk_size: int = 800,
             overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Унифицированная реализация RAG_call для проекта.
    - query: строка-запрос
    - data: путь/строка/список/словарь filename->content
    Возвращает: список словарей {"text":..., "score":..., "file":..., "chunk_id":...}
    """

    
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []

    if data is None:
        return []

    if isinstance(data, str) and os.path.exists(data):
        try:
            with open(data, "rb") as fh:
                obj = pickle.load(fh)
            txts = _extract_texts_from_pickle(obj)
            for i, t in enumerate(txts):
                texts.append(t)
                metas.append({"file": os.path.basename(data), "chunk_id": i})
        except Exception:
            with open(data, "r", encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
            chunks = _smart_chunk_text(txt, chunk_size=chunk_size, overlap=overlap)
            for i, c in enumerate(chunks):
                texts.append(c)
                metas.append({"file": os.path.basename(data), "chunk_id": i})

    elif isinstance(data, str):
        chunks = _smart_chunk_text(data, chunk_size=chunk_size, overlap=overlap)
        for i, c in enumerate(chunks):
            texts.append(c)
            metas.append({"file": None, "chunk_id": i})

    elif isinstance(data, (list, tuple)):
        for i, it in enumerate(data):
            texts.append(str(it))
            metas.append({"file": None, "chunk_id": i})

    elif isinstance(data, dict):
        for fname, content in data.items():
            chunks = _smart_chunk_text(content, chunk_size=chunk_size, overlap=overlap)
            for j, c in enumerate(chunks):
                texts.append(c)
                metas.append({"file": fname, "chunk_id": j})

    if not texts:
        return []

    
    if RaptorRagPipeline is not None:
        
        pipeline = RaptorRagPipeline()
        if hasattr(pipeline, "retrieve") or hasattr(pipeline, "query"):
            
            if hasattr(pipeline, "retrieve"):
                raw = pipeline.retrieve(query, top_k)
            else:
                raw = pipeline.query(query, top_k)
            
            raw_res = raw
            
        elif hasattr(pipeline, "run"):
            raw_res = pipeline.run(query=query, documents=texts, top_k=top_k)
        else:
            
            if hasattr(pipeline, "build_from_texts"):
                pipeline.build_from_texts(texts)
                raw_res = pipeline.query(query, top_k=top_k)
            else:
                
                raw_res = None
    else:
        raw_res = None

    # Embedding-based cosine similarity fallback using embedding_call
    if raw_res is None and embedding_call is not None:
        try:
            doc_embs = embedding_call(texts)  # List[List[float]]
            if not doc_embs:
                return []
            query_embs = embedding_call([query])
            if not query_embs:
                return []
            query_emb = query_embs[0]
        except Exception as exc:
            raise RuntimeError("Embedding_call failed") from exc

        def _dot(a, b):
            return sum((float(x) * float(y)) for x, y in zip(a, b))

        def _norm(a):
            val = _dot(a, a)
            return math.sqrt(val) if val > 0 else 1e-12

        qn = _norm(query_emb)
        scored = []
        for i, emb_vec in enumerate(doc_embs):
            try:
                score = _dot(query_emb, emb_vec) / (qn * _norm(emb_vec))
            except Exception:
                score = 0.0
            scored.append((i, float(score)))

        scored.sort(key=lambda t: t[1], reverse=True)
        raw_res = scored[:top_k]

    
    if raw_res is None:
        if SBertEmbeddingModel is None or FaissRetriever is None or FaissRetrieverConfig is None:
            raise RuntimeError("Не найдены локальные SBertEmbeddingModel / FaissRetriever в проекте. Проверь model/raptor/ и __init__.py импорты.")
        emb = SBertEmbeddingModel(model_name=sbert_model_name)
        retr_cfg = FaissRetrieverConfig(embedding_model=emb, top_k=top_k)
        retr = FaissRetriever(retr_cfg)
        
        if hasattr(retr, "build_from_texts"):
            retr.build_from_texts(texts)
        elif hasattr(retr, "index_texts"):
            retr.index_texts(texts)
        elif hasattr(retr, "index"):
            retr.index(texts)
        else:
            
            retr.build(texts)
        raw_res = retr.query(query, top_k=top_k)

    
    out: List[Dict[str, Any]] = []

    
    if isinstance(raw_res, (list, tuple)) and raw_res and all(isinstance(x, int) for x in raw_res):
        for idx in raw_res[:top_k]:
            if 0 <= idx < len(texts):
                out.append({"text": texts[idx], "score": None, "file": metas[idx].get("file"), "chunk_id": metas[idx].get("chunk_id")})
        return out

    
    if isinstance(raw_res, (list, tuple)) and raw_res and all(isinstance(x, (list, tuple)) for x in raw_res):
        for item in raw_res[:top_k]:
            if len(item) >= 2 and isinstance(item[0], int):
                idx, score = item[0], item[1]
                out.append({"text": texts[idx], "score": float(score) if isinstance(score,(int,float)) else None, "file": metas[idx].get("file"), "chunk_id": metas[idx].get("chunk_id")})
            elif len(item) >= 2 and isinstance(item[0], str):
                text = item[0]; score = item[1] if isinstance(item[1], (int,float)) else None
                try:
                    idx = texts.index(text)
                except ValueError:
                    idx = None
                if idx is not None:
                    out.append({"text": text, "score": score, "file": metas[idx].get("file"), "chunk_id": metas[idx].get("chunk_id")})
                else:
                    out.append({"text": text, "score": score, "file": None, "chunk_id": None})
            else:
                out.append({"text": str(item), "score": None, "file": None, "chunk_id": None})
        return out

    
    if isinstance(raw_res, (list, tuple)):
        for item in raw_res[:top_k]:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("doc") or None
                score = item.get("score") or item.get("distance") or None
                if text is None and (item.get("index") is not None or item.get("idx") is not None):
                    idx = item.get("index") or item.get("idx")
                    if isinstance(idx, int) and 0 <= idx < len(texts):
                        out.append({"text": texts[idx], "score": score, "file": metas[idx].get("file"), "chunk_id": metas[idx].get("chunk_id")})
                    else:
                        out.append({"text": str(item), "score": score, "file": None, "chunk_id": None})
                else:
                    if text is not None:
                        try:
                            idx = texts.index(text)
                        except ValueError:
                            idx = None
                        if idx is not None:
                            out.append({"text": text, "score": score, "file": metas[idx].get("file"), "chunk_id": metas[idx].get("chunk_id")})
                        else:
                            out.append({"text": text, "score": score, "file": None, "chunk_id": None})
                    else:
                        out.append({"text": str(item), "score": score, "file": None, "chunk_id": None})
            elif isinstance(item, str):
                try:
                    idx = texts.index(item)
                except ValueError:
                    idx = None
                if idx is not None:
                    out.append({"text": texts[idx], "score": None, "file": metas[idx].get("file"), "chunk_id": metas[idx].get("chunk_id")})
                else:
                    out.append({"text": item, "score": None, "file": None, "chunk_id": None})
            else:
                out.append({"text": str(item), "score": None, "file": None, "chunk_id": None})
        return out

    0
    return [{"text": str(raw_res), "score": None, "file": None, "chunk_id": None}]
