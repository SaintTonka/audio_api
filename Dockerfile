FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        gcc \
        python3-dev \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini .

RUN mkdir -p /app/static/audios && \
    chmod 777 /app/static/audios

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]