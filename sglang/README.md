# SGLang Service Container

This directory contains a CUDA-enabled Docker image that prepares the
models required by the workflow service (`model/local_calls.py`) and
starts an OpenAI-compatible SGLang server on port `8000`.

## Contents

- `Dockerfile` – GPU base image with Python, SGLang, and helper tools.
- `requirements.txt` – Runtime Python dependencies installed into the image.
- `models.yaml` – Declarative list of models to download at container start.
- `scripts/download_models.py` – Downloads the weights from Hugging Face based on `models.yaml`.
- `entrypoint.sh` – Downloads the weights and launches the SGLang server.

## Usage

```bash
docker build -f sglang/Dockerfile -t frogs-sglang ./sglang

docker run --rm \
  --gpus all \
  -p 8000:8000 \
  -e HF_TOKEN=<your_hf_access_token_if_needed> \
  -v /srv/models:/models \
  frogs-sglang
```

The first run downloads the model files declared in `models.yaml` into
`/models/<name>/...`. Mounting a host directory keeps the cache between runs.

### Environment variables

- `HF_TOKEN` – Optional Hugging Face token for gated model access.
- `SGLANG_PORT` – Port exposed by the SGLang server (default `8000`).
- `SGLANG_CHAT_NAME` – Friendly name registered for the chat model (default `chat`).
- `SGLANG_EXTRA_ARGS` – Additional CLI flags appended to the launch command.

### Extending the launch command

`entrypoint.sh` currently launches the chat model. Embedding and reranker
support may require additional SGLang CLI flags or parallel processes,
depending on how you want to expose them. Override the command when
starting the container to provide a custom launch procedure, for example:

```bash
docker run --rm --gpus all frogs-sglang \
  python -m sglang.launch_server \
    --model-path /models/chat/Qwen3-8B-Q4_K_M.gguf \
    --model-name chat \
    --port 8000 --host 0.0.0.0
```

Refer to the official SGLang documentation for advanced multi-model
configurations (embedding and reranker servers) and adjust `entrypoint.sh`
as needed.
