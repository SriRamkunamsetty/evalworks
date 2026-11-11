FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn pydantic httpx pytest

COPY src/ ./src/
RUN pip install --no-cache-dir -e .

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/api/v1/health || exit 1

ENTRYPOINT ["uvicorn", "agenthijack.main:app", "--host", "0.0.0.0", "--port", "8004"]
