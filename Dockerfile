FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates tini && \
    rm -rf /var/lib/apt/lists/*

# Fast installer
RUN pip install --no-cache-dir uv==0.3.2

WORKDIR /app
COPY pyproject.toml ./
RUN uv pip install --system .

COPY app ./app

# Security: non-root
RUN useradd -m appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8000/health || exit 1
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["uvicorn","app.main:create_app","--factory","--host","0.0.0.0","--port","8000","--workers","2"]
