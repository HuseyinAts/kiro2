#!/bin/bash
# -*- coding: utf-8 -*-
"""
Teknofest 2025 Eğitim Eylemci Platformu
Production Deployment Script

Bu script, platformun production ortamına güvenli deployment'ini sağlar:
- Zero-downtime blue-green deployment
- Database migration
- Health checks
- Rollback capability
- Monitoring integration
"""

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
SKIP_TESTS="${3:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Validate environment
validate_environment() {
    log "Validating deployment environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        development|staging|production)
            log "Environment validated: $ENVIRONMENT"
            ;;
        *)
            error "Invalid environment: $ENVIRONMENT. Must be development, staging, or production."
            exit 1
            ;;
    esac
    
    # Check required tools
    command -v docker >/dev/null 2>&1 || { error "Docker is required but not installed."; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { error "kubectl is required but not installed."; exit 1; }
    command -v aws >/dev/null 2>&1 || { error "AWS CLI is required but not installed."; exit 1; }
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if services are healthy
    if [[ "$ENVIRONMENT" != "development" ]]; then
        log "Checking current service health..."
        
        case $ENVIRONMENT in
            staging)
                HEALTH_URL="https://staging.teknofest-egitim.com/health"
                ;;
            production)
                HEALTH_URL="https://teknofest-egitim.com/health"
                ;;
        esac
        
        if curl -f "$HEALTH_URL" >/dev/null 2>&1; then
            success "Current services are healthy"
        else
            warning "Current services are not responding"
        fi
    fi
    
    # Check Docker images exist
    log "Verifying Docker images..."
    BACKEND_IMAGE="ghcr.io/teknofest-2025/teknofest-backend:$VERSION"
    FRONTEND_IMAGE="ghcr.io/teknofest-2025/teknofest-frontend:$VERSION"
    
    if docker manifest inspect "$BACKEND_IMAGE" >/dev/null 2>&1; then
        success "Backend image verified: $BACKEND_IMAGE"
    else
        error "Backend image not found: $BACKEND_IMAGE"
        exit 1
    fi
    
    if docker manifest inspect "$FRONTEND_IMAGE" >/dev/null 2>&1; then
        success "Frontend image verified: $FRONTEND_IMAGE"
    else
        error "Frontend image not found: $FRONTEND_IMAGE"
        exit 1
    fi
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        warning "Skipping tests (emergency deployment)"
        return 0
    fi
    
    log "Running deployment tests..."
    
    cd "$PROJECT_ROOT"
    
    # Backend tests
    log "Running backend tests..."
    cd backend
    python -m pytest tests/test_critical_*.py -v --timeout=300 || {
        error "Critical backend tests failed"
        exit 1
    }
    
    # Frontend tests
    log "Running frontend tests..."
    cd ../frontend
    npm test -- --watchAll=false --testTimeout=30000 || {
        error "Frontend tests failed"
        exit 1
    }
    
    success "All tests passed"
}

# Database migration
run_migrations() {
    log "Running database migrations for $ENVIRONMENT..."
    
    case $ENVIRONMENT in
        development)
            DATABASE_URL="$DEV_DATABASE_URL"
            ;;
        staging)
            DATABASE_URL="$STAGING_DATABASE_URL"
            ;;
        production)
            DATABASE_URL="$PRODUCTION_DATABASE_URL"
            ;;
    esac
    
    cd "$PROJECT_ROOT/backend"
    
    # Backup database (production only)
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log "Creating database backup..."
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        pg_dump "$DATABASE_URL" > "backups/$BACKUP_FILE" || {
            error "Database backup failed"
            exit 1
        }
        success "Database backup created: $BACKUP_FILE"
    fi
    
    # Run migrations
    DATABASE_URL="$DATABASE_URL" python -m alembic upgrade head || {
        error "Database migration failed"
        exit 1
    }
    
    success "Database migrations completed"
}