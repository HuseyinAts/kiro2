#!/usr/bin/env bash
#
# KIRO2 MVP Beta - One-Click Launch Script
#
# Usage:
#   ./launch-mvp.sh                  # Full launch (build + migrate + seed + start)
#   ./launch-mvp.sh --check-only     # Pre-flight checks only
#   ./launch-mvp.sh --skip-build     # Start without rebuilding Docker images
#   ./launch-mvp.sh --no-seed        # Skip user seeding
#   ./launch-mvp.sh --reset          # Tear down, prune, rebuild from scratch
#   ./launch-mvp.sh --down           # Stop all MVP containers
#

set -e

# ── Project root (script location) ──────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.mvp.yml"
ENV_FILE=".env.mvp"
ENV_EXAMPLE=".env.mvp.example"

# ── Colors ───────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[>>]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!!]${NC} $1"; }
error()   { echo -e "${RED}[XX]${NC} $1"; }
step()    { echo -e "\n${BOLD}[$1/7] $2${NC}"; }

# ── Phase tracking for error trap ────────────────────────────────────
CURRENT_PHASE="setup"

cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo ""
        error "Launch failed during: ${CURRENT_PHASE}"
        error "Exit code: ${exit_code}"
        echo ""
        info "Troubleshooting:"
        echo "  - Check container logs: docker compose -f $COMPOSE_FILE logs --tail=50"
        echo "  - Re-run pre-flight:   ./launch-mvp.sh --check-only"
        echo "  - Full reset:          ./launch-mvp.sh --reset"
    fi
}
trap cleanup EXIT

# ── Flag parsing ─────────────────────────────────────────────────────
FLAG_CHECK_ONLY=false
FLAG_SKIP_BUILD=false
FLAG_NO_SEED=false
FLAG_RESET=false
FLAG_DOWN=false

for arg in "$@"; do
    case "$arg" in
        --check-only)  FLAG_CHECK_ONLY=true ;;
        --skip-build)  FLAG_SKIP_BUILD=true ;;
        --no-seed)     FLAG_NO_SEED=true ;;
        --reset)       FLAG_RESET=true ;;
        --down)        FLAG_DOWN=true ;;
        --help|-h)
            echo "Usage: ./launch-mvp.sh [--check-only] [--skip-build] [--no-seed] [--reset] [--down]"
            exit 0
            ;;
        *)
            error "Unknown flag: $arg"
            echo "Usage: ./launch-mvp.sh [--check-only] [--skip-build] [--no-seed] [--reset] [--down]"
            exit 1
            ;;
    esac
done

# ── Detect docker compose command ────────────────────────────────────
DOCKER_COMPOSE=""
if docker compose version &>/dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &>/dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

# ── Handle --down early ──────────────────────────────────────────────
if [ "$FLAG_DOWN" = true ]; then
    if [ -z "$DOCKER_COMPOSE" ]; then
        error "Docker Compose not found"
        exit 1
    fi
    info "Stopping MVP containers..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down
    success "MVP containers stopped"
    exit 0
fi

# ══════════════════════════════════════════════════════════════════════
#  Phase 1: Pre-flight Checks
# ══════════════════════════════════════════════════════════════════════
step 1 "Pre-flight Checks"
CURRENT_PHASE="pre-flight checks"

CHECKS_PASSED=true

# Docker CLI
if docker --version &>/dev/null; then
    success "Docker CLI installed"
else
    error "Docker CLI not found - install Docker Desktop"
    CHECKS_PASSED=false
fi

# Docker daemon
if docker info &>/dev/null; then
    success "Docker daemon running"
else
    error "Docker daemon not running - start Docker Desktop"
    CHECKS_PASSED=false
fi

# Docker Compose
if [ -n "$DOCKER_COMPOSE" ]; then
    success "Docker Compose available ($DOCKER_COMPOSE)"
else
    error "Docker Compose not found"
    CHECKS_PASSED=false
fi

# Python
if python --version &>/dev/null; then
    success "Python available ($(python --version 2>&1))"
else
    error "Python not found - install Python 3.11+"
    CHECKS_PASSED=false
fi

# PostgreSQL (TCP check on port 5434)
if python -c "import socket; s=socket.create_connection(('localhost', 5434), timeout=3); s.close()" 2>/dev/null; then
    success "PostgreSQL reachable (port 5434)"
else
    error "PostgreSQL not reachable on port 5434"
    CHECKS_PASSED=false
fi

# Redis (TCP check on port 6379)
if python -c "import socket; s=socket.create_connection(('localhost', 6379), timeout=3); s.close()" 2>/dev/null; then
    success "Redis reachable (port 6379)"
else
    warn "Redis not reachable on port 6379 (non-blocking, but cache/sessions won't work)"
fi

# Port 8000 availability
if python -c "import socket; s=socket.socket(); s.settimeout(1); r=s.connect_ex(('localhost',8000)); s.close(); exit(0 if r!=0 else 1)" 2>/dev/null; then
    success "Port 8000 available"
else
    # Check if it's our container
    if docker ps --filter "name=kiro2-backend" --format "{{.Names}}" 2>/dev/null | grep -q "kiro2-backend"; then
        warn "Port 8000 in use by kiro2-backend (will be restarted)"
    else
        error "Port 8000 in use by another process"
        CHECKS_PASSED=false
    fi
fi

# Port 3000 availability
if python -c "import socket; s=socket.socket(); s.settimeout(1); r=s.connect_ex(('localhost',3000)); s.close(); exit(0 if r!=0 else 1)" 2>/dev/null; then
    success "Port 3000 available"
else
    if docker ps --filter "name=kiro2-frontend" --format "{{.Names}}" 2>/dev/null | grep -q "kiro2-frontend"; then
        warn "Port 3000 in use by kiro2-frontend (will be restarted)"
    else
        error "Port 3000 in use by another process"
        CHECKS_PASSED=false
    fi
fi

# Compose file exists
if [ -f "$COMPOSE_FILE" ]; then
    success "$COMPOSE_FILE found"
else
    error "$COMPOSE_FILE not found in project root"
    CHECKS_PASSED=false
fi

if [ "$CHECKS_PASSED" = false ]; then
    echo ""
    error "Pre-flight checks FAILED. Fix issues above and retry."
    exit 1
fi

if [ "$FLAG_CHECK_ONLY" = true ]; then
    echo ""
    success "All pre-flight checks passed!"
    exit 0
fi

# ══════════════════════════════════════════════════════════════════════
#  Phase 2: Environment File
# ══════════════════════════════════════════════════════════════════════
step 2 "Environment Setup"
CURRENT_PHASE="environment setup"

if [ -f "$ENV_FILE" ]; then
    success "Using existing $ENV_FILE"
else
    if [ ! -f "$ENV_EXAMPLE" ]; then
        error "$ENV_EXAMPLE not found. Cannot generate $ENV_FILE."
        exit 1
    fi

    info "Generating $ENV_FILE from template..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"

    # Auto-generate secrets
    JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

    # DB password
    if [ -n "$KIRO2_DB_PASSWORD" ]; then
        DB_PASS="$KIRO2_DB_PASSWORD"
        success "DB password set from KIRO2_DB_PASSWORD env var"
    else
        echo ""
        warn "No KIRO2_DB_PASSWORD env var found."
        read -sp "  Enter PostgreSQL password (or press Enter for default 'postgres'): " DB_PASS_INPUT
        echo ""
        DB_PASS="${DB_PASS_INPUT:-postgres}"
    fi

    # Replace placeholders using Python (handles any format in .env.mvp.example)
    # Variables passed via os.environ to avoid shell injection with special chars
    ENV_FILE="$ENV_FILE" JWT_SECRET="$JWT_SECRET" SECRET_KEY="$SECRET_KEY" \
    ENCRYPTION_KEY="$ENCRYPTION_KEY" DB_PASS="$DB_PASS" \
    python -c "
import os, re
env_file = os.environ['ENV_FILE']
with open(env_file, 'r') as f:
    content = f.read()
replacements = {
    'JWT_SECRET_KEY': os.environ['JWT_SECRET'],
    'SECRET_KEY': os.environ['SECRET_KEY'],
    'ENCRYPTION_KEY': os.environ['ENCRYPTION_KEY'],
}
for key, value in replacements.items():
    # Use str.replace per-line to avoid regex special chars in value
    prefix = key + '='
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = prefix + value
    content = '\n'.join(lines)
db_pass = os.environ['DB_PASS']
content = content.replace('YOUR_DB_PASSWORD', db_pass)
content = content.replace('changeme_strong_password_here', db_pass)
with open(env_file, 'w') as f:
    f.write(content)
"

    success "$ENV_FILE generated with auto-generated secrets"
fi

# ── Extract DATABASE_URL for host-side operations ────────────────────
HOST_DB_URL=$(grep "^DATABASE_URL=" "$ENV_FILE" | cut -d'=' -f2-)
HOST_DB_URL=$(echo "$HOST_DB_URL" | sed 's/host\.docker\.internal/localhost/g')

if [ -z "$HOST_DB_URL" ]; then
    error "DATABASE_URL not found in $ENV_FILE"
    exit 1
fi

# ══════════════════════════════════════════════════════════════════════
#  Phase 3: Database Migrations
# ══════════════════════════════════════════════════════════════════════
step 3 "Database Migrations"
CURRENT_PHASE="database migrations"

if python -c "import alembic" 2>/dev/null; then
    info "Running alembic upgrade head..."
    (cd backend && DATABASE_URL="$HOST_DB_URL" python -m alembic upgrade head)
    success "Migrations applied"
else
    warn "Alembic not installed on host. Skipping migrations."
    warn "Run manually: cd backend && pip install alembic && alembic upgrade head"
fi

# ══════════════════════════════════════════════════════════════════════
#  Phase 4: Seed Users
# ══════════════════════════════════════════════════════════════════════
step 4 "Seed Test Users"
CURRENT_PHASE="seed users"

if [ "$FLAG_NO_SEED" = true ]; then
    info "Skipping seed (--no-seed flag)"
else
    if [ -f "backend/scripts/seed_mvp_data.py" ]; then
        info "Seeding MVP test users..."
        (cd backend && DATABASE_URL="$HOST_DB_URL" python scripts/seed_mvp_data.py)
        success "Users seeded (idempotent)"
    else
        warn "Seed script not found: backend/scripts/seed_mvp_data.py"
    fi
fi

# ══════════════════════════════════════════════════════════════════════
#  Phase 5: Docker Build & Start
# ══════════════════════════════════════════════════════════════════════
step 5 "Docker Build & Start"
CURRENT_PHASE="docker build"

if [ "$FLAG_RESET" = true ]; then
    warn "Resetting: tearing down existing containers and volumes..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v 2>/dev/null || true
fi

if [ "$FLAG_SKIP_BUILD" = true ]; then
    info "Starting containers (skip build)..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d
else
    info "Building and starting containers..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up --build -d
fi

success "Containers started"

# ══════════════════════════════════════════════════════════════════════
#  Phase 6: Health Check Polling
# ══════════════════════════════════════════════════════════════════════
step 6 "Health Checks"
CURRENT_PHASE="health checks"

# Wait for backend
info "Waiting for backend (http://localhost:8000/health)..."
BACKEND_OK=false
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        BACKEND_OK=true
        break
    fi
    sleep 3
    printf "."
done
echo ""

if [ "$BACKEND_OK" = true ]; then
    success "Backend healthy"
else
    error "Backend not responding after 90s"
    info "Container logs:"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=30 backend
    exit 1
fi

# Wait for frontend
info "Waiting for frontend (http://localhost:3000)..."
FRONTEND_OK=false
for i in $(seq 1 10); do
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        FRONTEND_OK=true
        break
    fi
    sleep 3
    printf "."
done
echo ""

if [ "$FRONTEND_OK" = true ]; then
    success "Frontend healthy"
else
    error "Frontend not responding after 30s"
    info "Container logs:"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=30 frontend
    exit 1
fi

# ══════════════════════════════════════════════════════════════════════
#  Phase 7: Smoke Test & Summary
# ══════════════════════════════════════════════════════════════════════
step 7 "Smoke Test & Summary"
CURRENT_PHASE="smoke test"

# Read smoke test credentials from .env.mvp
SMOKE_EMAIL=$(grep "^SMOKE_TEST_EMAIL=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
SMOKE_PASS=$(grep "^SMOKE_TEST_PASSWORD=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)

LOGIN_OK=false
if [ -n "$SMOKE_EMAIL" ] && [ -n "$SMOKE_PASS" ]; then
    LOGIN_RESPONSE=$(curl -sf -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$SMOKE_EMAIL\",\"password\":\"$SMOKE_PASS\"}" 2>/dev/null) && LOGIN_OK=true

    if [ "$LOGIN_OK" = true ]; then
        success "Login smoke test passed"
    else
        warn "Login smoke test failed (auth may need debugging)"
    fi
else
    warn "Smoke test skipped (SMOKE_TEST_EMAIL/PASSWORD not in $ENV_FILE)"
fi

# ── Summary ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  KIRO2 MVP Beta - LAUNCH SUCCESSFUL${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}URLs:${NC}"
echo "    Frontend:  http://localhost:3000"
echo "    Backend:   http://localhost:8000"
echo "    API Docs:  http://localhost:8000/docs"
echo "    Health:    http://localhost:8000/health"
echo ""
echo -e "  ${BOLD}Test Credentials:${NC}"
echo "    ────────────────────────────────────────────────"
echo "    STUDENT  | test@kiro2.com      | Kiro2Beta2026@x"
echo "    STUDENT  | ogrenci@kiro2.com   | Kiro2Beta2026@x"
echo "    TEACHER  | ogretmen@kiro2.com  | Kiro2Beta2026@x"
echo "    ADMIN    | admin@kiro2.com     | Kiro2Beta2026@x"
echo "    PARENT   | veli@kiro2.com      | Kiro2Beta2026@x"
echo ""
echo -e "  ${BOLD}Manage:${NC}"
echo "    Logs:     $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f"
echo "    Stop:     ./launch-mvp.sh --down"
echo "    Reset:    ./launch-mvp.sh --reset"
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
