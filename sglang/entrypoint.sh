#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${SGLANG_CONFIG:-/app/config/models.yaml}"
MODELS_DIR="${SGLANG_MODELS_DIR:-/models}"
HF_TOKEN="${HF_TOKEN:-}"
EXTRA_ARGS=${SGLANG_EXTRA_ARGS:-}

echo "[entrypoint] Using config: ${CONFIG_PATH}"
python /app/scripts/download_models.py --config "${CONFIG_PATH}" --models-dir "${MODELS_DIR}" --token "${HF_TOKEN}"

CHAT_MODEL_PATH="${MODELS_DIR}/chat/Qwen3-8B-Q4_K_M.gguf"

if [[ ! -f "${CHAT_MODEL_PATH}" ]]; then
  echo "[entrypoint] Expected chat model missing at ${CHAT_MODEL_PATH}" >&2
  exit 1
fi

echo "[entrypoint] Launching SGLang OpenAI-compatible server on port ${SGLANG_PORT:-8000}"
exec python -m sglang.launch_server \
  --model-path "${CHAT_MODEL_PATH}" \
  --model-name "${SGLANG_CHAT_NAME:-chat}" \
  --port "${SGLANG_PORT:-8000}" \
  --host 0.0.0.0 \
  ${EXTRA_ARGS}
