# ==============================================================================
# VYOM+ Backend Service — Production Container
# ==============================================================================
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install curl for health check probing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Layer caching: install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app

# Create non-privileged service user for defense-in-depth
RUN useradd -m -u 1000 vyomuser && chown -R vyomuser:vyomuser /app
USER vyomuser

# Expose standard FastAPI service port
EXPOSE 8000

# Container health probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch ASGI production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
