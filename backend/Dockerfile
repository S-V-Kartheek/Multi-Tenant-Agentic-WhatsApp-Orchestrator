# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Build dependencies
# Install all Python packages in a separate layer for caching efficiency.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Production runtime
# Lean image with only what's needed to run.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application source
COPY app/ ./app/

# Ensure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Render/Cloud Run use PORT env var; default to 8080
EXPOSE 8080

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2", "--access-log"]
