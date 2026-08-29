# KIRO2 Production Dockerfile
#
# Node 22 SART: frontend/package.json vite ^7.1.6 kullaniyor ve Vite 7'nin
# gereksinimi Node ^20.19 || >=22.12. node:18-alpine'da postcss
# `crypto.hash is not a function` ile patliyordu (crypto.hash Node 20.12'de
# eklendi) -- yani bu imaj UZUN SUREDIR HIC BUILD OLMUYORDU ve
# security.yml -> container-scan job'i tam bu yuzden dusuyordu:
#   [vite-plugin-pwa:build] src/styles/fonts.css: [postcss] crypto.hash is not a function
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static

# Create non-root user
RUN useradd --create-home --shell /bin/bash kiro2
RUN chown -R kiro2:kiro2 /app
USER kiro2

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
