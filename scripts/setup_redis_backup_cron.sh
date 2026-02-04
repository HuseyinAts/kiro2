#!/bin/bash

# Setup Redis Backup Cron Job
# Türkiye Üniversite Sınavları Hazırlık Platformu
#
# Usage: sudo ./setup_redis_backup_cron.sh

set -e

# Configuration
BACKUP_SCRIPT_PATH="$(pwd)/backup_redis.sh"
BACKUP_DIR="$(pwd)/../backups/redis"
CRON_SCHEDULE="0 2 * * *"  # Daily at 2 AM

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if script exists
if [ ! -f "$BACKUP_SCRIPT_PATH" ]; then
    log_warn "Backup script not found at: $BACKUP_SCRIPT_PATH"
    exit 1
fi

# Make script executable
chmod +x "$BACKUP_SCRIPT_PATH"
log_info "Made backup script executable"

# Create backup directory
mkdir -p "$BACKUP_DIR"
log_info "Created backup directory: $BACKUP_DIR"

# Create cron job
CRON_JOB="$CRON_SCHEDULE $BACKUP_SCRIPT_PATH $BACKUP_DIR >> /var/log/redis_backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT_PATH"; then
    log_warn "Cron job already exists"
    log_info "Current cron jobs:"
    crontab -l | grep redis
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    log_info "Cron job added successfully"
fi

# Show cron schedule
log_info "Backup schedule: Daily at 2 AM"
log_info "Backup directory: $BACKUP_DIR"
log_info "Log file: /var/log/redis_backup.log"

# Create log file with proper permissions
sudo touch /var/log/redis_backup.log
sudo chmod 666 /var/log/redis_backup.log

log_info "Setup completed!"
echo ""
log_info "To view cron jobs: crontab -l"
log_info "To view backup log: tail -f /var/log/redis_backup.log"
log_info "To test backup manually: $BACKUP_SCRIPT_PATH $BACKUP_DIR"
