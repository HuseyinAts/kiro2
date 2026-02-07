#!/bin/bash
# KIRO2 Backend Health Check Script
# Used by Docker HEALTHCHECK and Kubernetes readiness/liveness probes
#
# Exit codes:
#   0 - Healthy
#   1 - Unhealthy
#
# Environment variables:
#   HEALTH_CHECK_URL - Health endpoint URL (default: http://localhost:8000/health)
#   HEALTH_CHECK_TIMEOUT - Timeout in seconds (default: 5)
#   CHECK_DATABASE - Check database connectivity (default: true)
#   CHECK_REDIS - Check Redis connectivity (default: true)

set -e

# Configuration
HEALTH_URL="${HEALTH_CHECK_URL:-http://localhost:8000/health}"
TIMEOUT="${HEALTH_CHECK_TIMEOUT:-5}"
CHECK_DB="${CHECK_DATABASE:-true}"
CHECK_REDIS_ENABLED="${CHECK_REDIS:-true}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check HTTP endpoint
check_http() {
    local url=$1
    local name=$2

    if curl -sf --max-time "$TIMEOUT" "$url" > /dev/null 2>&1; then
        log "${GREEN}[OK]${NC} $name is healthy"
        return 0
    else
        log "${RED}[FAIL]${NC} $name is not responding"
        return 1
    fi
}

# Check PostgreSQL
check_postgres() {
    if [ "$CHECK_DB" != "true" ]; then
        log "${YELLOW}[SKIP]${NC} Database check disabled"
        return 0
    fi

    # Use pg_isready if available
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5434}" -U "${POSTGRES_USER:-postgres}" -q; then
            log "${GREEN}[OK]${NC} PostgreSQL is ready"
            return 0
        else
            log "${RED}[FAIL]${NC} PostgreSQL is not ready"
            return 1
        fi
    fi

    # Fallback: check via Python
    python3 -c "
import sys
import asyncio
try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    import os

    async def check():
        url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2')
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        await engine.dispose()
        return True

    if asyncio.run(check()):
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'Database check failed: {e}')
    sys.exit(1)
" && log "${GREEN}[OK]${NC} PostgreSQL is ready" || { log "${RED}[FAIL]${NC} PostgreSQL is not ready"; return 1; }
}

# Check Redis
check_redis() {
    if [ "$CHECK_REDIS_ENABLED" != "true" ]; then
        log "${YELLOW}[SKIP]${NC} Redis check disabled"
        return 0
    fi

    # Use redis-cli if available
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; then
            log "${GREEN}[OK]${NC} Redis is ready"
            return 0
        else
            log "${RED}[FAIL]${NC} Redis is not ready"
            return 1
        fi
    fi

    # Fallback: check via Python
    python3 -c "
import sys
try:
    import redis
    import os

    host = os.getenv('REDIS_HOST', 'localhost')
    port = int(os.getenv('REDIS_PORT', '6379'))
    r = redis.Redis(host=host, port=port)
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f'Redis check failed: {e}')
    sys.exit(1)
" && log "${GREEN}[OK]${NC} Redis is ready" || { log "${RED}[FAIL]${NC} Redis is not ready"; return 1; }
}

# Main health check
main() {
    log "Starting health check..."

    failed=0

    # Check main application
    if ! check_http "$HEALTH_URL" "Backend API"; then
        failed=$((failed + 1))
    fi

    # Check database
    if ! check_postgres; then
        failed=$((failed + 1))
    fi

    # Check Redis
    if ! check_redis; then
        failed=$((failed + 1))
    fi

    # Summary
    if [ $failed -eq 0 ]; then
        log "${GREEN}All health checks passed${NC}"
        exit 0
    else
        log "${RED}$failed health check(s) failed${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
