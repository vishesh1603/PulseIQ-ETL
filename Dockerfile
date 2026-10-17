FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install dependencies first so Docker can cache this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts ./scripts
COPY tests ./tests
COPY docs ./docs
COPY sql ./sql

# Default command: run the pipeline.
CMD ["python", "-m", "pulseiq_etl"]
