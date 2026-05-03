FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-hf-local.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-hf-local.txt \
    && python -m pip install redis psycopg2-binary

COPY app ./app
COPY scripts ./scripts
COPY models ./models
COPY inputs ./inputs
COPY templates ./templates
COPY main.py ./
COPY .env.example ./

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["python", "main.py"]
CMD ["--project", "ssms", "--semver", "v0.1.0"]