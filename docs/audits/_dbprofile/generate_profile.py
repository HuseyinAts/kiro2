"""Deterministic per-column profiler — GUARANTEES every column of every table is covered.
Step 1: dump ALL columns (structural completeness proof) -> columns_meta.tsv
Step 2: generate per-column profile SQL for non-empty tables -> profile.sql
Run profile.sql via psql to get column_profile.tsv (null%/distinct/sample per column)."""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent
PSQL = r"C:/Program Files/PostgreSQL/18/bin/psql.exe"
ARGS = [PSQL, "-p", "5434", "-U", "postgres", "-d", "kiro2", "-A", "-t", "-F", "\t"]

def q(sql):
    r = subprocess.run(ARGS + ["-c", sql], capture_output=True, text=True, encoding="utf-8")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]

# inventory -> rows per table
rows_of = {}
for ln in (HERE / "inventory.tsv").read_text(encoding="utf-8").splitlines():
    if "\t" in ln:
        t, r, c = ln.split("\t")
        rows_of[t] = int(r)

# ALL columns (the completeness proof — 2421 rows)
cols = q("""
SELECT table_name, ordinal_position, column_name, data_type,
       is_nullable, coalesce(column_default,'')
FROM information_schema.columns
WHERE table_schema='public'
ORDER BY table_name, ordinal_position;""")
(HERE / "columns_meta.tsv").write_text(
    "table\tord\tcolumn\ttype\tnullable\tdefault\n" + "\n".join(cols) + "\n", encoding="utf-8")
print(f"columns_meta.tsv: {len(cols)} columns across {len(set(c.split(chr(9))[0] for c in cols))} tables")

# generate per-column profile SQL for NON-EMPTY tables
stmts = []
ncol = 0
for c in cols:
    parts = c.split("\t")
    tbl, col, typ = parts[0], parts[2], parts[3]
    if rows_of.get(tbl, 0) == 0:
        continue
    ncol += 1
    # null count + distinct count + up to 3 sample distinct values (text, 50 chars)
    stmts.append(
        f"SELECT '{tbl}' t,'{col}' c,'{typ}' typ,"
        f"count(*) FILTER (WHERE \"{col}\" IS NULL) nulls,"
        f"count(DISTINCT left(\"{col}\"::text,200)) dist,"
        f"replace(left(coalesce(string_agg(DISTINCT left(\"{col}\"::text,40),' | '),''),120),E'\\n',' ') samples "
        f"FROM (SELECT \"{col}\" FROM public.\"{tbl}\" LIMIT 200000) s_{ncol};")
hdr = "\\pset footer off\n\\timing off\n"
(HERE / "profile.sql").write_text(hdr + "\n".join(stmts) + "\n", encoding="utf-8")
print(f"profile.sql: {len(stmts)} per-column profile statements (non-empty tables)")
print("Run: psql ... -A -t -F tab -f profile.sql > column_profile.tsv")
