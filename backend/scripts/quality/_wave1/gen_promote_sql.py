"""Generate reversible backup + promote SQL for wave1 (AYT-Edebiyat).

Reads promote_A_ids.json (+ promote_B_ids.json if --tiers AB) and emits:
  wave1_backup.sql    CREATE TABLE ..._backup_20260619 AS SELECT id,status,metadata WHERE id IN (...)
  wave1_promote.sql    UPDATE status=auto_judged_high + jsonb_set wave1_run=true WHERE id IN (...)

correct_answer / is_active'e DOKUNULMAZ. Sadece quality_review_status + pipeline_metadata.

Usage:
  python gen_promote_sql.py --tiers A     # only TIER-A (g==q==key)
  python gen_promote_sql.py --tiers AB    # TIER-A + TIER-B
"""

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_wave1")
BACKUP_TABLE = "question_bank_wave1_ayt_edebiyat_backup_20260619"

ap = argparse.ArgumentParser()
ap.add_argument("--tiers", choices=["A", "AB"], default="A")
args = ap.parse_args()

ids = json.loads((BASE / "promote_A_ids.json").read_text(encoding="utf-8"))
if args.tiers == "AB":
    ids += json.loads((BASE / "promote_B_ids.json").read_text(encoding="utf-8"))
ids = sorted(set(ids))
if not ids:
    print("[!] promote id listesi BOS — DUR.")
    sys.exit(1)

id_list = ",\n  ".join(f"'{i}'" for i in ids)
in_clause = f"(\n  {id_list}\n)"

backup = f"""-- WAVE1 BACKUP (reversible). tiers={args.tiers}, n={len(ids)}.
-- Rollback: UPDATE question_bank q SET quality_review_status=b.quality_review_status,
--   pipeline_metadata=b.pipeline_metadata FROM {BACKUP_TABLE} b WHERE q.id=b.id;
DROP TABLE IF EXISTS {BACKUP_TABLE};
CREATE TABLE {BACKUP_TABLE} AS
SELECT id, quality_review_status, pipeline_metadata
FROM question_bank
WHERE id IN {in_clause};
SELECT count(*) AS backed_up FROM {BACKUP_TABLE};
"""

promote = f"""-- WAVE1 PROMOTE. tiers={args.tiers}, n={len(ids)}.
-- correct_answer / is_active DOKUNULMAZ. status + pipeline_metadata.wave1_run yalniz.
UPDATE question_bank
SET quality_review_status = 'auto_judged_high',
    pipeline_metadata = jsonb_set(
      COALESCE(pipeline_metadata::jsonb, '{{}}'::jsonb),
      '{{wave1_run}}', 'true'::jsonb)
WHERE id IN {in_clause};
SELECT count(*) AS promoted FROM question_bank
WHERE pipeline_metadata::jsonb ? 'wave1_run';
"""

(BASE / "wave1_backup.sql").write_text(backup, encoding="utf-8")
(BASE / "wave1_promote.sql").write_text(promote, encoding="utf-8")
print(
    f"wave1_backup.sql + wave1_promote.sql yazildi (tiers={args.tiers}, n={len(ids)})."
)
