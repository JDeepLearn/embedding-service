# syntax=docker/dockerfile:1

########################################
# Stage 1 — Build environment
########################################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install curl + uv
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY embedding_service ./embedding_service

# Install dependencies inside the builder
RUN uv pip install --system .

########################################
# Stage 2 — Runtime image
########################################
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy runtime dependencies and app
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /app/embedding_service ./embedding_service
COPY --from=builder /app/README.md ./

# Copy environment example
COPY .env.example .env

EXPOSE 8000

# Healthcheck — calls FastAPI /health
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# Run with standard uvicorn (uv is not needed at runtime)
CMD ["python", "-m", "uvicorn", "embedding_service.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
