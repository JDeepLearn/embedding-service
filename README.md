# Embedding Service

A **production-ready, on-premise embedding microservice** built with **FastAPI** and **Hugging Face Transformers**.
It supports any SentenceTransformer- or Transformer-based model (including **IBM Granite R2**)
and produces normalized dense embeddings for enterprise retrieval systems.

---

## Features

* Works with **any embedding model** (`SentenceTransformer` / `ModernBERT` / `Granite` family)
* **Local/offline model loading** (no internet dependency)
* Configurable via **environment variables**
* **JSON-structured logging** for observability
* **Prometheus metrics** and `/health`, `/info` endpoints
* **API-key security** (optional)
* Clean separation of config, routes, and domain logic
* Ready for CPU or GPU deployment

---

## Architecture Overview

```
FastAPI App
 ├── /embed   → generate embeddings
 ├── /info    → model & service info
 ├── /health  → health check
 ├── /metrics → Prometheus metrics (optional)
 └── Global exception handling + JSON logs
```

---

## Requirements

| Component             | Version  | Purpose           |
| --------------------- | -------- | ----------------- |
| Python                | ≥ 3.11   | Runtime           |
| Transformers          | ≥ 4.46.2 | Model loading     |
| Sentence-Transformers | ≥ 3.3.1  | Embedding wrapper |
| PyTorch               | ≥ 2.5.0  | Backend           |
| FastAPI               | ≥ 0.115  | API framework     |

---

## 1. Setup & Installation

Clone the repo and install dependencies with [uv](https://github.com/astral-sh/uv):

```bash
git clone https://github.com/JDeepLearn/embedding-service.git
cd embedding-service

# Install using uv
uv pip install -e .
```

---

## 2. Download Model Locally

The service expects models to be **available on the local filesystem** (`MODEL_PATH`).
Use the Hugging Face CLI to download the model before starting the service.

### Example: IBM Granite English R2

```bash
# Download and store locally
huggingface-cli download ibm-granite/granite-embedding-english-r2 \
  --local-dir /opt/models/granite-embedding-english-r2 \
  --local-dir-use-symlinks False
```

### Example: MiniLM baseline

```bash
huggingface-cli download sentence-transformers/all-MiniLM-L6-v2 \
  --local-dir /opt/models/all-MiniLM-L6-v2 \
  --local-dir-use-symlinks False
```

After downloading, update `.env` accordingly:

```bash
MODEL_NAME=granite-embedding-english-r2
MODEL_PATH=/opt/models/granite-embedding-english-r2
DEVICE=auto
LOG_LEVEL=INFO
```

---

## 3. Configuration (Environment Variables)

| Variable                | Description                              | Default                                  |
| ----------------------- | ---------------------------------------- | ---------------------------------------- |
| `MODEL_NAME`            | Model identifier (HF repo or local name) | granite-embedding-english-r2             |
| `MODEL_PATH`            | Filesystem path to model                 | /opt/models/granite-embedding-english-r2 |
| `DEVICE`                | `auto`, `cpu`, or `cuda`                 | auto                                     |
| `EMBED_BATCH_SIZE`      | Batch size for encoding                  | 32                                       |
| `MAX_SEQ_LENGTH`        | Token truncation length                  | 512                                      |
| `API_KEY`               | Optional API key for auth                | None                                     |
| `CORS_ALLOW_ORIGINS`    | Comma-separated origins for CORS         | None                                     |
| `MAX_TEXTS_PER_REQUEST` | Max texts per call                       | 64                                       |
| `MAX_CHARS_PER_TEXT`    | Max chars per text                       | 4000                                     |
| `MAX_TOTAL_CHARS`       | Max chars per batch                      | 256 000                                  |
| `METRICS_ENABLED`       | Expose `/metrics` if true                | True                                     |

You can also define these in a `.env` file in the project root.

---

## 4. Running Locally (via uv)

```bash
uv run uvicorn embedding_service.main:app --host 0.0.0.0 --port 8000
```

Check it’s working:

```bash
curl -X GET http://localhost:8000/health
```

Example embedding request:

```bash
curl -X POST "http://localhost:8000/embed" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": ["How to reset my password?", "Submit an insurance claim online."]
  }'
```

---

## 5. Running in Docker

### Build

```bash
docker build -t embedding-service:1.0 .
```

### Run (with model volume mounted)

```bash
docker run --rm \
  -p 8000:8000 \
  -e MODEL_NAME=granite-embedding-english-r2 \
  -e MODEL_PATH=/models/granite-embedding-english-r2 \
  -e DEVICE=auto \
  -v /opt/models/granite-embedding-english-r2:/models/granite-embedding-english-r2:ro \
  granite-embedding-service:1.0
```

The container logs will output structured JSON like:

```json
{"event": "embed_success", "request_id": "abcd1234", "num_inputs": 2, "latency_ms": 35}
```

---

## 6. Using Different Models

To switch models, simply change your environment variables and restart the service.

### Example: use BAAI BGE-base-EN

```bash
huggingface-cli download BAAI/bge-base-en \
  --local-dir /opt/models/bge-base-en \
  --local-dir-use-symlinks False

export MODEL_NAME=bge-base-en
export MODEL_PATH=/opt/models/bge-base-en
uv run uvicorn embedding_service.main:app --port 8000
```

No code changes required.

---

## 7. Observability

### Metrics

* `/metrics` (Prometheus format)
* Histograms:

  * `embedding_request_latency_seconds`
  * `embedding_text_length_chars`
  * `embedding_request_payload_chars`

### Logging

* Structured JSON lines to stdout
* Correlated via `X-Request-ID` header
* Example:

  ```json
  {"event":"embed_start","request_id":"9f7b...","num_inputs":2,"model":"granite-embedding-english-r2"}
  ```

---

## 8. Security

* Optional **API-key enforcement** (`API_KEY` env)
* **CORS control** for web clients (`CORS_ALLOW_ORIGINS`)
* **No outbound requests** (fully offline capable)
* Explicit warning for `trust_remote_code=True` — ensure models are from trusted internal or verified HF sources.

---

## 9. Health, Info & Diagnostics

| Endpoint   | Purpose                  |
| ---------- | ------------------------ |
| `/health`  | Liveness check           |
| `/info`    | Model + service metadata |
| `/metrics` | Prometheus metrics       |
| `/embed`   | Embedding inference      |

Example `/info` response:

```json
{
  "model_name": "granite-embedding-english-r2",
  "model_version": "1.0.0",
  "embedding_dim": 1024,
  "device": "cuda",
  "service_version": "1.5.0",
  "max_texts_per_request": 64,
  "max_chars_per_text": 4000,
  "max_total_chars": 256000,
  "batch_size": 32,
  "max_seq_length": 512,
  "metrics_enabled": true,
  "log_level": "INFO",
  "generated_at": "2025-11-07T20:00:00Z"
}
```

---

## 10. Troubleshooting

| Issue                                          | Possible Cause               | Fix                            |
| ---------------------------------------------- | ---------------------------- | ------------------------------ |
| `The checkpoint ... model type modernbert ...` | Transformers version too old | Upgrade `transformers>=4.46.2` |
| `no such directory for model_path`             | MODEL_PATH incorrect         | Check env or mount path        |
| CUDA not available                             | GPU missing / driver issue   | Use `DEVICE=cpu`               |
| Slow performance                               | Too small batch size         | Increase `EMBED_BATCH_SIZE`    |
| OOM on GPU                                     | Too large batch size         | Reduce `EMBED_BATCH_SIZE`      |

---

## 🏁 11. License & Attribution

* IBM Granite models © IBM Research, licensed under the terms in their [Hugging Face model card](https://huggingface.co/ibm-granite/granite-embedding-english-r2).
* Other models follow their respective licenses.

---