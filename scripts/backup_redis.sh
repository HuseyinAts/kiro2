#!/bin/bash

# Redis Backup Script
# Türkiye Üniversite Sınavları Hazırlık Platformu
#
# Usage: ./backup_redis.sh [backup_dir]
# Example: ./backup_redis.sh /backups/redis

set -e

# Configuration
REDIS_CONTAINER="turkiye_sinav_redis"
REDIS_DATA_DIR="/data"
BACKUP_DIR="${1:-./backups/redis}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="redis_backup_${TIMESTAMP}"
RETENTION_DAYS=7

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

# Check if Redis container is running
check_redis() {
    if ! docker ps | grep -q "$REDIS_CONTAINER"; then
        log_error "Redis container '$REDIS_CONTAINER' is not running"
        exit 1
    fi
    log_info "Redis container is running"
}

# Trigger Redis BGSAVE
trigger_bgsave() {
    log_info "Triggering Redis BGSAVE..."
    docker exec "$REDIS_CONTAINER" redis-cli BGSAVE

    # Wait for BGSAVE to complete
    while true; do
        SAVE_STATUS=$(docker exec "$REDIS_CONTAINER" redis-cli LASTSAVE)
        sleep 1
        NEW_STATUS=$(docker exec "$REDIS_CONTAINER" redis-cli LASTSAVE)

        if [ "$SAVE_STATUS" != "$NEW_STATUS" ]; then
            log_info "BGSAVE completed successfully"
            break
        fi

        # Timeout after 60 seconds
        COUNTER=$((COUNTER + 1))
        if [ $COUNTER -gt 60 ]; then
            log_warn "BGSAVE timeout - proceeding with backup anyway"
            break
        fi
    done
}

# Create backup directory
create_backup_dir() {
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
    log_info "Created backup directory: $BACKUP_DIR/$BACKUP_NAME"
}

# Backup Redis data files
backup_data_files() {
    log_info "Backing up Redis data files..."

    # Copy RDB snapshot
    if docker exec "$REDIS_CONTAINER" test -f "$REDIS_DATA_DIR/dump.rdb"; then
        docker cp "$REDIS_CONTAINER:$REDIS_DATA_DIR/dump.rdb" "$BACKUP_DIR/$BACKUP_NAME/"
        log_info "Copied dump.rdb"
    else
        log_warn "dump.rdb not found"
    fi

    # Copy AOF file
    if docker exec "$REDIS_CONTAINER" test -f "$REDIS_DATA_DIR/appendonly.aof"; then
        docker cp "$REDIS_CONTAINER:$REDIS_DATA_DIR/appendonly.aof" "$BACKUP_DIR/$BACKUP_NAME/"
        log_info "Copied appendonly.aof"
    else
        log_warn "appendonly.aof not found"
    fi

    # Copy Redis config
    if docker exec "$REDIS_CONTAINER" test -f "/usr/local/etc/redis/redis.conf"; then
        docker cp "$REDIS_CONTAINER:/usr/local/etc/redis/redis.conf" "$BACKUP_DIR/$BACKUP_NAME/"
        log_info "Copied redis.conf"
    fi
}

# Get Redis info
backup_redis_info() {
    log_info "Saving Redis INFO..."
    docker exec "$REDIS_CONTAINER" redis-cli INFO > "$BACKUP_DIR/$BACKUP_NAME/redis_info.txt"
    docker exec "$REDIS_CONTAINER" redis-cli CONFIG GET '*' > "$BACKUP_DIR/$BACKUP_NAME/redis_config.txt"
}

# Create backup metadata
create_metadata() {
    cat > "$BACKUP_DIR/$BACKUP_NAME/backup_metadata.txt" << EOF
Backup Timestamp: $TIMESTAMP
Redis Container: $REDIS_CONTAINER
Backup Directory: $BACKUP_DIR/$BACKUP_NAME
Backup Method: BGSAVE + File Copy

Files Backed Up:
- dump.rdb (RDB snapshot)
- appendonly.aof (AOF log)
- redis.conf (configuration)
- redis_info.txt (Redis INFO)
- redis_config.txt (Redis CONFIG)

Restoration Instructions:
1. Stop Redis container: docker stop $REDIS_CONTAINER
2. Copy backup files to Redis data directory
3. Start Redis container: docker start $REDIS_CONTAINER
4. Verify data: docker exec $REDIS_CONTAINER redis-cli DBSIZE

Automated Restoration:
./restore_redis.sh $BACKUP_DIR/$BACKUP_NAME
EOF
    log_info "Created backup metadata"
}

# Compress backup
compress_backup() {
    log_info "Compressing backup..."
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

    if [ $? -eq 0 ]; then
        rm -rf "$BACKUP_NAME"
        BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
        log_info "Backup compressed: ${BACKUP_NAME}.tar.gz ($BACKUP_SIZE)"
    else
        log_error "Compression failed"
        exit 1
    fi
}

# Clean old backups
clean_old_backups() {
    log_info "Cleaning backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "redis_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

    REMAINING=$(find "$BACKUP_DIR" -name "redis_backup_*.tar.gz" -type f | wc -l)
    log_info "Remaining backups: $REMAINING"
}

# Verify backup
verify_backup() {
    log_info "Verifying backup integrity..."
    cd "$BACKUP_DIR"

    if tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
        log_info "Backup verification successful"
    else
        log_error "Backup verification failed - archive is corrupted"
        exit 1
    fi
}

# Main execution
main() {
    log_info "=== Redis Backup Started ==="
    log_info "Timestamp: $TIMESTAMP"

    check_redis
    create_backup_dir
    trigger_bgsave
    backup_data_files
    backup_redis_info
    create_metadata
    compress_backup
    verify_backup
    clean_old_backups

    log_info "=== Redis Backup Completed Successfully ==="
    log_info "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
}

# Run main function
main
