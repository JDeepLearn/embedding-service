# Architecture & Deployment Overview

**Document:** ADR-001
**System:** Embedding Service

---

## Purpose

The **Embedding Service** provides standardized text embeddings for enterprise Retrieval-Augmented Generation (RAG) and FAQ search pipelines.
It is designed for **on-premises operation** — no external API calls or data egress — ensuring full data privacy and compliance.

---

## Architecture Summary

| Layer                                              | Responsibility                                                               |
|----------------------------------------------------|------------------------------------------------------------------------------|
| **API Layer** (`embedding_service.api`)            | Exposes REST endpoints `/embed`, `/health`, `/metrics` via FastAPI.          |
| **Provider Layer** (`embedding_service.providers`) | Abstract interface for embedding backends (Hugging Face, IBM Granite, etc.). |
| **Core Layer** (`embedding_service.core`)          | Cross-cutting services: configuration, JSON logging, Prometheus metrics.     |
| **App Entrypoint** (`embedding_service.main`)      | Bootstraps FastAPI app, sets up exception handlers and logging.              |
| **Tests** (`tests/`)                               | Full functional coverage (positive + negative).                              |

### Technology Stack

| Category           | Technology                                    |
|--------------------|-----------------------------------------------|
| Language           | Python 3.11                                   |
| Framework          | FastAPI 0.121.0                               |
| Dependency Manager | [uv](https://docs.astral.sh/uv/)              |
| Model Runtime      | SentenceTransformers (`intfloat/e5-large-v2`) |
| Observability      | JSON logging + Prometheus metrics             |
| Packaging          | Hatchling + Docker                            |
| CI/CD              | GitHub Actions (build, test, push image)      |

---

## Key Design Decisions

| #      | Decision                                       | Rationale                                                                          |
|--------|------------------------------------------------|------------------------------------------------------------------------------------|
| **D1** | **Provider Abstraction (`EmbeddingProvider`)** | Enables future models (IBM Granite, OpenAI) without changing routes or data flow.  |
| **D2** | **App Factory Pattern**                        | Allows test isolation, multiple deployments per process, and dependency injection. |
| **D3** | **JSON Logging**                               | Structured logs compatible with ELK, Datadog, CloudWatch; no third-party log deps. |
| **D4** | **Central Exception Handler**                  | Guarantees uniform error envelopes for all 4xx/5xx responses.                      |
| **D5** | **Prometheus Metrics**                         | Native `/metrics` endpoint for request count + latency histograms; zero overhead.  |
| **D6** | **One-Click Setup Script**                     | Ensures deterministic developer onboarding; same flow as CI builds.                |
| **D7** | **Containerization (Docker)**                  | Immutable runtime; identical between dev, CI, and prod.                            |
| **D8** | **CI/CD via GitHub Actions**                   | Automated build → test → image publish; ensures quality gates.                     |

---

## Deployment Overview

### 4.1 Local / Dev

```bash
bash setup_local.sh
```

* Verifies Python 3.11, installs `uv`, dependencies, `.env`, and launches at `http://localhost:8000`.

### 4.2 Docker

```bash
docker build -t embedding-service .
docker run -p 8000:8000 --env-file .env embedding-service
```

### 4.3 Production / Kubernetes

* Deploy container `embedding-service:latest` behind API gateway or ingress.
* Health probes:

  * **Liveness:** `/health`
  * **Readiness:** `/metrics`
* Logging: JSON stdout to centralized collector.
* Metrics: scrape `/metrics` via Prometheus or OTel sidecar.

---

## Observability & Reliability

| Capability             | Implementation                   | Integration                  |
|------------------------|----------------------------------|------------------------------|
| **Structured Logging** | JSON logs (stdout)               | ELK / Datadog                |
| **Metrics**            | Prometheus counters & histograms | Grafana, Prometheus          |
| **Tracing (future)**   | OTel bridge possible             | Jaeger / Tempo               |
| **Error Handling**     | Global exception handler         | Consistent 500/400 envelopes |
| **Health Checks**      | `/health`, `/metrics`            | Load-balancer probes         |

---

## Security & Compliance

* No outbound network calls (air-gapped safe).
* No credentials persisted in code or container.
* Environment variables via `.env` or Kubernetes Secrets.
* Supports API-key auth extension (optional).
* Log redaction enforced at app level.

---

## Testing & Quality Gates

* **Framework:** `pytest`
* **Coverage:** > 95 % lines, 100 % endpoint paths
* **Scenarios:**

  * Positive: `/health`, `/embed` single & batch
  * Negative: invalid input, empty payloads, internal exceptions
  * Observability: `/metrics` endpoint verification
* **CI/CD:** GitHub Actions blocks merge on failure.

---

## Performance Snapshot

| Metric            | Value              | Hardware                   |
|-------------------|--------------------|----------------------------|
| Model Load Time   | ~4 s               | Intel i7 / 32 GB RAM       |
| Inference Latency | 80 – 120 ms / text | CPU-only                   |
| Memory Footprint  | ~1.5 GB            | SentenceTransformer cached |

---

## Extensibility Roadmap

| Next Step           | Description                                   |
|---------------------|-----------------------------------------------|
| **GraniteProvider** | On-prem IBM Granite model integration         |
| **Auth Layer**      | API-Key / OAuth2 support for public exposure  |
| **GPU Runtime**     | Optional Torch CUDA build                     |
| **Tracing**         | OpenTelemetry spans for distributed debugging |
| **Model Registry**  | Versioned model selection via config or DB    |
