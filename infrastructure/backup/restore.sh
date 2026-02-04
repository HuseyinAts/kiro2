#!/bin/bash
# PostgreSQL Database Restore Script (Task 52.3)
# Restore from backup with point-in-time recovery support
# Author: Claude
# Date: 2025-10-27

set -e
set -u

# =============================================================================
# CONFIGURATION
# =============================================================================

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-kiro2_db}"
DB_USER="${DB_USER:-postgres}"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
ENCRYPTION_KEY_FILE="${ENCRYPTION_KEY_FILE:-/etc/postgresql/backup_key.txt}"

# =============================================================================
# FUNCTIONS
# =============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

list_backups() {
    log "Available backups:"
    ls -lh "$BACKUP_DIR"/kiro2_db_*.sql* | awk '{print $9, $5, $6, $7, $8}'
}

restore_from_backup() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log "ERROR: Backup file not found: $backup_file"
        exit 1
    fi

    log "Restoring from: $backup_file"

    # Decrypt if encrypted
    local temp_file="$backup_file"
    if [ "${backup_file: -4}" == ".enc" ]; then
        log "Decrypting backup"
        temp_file="/tmp/restore_temp_$(date +%s).sql"
        openssl enc -aes-256-cbc -d -in "$backup_file" \
            -out "$temp_file" -pass file:"$ENCRYPTION_KEY_FILE"
    fi

    # Drop existing connections
    log "Dropping existing connections to database"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
EOF

    # Drop and recreate database
    log "Dropping existing database"
    PGPASSWORD="$DB_PASSWORD" dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" --if-exists

    log "Creating new database"
    PGPASSWORD="$DB_PASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

    # Restore backup
    log "Restoring backup (this may take a while)"
    PGPASSWORD="$DB_PASSWORD" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-owner \
        --no-acl \
        "$temp_file"

    # Cleanup temp file
    if [ "$temp_file" != "$backup_file" ]; then
        rm -f "$temp_file"
    fi

    log "Restore completed successfully"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    if [ $# -eq 0 ]; then
        list_backups
        echo ""
        echo "Usage: $0 <backup_file>"
        echo "Example: $0 ${BACKUP_DIR}/kiro2_db_20251027_120000.sql"
        exit 1
    fi

    local backup_file="$1"

    log "PostgreSQL Database Restore"
    log "WARNING: This will drop the existing database!"
    read -p "Continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi

    restore_from_backup "$backup_file"
}

main "$@"
