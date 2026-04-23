"""
Database Migration Runner
Executes SQL migration files in order

Usage:
    python backend/migrations/run_migrations.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
    or individual variables:
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
"""

import asyncio
import codecs
import os
import sys
from pathlib import Path

import asyncpg

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

async def get_database_url() -> str:
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        return database_url

    # Build from individual components
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5434')
    db = os.getenv('POSTGRES_DB', 'kiro2_db')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')

    return f'postgresql://{user}:{password}@{host}:{port}/{db}'

async def create_migrations_table(conn: asyncpg.Connection):
    """Create migrations tracking table if not exists"""
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    ''')
    print(f"{GREEN}[OK]{RESET} Migrations table ready")

async def get_applied_migrations(conn: asyncpg.Connection) -> set:
    """Get list of already applied migrations"""
    rows = await conn.fetch('SELECT version FROM schema_migrations')
    return {row['version'] for row in rows}

async def get_migration_files() -> list[tuple[str, Path]]:
    """Get list of migration files to apply"""
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob('*.sql'))

    migrations = []
    for filepath in migration_files:
        version = filepath.stem  # e.g., "001_create_users_table"
        migrations.append((version, filepath))

    return migrations

async def apply_migration(conn: asyncpg.Connection, version: str, filepath: Path):
    """Apply a single migration"""
    print(f"{BLUE}-->{RESET} Applying migration: {version}")

    # Read SQL file with explicit UTF-8 encoding
    with open(filepath, encoding='utf-8', errors='replace') as f:
        sql_content = f.read()

    # Execute migration in transaction
    async with conn.transaction():
        try:
            await conn.execute(sql_content)

            # Record migration
            description = version.replace('_', ' ').title()
            await conn.execute(
                'INSERT INTO schema_migrations (version, description) VALUES ($1, $2)',
                version,
                description
            )

            print(f"{GREEN}[OK]{RESET} Migration {version} applied successfully")
            return True

        except Exception as e:
            print(f"{RED}[ERROR]{RESET} Migration {version} failed: {e}")
            raise

async def run_migrations():
    """Main migration runner"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Database Migration Runner{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Get database URL
    database_url = await get_database_url()
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}\n")

    # Connect to database
    try:
        conn = await asyncpg.connect(database_url)
        # Set client encoding to UTF-8
        await conn.execute("SET client_encoding = 'UTF8'")
        print(f"{GREEN}[OK]{RESET} Connected to database\n")
    except Exception as e:
        print(f"{RED}[ERROR]{RESET} Failed to connect to database: {e}")
        return False

    try:
        # Create migrations table
        await create_migrations_table(conn)

        # Get applied migrations
        applied = await get_applied_migrations(conn)
        print(f"Already applied: {len(applied)} migrations\n")

        # Get migration files
        migrations = await get_migration_files()
        pending = [(v, p) for v, p in migrations if v not in applied]

        if not pending:
            print(f"{YELLOW}[OK]{RESET} No pending migrations\n")
            return True

        print(f"Found {len(pending)} pending migrations:\n")

        # Apply each pending migration
        success_count = 0
        for version, filepath in pending:
            try:
                await apply_migration(conn, version, filepath)
                success_count += 1
            except Exception:
                print(f"\n{RED}Migration failed, stopping here{RESET}")
                break

        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{GREEN}[OK]{RESET} Applied {success_count}/{len(pending)} migrations")
        print(f"{BLUE}{'='*60}{RESET}\n")

        return success_count == len(pending)

    finally:
        await conn.close()

if __name__ == '__main__':
    try:
        success = asyncio.run(run_migrations())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Migration cancelled{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(1)
