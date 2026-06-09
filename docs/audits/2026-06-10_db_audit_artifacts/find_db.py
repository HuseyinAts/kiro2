"""Locate the REAL KIRO2 database using the backend's own configured connection.
Prints masked URL, connects via the app's driver, checks question_bank, lists top tables.
Read-only."""
import os, re

url = (os.environ.get("DATABASE_URL")
       or os.environ.get("ASYNC_DATABASE_URL")
       or os.environ.get("SQLALCHEMY_DATABASE_URI")
       or "")

masked = re.sub(r"://([^:/]+):[^@]+@", r"://\1:****@", url)
print("DATABASE_URL (masked):", masked or "(empty)")
print("target host/db:", url.split("@")[-1] if "@" in url else "(unknown)")
if not url:
    print("!! No DB URL in backend env. Check config file / .env mounting.")

plain = re.sub(r"\+\w+", "", url)  # strip +asyncpg / +psycopg etc.


def report_sync():
    import sqlalchemy as sa
    eng = sa.create_engine(plain, connect_args={"connect_timeout": 5})
    with eng.connect() as c:
        db = c.exec_driver_sql("SELECT current_database()").scalar()
        host = c.exec_driver_sql("SELECT inet_server_addr()::text").scalar()
        hasqb = c.exec_driver_sql(
            "SELECT to_regclass('public.question_bank') IS NOT NULL").scalar()
        print(f"[sqlalchemy] connected  db={db}  server_addr={host}  has_question_bank={hasqb}")
        if hasqb:
            print("question_bank rows:",
                  c.exec_driver_sql("SELECT count(*) FROM question_bank").scalar())
        rows = c.exec_driver_sql(
            "SELECT relname, n_live_tup FROM pg_stat_user_tables "
            "ORDER BY n_live_tup DESC LIMIT 20").fetchall()
        print("top 20 tables (name, live_rows):")
        for r in rows:
            print("   ", r[0], r[1])
        print("total user tables:",
              c.exec_driver_sql(
                  "SELECT count(*) FROM information_schema.tables "
                  "WHERE table_schema='public'").scalar())


def report_asyncpg():
    import asyncio, asyncpg

    async def run():
        conn = await asyncpg.connect(dsn=plain, timeout=5)
        try:
            db = await conn.fetchval("SELECT current_database()")
            host = await conn.fetchval("SELECT inet_server_addr()::text")
            hasqb = await conn.fetchval(
                "SELECT to_regclass('public.question_bank') IS NOT NULL")
            print(f"[asyncpg] connected  db={db}  server_addr={host}  has_question_bank={hasqb}")
            if hasqb:
                print("question_bank rows:",
                      await conn.fetchval("SELECT count(*) FROM question_bank"))
            rows = await conn.fetch(
                "SELECT relname, n_live_tup FROM pg_stat_user_tables "
                "ORDER BY n_live_tup DESC LIMIT 20")
            print("top 20 tables (name, live_rows):")
            for r in rows:
                print("   ", r["relname"], r["n_live_tup"])
            total = await conn.fetchval(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema='public'")
            print("total user tables:", total)
        finally:
            await conn.close()

    asyncio.run(run())


err = []
for fn in (report_sync, report_asyncpg):
    try:
        fn()
        break
    except Exception as e:
        err.append(f"{fn.__name__}: {e!r}")
else:
    print("!! Could not connect with either driver:")
    for e in err:
        print("   ", e)
