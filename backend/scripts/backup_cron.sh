#!/bin/bash
# Automated Backup Cron Script - Task 52.3
# Schedule: Daily full backup at 2 AM, hourly WAL archiving

# Load environment variables
if [ -f /app/.env ]; then
    source /app/.env
fi

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgresql}"
LOG_DIR="${LOG_DIR:-/var/log/postgresql-backup}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Create directories
mkdir -p "$LOG_DIR"

# Log file with timestamp
LOG_FILE="$LOG_DIR/backup_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting automated backup process"

# Run full backup
log "Creating full backup..."
python3 /app/backend/scripts/automated_backup.py \
    --type full \
    --host "$DB_HOST" \
    --port "$DB_PORT" \
    --database "$DB_NAME" \
    --user "$DB_USER" \
    --backup-dir "$BACKUP_DIR" >> "$LOG_FILE" 2>&1

BACKUP_STATUS=$?

if [ $BACKUP_STATUS -eq 0 ]; then
    log "Backup completed successfully"

    # Cleanup old backups
    log "Cleaning up old backups..."
    python3 /app/backend/scripts/automated_backup.py \
        --cleanup \
        --backup-dir "$BACKUP_DIR" >> "$LOG_FILE" 2>&1

    log "Cleanup completed"
else
    log "ERROR: Backup failed with status $BACKUP_STATUS"

    # Send alert (email, Slack, etc.)
    # curl -X POST ... send notification

    exit 1
fi

log "Backup process finished"

# Keep only last 7 days of logs
find "$LOG_DIR" -name "backup_*.log" -mtime +7 -delete

exit 0
