"""KIRO2 FULL DB AUDIT (schema + data-quality), READ-ONLY.
Runs through the backend's own DATABASE_URL (psycopg2 sync).
Writes a complete plain-text report to /tmp/db_audit_output.txt.
Catalog-driven: discovers every table & column. No truncation."""
import os, re, sys, datetime

url = (os.environ.get("DATABASE_URL")
       or os.environ.get("ASYNC_DATABASE_URL")
       or os.environ.get("SQLALCHEMY_DATABASE_URI") or "")
plain = re.sub(r"\+\w+", "", url)  # strip +asyncpg etc -> psycopg2

import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})

OUT = "/tmp/db_audit_output.txt"
fh = open(OUT, "w", encoding="utf-8")
def w(*a):
    line = " ".join(str(x) for x in a)
    fh.write(line + "\n")
def hdr(t):
    w("\n" + "=" * 70); w(t); w("=" * 70)

def q(conn, sql):
    return conn.exec_driver_sql(sql).fetchall()
def qquote(name):
    return '"' + name.replace('"', '""') + '"'

with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    w("KIRO2 FULL DB AUDIT  -", datetime.datetime.now().isoformat())
    w("target:", re.sub(r"://([^:/]+):[^@]+@", r"://\1:****@", url))

    # ---- A. OVERVIEW ----
    hdr("A. DATABASE OVERVIEW")
    row = q(c, "SELECT current_database(), pg_size_pretty(pg_database_size(current_database())), "
               "(SELECT count(*) FROM pg_tables WHERE schemaname='public'), "
               "(SELECT count(*) FROM pg_views WHERE schemaname='public')")[0]
    w(f"db={row[0]}  size={row[1]}  public_tables={row[2]}  public_views={row[3]}")
    enc = q(c, "SELECT pg_encoding_to_char(encoding), datcollate, datctype FROM pg_database WHERE datname=current_database()")[0]
    w(f"encoding={enc[0]}  collate={enc[1]}  ctype={enc[2]}")

    # ---- B. TABLE INVENTORY ----
    hdr("B. TABLE INVENTORY (size, est/live/dead rows, last analyze)")
    rows = q(c, """SELECT c.relname, pg_size_pretty(pg_total_relation_size(c.oid)),
                          c.reltuples::bigint, s.n_live_tup, s.n_dead_tup,
                          s.last_analyze, s.last_autoanalyze
                   FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                   LEFT JOIN pg_stat_user_tables s ON s.relid=c.oid
                   WHERE c.relkind='r' AND n.nspname='public'
                   ORDER BY pg_total_relation_size(c.oid) DESC""")
    w(f"{'table':45} {'size':>10} {'est':>10} {'live':>10} {'dead':>8}  last_analyze")
    for r in rows:
        la = r[5] or r[6]
        w(f"{r[0]:45} {str(r[1]):>10} {str(r[2]):>10} {str(r[3]):>10} {str(r[4]):>8}  {la}")

    # ---- C. EXACT ROW COUNTS ----
    hdr("C. EXACT ROW COUNTS (every table)")
    tbls = [r[0] for r in q(c, "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")]
    counts = {}
    for t in tbls:
        try:
            n = c.exec_driver_sql(f'SELECT count(*) FROM public.{qquote(t)}').scalar()
        except Exception as e:
            n = f"ERR {e.__class__.__name__}"
        counts[t] = n
    for t in sorted(counts, key=lambda x: (counts[x] if isinstance(counts[x], int) else -1), reverse=True):
        w(f"{t:50} {counts[t]}")

    # ---- D. ALL COLUMNS ----
    hdr("D. ALL COLUMNS (table.column : type | nullable | default)")
    rows = q(c, """SELECT table_name, ordinal_position, column_name, data_type,
                          COALESCE(character_maximum_length::text,
                                   numeric_precision::text,'') ,
                          is_nullable, column_default
                   FROM information_schema.columns
                   WHERE table_schema='public'
                   ORDER BY table_name, ordinal_position""")
    cur = None
    for r in rows:
        if r[0] != cur:
            cur = r[0]; w(f"\n# {cur}")
        lp = f"({r[4]})" if r[4] else ""
        nn = "NULL" if r[5] == "YES" else "NOT NULL"
        dflt = f" default={r[6]}" if r[6] else ""
        w(f"   {r[2]} : {r[3]}{lp} | {nn}{dflt}")

    # ---- E. CONSTRAINTS ----
    hdr("E. CONSTRAINTS (PK/FK/UNIQUE/CHECK)")
    rows = q(c, """SELECT rel.relname, c.conname,
                     CASE c.contype WHEN 'p' THEN 'PK' WHEN 'f' THEN 'FK'
                          WHEN 'u' THEN 'UNIQUE' WHEN 'c' THEN 'CHECK'
                          WHEN 'x' THEN 'EXCLUDE' ELSE c.contype::text END,
                     pg_get_constraintdef(c.oid)
                   FROM pg_constraint c
                   JOIN pg_class rel ON rel.oid=c.conrelid
                   JOIN pg_namespace n ON n.oid=rel.relnamespace
                   WHERE n.nspname='public'
                   ORDER BY rel.relname, 3, c.conname""")
    cur = None
    for r in rows:
        if r[0] != cur:
            cur = r[0]; w(f"\n# {cur}")
        w(f"   [{r[2]}] {r[1]} :: {r[3]}")

    # ---- F. TABLES WITHOUT PK ----
    hdr("F. GAP: TABLES WITHOUT PRIMARY KEY")
    rows = q(c, """SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                   WHERE c.relkind='r' AND n.nspname='public'
                     AND NOT EXISTS (SELECT 1 FROM pg_constraint k WHERE k.conrelid=c.oid AND k.contype='p')
                   ORDER BY 1""")
    if rows:
        for r in rows: w("   ", r[0])
    else:
        w("   (none)")

    # ---- G. INDEXES ----
    hdr("G. INDEXES")
    rows = q(c, "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename, indexname")
    cur = None
    for r in rows:
        if r[0] != cur:
            cur = r[0]; w(f"\n# {cur}")
        w(f"   {r[1]} :: {r[2]}")

    # ---- H. UNINDEXED FKs ----
    hdr("H. GAP: FOREIGN KEYS WITHOUT SUPPORTING INDEX")
    rows = q(c, """SELECT rel.relname, c.conname, pg_get_constraintdef(c.oid)
                   FROM pg_constraint c
                   JOIN pg_class rel ON rel.oid=c.conrelid
                   JOIN pg_namespace n ON n.oid=rel.relnamespace
                   WHERE c.contype='f' AND n.nspname='public'
                     AND NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid=c.conrelid AND c.conkey[1]=i.indkey[0])
                   ORDER BY rel.relname""")
    if rows:
        for r in rows: w(f"   {r[0]}.{r[1]} :: {r[2]}")
    else:
        w("   (none)")

    # ---- L. ENUMS ----
    hdr("L. ENUM TYPES")
    rows = q(c, """SELECT t.typname, string_agg(e.enumlabel,', ' ORDER BY e.enumsortorder)
                   FROM pg_type t JOIN pg_enum e ON e.enumtypid=t.oid
                   JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='public'
                   GROUP BY t.typname ORDER BY t.typname""")
    if rows:
        for r in rows: w(f"   {r[0]}: {r[1]}")
    else:
        w("   (none)")

    # ---- M. ALEMBIC ----
    hdr("M. ALEMBIC MIGRATION HEAD")
    if c.exec_driver_sql("SELECT to_regclass('public.alembic_version') IS NOT NULL").scalar():
        w("   ", [r[0] for r in q(c, "SELECT version_num FROM alembic_version")])
    else:
        w("   (no alembic_version table)")

    # ---- I. NULL COUNTS per column (one scan per table) ----
    hdr("I. NULL COUNTS per column  (col : nulls/total = pct)")
    cols_by_tbl = {}
    for r in q(c, "SELECT table_name, column_name, ordinal_position FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position"):
        cols_by_tbl.setdefault(r[0], []).append(r[1])
    for t, cols in cols_by_tbl.items():
        sel = ", ".join(f'count(*) FILTER (WHERE {qquote(col)} IS NULL) AS c{i}' for i, col in enumerate(cols))
        try:
            row = c.exec_driver_sql(f'SELECT count(*) AS total, {sel} FROM public.{qquote(t)}').fetchone()
        except Exception as e:
            w(f"\n# {t}  ERROR {e.__class__.__name__}: {e}"); continue
        total = row[0]
        w(f"\n# {t}  (total={total})")
        for i, col in enumerate(cols):
            nulls = row[i + 1]
            pct = (100.0 * nulls / total) if total else 0.0
            flag = "  <-- ALL NULL" if total and nulls == total else ("  <-- high" if pct >= 50 and total else "")
            w(f"   {col} : {nulls}/{total} = {pct:.1f}%{flag}")

    # ---- K. FK ORPHANS ----
    hdr("K. FK ORPHAN CHECK (referential integrity)")
    fkmeta = q(c, """
      WITH fk AS (
        SELECT c.oid conoid, c.conname, c.conrelid, c.confrelid, c.conkey, c.confkey,
               rel.relname tbl, frel.relname ftbl
        FROM pg_constraint c
        JOIN pg_class rel ON rel.oid=c.conrelid
        JOIN pg_namespace ns ON ns.oid=rel.relnamespace
        JOIN pg_class frel ON frel.oid=c.confrelid
        WHERE c.contype='f' AND ns.nspname='public')
      SELECT fk.conname, fk.tbl, fk.ftbl,
             string_agg('c.'||quote_ident(att.attname)||' = p.'||quote_ident(fatt.attname),' AND ' ORDER BY k.ord),
             string_agg('c.'||quote_ident(att.attname)||' IS NOT NULL',' AND ' ORDER BY k.ord)
      FROM fk
      JOIN LATERAL unnest(fk.conkey)  WITH ORDINALITY AS k(attnum,ord)   ON true
      JOIN LATERAL unnest(fk.confkey) WITH ORDINALITY AS fk2(fattnum,ford) ON fk2.ford=k.ord
      JOIN pg_attribute att  ON att.attrelid=fk.conrelid  AND att.attnum=k.attnum
      JOIN pg_attribute fatt ON fatt.attrelid=fk.confrelid AND fatt.attnum=fk2.fattnum
      GROUP BY fk.conname, fk.tbl, fk.ftbl ORDER BY fk.tbl, fk.conname""")
    any_orphan = False
    for conname, tbl, ftbl, joincond, notnull in fkmeta:
        sql = (f'SELECT count(*) FROM public.{qquote(tbl)} c '
               f'WHERE ({notnull}) AND NOT EXISTS (SELECT 1 FROM public.{qquote(ftbl)} p WHERE {joincond})')
        try:
            n = c.exec_driver_sql(sql).scalar()
        except Exception as e:
            w(f"   {conname} ({tbl}->{ftbl}) ERROR {e.__class__.__name__}"); continue
        if n and n > 0:
            any_orphan = True
            w(f"   !! {conname}: {tbl} -> {ftbl}  ORPHANS={n}")
    if not any_orphan:
        w("   (no orphan FK rows found)")

    # ---- J. KIRO2 QUALITY ----
    hdr("J. KIRO2-SPECIFIC QUALITY CHECKS")
    def colexists(t, col):
        return c.exec_driver_sql(
            "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND column_name=%s)" ,
            (t, col)).scalar()
    qb = "question_bank"
    if c.exec_driver_sql("SELECT to_regclass('public.question_bank') IS NOT NULL").scalar():
        if colexists(qb, "is_active"):
            r = q(c, "SELECT count(*), count(*) FILTER (WHERE is_active), count(*) FILTER (WHERE NOT is_active) FROM question_bank")[0]
            w(f"J1 question_bank: total={r[0]} active={r[1]} inactive={r[2]}")
        if c.exec_driver_sql("SELECT to_regclass('public.questions') IS NOT NULL").scalar():
            w("J1 legacy questions total:", c.exec_driver_sql("SELECT count(*) FROM questions").scalar())
        if colexists(qb, "quality_review_status") and colexists(qb, "is_active"):
            w("J2 quality_review_status (status | n | still_active):")
            for r in q(c, "SELECT quality_review_status, count(*), count(*) FILTER (WHERE is_active) FROM question_bank GROUP BY 1 ORDER BY 2 DESC"):
                leak = "   <-- LEAK (rejected+active)" if (r[0] == "rejected" and r[2]) else ""
                w(f"     {r[0]} | {r[1]} | active={r[2]}{leak}")
        if colexists(qb, "subject_area"):
            w("J3 subject_area distribution:")
            for r in q(c, "SELECT subject_area, count(*) FROM question_bank GROUP BY 1 ORDER BY 1"):
                w(f"     {r[0]} | {r[1]}")
            w("J3 subject_area NOT uppercase:",
              c.exec_driver_sql("SELECT count(*) FROM question_bank WHERE subject_area IS NOT NULL AND subject_area<>upper(subject_area)").scalar())
        if colexists(qb, "exam_type"):
            w("J4 exam_type distribution:")
            for r in q(c, "SELECT exam_type, count(*) FROM question_bank GROUP BY 1 ORDER BY 2 DESC"):
                w(f"     {r[0]} | {r[1]}")
        if colexists(qb, "question_image_url"):
            r = q(c, "SELECT count(*), count(*) FILTER (WHERE question_image_url IS NULL OR question_image_url='') FROM question_bank")[0]
            w(f"J5 image coverage: total={r[0]} missing={r[1]} ({100.0*r[1]/r[0]:.1f}% missing)")
        if colexists(qb, "question_text"):
            r = q(c, "SELECT count(*), COALESCE(sum(c-1),0) FROM (SELECT md5(question_text) h, count(*) c FROM question_bank WHERE question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1) t")[0]
            w(f"J6 duplicate question_text: groups={r[0]} extra_rows={r[1]}")
            r = q(c, "SELECT count(*) FILTER (WHERE position(chr(65533) in question_text)>0), count(*) FILTER (WHERE question_text ~ '[[:cntrl:]]') FROM question_bank WHERE question_text IS NOT NULL")[0]
            w(f"J7 encoding flags: replacement_char_rows={r[0]} control_char_rows={r[1]}")
            w("J8 empty(whitespace) question_text:",
              c.exec_driver_sql("SELECT count(*) FROM question_bank WHERE question_text IS NOT NULL AND btrim(question_text)=''").scalar())

    w("\n" + "=" * 70); w("AUDIT COMPLETE", datetime.datetime.now().isoformat()); w("=" * 70)

fh.close()
nlines = sum(1 for _ in open(OUT, encoding="utf-8"))
print(f"WROTE {OUT}  ({nlines} lines)")
