# ==============================================================================
# EventSignal - Unified Cloud Run Dockerfile (Frontend SPA + FastAPI Backend)
# ==============================================================================

# Stage 1: Build React 19 + Vite Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# Empty VITE_API_BASE_URL configures same-origin relative API requests (/api/v1/...)
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Runtime Environment with FastAPI & Pre-seeded Demo Community
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    APP_ENV=development \
    BACKEND_PORT=8080 \
    BACKEND_HOST=0.0.0.0 \
    DEMO_MODE_ENABLED=true \
    DATABASE_URL=sqlite:///./data/eventsignal.db

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application source
COPY backend ./backend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create writable directory for local SQLite database
RUN mkdir -p /app/data /app/backend/data && chmod -R 777 /app/data /app/backend/data

WORKDIR /app/backend

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8080}"]
