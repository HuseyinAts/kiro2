import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ids=json.load(open("vp116_confirmed_ids.json", encoding="utf-8"))
assert ids, "no confirmed ids"
inc="(\n  "+",\n  ".join(f"'{i}'" for i in ids)+"\n)"
BT="question_bank_vp116_status_backup_20260619"
Path("vp116_backup.sql").write_text(
 f"""-- VP116 BACKUP (reversible). n={len(ids)}.
DROP TABLE IF EXISTS {BT};
CREATE TABLE {BT} AS SELECT id, quality_review_status, pipeline_metadata FROM question_bank WHERE id IN {inc};
SELECT count(*) AS backed_up FROM {BT};
""", encoding="utf-8")
Path("vp116_promote.sql").write_text(
 f"""-- VP116 PROMOTE: verified_provisional + Opus-confirmed (2-signal) -> status auto_judged_high.
-- correct_answer/is_active DOKUNULMAZ. status + provenance flag yalniz. n={len(ids)}.
UPDATE question_bank
SET quality_review_status='auto_judged_high',
    pipeline_metadata = jsonb_set(COALESCE(pipeline_metadata::jsonb,'{{}}'::jsonb),'{{vp_status_promote_2signal}}','true'::jsonb)
WHERE id IN {inc};
SELECT count(*) AS promoted FROM question_bank WHERE pipeline_metadata::jsonb ? 'vp_status_promote_2signal';
""", encoding="utf-8")
print(f"vp116_backup.sql + vp116_promote.sql yazildi (n={len(ids)})")
