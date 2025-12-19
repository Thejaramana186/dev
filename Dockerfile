
FROM python:3.11-slim AS builder

WORKDIR /app


COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY app/ ./app


FROM python:3.11-slim

WORKDIR /app


COPY --from=builder /usr/local /usr/local


COPY app/ ./app


EXPOSE 8000


CMD ["gunicorn", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]
