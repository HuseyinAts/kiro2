import asyncio
import asyncpg


async def check_schema():
    conn = await asyncpg.connect(
        "postgresql://teknofest:TeknoFest2025SecurePass@localhost:5432/teknofest_db"
    )

    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )
    views = await conn.fetch(
        "SELECT viewname FROM pg_views WHERE schemaname='public' ORDER BY viewname"
    )

    print("TABLES:")
    for r in tables:
        print(f'  {r["tablename"]}')

    print("\nVIEWS:")
    for r in views:
        print(f'  {r["viewname"]}')

    await conn.close()


asyncio.run(check_schema())
