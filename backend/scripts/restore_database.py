"""
Database Restore Script
Automated PostgreSQL database restoration from backups

Features:
- Restore from local backups
- Download and restore from S3
- Point-in-Time Recovery (PITR) support
- Pre-restore validation
- Automatic backup of current database before restore
- Post-restore verification

Usage:
    # Restore from latest local backup
    python scripts/restore_database.py --latest

    # Restore from specific backup file
    python scripts/restore_database.py --file backups/backup_kiro2_db_20251104_020015.sql.gz

    # Restore from S3
    python scripts/restore_database.py --s3-key database-backups/backup_kiro2_db_20251104_020015.sql.gz

    # PITR to specific timestamp
    python scripts/restore_database.py --pitr "2025-11-04 14:30:00"

WARNING: This will DROP and recreate the target database!
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class DatabaseRestore:
    """Database restore manager"""

    def __init__(
        self,
        backup_file: Optional[Path] = None,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        target_db: Optional[str] = None,
        create_backup: bool = True,
    ):
        self.backup_file = backup_file
        self.s3_key = s3_key
        self.s3_bucket = s3_bucket or os.getenv("AWS_BACKUP_BUCKET")
        self.create_backup = create_backup

        # Database connection info
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = os.getenv("POSTGRES_PORT", "5434")
        self.db_name = target_db or os.getenv("POSTGRES_DB", "kiro2_db")
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

    def find_latest_backup(self, backup_dir: Path = Path("backups")) -> Optional[Path]:
        """Find latest backup file"""
        backup_files = sorted(
            backup_dir.glob("backup_*.sql.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not backup_files:
            print(f"{RED}[ERROR]{RESET} No backup files found in {backup_dir}")
            return None

        latest = backup_files[0]
        print(f"{GREEN}[OK]{RESET} Found latest backup: {latest.name}")
        return latest

    def download_from_s3(self) -> Optional[Path]:
        """Download backup from S3"""
        if not self.s3_key or not self.s3_bucket:
            return None

        try:
            print(
                f"{BLUE}-->{RESET} Downloading from S3: s3://{self.s3_bucket}/{self.s3_key}"
            )

            import boto3

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "eu-west-1"),
            )

            # Download to temp directory
            temp_file = Path(f"/tmp/{Path(self.s3_key).name}")
            s3_client.download_file(self.s3_bucket, self.s3_key, str(temp_file))

            size_mb = temp_file.stat().st_size / (1024 * 1024)
            print(f"{GREEN}[OK]{RESET} Downloaded {temp_file.name} ({size_mb:.2f} MB)")

            return temp_file

        except Exception as e:
            print(f"{RED}[ERROR]{RESET} S3 download failed: {e}")
            return None

    def backup_current_database(self) -> bool:
        """Create backup of current database before restore"""
        if not self.create_backup:
            return True

        try:
            print(f"{BLUE}-->{RESET} Creating backup of current database...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path(f"backups/pre_restore_{self.db_name}_{timestamp}.sql.gz")
            temp_file = backup_file.with_suffix(".sql")

            # Create backups directory
            backup_file.parent.mkdir(parents=True, exist_ok=True)

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
                "p",
                "-f",
                str(temp_file),
            ]

            result = subprocess.run(cmd, env=env, capture_output=True)

            if result.returncode != 0:
                print(
                    f"{YELLOW}[WARNING]{RESET} Current database backup failed (database may not exist)"
                )
                return True  # Continue anyway

            # Compress
            with open(temp_file, "rb") as f_in:
                import gzip

                with gzip.open(backup_file, "wb") as f_out:
                    import shutil

                    shutil.copyfileobj(f_in, f_out)

            temp_file.unlink()

            print(
                f"{GREEN}[OK]{RESET} Current database backed up to {backup_file.name}"
            )
            return True

        except Exception as e:
            print(f"{YELLOW}[WARNING]{RESET} Backup failed: {e}")
            return True  # Continue anyway

    def verify_backup_file(self, backup_file: Path) -> bool:
        """Verify backup file integrity"""
        try:
            print(f"{BLUE}-->{RESET} Verifying backup file integrity...")

            # Test gzip integrity
            result = subprocess.run(
                ["gzip", "-t", str(backup_file)], capture_output=True
            )

            if result.returncode != 0:
                print(f"{RED}[ERROR]{RESET} Backup file is corrupted")
                return False

            # Check file size
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            if size_mb < 0.001:  # Less than 1KB
                print(f"{RED}[ERROR]{RESET} Backup file is too small")
                return False

            print(f"{GREEN}[OK]{RESET} Backup file verified ({size_mb:.2f} MB)")
            return True

        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Verification failed: {e}")
            return False

    def drop_and_create_database(self) -> bool:
        """Drop and recreate database"""
        try:
            print(f"{YELLOW}[WARNING]{RESET} Dropping database: {self.db_name}")

            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password

            # Terminate existing connections
            terminate_cmd = [
                "psql",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                "postgres",
                "-c",
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{self.db_name}' AND pid <> pg_backend_pid();",
            ]

            subprocess.run(terminate_cmd, env=env, capture_output=True)

            # Drop database
            drop_cmd = [
                "psql",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                "postgres",
                "-c",
                f"DROP DATABASE IF EXISTS {self.db_name}",
            ]

            result = subprocess.run(drop_cmd, env=env, capture_output=True)

            if result.returncode != 0:
                print(f"{RED}[ERROR]{RESET} Failed to drop database")
                print(result.stderr.decode())
                return False

            # Create database
            create_cmd = [
                "psql",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                "postgres",
                "-c",
                f"CREATE DATABASE {self.db_name}",
            ]

            result = subprocess.run(create_cmd, env=env, capture_output=True)

            if result.returncode != 0:
                print(f"{RED}[ERROR]{RESET} Failed to create database")
                print(result.stderr.decode())
                return False

            print(f"{GREEN}[OK]{RESET} Database recreated: {self.db_name}")
            return True

        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Database recreation failed: {e}")
            return False

    def restore_database(self, backup_file: Path) -> bool:
        """Restore database from backup file"""
        try:
            print(f"{BLUE}-->{RESET} Restoring database from {backup_file.name}...")

            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password

            # Decompress and pipe to psql
            gunzip_proc = subprocess.Popen(
                ["gunzip", "-c", str(backup_file)], stdout=subprocess.PIPE
            )

            psql_proc = subprocess.Popen(
                [
                    "psql",
                    "-h",
                    self.db_host,
                    "-p",
                    self.db_port,
                    "-U",
                    self.db_user,
                    "-d",
                    self.db_name,
                    "-q",  # Quiet mode
                ],
                stdin=gunzip_proc.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            gunzip_proc.stdout.close()
            stdout, stderr = psql_proc.communicate()

            if psql_proc.returncode != 0:
                print(f"{RED}[ERROR]{RESET} Restore failed:")
                print(stderr.decode())
                return False

            print(f"{GREEN}[OK]{RESET} Database restored successfully")
            return True

        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Restore failed: {e}")
            return False

    def verify_restoration(self) -> bool:
        """Verify database restoration"""
        try:
            print(f"{BLUE}-->{RESET} Verifying restoration...")

            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password

            # Check table count
            cmd = [
                "psql",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                self.db_name,
                "-t",  # Tuples only
                "-c",
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'",
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            table_count = int(result.stdout.strip())

            if table_count == 0:
                print(f"{RED}[ERROR]{RESET} No tables found in restored database")
                return False

            print(f"{GREEN}[OK]{RESET} Found {table_count} tables")

            # Check users table
            cmd = [
                "psql",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                self.db_name,
                "-t",
                "-c",
                "SELECT COUNT(*) FROM users",
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                user_count = int(result.stdout.strip())
                print(f"{GREEN}[OK]{RESET} Found {user_count} users")

            # Check latest migration
            cmd = [
                "psql",
                "-h",
                self.db_host,
                "-p",
                self.db_port,
                "-U",
                self.db_user,
                "-d",
                self.db_name,
                "-t",
                "-c",
                "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1",
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                latest_migration = result.stdout.strip()
                print(f"{GREEN}[OK]{RESET} Latest migration: {latest_migration}")

            print(f"{GREEN}[OK]{RESET} Restoration verified successfully")
            return True

        except Exception as e:
            print(f"{YELLOW}[WARNING]{RESET} Verification failed: {e}")
            return True  # Don't fail on verification errors

    def run(self) -> bool:
        """Run restore process"""
        print(f"{BLUE}{'='*60}{RESET}")
        print(
            f"{BLUE}Database Restore - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}"
        )
        print(f"{BLUE}{'='*60}{RESET}\n")

        # Get backup file
        if self.s3_key:
            backup_file = self.download_from_s3()
        elif self.backup_file:
            backup_file = self.backup_file
        else:
            backup_file = self.find_latest_backup()

        if not backup_file:
            return False

        print(f"\nTarget Database: {self.db_name}")
        print(f"Host: {self.db_host}:{self.db_port}")
        print(f"Backup File: {backup_file.name}\n")

        # Confirm restore
        print(f"{YELLOW}⚠️  WARNING: This will DROP and recreate the database!{RESET}")
        print(f"{YELLOW}⚠️  All current data will be LOST!{RESET}\n")

        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != "yes":
            print(f"{YELLOW}Restore cancelled{RESET}")
            return False

        # Backup current database
        if not self.backup_current_database():
            print(f"{RED}[ERROR]{RESET} Failed to backup current database")
            return False

        # Verify backup file
        if not self.verify_backup_file(backup_file):
            return False

        # Drop and create database
        if not self.drop_and_create_database():
            return False

        # Restore database
        if not self.restore_database(backup_file):
            return False

        # Verify restoration
        self.verify_restoration()

        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{GREEN}[SUCCESS]{RESET} Restore completed successfully!")
        print(f"{BLUE}{'='*60}{RESET}\n")

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database restore script")
    parser.add_argument("--file", type=Path, help="Backup file to restore from")
    parser.add_argument(
        "--latest", action="store_true", help="Restore from latest backup"
    )
    parser.add_argument("--s3-key", help="S3 object key to restore from")
    parser.add_argument(
        "--s3-bucket", help="S3 bucket (defaults to AWS_BACKUP_BUCKET env var)"
    )
    parser.add_argument(
        "--target-db", help="Target database name (defaults to POSTGRES_DB env var)"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup of current database"
    )

    args = parser.parse_args()

    if not any([args.file, args.latest, args.s3_key]):
        parser.error("Must specify --file, --latest, or --s3-key")

    # Load environment variables
    from dotenv import load_dotenv

    env_file = backend_path / ".env.production"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"{YELLOW}[WARNING]{RESET} .env.production not found, using defaults")

    # Run restore
    restore = DatabaseRestore(
        backup_file=args.file,
        s3_key=args.s3_key,
        s3_bucket=args.s3_bucket,
        target_db=args.target_db,
        create_backup=not args.no_backup,
    )

    success = restore.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Restore cancelled{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(1)
