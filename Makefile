.PHONY: install run build test lint fmt

install:
\tuv pip install --system .

run:
\tuvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload

build:
\tdocker build -t embedding-service:local .

test:
\tpytest -q --disable-warnings

lint:
\truff check .
\tmypy app

fmt:
\truff format .
