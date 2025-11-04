# syntax=docker/dockerfile:1

########################################
# Stage 1 — Build & Install Dependencies
########################################
FROM python:3.11-slim AS builder

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install curl + uv (modern dependency manager)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY embedding_service ./embedding_service

# Install dependencies in isolated env
RUN uv pip install --system .

########################################
# Stage 2 — Runtime Image
########################################
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"

# Copy runtime dependencies and app
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /app/embedding_service ./embedding_service
COPY --from=builder /app/README.md ./

# Copy environment template (optional)
COPY .env.example .env

# Expose API port
EXPOSE 8000

# Healthcheck (Docker native)
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# Launch FastAPI using uvicorn
CMD ["uv", "run", "uvicorn", "embedding_service.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]