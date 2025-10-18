SG_LANG_BASE_URL = "http://127.0.0.1:8000/v1"
SG_LANG_API_KEY = ""

# Chat model (Qwen3 7B) exposed via the SGLang chat completions endpoint.
SG_LANG_CHAT_URL = f"{SG_LANG_BASE_URL}/chat/completions"
SG_LANG_CHAT_MODEL = "Qwen/Qwen3-7B-Instruct"

# Embeddings model (Qwen-embeddings) exposed via the SGLang embeddings endpoint.
SG_LANG_EMBEDDINGS_URL = f"{SG_LANG_BASE_URL}/embeddings"
SG_LANG_EMBEDDINGS_MODEL = "Qwen/Qwen-Embedding"

# Reranker model (Qwen3 Rerank 4B) exposed via the SGLang completions endpoint.
SG_LANG_RERANK_URL = f"{SG_LANG_BASE_URL}/completions"
SG_LANG_RERANK_MODEL = "Qwen/Qwen3-Rerank-4B"
