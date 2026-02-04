#!/bin/bash
# PostgreSQL Automated Backup Script (Task 52.3)
# Daily full backup with compression and encryption
# Author: Claude
# Date: 2025-10-27

set -e  # Exit on error
set -u  # Exit on undefined variable

# =============================================================================
# CONFIGURATION
# =============================================================================

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-kiro2_db}"
DB_USER="${DB_USER:-postgres}"

# Backup paths
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# WAL Archive (for PITR)
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-/var/lib/postgresql/wal_archive}"

# Encryption (optional)
ENCRYPTION_ENABLED="${ENCRYPTION_ENABLED:-true}"
ENCRYPTION_KEY_FILE="${ENCRYPTION_KEY_FILE:-/etc/postgresql/backup_key.txt}"

# Notifications
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_TO="${EMAIL_TO:-admin@example.com}"

# =============================================================================
# FUNCTIONS
# =============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

send_notification() {
    local message="$1"
    local level="${2:-INFO}"

    log "$level: $message"

    # Slack notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"[$level] PostgreSQL Backup: $message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi

    # Email notification (requires mailx or sendmail)
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "[$level] PostgreSQL Backup" "$EMAIL_TO" || true
    fi
}

check_disk_space() {
    local required_gb=10
    local available_gb=$(df -BG "$BACKUP_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')

    if [ "$available_gb" -lt "$required_gb" ]; then
        send_notification "Low disk space: ${available_gb}GB available, ${required_gb}GB required" "ERROR"
        exit 1
    fi
}

# =============================================================================
# MAIN BACKUP PROCESS
# =============================================================================

main() {
    log "Starting PostgreSQL backup process"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$WAL_ARCHIVE_DIR"

    # Check disk space
    check_disk_space

    # Generate backup filename
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/kiro2_db_${TIMESTAMP}.sql"

    # Perform backup
    log "Creating backup: $BACKUP_FILE"

    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="$BACKUP_FILE" 2>&1; then

        log "Backup created successfully"

        # Encrypt backup if enabled
        if [ "$ENCRYPTION_ENABLED" = "true" ] && [ -f "$ENCRYPTION_KEY_FILE" ]; then
            log "Encrypting backup"
            openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" \
                -out "${BACKUP_FILE}.enc" -pass file:"$ENCRYPTION_KEY_FILE"

            rm "$BACKUP_FILE"
            BACKUP_FILE="${BACKUP_FILE}.enc"
            log "Backup encrypted"
        fi

        # Get backup size
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log "Backup size: $BACKUP_SIZE"

        # Verify backup integrity
        log "Verifying backup integrity"
        if [ "${BACKUP_FILE: -4}" == ".enc" ]; then
            # Decrypt and verify
            openssl enc -aes-256-cbc -d -in "$BACKUP_FILE" \
                -pass file:"$ENCRYPTION_KEY_FILE" | pg_restore --list > /dev/null 2>&1
        else
            pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1
        fi

        if [ $? -eq 0 ]; then
            log "Backup verification successful"
            send_notification "Backup completed successfully. Size: $BACKUP_SIZE" "SUCCESS"
        else
            send_notification "Backup verification failed" "ERROR"
            exit 1
        fi

    else
        send_notification "Backup creation failed" "ERROR"
        exit 1
    fi

    # Cleanup old backups
    log "Cleaning up old backups (retention: $BACKUP_RETENTION_DAYS days)"
    find "$BACKUP_DIR" -name "kiro2_db_*.sql*" -mtime +$BACKUP_RETENTION_DAYS -delete

    # Cleanup old WAL files
    find "$WAL_ARCHIVE_DIR" -name "*.gz" -mtime +$BACKUP_RETENTION_DAYS -delete

    log "Backup process completed"
}

# Run main function
main "$@"
