import asyncio
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("varchar_restorer")

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)


async def run_migration():
    logger.info("Initializing VARCHAR Restorer Engine...")
    engine = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        fks_query = text("""
            SELECT
                c.conname AS constraint_name,
                conrelid::regclass::text AS table_name,
                a.attname AS column_name,
                confrelid::regclass::text AS referenced_table_name,
                af.attname AS referenced_column_name,
                c.confupdtype,
                c.confdeltype
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
            JOIN pg_attribute af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
            WHERE c.contype = 'f';
        """)
        fks_results = await conn.execute(fks_query)
        fks = fks_results.fetchall()

        cols_query = text("""
            SELECT table_name, column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND data_type = 'uuid'
              AND (column_name = 'id' OR column_name LIKE '%_id');
        """)
        cols_results = await conn.execute(cols_query)
        cols = cols_results.fetchall()

        target_columns = [(row[0], row[1]) for row in cols]

        logger.info(f"Found {len(fks)} foreign keys.")
        logger.info(f"Found {len(target_columns)} UUID columns to revert.")

        for fk in fks:
            constraint_name = fk[0]
            table_name = fk[1]
            try:
                await conn.execute(
                    text(
                        f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{constraint_name}";'
                    )
                )
            except Exception:
                pass

        for table_name, column_name in target_columns:
            try:
                alter_stmt = f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE character varying(36) USING "{column_name}"::text;'
                await conn.execute(text(alter_stmt))
                logger.info(f"Reverted {table_name}.{column_name} to VARCHAR")
            except Exception as e:
                logger.error(f"Error reverting {table_name}.{column_name}: {e}")

        action_map = {
            "a": "NO ACTION",
            "r": "RESTRICT",
            "c": "CASCADE",
            "n": "SET NULL",
            "d": "SET DEFAULT",
        }
        for fk in fks:
            constraint_name = fk[0]
            table_name = fk[1]
            column_name = fk[2]
            ref_table = fk[3]
            ref_col = fk[4]
            upd = action_map.get(fk[5], "NO ACTION")
            del_ = action_map.get(fk[6], "NO ACTION")

            create_fk = f"""
                ALTER TABLE "{table_name}"
                ADD CONSTRAINT "{constraint_name}"
                FOREIGN KEY ("{column_name}")
                REFERENCES "{ref_table}" ("{ref_col}")
                ON UPDATE {upd} ON DELETE {del_};
            """
            try:
                await conn.execute(text(create_fk))
                logger.info(f"Recreated FK {constraint_name} on {table_name}")
            except Exception as e:
                logger.error(
                    f"Error recreating FK {constraint_name} on {table_name}: {e}"
                )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
