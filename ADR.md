# **Architecture Decision Record (ADR-001): Granite Embedding Service**

---

## 1. Context

The organization requires an **on-premise, enterprise-grade embedding service** to power Retrieval-Augmented Generation (RAG) systems and AI knowledge products.
Key drivers include:

* **Data Sovereignty & Security:** No external API dependencies (all model inference must run locally).
* **Model Agnosticism:** Ability to switch between Granite, BGE, MiniLM, or other Hugging Face embedding models without code change.
* **Operational Excellence:** Support for observability, scalability, and clean deployment via container orchestration (Kubernetes / OpenShift).
* **Standardization:** Alignment with internal AI Service Framework and MCP (Model Context Protocol) integration standards.

---

## 2. Decision

### 2.1 Adopt a modular **FastAPI-based Embedding Microservice**

* Core framework: **FastAPI** for its async I/O model, OpenAPI schema generation, and performance.
* Each endpoint (`/embed`, `/info`, `/health`, `/metrics`) adheres to **enterprise REST standards** and emits **JSON-structured logs**.

### 2.2 Use **IBM Granite-Embedding-English-R2** as the primary foundation model

* Hosted locally via **Hugging Face Hub** download (`huggingface-cli download`).
* Supports fallback or alternative models via `MODEL_PATH` and `MODEL_NAME` environment variables.
* Model loaded using **SentenceTransformer** abstraction with **ModernBERT fallback** (`trust_remote_code=True`).

### 2.3 Design for **Offline / Air-Gapped Environments**

* All dependencies pre-installed; model files are mounted via Docker volume.
* No internet connectivity required at runtime.

### 2.4 Adopt a **12-Factor, Configuration-Driven Design**

* All tunables (batch size, truncation length, API key, CORS, metrics) are controlled through environment variables or `.env` files.
* `.env.example` provides standard operational defaults.
* Code uses Pydantic `BaseSettings` for typed validation and secure configuration loading.

### 2.5 Implement **Centralized Observability**

* Structured JSON logging (`logger.py`) for ingestion by ELK or Loki.
* Prometheus metrics via `/metrics` endpoint.
* Request correlation through `request_id` field.
* Docker-level `HEALTHCHECK` integrated with `/health`.

### 2.6 Enforce **Security and Compliance**

* Optional `X-API-Key` header authentication.
* CORS restrictions enforced through `CORS_ALLOW_ORIGINS` env variable.
* Explicit security disclaimer on `trust_remote_code` usage.
* No data persistence; stateless container design ensures clean restarts.

### 2.7 Ensure **Testability and CI/CD Integration**

* Full `pytest` suite validates API endpoints, model readiness, and input boundaries.
* Lightweight scaling benchmark built into tests.
* CI pipeline spins up service container, runs tests, and enforces health readiness.

### 2.8 Containerization Strategy

* Runtime built on **`python:3.12-slim`** for small footprint.
* Deterministic, reproducible builds via `pyproject.toml` and pinned dependencies.
* Stateless service that scales horizontally under orchestration.
* Optional health probes and Prometheus scraping configuration for Kubernetes.

---
## 3. Consequences

### 3.1 Positive Outcomes

* On-premise deployment with zero data leakage.
* Supports any Hugging Face embedding model without code change.
* Enterprise observability (Prometheus + JSON logs).
* Security features (API key, CORS, input limits).
* Simplified developer onboarding and maintainability.

### 4.2 Trade-Offs

* ⚠️ Slightly higher image size (~1.5–2 GB) due to PyTorch dependencies.
* ⚠️ Model load time (~5–15 s) on startup, mitigated by warm-up logic.
* ⚠️ `trust_remote_code=True` requires governance approval when using non-internal models.

---

## 5. Implementation Summary

| Component         | Description                                      |
| ----------------- | ------------------------------------------------ |
| **Language**      | Python 3.11+                                     |
| **Framework**     | FastAPI                                          |
| **Runtime**       | uvicorn with async I/O                           |
| **Config System** | Pydantic Settings (`config.py`)                  |
| **Logging**       | JSON via standard logger                         |
| **Model Loader**  | `SentenceTransformer` with ModernBERT fallback   |
| **Testing**       | `pytest`, `requests`, `numpy`                    |
| **Packaging**     | `pyproject.toml` (uv-compatible)                 |
| **Deployment**    | Docker (Python 3.12 slim base)                   |
| **Monitoring**    | Prometheus metrics, ELK logs                     |
| **Security**      | API-key header, input validation, no persistence |

---

## 6. Operational Lifecycle

| Phase        | Responsibility     | Artifacts                           |
| ------------ | ------------------ | ----------------------------------- |
| **Build**    | CI pipeline        | Docker image, test reports          |
| **Deploy**   | Platform Ops       | Kubernetes manifest / Helm chart    |
| **Monitor**  | SRE team           | Prometheus + Grafana dashboards     |
| **Evaluate** | AI Engineering     | Model metrics (nDCG, MRR, Recall@K) |
| **Upgrade**  | Architecture Board | Controlled via ADR versioning       |

---

## 7. Governance & Compliance

* Security review required before approving any model using `trust_remote_code=True`.
* Changes to core architecture (framework, model family, runtime base image) must result in a new ADR revision (ADR-002, ADR-003, etc.).
* Aligns with ISO 27001 and internal AI Model Lifecycle Management (MLLM) policy.

---

## 8. Future Enhancements

1. **Model Context Protocol (MCP) Integration** for standardized cross-module communication.
2. **Multi-model routing layer** (e.g., `/embed/{model}`) for online A/B testing.
3. **Automatic model warm-up** to reduce startup latency.
4. **Optional gRPC interface** for low-latency inference workloads.
5. **Fine-tuning pipeline** for domain-specific embeddings (insurance, finance, etc.).

---

## 9. References

* [IBM Granite Embedding R2 Model Card](https://huggingface.co/ibm-granite/granite-embedding-english-r2)
* [FastAPI Documentation](https://fastapi.tiangolo.com)
* [Sentence-Transformers Docs](https://www.sbert.net)
* [Hugging Face Transformers](https://huggingface.co/docs/transformers)
* [Twelve-Factor App Principles](https://12factor.net)
* [OpenTelemetry / Prometheus Standards](https://opentelemetry.io)

---

## 10. Decision Summary

| Category          | Decision                                |
| ----------------- | --------------------------------------- |
| **Architecture**  | Modular FastAPI microservice            |
| **Model**         | IBM Granite Embedding English R2        |
| **Deployment**    | Docker + Kubernetes                     |
| **Observability** | Prometheus + JSON logs                  |
| **Security**      | API key + CORS + offline mode           |
| **Extensibility** | Model-agnostic, fallback-aware          |
| **Compliance**    | ISO 27001 / AI lifecycle policy aligned |

---

**Final Decision:**

> Deploy and standardize the **Granite Embedding Service** as the enterprise embedding microservice architecture for all RAG and knowledge retrieval workloads.
> Future model upgrades or architectural shifts will require ADR revision approval.

---