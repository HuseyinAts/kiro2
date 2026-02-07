from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (check both backend and root directories)
# Note: override=False ensures environment variables (e.g., from CI/CD) take precedence
backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
env_file = root_dir / ".env" if (root_dir / ".env").exists() else backend_dir / ".env"
load_dotenv(env_file, override=False)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import your models
from models.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Read database URL from environment (Single Source of Truth)
# Prefer DATABASE_URL_SYNC for migrations (sync driver)
database_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError(
        "DATABASE_URL or DATABASE_URL_SYNC must be set for Alembic migrations.\n"
        "Create a .env file with:\n"
        "  DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/kiro2"
    )

# Convert async driver to sync driver for Alembic
# postgresql+asyncpg:// -> postgresql://
# sqlite+aiosqlite:// -> sqlite://
sync_url = database_url.replace("+asyncpg", "").replace("+aiosqlite", "")
config.set_main_option("sqlalchemy.url", sync_url)

# Log which database is being used (mask password)
import re
safe_url = re.sub(r':([^@]+)@', ':***@', sync_url)
print(f"[ALEMBIC] Using database: {safe_url}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
