FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && pip install --no-cache-dir redis psycopg2 \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /var/lib/apt/lists/*
    
COPY src/ .

CMD ["python", "main_mock.py"]