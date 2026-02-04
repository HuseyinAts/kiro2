#!/bin/bash

# KIRO2 Backend Production Entrypoint Script
# Turkish University Exam Preparation Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Wait for dependencies to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    log "Waiting for $service_name to be ready ($host:$port)..."
    
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $attempt -eq $max_attempts ]; then
            error "$service_name is not available after $max_attempts attempts"
            exit 1
        fi
        
        log "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    success "$service_name is ready!"
}

# Parse database URL to extract components
parse_database_url() {
    if [ -n "$DATABASE_URL" ]; then
        # Extract host and port from DATABASE_URL
        # Format: postgresql://user:pass@host:port/db
        DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        
        if [ -z "$DB_PORT" ]; then
            DB_PORT=5432
        fi
        
        export DB_HOST DB_PORT
    fi
}

# Parse Redis URL
parse_redis_url() {
    if [ -n "$REDIS_URL" ]; then
        # Extract host and port from REDIS_URL
        # Format: redis://host:port/db
        REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
        REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/[^:]*:\([0-9]*\).*/\1/p')
        
        if [ -z "$REDIS_HOST" ]; then
            REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/\([^\/]*\).*/\1/p')
        fi
        
        if [ -z "$REDIS_PORT" ]; then
            REDIS_PORT=6379
        fi
        
        export REDIS_HOST REDIS_PORT
    fi
}

# Parse Elasticsearch URL
parse_elasticsearch_url() {
    if [ -n "$ELASTICSEARCH_URL" ]; then
        # Extract host and port from ELASTICSEARCH_URL
        # Format: http://host:port
        ES_HOST=$(echo "$ELASTICSEARCH_URL" | sed -n 's/https\?:\/\/\([^:]*\):.*/\1/p')
        ES_PORT=$(echo "$ELASTICSEARCH_URL" | sed -n 's/https\?:\/\/[^:]*:\([0-9]*\).*/\1/p')
        
        if [ -z "$ES_HOST" ]; then
            ES_HOST=$(echo "$ELASTICSEARCH_URL" | sed -n 's/https\?:\/\/\([^\/]*\).*/\1/p')
        fi
        
        if [ -z "$ES_PORT" ]; then
            ES_PORT=9200
        fi
        
        export ES_HOST ES_PORT
    fi
}

# Validate environment variables
validate_environment() {
    log "Validating environment variables..."
    
    required_vars=(
        "ENVIRONMENT"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "DATABASE_URL"
        "REDIS_URL"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    # Check if running in production
    if [ "$ENVIRONMENT" != "production" ]; then
        warning "Not running in production mode (ENVIRONMENT=$ENVIRONMENT)"
    fi
    
    # Check if debug is disabled
    if [ "$DEBUG" = "true" ]; then
        warning "Debug mode is enabled in production!"
    fi
    
    success "Environment variables validated"
}

# Wait for all dependencies
wait_for_dependencies() {
    log "Waiting for dependencies to be ready..."
    
    # Parse URLs
    parse_database_url
    parse_redis_url
    parse_elasticsearch_url
    
    # Wait for PostgreSQL
    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
        wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
    fi
    
    # Wait for Redis
    if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
        wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
    fi
    
    # Wait for Elasticsearch (optional)
    if [ -n "$ES_HOST" ] && [ -n "$ES_PORT" ]; then
        wait_for_service "$ES_HOST" "$ES_PORT" "Elasticsearch" || warning "Elasticsearch not available, continuing..."
    fi
    
    success "All dependencies are ready"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Check if we can connect to database
    python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sys
import os

async def check_db():
    try:
        engine = create_async_engine(os.getenv('DATABASE_URL'))
        async with engine.begin() as conn:
            result = await conn.execute('SELECT 1')
            print('Database connection successful')
        await engine.dispose()
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" || {
        error "Cannot connect to database"
        exit 1
    }
    
    # Run Alembic migrations if available
    if [ -f "alembic.ini" ] && [ -d "alembic" ]; then
        log "Running Alembic migrations..."
        alembic upgrade head || {
            error "Database migration failed"
            exit 1
        }
        success "Database migrations completed"
    else
        log "No Alembic configuration found, skipping migrations"
    fi
}

# Initialize application data
initialize_app() {
    log "Initializing application..."
    
    # Create necessary directories
    mkdir -p /app/logs /app/uploads /app/temp /app/static
    
    # Initialize search indices if Elasticsearch is available
    if [ -n "$ES_HOST" ]; then
        python -c "
import asyncio
from elasticsearch import AsyncElasticsearch
import sys
import os

async def init_elasticsearch():
    try:
        es = AsyncElasticsearch([os.getenv('ELASTICSEARCH_URL')])
        
        # Check if cluster is healthy
        health = await es.cluster.health()
        print(f'Elasticsearch cluster health: {health.get(\"status\", \"unknown\")}')
        
        # Initialize indices (you can add your index creation logic here)
        
        await es.close()
        return True
    except Exception as e:
        print(f'Elasticsearch initialization failed: {e}')
        return False

if '${ES_HOST}':
    result = asyncio.run(init_elasticsearch())
    sys.exit(0 if result else 1)
else:
    print('Elasticsearch not configured, skipping initialization')
    sys.exit(0)
" || warning "Elasticsearch initialization failed"
    fi
    
    success "Application initialized"
}

# Setup logging
setup_logging() {
    log "Setting up logging..."
    
    # Create log directory
    mkdir -p /app/logs
    
    # Set log file permissions
    touch /app/logs/app.log
    touch /app/logs/error.log
    touch /app/logs/access.log
    
    # Configure log rotation (if logrotate is available)
    if command -v logrotate >/dev/null 2>&1; then
        cat > /tmp/kiro2-logrotate << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 kiro2 kiro2
}
EOF
    fi
    
    success "Logging configured"
}

# Health check function
health_check() {
    log "Running initial health check..."
    
    # Check if the application can start
    timeout 10s python -c "
from main import app
print('Application imports successful')
" || {
        error "Application health check failed"
        exit 1
    }
    
    success "Initial health check passed"
}

# Prestart hook
prestart_hook() {
    log "Running prestart hook..."
    
    # You can add any custom prestart logic here
    # For example: warming up caches, checking external services, etc.
    
    # Warm up critical imports
    python -c "
import uvicorn
import fastapi
import sqlalchemy
import redis
print('Critical dependencies imported successfully')
"
    
    success "Prestart hook completed"
}

# Main entrypoint logic
main() {
    log "🚀 Starting KIRO2 Backend Production Server..."
    log "Instance ID: ${INSTANCE_ID:-unknown}"
    log "Environment: ${ENVIRONMENT:-unknown}"
    log "Python version: $(python --version)"
    
    # Run initialization steps
    validate_environment
    setup_logging
    wait_for_dependencies
    run_migrations
    initialize_app
    health_check
    prestart_hook
    
    success "🎉 Initialization completed successfully!"
    log "Starting application with command: $*"
    
    # Execute the main command
    exec "$@"
}

# Signal handlers for graceful shutdown
shutdown() {
    log "Received shutdown signal, gracefully shutting down..."
    # Add any cleanup logic here
    exit 0
}

trap shutdown SIGTERM SIGINT

# Install netcat if not available (for service checking)
if ! command -v nc >/dev/null 2>&1; then
    log "Installing netcat for service checking..."
    apt-get update && apt-get install -y netcat-openbsd
fi

# Run main function
main "$@"