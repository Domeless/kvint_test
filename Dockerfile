FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    TZ=Etc/UTC \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY app/ ./app/
COPY tools/ ./tools/
COPY producer.py ./producer.py
RUN uv sync --locked --no-dev --no-editable && \
    groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --no-create-home app

USER app
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-config", "/app/app/logging.json"]
