#!/bin/bash

# Redis Restore Script
# Türkiye Üniversite Sınavları Hazırlık Platformu
#
# Usage: ./restore_redis.sh <backup_file>
# Example: ./restore_redis.sh ./backups/redis/redis_backup_20250104_143000.tar.gz

set -e

# Configuration
REDIS_CONTAINER="turkiye_sinav_redis"
REDIS_DATA_DIR="/data"
BACKUP_FILE="$1"
TEMP_DIR="/tmp/redis_restore_$$"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation
if [ -z "$BACKUP_FILE" ]; then
    log_error "Usage: $0 <backup_file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if Redis container exists
check_redis() {
    if ! docker ps -a | grep -q "$REDIS_CONTAINER"; then
        log_error "Redis container '$REDIS_CONTAINER' not found"
        exit 1
    fi
    log_info "Redis container found"
}

# Backup current data (safety measure)
backup_current_data() {
    log_warn "Creating safety backup of current data..."
    SAFETY_BACKUP="/tmp/redis_safety_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$SAFETY_BACKUP"

    if docker exec "$REDIS_CONTAINER" test -f "$REDIS_DATA_DIR/dump.rdb"; then
        docker cp "$REDIS_CONTAINER:$REDIS_DATA_DIR/dump.rdb" "$SAFETY_BACKUP/" 2>/dev/null || true
    fi

    if docker exec "$REDIS_CONTAINER" test -f "$REDIS_DATA_DIR/appendonly.aof"; then
        docker cp "$REDIS_CONTAINER:$REDIS_DATA_DIR/appendonly.aof" "$SAFETY_BACKUP/" 2>/dev/null || true
    fi

    log_info "Safety backup created at: $SAFETY_BACKUP"
}

# Extract backup
extract_backup() {
    log_info "Extracting backup..."
    mkdir -p "$TEMP_DIR"
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

    # Find the backup directory (it's the only directory in TEMP_DIR)
    BACKUP_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)

    if [ -z "$BACKUP_DIR" ]; then
        log_error "No backup directory found in archive"
        exit 1
    fi

    log_info "Backup extracted to: $BACKUP_DIR"
}

# Show backup info
show_backup_info() {
    if [ -f "$BACKUP_DIR/backup_metadata.txt" ]; then
        log_info "=== Backup Information ==="
        cat "$BACKUP_DIR/backup_metadata.txt"
        echo ""
    fi
}

# Confirm restoration
confirm_restore() {
    echo -e "${YELLOW}WARNING: This will replace current Redis data!${NC}"
    echo -e "${YELLOW}A safety backup has been created at: $SAFETY_BACKUP${NC}"
    echo ""
    read -p "Continue with restore? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log_info "Restore cancelled by user"
        rm -rf "$TEMP_DIR"
        exit 0
    fi
}

# Stop Redis
stop_redis() {
    log_info "Stopping Redis container..."
    docker stop "$REDIS_CONTAINER"
    log_info "Redis stopped"
}

# Restore data files
restore_data_files() {
    log_info "Restoring Redis data files..."

    # Clear current data directory
    docker exec "$REDIS_CONTAINER" sh -c "rm -f $REDIS_DATA_DIR/dump.rdb $REDIS_DATA_DIR/appendonly.aof" 2>/dev/null || true

    # Restore RDB snapshot
    if [ -f "$BACKUP_DIR/dump.rdb" ]; then
        docker cp "$BACKUP_DIR/dump.rdb" "$REDIS_CONTAINER:$REDIS_DATA_DIR/"
        log_info "Restored dump.rdb"
    else
        log_warn "dump.rdb not found in backup"
    fi

    # Restore AOF file
    if [ -f "$BACKUP_DIR/appendonly.aof" ]; then
        docker cp "$BACKUP_DIR/appendonly.aof" "$REDIS_CONTAINER:$REDIS_DATA_DIR/"
        log_info "Restored appendonly.aof"
    else
        log_warn "appendonly.aof not found in backup"
    fi

    # Set proper permissions
    docker exec "$REDIS_CONTAINER" chown -R redis:redis "$REDIS_DATA_DIR"
}

# Start Redis
start_redis() {
    log_info "Starting Redis container..."
    docker start "$REDIS_CONTAINER"

    # Wait for Redis to be ready
    sleep 5

    MAX_RETRIES=30
    RETRY=0
    while [ $RETRY -lt $MAX_RETRIES ]; do
        if docker exec "$REDIS_CONTAINER" redis-cli ping > /dev/null 2>&1; then
            log_info "Redis is ready"
            break
        fi
        RETRY=$((RETRY + 1))
        sleep 1
    done

    if [ $RETRY -eq $MAX_RETRIES ]; then
        log_error "Redis failed to start"
        exit 1
    fi
}

# Verify restoration
verify_restore() {
    log_info "Verifying restoration..."

    # Check database size
    DBSIZE=$(docker exec "$REDIS_CONTAINER" redis-cli DBSIZE)
    log_info "Database size: $DBSIZE keys"

    # Show Redis info
    log_info "Redis server info:"
    docker exec "$REDIS_CONTAINER" redis-cli INFO server | grep redis_version
    docker exec "$REDIS_CONTAINER" redis-cli INFO persistence | grep -E "aof_enabled|rdb_last_save_time"

    if [ "$DBSIZE" -gt 0 ]; then
        log_info "Restoration verified successfully"
    else
        log_warn "Database is empty - verify backup file"
    fi
}

# Cleanup
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}

# Main execution
main() {
    log_info "=== Redis Restore Started ==="
    log_info "Backup file: $BACKUP_FILE"

    check_redis
    extract_backup
    show_backup_info
    backup_current_data
    confirm_restore
    stop_redis
    restore_data_files
    start_redis
    verify_restore
    cleanup

    log_info "=== Redis Restore Completed Successfully ==="
    log_info "Safety backup location: $SAFETY_BACKUP"
    echo ""
    log_info "To verify data, run: docker exec $REDIS_CONTAINER redis-cli KEYS '*'"
}

# Run main function
main
