FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./

# Install CPU-only PyTorch first to avoid downloading CUDA wheels
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.10.0

RUN uv sync --frozen --no-dev --no-install-project

COPY api ./api
RUN uv sync --frozen --no-dev

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health/ || exit 1

CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
