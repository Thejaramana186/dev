FROM python:3.11-slim as builder

WORKDIR /app
COPY app/ ./app
COPY app/requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY app/ ./app

EXPOSE 8080

CMD ["gunicorn", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]