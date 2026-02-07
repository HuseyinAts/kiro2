import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def check_tables():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/turkiye_sinav_db"
    )
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
            )
        )
        tables = [row[0] for row in result]
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        # Check alembic version
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            versions = [row[0] for row in result]
            print(f"\nAlembic versions: {versions}")
        except:
            print("\nNo alembic_version table")

    await engine.dispose()


asyncio.run(check_tables())
