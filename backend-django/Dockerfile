FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

RUN uv run python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi", "-b", "0.0.0.0:8000", "-w", "4"]
