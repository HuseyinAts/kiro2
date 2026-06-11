"""Find where external changes went: list ALL databases on the :5434 host PG server
(same server backend uses) + recent write activity in current kiro2 db. READ-ONLY."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":15})
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    print("FIND CHANGES -", datetime.datetime.now().isoformat())
    print("target server (DATABASE_URL host):", (url.split('@')[-1] if '@' in url else url))
    print("\n=== :5434 sunucusundaki TUM database'ler (boyut DESC) ===")
    for r in c.exec_driver_sql("""SELECT datname, pg_size_pretty(pg_database_size(datname)) sz,
            (SELECT rolname FROM pg_roles WHERE oid=datdba) owner
            FROM pg_database WHERE datistemplate=false ORDER BY pg_database_size(datname) DESC""").fetchall():
        print(f"   {r[0]:24} {r[1]:>10}   owner={r[2]}")
    print("\n=== current db (kiro2) — son yazilan 15 tablo (last_autoanalyze DESC) ===")
    for r in c.exec_driver_sql("""SELECT relname, n_tup_ins, n_tup_upd, n_tup_del, last_autoanalyze
            FROM pg_stat_user_tables WHERE schemaname='public' AND last_autoanalyze IS NOT NULL
            ORDER BY last_autoanalyze DESC LIMIT 15""").fetchall():
        print(f"   {r[0]:46} ins={r[1]} upd={r[2]} del={r[3]}  {str(r[4])[:19]}")
    print("\n=== en yeni yazma zamani (current db) ===")
    mx = c.exec_driver_sql("SELECT max(last_autoanalyze) FROM pg_stat_user_tables WHERE schemaname='public'").scalar()
    print("   max last_autoanalyze:", mx)
