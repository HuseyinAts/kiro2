#!/bin/bash
#
# PostgreSQL Automated Backup Script
# INFRASTRUCTURE FIX: Daily database backups with 30-day retention
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
DB_NAME="${POSTGRES_DB:-turkiye_sinav_db}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_CONTAINER="${POSTGRES_CONTAINER:-postgres}"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "========================================="
echo "PostgreSQL Backup Starting"
echo "========================================="
echo "Database: $DB_NAME"
echo "Timestamp: $TIMESTAMP"
echo "Backup file: $BACKUP_FILE"
echo ""

# Perform backup
echo "[1/4] Creating database dump..."
if command -v docker &> /dev/null; then
    # Using Docker
    docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
else
    # Direct PostgreSQL
    pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
fi

# Check if backup was successful
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file was not created"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✓ Backup created successfully ($BACKUP_SIZE)"
echo ""

# Verify backup integrity
echo "[2/4] Verifying backup integrity..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "✓ Backup file is valid"
else
    echo "ERROR: Backup file is corrupted"
    exit 1
fi
echo ""

# Clean old backups
echo "[3/4] Cleaning old backups (retention: $RETENTION_DAYS days)..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "✓ Deleted $DELETED_COUNT old backup(s)"
echo ""

# List recent backups
echo "[4/4] Recent backups:"
ls -lht "$BACKUP_DIR"/backup_*.sql.gz | head -5
echo ""

echo "========================================="
echo "Backup Complete"
echo "========================================="
echo "Backup location: $BACKUP_FILE"
echo "Backup size: $BACKUP_SIZE"
echo ""

# Send notification (optional - requires configuration)
if [ -n "$BACKUP_WEBHOOK_URL" ]; then
    curl -X POST "$BACKUP_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"PostgreSQL backup completed: $BACKUP_FILE ($BACKUP_SIZE)\"}" \
        2>/dev/null || true
fi

exit 0
