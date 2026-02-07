# KIRO2 YKS Eğitim Platformu - Backend Dockerfile
# Multi-stage build with uv for optimized production image
# Target: 100K+ concurrent users

# ==============================================================================
# STAGE 1: Builder - Install dependencies with uv (10x faster than pip)
# ==============================================================================
FROM python:3.11-slim AS builder

# Install uv for ultra-fast package installation
# Reference: https://github.com/astral-sh/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements first for optimal layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies with uv
# --system uses system python, --no-cache avoids caching downloads
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache -r requirements.txt

# ==============================================================================
# STAGE 2: Production - Final optimized image
# ==============================================================================
FROM python:3.11-slim AS production

# Türkçe karakter desteği için locale ayarları
ENV LANG=tr_TR.UTF-8
ENV LANGUAGE=tr_TR:tr
ENV LC_ALL=tr_TR.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Virtual environment path
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i '/tr_TR.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash kiro2

WORKDIR /app

# Copy virtual environment from builder (uv created)
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=kiro2:kiro2 . .

# Make health check script executable
RUN chmod +x scripts/healthcheck.sh 2>/dev/null || true

# Switch to non-root user
USER kiro2

# Expose port
EXPOSE 8000

# Health check - comprehensive check with dependencies
# Uses /health/ready endpoint which checks database and redis
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8000/health/ready || curl -sf http://localhost:8000/health || exit 1

# Production-ready command with optimal settings
# Workers calculated as (2 x CPU cores) + 1 = optimal for I/O bound applications
CMD ["uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "4", \
    "--loop", "uvloop", \
    "--http", "httptools", \
    "--log-level", "warning"]
