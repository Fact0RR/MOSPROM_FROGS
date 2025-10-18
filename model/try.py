from tools import RAG_call
from utils import build_rag_chunks_from_markdown
import os


def main():
    base_dir = os.path.dirname(__file__)
    md_path = os.path.join(base_dir, "synthetic_kb_QA_ALL.md")

    # 1) Подготовим чанки из синтетического markdown
    texts, metas = build_rag_chunks_from_markdown(
        md_path,
        chunk_mode="sections",
        chunk_size=800,
        overlap=200,
        use_tokens=False,
    )

    if not texts:
        print("No chunks produced. Check the file path or content.")
        return

    # 2) Простой запрос к RAG
    query = "Какие правила командировок и расходов?"
    try:
        results = RAG_call(query, data=texts, top_k=5)
    except Exception as exc:
        print("RAG_call failed:", exc)
        return

    # 3) Печать топ-результатов (скор, секция, фрагмент текста)
    print(f"Query: {query}")
    print(f"Chunks: {len(texts)} | TopK returned: {len(results)}")
    print("=" * 80)
    for i, r in enumerate(results, 1):
        score = r.get("score") or 0.0
        idx = r.get("chunk_id")
        section = None
        if isinstance(idx, int) and 0 <= idx < len(metas):
            section = metas[idx].get("section")
        print(f"#{i} | score={score:.4f} | section={section}")
        print((r.get("text") or "")[:300].replace("\n", " "))
        print("-" * 80)


if __name__ == "__main__":
    main()

