# ── Aegis Backend — Docker Image ──────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY aegis_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install the Sentinel SDK
COPY aegis_sdk/ ./aegis_sdk/
RUN pip install --no-cache-dir ./aegis_sdk

# Copy backend source
COPY aegis_backend/ ./aegis_backend/

# Expose port (Render / Cloud Run inject $PORT)
EXPOSE 8000

# Start FastAPI
CMD ["sh", "-c", "cd aegis_backend && uvicorn backend:app --host 0.0.0.0 --port ${PORT:-8000}"]
