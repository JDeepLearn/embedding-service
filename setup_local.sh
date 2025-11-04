#!/usr/bin/env bash
set -e

echo "🚀 Setting up Embedding Service locally..."

# --- Check Python version ---
if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 not found. Please install Python 3.11+ first."
  exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$PY_VERSION" < "3.11" ]]; then
  echo "❌ Python 3.11+ required. Found $PY_VERSION"
  exit 1
fi

# --- Install uv if missing ---
if ! command -v uv &> /dev/null; then
  echo "📦 Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# --- Create venv ---
if [ ! -d ".venv" ]; then
  echo "🧱 Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

# --- Install project dependencies ---
echo "📦 Installing dependencies..."
uv pip install --upgrade pip
uv pip install -e .

# --- Copy environment file if needed ---
if [ ! -f ".env" ]; then
  echo "🧾 Copying .env.example to .env..."
  cp .env.example .env
fi

# --- Launch the app ---
echo "🚀 Starting Embedding Service at http://localhost:8000 ..."
uv run uvicorn embedding_service.main:create_app --factory --host 0.0.0.0 --port 8000