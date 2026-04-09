import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

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

safe_url = re.sub(r":([^@]+)@", ":***@", sync_url)
print(f"[ALEMBIC] Using database: {safe_url}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# ============================================================================
# GÜVENLİK KONFIGÜRASYONU — ALEMBIC DRIFT KORUMALARI
# ============================================================================
# ⚠️  ALTIN KURAL: "alembic revision --autogenerate" TEHLİKELİDİR!
#
# Neden: 108 tablo henüz DB'de oluşturulmamış (gelecek özellikler için model var).
#        Autogenerate bunların hepsini CREATE etmeye çalışır → gereksiz migration.
#        Ayrıca DB-only kolonlar (is_calib_pool vb.) varsa DROP önerir.
#
# GÜVENLİ YÖNTEM: Elle migration yaz:
#   alembic revision -m "açıklayıcı_isim"
#   → Dosyayı aç, upgrade/downgrade fonksiyonlarını elle yaz
#
# Autogenerate SADECE şu durumda kullanılabilir:
#   1. include_object() hook güncel
#   2. ALEMBIC_EXCLUDE_TABLES güncel
#   3. Üretilen migration MUTLAKA gözden geçirilmeli (DROP/ALTER kontrol)
# Alembic autogenerate'in DOKUNMAMASI gereken tablolar.
# Bu tablolar ya DB-only'dir ya da başka migration araçlarıyla yönetilir.
# ÖNEMLİ: Bu listeye EKLE, çıkarma — çıkarmak DROP riskine yol açar.
ALEMBIC_EXCLUDE_TABLES = {
    # DB-only tablolar (ORM modeli yok, elle SQL ile yaratıldı)
    "subjects",  # yks_estimator.py kullanıyor, slug dahil
    # "user_item_fsrs",  # Migration 20260410/user_item_fsrs_001 tarafından yönetiliyor
    "user_theta",  # eski theta storage
    "yks_exam_goals",  # YKS hedef tablosu
    # Chat/session tabloları (legacy, ORM dışı)
    "chat_sessions",
    "chat_messages",
    # Analytics/tracking (legacy, ORM dışı)
    "kiro2_learning_events_synthetic",
    "parent_notifications",
    "learning_progress_daily",
    "streak_tracking",
    "daily_plans",
    "platform_stats",
    # Sprint 5 ile elle oluşturulan tablolar (02.04.2026)
    "weekly_reports",
    "osym_questions",
    "osb_settings",
    "performance_history",
    "study_rooms",
}


def include_object(object, name, type_, reflected, compare_to):
    """
    Alembic autogenerate'e hangi nesnelerin dahil edileceğini belirler.
    KURAL: Bu fonksiyon olmadan autogenerate çalıştırma!
    """
    # DB-only tabloları atla (DROP önerisini önle)
    if type_ == "table" and name in ALEMBIC_EXCLUDE_TABLES:
        return False
    # pgvector 'embedding' kolonunu atla (SQLAlchemy NullType → karşılaştırma hatası)
    if type_ == "column" and name == "embedding":
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=False,  # VARCHAR/String, NUMERIC/Float gürültüsünü sustur
        compare_server_default=False,  # Server default farklarını sustur
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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=False,  # VARCHAR/String, NUMERIC/Float gürültüsünü sustur
            compare_server_default=False,  # Server default farklarını sustur
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
