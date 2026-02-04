#!/bin/bash
#
# PostgreSQL Database Restore Script
# Restores from backup created by backup_postgres.sh
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
DB_NAME="${POSTGRES_DB:-turkiye_sinav_db}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_CONTAINER="${POSTGRES_CONTAINER:-postgres}"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lt "$BACKUP_DIR"/backup_*.sql.gz | head -10
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "========================================="
echo "PostgreSQL Restore"
echo "========================================="
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
echo ""

# Warning prompt
read -p "WARNING: This will OVERWRITE the database '$DB_NAME'. Continue? (yes/no) " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

echo ""
echo "[1/3] Verifying backup file..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "✓ Backup file is valid"
else
    echo "ERROR: Backup file is corrupted"
    exit 1
fi

echo ""
echo "[2/3] Dropping existing database..."
if command -v docker &> /dev/null; then
    docker exec "$DB_CONTAINER" dropdb -U "$DB_USER" --if-exists "$DB_NAME"
    docker exec "$DB_CONTAINER" createdb -U "$DB_USER" "$DB_NAME"
else
    dropdb -U "$DB_USER" --if-exists "$DB_NAME"
    createdb -U "$DB_USER" "$DB_NAME"
fi
echo "✓ Database recreated"

echo ""
echo "[3/3] Restoring from backup..."
if command -v docker &> /dev/null; then
    gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" "$DB_NAME"
else
    gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" "$DB_NAME"
fi
echo "✓ Database restored successfully"

echo ""
echo "========================================="
echo "Restore Complete"
echo "========================================="

exit 0
