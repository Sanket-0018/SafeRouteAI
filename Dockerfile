# ── Stage 1: Build React/Vite Frontend ─────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build production bundle
COPY frontend/ ./
ENV VITE_API_BASE_URL=""
RUN npm run build

# ── Stage 2: Python Runtime & FastAPI Application ─────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (libgomp1 required for LightGBM OpenMP support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY api/ ./api/
COPY src/ ./src/

# Copy models and metadata
COPY models/ ./models/

# Copy precomputed reports and intelligence outputs
COPY outputs/ ./outputs/

# Copy production runtime data (official blackspots, places index, knowledge base)
COPY data/ ./data/

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Render dynamically injects PORT (defaults to 10000)
ENV PORT=10000
ENV PYTHONUNBUFFERED=1
EXPOSE 10000

# Start FastAPI with Uvicorn binding to 0.0.0.0 and $PORT
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
