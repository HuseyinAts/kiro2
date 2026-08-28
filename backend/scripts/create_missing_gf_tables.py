"""Create missing GF tables from their ORM models (stamp-drift remediation).

Root cause (Session 2026-06-23): alembic is stamped at head but 7 tables were
never physically created. Their ORM models exist but their Tables are not on the
central Base.metadata until their modules are imported. This script imports those
modules, then creates ONLY the requested tables with checkfirst=True (additive,
never drops, never touches existing tables/data).

Usage (inside container):
    python /app/scripts/create_missing_gf_tables.py teacher_pool_profiles
    python /app/scripts/create_missing_gf_tables.py --all
    python /app/scripts/create_missing_gf_tables.py --verify-only
"""

import asyncio
import sys

# Importing these modules registers their Table objects on core.database.Base.metadata
import models
import models.eba_video
import models.khan_content
import models.kvkk_models
import models.teacher_classroom
import models.teacher_pool
import models.video_solution  # noqa: F401
from core.database import Base, db_manager  # db_manager.engine after initialize()

TARGET_TABLES = [
    "teacher_pool_profiles",
    "teacher_classrooms",
    "video_solutions",
    "kvkk_consents",
    "khan_oauth_tokens",
    "eba_video_watches",
    "kvkk_data_export_requests",
]


def _registered():
    return set(Base.metadata.tables.keys())


async def _verify():
    from sqlalchemy import text

    async with db_manager.engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name = ANY(:names)"
            ),
            {"names": TARGET_TABLES},
        )
        present = {r[0] for r in rows}
    for t in TARGET_TABLES:
        print(f"  {t:35} {'EXISTS' if t in present else 'MISSING'}")
    return present


async def _create(table_names):
    reg = _registered()
    missing_from_meta = [t for t in table_names if t not in reg]
    if missing_from_meta:
        print(f"ABORT: not on metadata after import: {missing_from_meta}")
        sys.exit(2)
    tables = [Base.metadata.tables[t] for t in table_names]
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=tables, checkfirst=True
            )
        )
    print(f"create_all done (checkfirst=True) for: {table_names}")


async def main():
    await db_manager.initialize()
    args = sys.argv[1:]
    if not args or args == ["--verify-only"]:
        print("=== verify ===")
        await _verify()
        return
    if args == ["--all"]:
        targets = TARGET_TABLES
    else:
        targets = args
        bad = [t for t in targets if t not in TARGET_TABLES]
        if bad:
            print(f"ABORT: not in allowlist: {bad}")
            sys.exit(2)
    print("=== before ===")
    await _verify()
    await _create(targets)
    print("=== after ===")
    await _verify()


if __name__ == "__main__":
    asyncio.run(main())
