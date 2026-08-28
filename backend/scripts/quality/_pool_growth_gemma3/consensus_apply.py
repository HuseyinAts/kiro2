"""Full-run consensus PROMOTION (2-model blind agreement -> auto_judged_high).

Context (measured in pilot + 30-dispute manual audit):
  - All rows are verified_provisional => qwen3:14b ALREADY blind-solved == DB key.
  - gemma3:12b is the 2nd INDEPENDENT (non-Qwen) blind signal.
  - AGREE (gemma3 == DB key) => 2 independent blind models both produced the
    stored answer => promote to auto_judged_high (enters v_safe_for_beta).
  - DISPUTE (gemma3 != DB key): audit found these are gemma3 errors, NOT DB errors
    (0 DB errors in 30 audited). We only FLAG them (for a future stronger-model
    recovery pass). Status is NOT changed; they stay unverified.
  - gemma3 confidence is degenerate (always >=0.9) -> NOT used as a gate.

INVARIANTS (never violated):
  - correct_answer  : NEVER touched (gemma3 == DB on agrees, so nothing to change).
  - is_active       : NEVER touched.
  - Only AGREES change quality_review_status (unverified -> auto_judged_high).
  - Full backup table written first -> fully reversible.

Usage:
  python consensus_apply.py            # dry-run: classify + write apply.sql, NO DB writes
  python consensus_apply.py apply      # backup + execute via psql
"""

import csv
import glob
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_pool_growth_gemma3")
MASTER = BASE / "master.csv"
PREDS_GLOB = str(BASE / "batches" / "preds_*.json")
APPLY_SQL = BASE / "apply.sql"
RUN_TAG = "2026_06_12_gemma3_consensus"
SECOND_MODEL = "gemma3:12b-it-qat"
BACKUP_TABLE = "question_bank_gemma3_consensus_backup_20260612"
PSQL = r"C:/Program Files/PostgreSQL/18/bin/psql.exe"

mode = sys.argv[1] if len(sys.argv) > 1 else "dry"

# id -> {key, subject}
meta = {}
with MASTER.open(encoding="utf-8", newline="") as f:
    for record in csv.reader(f):
        if not record:
            continue
        o = json.loads(record[0])
        meta[o["id"]] = {"key": str(o["key"]).strip().upper(), "subject": o.get("subject", "?")}

preds = {}
for fp in sorted(glob.glob(PREDS_GLOB)):
    try:
        data = json.loads(Path(fp).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARN unreadable {fp}: {e}")
        continue
    for p in data:
        if p.get("id") in meta:
            preds[p["id"]] = p

agree, dispute, unsolvable = [], [], []
solver_dist = Counter()
subj = defaultdict(lambda: {"a": 0, "d": 0, "u": 0})
for qid, m in meta.items():
    p = preds.get(qid)
    if not p:
        continue
    a = str(p.get("answer", "")).strip().upper()
    conf = round(float(p.get("confidence", 0) or 0), 2)
    if a in ("A", "B", "C", "D", "E"):
        solver_dist[a] += 1
        if a == m["key"]:
            agree.append((qid, a, conf))
            subj[m["subject"]]["a"] += 1
        else:
            dispute.append((qid, a, conf))
            subj[m["subject"]]["d"] += 1
    else:
        unsolvable.append((qid, a))
        subj[m["subject"]]["u"] += 1

total_pred = len(preds)
solved = sum(solver_dist.values())
print(f"=== GEMMA3 CONSENSUS (mode={mode}) ===")
print(f"candidates(master)={len(meta)}  predictions={total_pred}  missing={len(meta)-total_pred}")
print(f"AGREE(promote)={len(agree)}  DISPUTE(flag only)={len(dispute)}  UNSOLVABLE(flag only)={len(unsolvable)}")
if total_pred:
    print(f"promote_rate = {len(agree)/total_pred:.1%}")
print("--- A-BIAS GUARD (gemma3 answer dist, solved only) ---")
for opt in "ABCDE":
    n = solver_dist[opt]
    print(f"  {opt}: {n:5d}  {n/solved:.1%}" if solved else f"  {opt}: 0")
if solved:
    top = max(solver_dist.values()) / solved
    print(f"  max_bucket={top:.1%}  ({'PATHOLOGICAL' if top > 0.45 else 'ok'})")
print("--- per subject (a=promote / d=dispute / u=unsolvable) ---")
for name in sorted(subj, key=lambda k: -(subj[k]['a']+subj[k]['d']+subj[k]['u'])):
    s = subj[name]
    tot = s['a']+s['d']+s['u']
    print(f"  {name:12} n={tot:4} promote={s['a']:4} dispute={s['d']:4} unsolv={s['u']:3} promote%={100*s['a']/tot:4.1f}")

if mode != "apply":
    print("\n[dry-run] NO DB writes. Re-run with 'apply' to promote agrees + flag disputes.")
    sys.exit(0)


def jmerge_obj(d):
    return json.dumps(d).replace("'", "''")


touched = [p[0] for p in agree] + [p[0] for p in dispute] + [p[0] for p in unsolvable]
id_list = ",".join(f"'{i}'" for i in touched)

lines = ["\\set ON_ERROR_STOP on", "BEGIN;"]
lines.append(f"DROP TABLE IF EXISTS {BACKUP_TABLE};")
lines.append(
    f"CREATE TABLE {BACKUP_TABLE} AS SELECT id, correct_answer, quality_review_status, "
    f"is_active, pipeline_metadata FROM question_bank WHERE id IN ({id_list});"
)
# AGREES -> promote to auto_judged_high (status change) + provenance. correct_answer NOT touched.
for pid, a, conf in agree:
    obj = jmerge_obj({
        "consensus_2signal_run": RUN_TAG,
        "consensus_second_model": SECOND_MODEL,
        "gemma3_blind_answer": a,
        "gemma3_blind_conf": conf,
    })
    lines.append(
        "UPDATE question_bank SET quality_review_status='auto_judged_high', "
        f"pipeline_metadata=(pipeline_metadata::jsonb || '{obj}'::jsonb)::json "
        f"WHERE id='{pid}' AND quality_review_status='unverified';"
    )
# DISPUTES -> flag only (no status change), for future recovery pass.
for pid, a, conf in dispute:
    obj = jmerge_obj({"gemma3_blind_dispute": a, "gemma3_dispute_run": RUN_TAG, "gemma3_dispute_conf": conf})
    lines.append(
        "UPDATE question_bank SET "
        f"pipeline_metadata=(pipeline_metadata::jsonb || '{obj}'::jsonb)::json WHERE id='{pid}';"
    )
for pid, a in unsolvable:
    obj = jmerge_obj({"gemma3_blind_unsolvable": RUN_TAG})
    lines.append(
        "UPDATE question_bank SET "
        f"pipeline_metadata=(pipeline_metadata::jsonb || '{obj}'::jsonb)::json WHERE id='{pid}';"
    )
lines.append("COMMIT;")
lines.append(
    f"SELECT (SELECT count(*) FROM question_bank WHERE pipeline_metadata::jsonb->>'consensus_2signal_run'='{RUN_TAG}') AS promoted, "
    f"(SELECT count(*) FROM {BACKUP_TABLE}) AS backup_rows;"
)
APPLY_SQL.write_text("\n".join(lines), encoding="utf-8")
print(f"\napply.sql written: promote={len(agree)} flag_dispute={len(dispute)} flag_unsolv={len(unsolvable)}")

env = dict(os.environ)
env.setdefault("PGPASSWORD", env.get("KIRO2_DB_PASSWORD", "postgres"))
r = subprocess.run(
    [PSQL, "-h", "localhost", "-p", "5434", "-U", "postgres", "-d", "kiro2",
     "-v", "ON_ERROR_STOP=1", "-f", str(APPLY_SQL)],
    env=env, capture_output=True, text=True,
)
print("STDOUT:", r.stdout[-2000:])
print("STDERR:", r.stderr[-1500:])
print("returncode:", r.returncode)
