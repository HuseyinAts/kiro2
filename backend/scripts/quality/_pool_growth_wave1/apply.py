"""Wave-1 apply: classify blind-solver predictions vs DB answer key, flag pool.

Usage:
  python apply.py            # dry-run: print classification + A-bias, write nothing
  python apply.py apply      # backup + apply metadata flags via psql

Safety invariants (NON-NEGOTIABLE):
  - correct_answer, is_active, quality_review_status are NEVER touched.
  - Only pipeline_metadata (json) gets merged flags. Fully reversible via backup.
  - AGREE (blind == DB) AND confidence >= MIN_CONF -> verified_provisional="true".
  - DISPUTE (blind != DB)      -> blind_answer_dispute_solver flag (2nd-signal queue).
  - UNSOLVABLE                 -> blind_unsolvable_solver flag (quarantine candidate).
"""

import csv
import glob
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_pool_growth_wave1")
MASTER = BASE / "master.csv"
PREDS_GLOB = str(BASE / "batches" / "preds_*.json")
APPLY_SQL = BASE / "apply.sql"
RUN_TAG = "2026_06_03_wave1"
BACKUP_TABLE = "question_bank_pool_growth_wave1_backup_20260603"
MIN_CONF = 0.6
PSQL = r"C:/Program Files/PostgreSQL/18/bin/psql.exe"

mode = sys.argv[1] if len(sys.argv) > 1 else "dry"

# ---- load answer key (master is single-col CSV of JSON objects) ----
key = {}
subject = {}
with MASTER.open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if not record:
            continue
        o = json.loads(record[0])
        key[o["id"]] = o["key"]
        subject[o["id"]] = o.get("subject")

# ---- load predictions ----
preds = {}
files = sorted(glob.glob(PREDS_GLOB))
for fp in files:
    try:
        data = json.loads(Path(fp).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARN unreadable {fp}: {e}")
        continue
    for p in data:
        pid = p.get("id")
        if pid in key:
            preds[pid] = p

# ---- classify ----
agree, dispute, unsolvable, weak_agree, bad = [], [], [], [], []
solver_dist = Counter()
for pid, ans in key.items():
    p = preds.get(pid)
    if not p:
        continue
    a = str(p.get("answer", "")).strip().upper()
    conf = float(p.get("confidence", 0) or 0)
    if a in ("A", "B", "C", "D", "E"):
        solver_dist[a] += 1
        if a == ans:
            (agree if conf >= MIN_CONF else weak_agree).append((pid, a, conf))
        else:
            dispute.append((pid, a, conf, ans))
    elif a in ("UNSOLVABLE", "UNSOLVED", "SKIP"):
        unsolvable.append((pid, conf))
    else:
        bad.append((pid, a))

solved = sum(solver_dist.values())
total_pred = len(preds)
print(f"=== WAVE-1 CLASSIFICATION (mode={mode}) ===")
print(
    f"candidates(master)={len(key)}  predictions={total_pred}  missing={len(key) - total_pred}"
)
print(
    f"AGREE(conf>={MIN_CONF})={len(agree)}  weak_agree(conf<{MIN_CONF})={len(weak_agree)}"
)
print(f"DISPUTE={len(dispute)}  UNSOLVABLE={len(unsolvable)}  bad_parse={len(bad)}")
if total_pred:
    print(
        f"AGREE_rate={len(agree) / total_pred:.1%}  DISPUTE_rate={len(dispute) / total_pred:.1%}"
    )
print("--- A-BIAS GUARD (solver answer distribution, solved only) ---")
for opt in "ABCDE":
    n = solver_dist[opt]
    print(f"  {opt}: {n:5d}  {n / solved:.1%}" if solved else f"  {opt}: 0")
if solved:
    top = max(solver_dist.values()) / solved
    print(f"  max_bucket={top:.1%}  ({'PATHOLOGICAL' if top > 0.45 else 'ok'})")

if mode != "apply":
    print("\n[dry-run] no DB writes. Re-run with 'apply' to flag the pool.")
    sys.exit(0)


# ---- build apply.sql ----
def merge(pid, obj):
    j = json.dumps(obj).replace("'", "''")
    return (
        f"UPDATE question_bank SET pipeline_metadata = "
        f"(COALESCE(pipeline_metadata::jsonb,'{{}}'::jsonb) || '{j}'::jsonb)::json "
        f"WHERE id = '{pid}';"
    )


touched = [p[0] for p in agree] + [p[0] for p in dispute] + [p[0] for p in unsolvable]
id_list = ",".join(f"'{i}'" for i in touched)

lines = ["BEGIN;"]
lines.append(f"DROP TABLE IF EXISTS {BACKUP_TABLE};")
lines.append(
    f"CREATE TABLE {BACKUP_TABLE} AS SELECT id, pipeline_metadata, "
    f"quality_review_status, is_active FROM question_bank WHERE id IN ({id_list});"
)
for pid, a, conf in agree:
    lines.append(
        merge(
            pid,
            {
                "verified_provisional": "true",
                "pool_growth_solver": RUN_TAG,
                "blind_solve_method": "single_solver_agree",
                "blind_solver_answer": a,
                "blind_solver_conf": round(conf, 2),
            },
        )
    )
for pid, a, conf, ans in dispute:
    lines.append(
        merge(
            pid,
            {
                "blind_answer_dispute_solver": RUN_TAG,
                "blind_predicted": a,
                "blind_solver_conf": round(conf, 2),
            },
        )
    )
for pid, conf in unsolvable:
    lines.append(merge(pid, {"blind_unsolvable_solver": RUN_TAG}))
lines.append("COMMIT;")
APPLY_SQL.write_text("\n".join(lines), encoding="utf-8")
print(
    f"\napply.sql written: {len(touched)} rows touched "
    f"(agree={len(agree)} dispute={len(dispute)} unsolvable={len(unsolvable)})"
)

# ---- run ----
env = dict(os.environ)
env.setdefault("PGPASSWORD", env.get("KIRO2_DB_PASSWORD", "postgres"))
r = subprocess.run(
    [
        PSQL,
        "-h",
        "localhost",
        "-p",
        "5434",
        "-U",
        "postgres",
        "-d",
        "kiro2",
        "-v",
        "ON_ERROR_STOP=1",
        "-f",
        str(APPLY_SQL),
    ],
    env=env,
    capture_output=True,
    text=True,
)
print("STDOUT:", r.stdout[-2000:])
print("STDERR:", r.stderr[-2000:])
print("returncode:", r.returncode)
