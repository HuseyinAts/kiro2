# Docker Image Optimization Guide
## Video Recommendation System - Production Deployment

Bu doküman, Docker image'lerinin production için optimize edilmesi ve boyutunun küçültülmesi için best practice'leri içermektedir.

## İçindekiler

1. [Mevcut Durum](#mevcut-durum)
2. [Optimization Stratejileri](#optimization-stratejileri)
3. [Multi-Stage Build](#multi-stage-build)
4. [Layer Caching](#layer-caching)
5. [Security Hardening](#security-hardening)
6. [Image Scanning](#image-scanning)
7. [Performance Tuning](#performance-tuning)

---

## Mevcut Durum

### Current Image Stats

```bash
# Image boyutunu kontrol et
docker images turkiye-sinav-backend:latest

# Beklenen çıktı:
# REPOSITORY                  TAG       SIZE
# turkiye-sinav-backend      latest    ~450MB (optimized)
```

### Image Layers

```bash
# Image layer'larını görüntüle
docker history turkiye-sinav-backend:latest

# Layer boyutlarını analiz et
dive turkiye-sinav-backend:latest
```

---

## Optimization Stratejileri

### 1. Base Image Selection

**❌ Kötü:**
```dockerfile
FROM python:3.11
```
- Size: ~1GB
- Gereksiz paketler içerir

**✅ İyi:**
```dockerfile
FROM python:3.11-slim-bullseye
```
- Size: ~150MB
- Minimal paketler
- Production için yeterli

**🚀 En İyi:**
```dockerfile
FROM python:3.11-alpine
```
- Size: ~50MB
- En minimal
- Bazı Python paketleri compile gerektirebilir

**Seçimimiz:** `python:3.11-slim-bullseye`
- Boyut/özellik dengesi iyi
- Çoğu Python paketi çalışır
- Production-ready

### 2. Multi-Stage Build

**Avantajları:**
- Build dependencies production image'e dahil edilmez
- Image boyutu %50-70 azalır
- Security surface area küçülür

**Örnek:**
```dockerfile
# Build stage
FROM python:3.11-slim-bullseye as builder
RUN apt-get update && apt-get install -y build-essential
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim-bullseye
COPY --from=builder /root/.local /root/.local
COPY . /app
```

### 3. Layer Optimization

**❌ Kötü:**
```dockerfile
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN rm -rf /var/lib/apt/lists/*
```
- 4 layer oluşturur
- Cache inefficient

**✅ İyi:**
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget && \
    rm -rf /var/lib/apt/lists/*
```
- 1 layer oluşturur
- Cache efficient
- Boyut küçük

### 4. .dockerignore Kullanımı

**`.dockerignore` dosyası:**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# Testing
.pytest_cache/
.coverage
htmlcov/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Documentation
docs/
*.md
!README.md

# Development
.env.development
.env.local
docker-compose.yml
Dockerfile.dev

# Large files
*.db
*.sqlite
uploads/
temp/
```

**Avantajları:**
- Build context küçülür
- Build hızlanır
- Gereksiz dosyalar image'e dahil edilmez

### 5. Dependency Optimization

**requirements.txt optimization:**
```bash
# Sadece production dependencies
pip freeze | grep -v "pytest\|black\|flake8" > requirements.txt

# Veya requirements.txt ve requirements-dev.txt ayır
pip install -r requirements.txt  # Production
pip install -r requirements-dev.txt  # Development only
```

**Minimal dependencies:**
```txt
# requirements.txt (production only)
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
redis==5.0.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiohttp==3.9.1
```

---

## Multi-Stage Build

### Optimized Dockerfile.production

```dockerfile
# =============================================================================
# Build Stage
# =============================================================================
FROM python:3.11-slim-bullseye as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Production Stage
# =============================================================================
FROM python:3.11-slim-bullseye as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    locales \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set Turkish locale
ENV LC_ALL=tr_TR.UTF-8 \
    LANG=tr_TR.UTF-8 \
    LANGUAGE=tr_TR:tr \
    TZ=Europe/Istanbul

RUN sed -i '/tr_TR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# Create non-root user
RUN groupadd -r kiro2 && \
    useradd -r -g kiro2 -d /app -s /bin/bash kiro2

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=kiro2:kiro2 . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/temp /app/static && \
    chown -R kiro2:kiro2 /app

# Create health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:8000/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Switch to non-root user
USER kiro2

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/healthcheck.sh

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Build Optimization

```bash
# Build with BuildKit (faster)
DOCKER_BUILDKIT=1 docker build -f Dockerfile.production -t turkiye-sinav-backend:latest .

# Build with cache
docker build --cache-from turkiye-sinav-backend:latest -f Dockerfile.production -t turkiye-sinav-backend:v1.2.0 .

# Build with specific platform
docker build --platform linux/amd64 -f Dockerfile.production -t turkiye-sinav-backend:latest .
```

---

## Layer Caching

### Cache Optimization Strategies

**1. Order matters:**
```dockerfile
# ❌ Kötü - Her code değişikliğinde dependencies yeniden install edilir
COPY . /app
RUN pip install -r requirements.txt

# ✅ İyi - Dependencies sadece requirements.txt değiştiğinde install edilir
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
```

**2. Separate frequently changing files:**
```dockerfile
# Static files first (rarely change)
COPY config/ /app/config/
COPY scripts/ /app/scripts/

# Application code last (frequently changes)
COPY app/ /app/app/
COPY main.py /app/
```

**3. Use .dockerignore:**
- Gereksiz dosyaları exclude et
- Build context küçült
- Cache hit rate artır

---

## Security Hardening

### 1. Non-Root User

```dockerfile
# Create non-root user
RUN groupadd -r kiro2 && \
    useradd -r -g kiro2 -d /app -s /bin/bash kiro2

# Switch to non-root user
USER kiro2
```

**Avantajları:**
- Container escape durumunda limited access
- Security best practice
- Kubernetes SecurityContext ile uyumlu

### 2. Read-Only Root Filesystem

```yaml
# Kubernetes deployment
securityContext:
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
```

**Gerekli volume mounts:**
```yaml
volumeMounts:
- name: tmp
  mountPath: /tmp
- name: logs
  mountPath: /app/logs
```

### 3. Minimal Base Image

```dockerfile
# Use slim or alpine variants
FROM python:3.11-slim-bullseye

# Remove unnecessary packages
RUN apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*
```

### 4. No Secrets in Image

```dockerfile
# ❌ Kötü - Secret image'e dahil edilir
ENV SECRET_KEY=my-secret-key

# ✅ İyi - Secret runtime'da inject edilir
# Kubernetes secret veya environment variable kullan
```

---

## Image Scanning

### 1. Trivy Scan

```bash
# Image'i scan et
trivy image turkiye-sinav-backend:latest

# Sadece HIGH ve CRITICAL vulnerabilities
trivy image --severity HIGH,CRITICAL turkiye-sinav-backend:latest

# JSON output
trivy image -f json -o scan-results.json turkiye-sinav-backend:latest
```

### 2. Snyk Scan

```bash
# Snyk ile scan
snyk container test turkiye-sinav-backend:latest

# Fix önerileri
snyk container test turkiye-sinav-backend:latest --json | snyk-to-html -o scan-report.html
```

### 3. Docker Scout

```bash
# Docker Scout ile scan
docker scout cves turkiye-sinav-backend:latest

# Recommendations
docker scout recommendations turkiye-sinav-backend:latest
```

### 4. CI/CD Integration

```yaml
# GitHub Actions
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'turkiye-sinav-backend:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
```

---

## Performance Tuning

### 1. Uvicorn Workers

```dockerfile
# Optimal worker count: (2 x CPU cores) + 1
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--log-level", "info"]
```

### 2. Python Optimization

```dockerfile
# Enable Python optimizations
ENV PYTHONOPTIMIZE=1

# Precompile Python files
RUN python -m compileall /app
```

### 3. Startup Time Optimization

```dockerfile
# Lazy imports
# Import heavy libraries only when needed

# Preload common modules
RUN python -c "import fastapi; import sqlalchemy; import redis"
```

### 4. Memory Optimization

```dockerfile
# Set memory limits
ENV MALLOC_ARENA_MAX=2
ENV PYTHONMALLOC=malloc
```

---

## Image Size Comparison

| Strategy | Size | Build Time | Security |
|----------|------|------------|----------|
| python:3.11 (full) | ~1GB | Fast | Medium |
| python:3.11-slim | ~450MB | Fast | Good |
| python:3.11-alpine | ~200MB | Slow | Good |
| Multi-stage (slim) | ~450MB | Medium | Excellent |
| Multi-stage (alpine) | ~200MB | Slow | Excellent |

**Seçimimiz:** Multi-stage build with slim base
- Boyut: ~450MB (acceptable)
- Build time: Medium (acceptable)
- Security: Excellent
- Compatibility: Excellent

---

## Build & Push Workflow

### 1. Local Build

```bash
# Build
DOCKER_BUILDKIT=1 docker build \
  -f backend/Dockerfile.production \
  -t turkiye-sinav-backend:latest \
  -t turkiye-sinav-backend:v1.2.0 \
  .

# Test
docker run --rm turkiye-sinav-backend:latest python -c "import main; print('OK')"

# Scan
trivy image turkiye-sinav-backend:latest

# Size check
docker images turkiye-sinav-backend:latest
```

### 2. Push to Registry

```bash
# Tag for registry
docker tag turkiye-sinav-backend:latest ghcr.io/org/turkiye-sinav-backend:latest
docker tag turkiye-sinav-backend:v1.2.0 ghcr.io/org/turkiye-sinav-backend:v1.2.0

# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Push
docker push ghcr.io/org/turkiye-sinav-backend:latest
docker push ghcr.io/org/turkiye-sinav-backend:v1.2.0
```

### 3. CI/CD Pipeline

```yaml
# .github/workflows/docker-build.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          file: backend/Dockerfile.production
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.meta.outputs.tags }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## Best Practices Checklist

### Build Time
- [ ] Use multi-stage build
- [ ] Optimize layer caching
- [ ] Use .dockerignore
- [ ] Minimize layer count
- [ ] Use BuildKit

### Image Size
- [ ] Use slim/alpine base image
- [ ] Remove build dependencies
- [ ] Clean package manager cache
- [ ] Remove unnecessary files
- [ ] Compress static assets

### Security
- [ ] Run as non-root user
- [ ] Scan for vulnerabilities
- [ ] No secrets in image
- [ ] Use specific version tags
- [ ] Sign images (optional)

### Performance
- [ ] Optimize worker count
- [ ] Enable Python optimizations
- [ ] Precompile Python files
- [ ] Set memory limits
- [ ] Use health checks

### Maintenance
- [ ] Tag images properly
- [ ] Document Dockerfile
- [ ] Automate builds (CI/CD)
- [ ] Monitor image size
- [ ] Regular security updates

---

**Son Güncelleme:** 3 Kasım 2025
**Versiyon:** 1.0.0
**Hazırlayan:** DevOps Team
