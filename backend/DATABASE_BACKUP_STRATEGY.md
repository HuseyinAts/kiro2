# Database Backup Strategy

## 🎯 Overview

Comprehensive database backup and disaster recovery strategy for YKS Hazırlık Platform production database.

## 📋 Backup Types

### 1. Full Backups (Daily)

- **Frequency**: Every day at 2:00 AM (low traffic)
- **Retention**: 30 days
- **Method**: `pg_dump` with gzip compression
- **Storage**: Local + S3 (optional)
- **Size**: ~100-500 MB compressed

### 2. Incremental Backups (Hourly) - Optional

- **Frequency**: Every hour
- **Retention**: 7 days
- **Method**: WAL (Write-Ahead Logging) archiving
- **Storage**: S3
- **Enables**: Point-in-Time Recovery (PITR)

### 3. Transaction Log Backups (Continuous)

- **Frequency**: Real-time
- **Retention**: 7 days
- **Method**: PostgreSQL WAL streaming
- **Enables**: PITR with 1-second granularity

## 🚀 Quick Start

### Step 1: Setup Backup Directory

```bash
# Create backup directory
mkdir -p /var/backups/postgresql
mkdir -p /var/backups/postgresql/wal

# Set permissions
chown postgres:postgres /var/backups/postgresql
chmod 700 /var/backups/postgresql
```

### Step 2: Configure PostgreSQL for WAL Archiving

Edit `postgresql.conf`:

```conf
# Enable WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /var/backups/postgresql/wal/%f && cp %p /var/backups/postgresql/wal/%f'
archive_timeout = 300  # Force WAL file switch every 5 minutes

# Keep enough WAL for PITR
wal_keep_size = 1024  # Keep 1GB of WAL files
max_wal_senders = 3
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### Step 3: Install Dependencies

```bash
# Python dependencies
pip install python-dotenv boto3 pydantic

# System dependencies (if not installed)
sudo apt-get install postgresql-client-14 gzip
```

### Step 4: Configure S3 (Optional)

Add to `.env.production`:

```bash
# AWS S3 for backup storage
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
AWS_REGION=eu-west-1
AWS_BACKUP_BUCKET=yks-platform-backups

# Admin notification email
ADMIN_EMAIL=admin@yourdomain.com
```

Create S3 bucket:

```bash
aws s3 mb s3://yks-platform-backups --region eu-west-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket yks-platform-backups \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket yks-platform-backups \
    --server-side-encryption-configuration '{
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
    }'

# Set lifecycle policy (delete after 90 days)
aws s3api put-bucket-lifecycle-configuration \
    --bucket yks-platform-backups \
    --lifecycle-configuration file://s3-lifecycle-policy.json
```

### Step 5: Schedule Daily Backups

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add backup job (daily at 2 AM)
0 2 * * * cd /var/www/yks-platform/backend && /usr/bin/python3 scripts/backup_database.py --s3-bucket yks-platform-backups >> logs/backup.log 2>&1

# Add WAL cleanup job (weekly)
0 3 * * 0 find /var/backups/postgresql/wal -type f -mtime +7 -delete
```

## 📖 Manual Backup

### Create Backup

```bash
cd backend

# Basic backup (local only)
python scripts/backup_database.py

# Backup with S3 upload
python scripts/backup_database.py --s3-bucket yks-platform-backups

# Custom retention period
python scripts/backup_database.py --retention-days 60

# Skip verification (faster, not recommended)
python scripts/backup_database.py --no-verify
```

**Expected Output**:

```
============================================================
Database Backup - 2025-11-04 02:00:15
============================================================

Database: kiro2_db
Host: localhost:5432
Backup Directory: /var/www/yks-platform/backend/backups
Retention: 30 days
S3 Bucket: yks-platform-backups

--> Creating backup: backup_kiro2_db_20251104_020015.sql.gz
--> Compressing backup...
[OK] Backup created: backup_kiro2_db_20251104_020015.sql.gz (245.67 MB)
--> Verifying backup integrity...
[OK] Backup verified successfully
--> Uploading to S3: yks-platform-backups
[OK] Uploaded to s3://yks-platform-backups/database-backups/backup_kiro2_db_20251104_020015.sql.gz
--> Cleaning up old backups (retention: 30 days)...
  Deleting: backup_kiro2_db_20251003_020012.sql.gz
[OK] Deleted 1 old backup(s)
[OK] Notification sent to admin@yourdomain.com

============================================================
[SUCCESS] Backup completed successfully!
============================================================
```

## 🔄 Restore Procedures

### Restore from Full Backup

```bash
# 1. Stop application
sudo systemctl stop yks-platform

# 2. Download backup from S3 (if needed)
aws s3 cp s3://yks-platform-backups/database-backups/backup_kiro2_db_20251104_020015.sql.gz .

# 3. Decompress backup
gunzip backup_kiro2_db_20251104_020015.sql.gz

# 4. Drop existing database (CAREFUL!)
psql -U postgres -c "DROP DATABASE IF EXISTS kiro2_db"
psql -U postgres -c "CREATE DATABASE kiro2_db OWNER yks_user"

# 5. Restore database
psql -U postgres -d kiro2_db -f backup_kiro2_db_20251104_020015.sql

# 6. Verify restoration
psql -U postgres -d kiro2_db -c "SELECT COUNT(*) FROM users;"
psql -U postgres -d kiro2_db -c "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1;"

# 7. Start application
sudo systemctl start yks-platform
```

### Point-in-Time Recovery (PITR)

Restore to specific timestamp (requires WAL archiving):

```bash
# 1. Stop PostgreSQL
sudo systemctl stop postgresql

# 2. Backup current data directory
sudo mv /var/lib/postgresql/14/main /var/lib/postgresql/14/main.old

# 3. Create new data directory
sudo mkdir /var/lib/postgresql/14/main
sudo chown postgres:postgres /var/lib/postgresql/14/main

# 4. Restore base backup
sudo -u postgres pg_basebackup -h localhost -D /var/lib/postgresql/14/main -U postgres -v -P

# 5. Create recovery.conf
sudo -u postgres cat > /var/lib/postgresql/14/main/recovery.conf << EOF
restore_command = 'cp /var/backups/postgresql/wal/%f %p'
recovery_target_time = '2025-11-04 14:30:00'
recovery_target_action = 'promote'
EOF

# 6. Start PostgreSQL (will enter recovery mode)
sudo systemctl start postgresql

# 7. Monitor recovery
tail -f /var/log/postgresql/postgresql-14-main.log

# 8. Verify restoration
psql -U postgres -d kiro2_db -c "SELECT NOW();"
```

## 📊 Backup Verification

### Automated Verification

The backup script automatically verifies:

1. **Gzip Integrity**: `gzip -t` test
2. **File Size**: Must be > 1 KB
3. **SQL Syntax**: Optional restore to test database

### Manual Verification

```bash
# Test gzip integrity
gzip -t backup_kiro2_db_20251104_020015.sql.gz

# View backup contents
zcat backup_kiro2_db_20251104_020015.sql.gz | head -n 50

# Restore to test database
gunzip -c backup_kiro2_db_20251104_020015.sql.gz | psql -U postgres -d test_restore
```

## 🔒 Security Best Practices

### 1. Encrypt Backups

```bash
# Encrypt before upload
gpg --symmetric --cipher-algo AES256 backup_kiro2_db_20251104_020015.sql.gz

# Decrypt for restore
gpg --decrypt backup_kiro2_db_20251104_020015.sql.gz.gpg > backup.sql.gz
```

### 2. Secure Backup Storage

- Use S3 server-side encryption (AES-256)
- Enable S3 bucket versioning
- Use IAM roles with minimum permissions
- Enable S3 access logging

### 3. Backup Access Control

```bash
# Restrict backup directory permissions
chmod 700 /var/backups/postgresql
chown postgres:postgres /var/backups/postgresql

# Backup files should be readable only by postgres user
chmod 600 /var/backups/postgresql/*.sql.gz
```

### 4. Audit Backup Access

Enable S3 CloudTrail for backup bucket:

```bash
aws cloudtrail create-trail \
    --name yks-backup-audit \
    --s3-bucket-name yks-platform-audit-logs

aws cloudtrail start-logging --name yks-backup-audit
```

## 📈 Monitoring and Alerts

### 1. Backup Success Monitoring

Add to [monitoring/prometheus/alerts/backup_alerts.yml](monitoring/prometheus/alerts/backup_alerts.yml):

```yaml
groups:
  - name: database_backup
    interval: 1m
    rules:
      - alert: BackupFailed
        expr: time() - backup_last_success_timestamp > 86400
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Database backup failed"
          description: "No successful backup in last 24 hours"

      - alert: BackupTooOld
        expr: time() - backup_last_success_timestamp > 172800
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Database backup too old"
          description: "Last successful backup is older than 48 hours"

      - alert: BackupSizeTooSmall
        expr: backup_file_size_bytes < 1048576
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Backup file too small"
          description: "Backup file size is less than 1 MB"
```

### 2. Email Notifications

Configured automatically in backup script. Sends email on:
- Backup success (daily summary)
- Backup failure (immediate alert)
- Verification failure

### 3. Slack/PagerDuty Integration

Add webhook to `.env.production`:

```bash
BACKUP_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🚨 Disaster Recovery Plan

### Scenario 1: Database Corruption

**Recovery Time Objective (RTO)**: 30 minutes
**Recovery Point Objective (RPO)**: 24 hours

1. Identify corruption
2. Stop application
3. Restore from last night's backup
4. Verify data integrity
5. Start application

### Scenario 2: Data Center Failure

**RTO**: 2 hours
**RPO**: 24 hours

1. Provision new database server
2. Download backup from S3
3. Restore database
4. Update application DNS/connection strings
5. Start application

### Scenario 3: Accidental Data Deletion

**RTO**: 1 hour
**RPO**: 1 second (with PITR)

1. Determine deletion timestamp
2. Perform PITR to 1 minute before deletion
3. Export deleted data
4. Re-import to current database

## 📝 Backup Checklist

Use this checklist monthly to verify backup health:

### Monthly Verification
- [ ] Test restore from last week's backup
- [ ] Verify S3 bucket contains all expected backups
- [ ] Check backup file sizes (should be consistent)
- [ ] Verify email notifications are being received
- [ ] Test PITR (if configured)
- [ ] Review backup logs for errors

### Quarterly Tasks
- [ ] Perform full disaster recovery drill
- [ ] Review and update backup retention policy
- [ ] Test backup restoration to different environment
- [ ] Review S3 storage costs and optimize
- [ ] Update backup documentation

### Annual Tasks
- [ ] Review and update disaster recovery plan
- [ ] Rotate backup encryption keys
- [ ] Audit backup access logs
- [ ] Benchmark backup and restore times
- [ ] Update backup capacity planning

## 📊 Backup Metrics

Track these metrics:

```python
# Prometheus metrics
backup_last_success_timestamp  # Unix timestamp of last successful backup
backup_duration_seconds        # Time taken for backup
backup_file_size_bytes         # Size of backup file
backup_verification_passed     # 1 = passed, 0 = failed
backup_s3_upload_success       # 1 = success, 0 = failed
```

## 🔧 Troubleshooting

### Error: "pg_dump: command not found"

```bash
# Install PostgreSQL client tools
sudo apt-get install postgresql-client-14
```

### Error: "FATAL: password authentication failed"

```bash
# Verify database credentials
psql -h localhost -U postgres -d kiro2_db -c "SELECT 1"

# Check .env.production file
cat .env.production | grep POSTGRES
```

### Error: "No space left on device"

```bash
# Check disk space
df -h

# Clean up old backups
find backups/ -name "backup_*.sql.gz" -mtime +30 -delete

# Compress existing backups
gzip backups/*.sql
```

### Error: "S3 upload failed: NoCredentialsError"

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

## 📚 Additional Resources

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [AWS S3 Backup Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/backup-best-practices.html)
- [PITR with PostgreSQL](https://www.postgresql.org/docs/current/continuous-archiving.html)

## 📞 Emergency Contacts

**Database Issues**:
- Primary DBA: admin@yourdomain.com
- Backup DBA: backup-admin@yourdomain.com
- On-call rotation: +90-XXX-XXX-XXXX

**AWS Support**:
- Support case portal: https://console.aws.amazon.com/support/
- Enterprise support phone: (Available in AWS console)

---

**Last Updated**: 2025-11-04
**Version**: 1.0.0
**Status**: Production Ready ✅
