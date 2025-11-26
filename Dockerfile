# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app

# ---- Stage 2: Runtime ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY app/ ./app

# Expose the app port
EXPOSE 8000

# Start Gunicorn server with Uvicorn workers
CMD ["gunicorn", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]
