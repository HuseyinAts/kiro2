"""
Database Backup Script
Automated PostgreSQL backup with compression and retention management

Features:
- Full database dumps
- Automatic compression (gzip)
- Retention policy (default: 30 days)
- S3 upload support (optional)
- Backup verification
- Email notifications on failure

Usage:
    # Basic backup
    python scripts/backup_database.py

    # Custom retention period
    python scripts/backup_database.py --retention-days 60

    # Upload to S3
    python scripts/backup_database.py --s3-bucket my-backups

    # Scheduled via cron (daily at 2 AM)
    0 2 * * * cd /path/to/backend && python scripts/backup_database.py >> logs/backup.log 2>&1
"""

import os
import sys
import gzip
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class DatabaseBackup:
    """Database backup manager"""

    def __init__(
        self,
        backup_dir: str = "backups",
        retention_days: int = 30,
        s3_bucket: Optional[str] = None,
        verify: bool = True,
    ):
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.s3_bucket = s3_bucket
        self.verify = verify

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Database connection info
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = os.getenv("POSTGRES_PORT", "5434")
        self.db_name = os.getenv("POSTGRES_DB", "kiro2_db")
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

    def get_backup_filename(self) -> str:
        """Generate backup filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{self.db_name}_{timestamp}.sql.gz"

    def create_backup(self) -> Optional[Path]:
        """Create database backup"""
        backup_file = self.backup_dir / self.get_backup_filename()
        temp_file = backup_file.with_suffix(".sql")

        try:
            print(f"{BLUE}-->{RESET} Creating backup: {backup_file.name}")

            # Set password in environment
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password

            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                self.db_name,
                "-F",
                "p",  # Plain SQL format
                "-f",
                str(temp_file),
                "--verbose",
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"{RED}[ERROR]{RESET} pg_dump failed:")
                print(result.stderr)
                return None

            # Compress the backup
            print(f"{BLUE}-->{RESET} Compressing backup...")
            with open(temp_file, "rb") as f_in:
                with gzip.open(backup_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed file
            temp_file.unlink()

            # Get file size
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(
                f"{GREEN}[OK]{RESET} Backup created: {backup_file.name} ({size_mb:.2f} MB)"
            )

            return backup_file

        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Backup failed: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return None

    def verify_backup(self, backup_file: Path) -> bool:
        """Verify backup integrity"""
        if not self.verify:
            return True

        try:
            print(f"{BLUE}-->{RESET} Verifying backup integrity...")

            # Test gzip integrity
            result = subprocess.run(
                ["gzip", "-t", str(backup_file)], capture_output=True
            )

            if result.returncode != 0:
                print(f"{RED}[ERROR]{RESET} Backup file is corrupted")
                return False

            # Check if file is not empty
            if backup_file.stat().st_size < 1024:  # Less than 1KB
                print(f"{RED}[ERROR]{RESET} Backup file is too small")
                return False

            print(f"{GREEN}[OK]{RESET} Backup verified successfully")
            return True

        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Verification failed: {e}")
            return False

    def upload_to_s3(self, backup_file: Path) -> bool:
        """Upload backup to S3"""
        if not self.s3_bucket:
            return True  # Skip if no S3 bucket configured

        try:
            print(f"{BLUE}-->{RESET} Uploading to S3: {self.s3_bucket}")

            import boto3

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "eu-west-1"),
            )

            # Upload with server-side encryption
            s3_key = f"database-backups/{backup_file.name}"
            s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    "ServerSideEncryption": "AES256",
                    "StorageClass": "STANDARD_IA",  # Infrequent Access (cheaper)
                },
            )

            print(f"{GREEN}[OK]{RESET} Uploaded to s3://{self.s3_bucket}/{s3_key}")
            return True

        except Exception as e:
            print(f"{YELLOW}[WARNING]{RESET} S3 upload failed: {e}")
            return False

    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            print(
                f"{BLUE}-->{RESET} Cleaning up old backups (retention: {self.retention_days} days)..."
            )

            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0

            for backup_file in self.backup_dir.glob("backup_*.sql.gz"):
                # Get file modification time
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)

                if file_time < cutoff_date:
                    print(f"{BLUE}  Deleting:{RESET} {backup_file.name}")
                    backup_file.unlink()
                    deleted_count += 1

            print(f"{GREEN}[OK]{RESET} Deleted {deleted_count} old backup(s)")

        except Exception as e:
            print(f"{YELLOW}[WARNING]{RESET} Cleanup failed: {e}")

    def send_notification(
        self, success: bool, backup_file: Optional[Path] = None, error: str = ""
    ):
        """Send email notification"""
        if not os.getenv("SMTP_HOST"):
            return  # Skip if email not configured

        try:
            smtp_host = os.getenv("SMTP_HOST")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_user)

            # Admin email (should be in .env)
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")

            msg = MIMEMultipart()
            msg["From"] = smtp_from
            msg["To"] = admin_email
            msg[
                "Subject"
            ] = f"[YKS Platform] Database Backup {'Success' if success else 'FAILED'}"

            if success:
                body = f"""
Database Backup Completed Successfully

Database: {self.db_name}
Backup File: {backup_file.name if backup_file else 'N/A'}
Size: {backup_file.stat().st_size / (1024*1024):.2f} MB
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Location: {backup_file.parent if backup_file else 'N/A'}
S3 Bucket: {self.s3_bucket if self.s3_bucket else 'Not configured'}

Retention Policy: {self.retention_days} days
"""
            else:
                body = f"""
⚠️ DATABASE BACKUP FAILED ⚠️

Database: {self.db_name}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {error}

Please investigate immediately!
"""

            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            print(f"{GREEN}[OK]{RESET} Notification sent to {admin_email}")

        except Exception as e:
            print(f"{YELLOW}[WARNING]{RESET} Failed to send notification: {e}")

    def run(self):
        """Run backup process"""
        print(f"{BLUE}{'='*60}{RESET}")
        print(
            f"{BLUE}Database Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}"
        )
        print(f"{BLUE}{'='*60}{RESET}\n")

        print(f"Database: {self.db_name}")
        print(f"Host: {self.db_host}:{self.db_port}")
        print(f"Backup Directory: {self.backup_dir.absolute()}")
        print(f"Retention: {self.retention_days} days")
        print(f"S3 Bucket: {self.s3_bucket or 'Not configured'}\n")

        # Create backup
        backup_file = self.create_backup()

        if not backup_file:
            self.send_notification(False, error="Backup creation failed")
            return False

        # Verify backup
        if not self.verify_backup(backup_file):
            self.send_notification(False, backup_file, "Backup verification failed")
            return False

        # Upload to S3
        self.upload_to_s3(backup_file)

        # Cleanup old backups
        self.cleanup_old_backups()

        # Send success notification
        self.send_notification(True, backup_file)

        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{GREEN}[SUCCESS]{RESET} Backup completed successfully!")
        print(f"{BLUE}{'='*60}{RESET}\n")

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database backup script")
    parser.add_argument(
        "--backup-dir", default="backups", help="Backup directory (default: backups)"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Retention period in days (default: 30)",
    )
    parser.add_argument("--s3-bucket", help="S3 bucket for remote backup storage")
    parser.add_argument(
        "--no-verify", action="store_true", help="Skip backup verification"
    )

    args = parser.parse_args()

    # Load environment variables
    from dotenv import load_dotenv

    env_file = backend_path / ".env.production"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"{YELLOW}[WARNING]{RESET} .env.production not found, using defaults")

    # Run backup
    backup = DatabaseBackup(
        backup_dir=args.backup_dir,
        retention_days=args.retention_days,
        s3_bucket=args.s3_bucket,
        verify=not args.no_verify,
    )

    success = backup.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Backup cancelled{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(1)
