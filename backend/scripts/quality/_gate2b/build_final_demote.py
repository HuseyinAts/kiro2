"""Build the FINAL reliable demote set + reversible apply SQL.

Sources (all Opus-validated, NOT raw gate output):
  - proxy garble (dup options / OCR-doubled prefix): demote_reliable.json -> 50, ~100% precision
  - Opus-confirmed garble/degenerate from gemma-flagged review: 12 (hand-judged)

Total ~62. Everything else from the 818 raw candidates is REJECTED as noise
(qwen-unsolvable 36%, answer-wrong 27% precision -> would delete hard valid Q).

Mechanism: dedicated exclusion table gate2c_demoted. NO writes to question_bank,
NO touching is_active / correct_answer. Reversible by TRUNCATE gate2c_demoted +
restoring the pre-D6 view. No DB writes from THIS script (emits SQL files only).
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_gate2b")

# 12 Opus-confirmed bad from the 30 gemma-flagged (proxy already excluded)
OPUS_CONFIRMED = [
    ("369872f9-df56-59d1-8dfc-6d5b73333f4a", "opus_degenerate"),   # #1  multi/ambiguous
    ("a22455db-f26d-55ac-b281-255165d08b54", "opus_garble"),        # #3  ağaçlar
    ("20ed4349-755f-5149-bcc1-9893cd7e1019", "opus_garble"),        # #6  mitoloji
    ("990e6932-2151-54ec-96a8-0c469c00e559", "opus_garble"),        # #7  öznellik
    ("a98d145c-2b5b-5a7e-bfd2-3c7c86ef1902", "opus_garble"),        # #9  balon
    ("8b507ab8-1062-5775-bf51-9cf59347c68f", "opus_garble"),        # #10 Türkçe öğretimi
    ("e9d0aaaf-fff2-5136-9dbc-933720c439e5", "opus_garble"),        # #11 şiir
    ("6c9d84ff-e554-51ec-8abb-73b043f0dba9", "opus_garble"),        # #19 kedi
    ("c8d1fd23-e0a9-5d3b-ab7f-70157ad43582", "opus_garble"),        # #20 divan şiiri
    ("8dd6df00-582a-511d-bc2f-3203339cff1e", "opus_degenerate"),    # #21 fonksiyon eşleme
    ("b4a96f1b-a91d-5712-a24d-4e0fe0b3c8db", "opus_garble"),        # #29 tarihsel roman
    ("7330a1a6-9dbe-525d-a4a3-699bbabea13d", "opus_garble"),        # #30 yazınsal ilk
]

reliable = json.loads((BASE / "demote_reliable.json").read_text(encoding="utf-8"))
proxy = reliable["proxy"]

final = {}  # id -> reason (proxy wins if overlap)
for qid, reason in OPUS_CONFIRMED:
    final[qid] = reason
for qid in proxy:
    final[qid] = "proxy_garble"

(BASE / "final_demote_ids.json").write_text(
    json.dumps({"ids": sorted(final), "by_reason": {
        "proxy_garble": sum(1 for r in final.values() if r == "proxy_garble"),
        "opus_garble": sum(1 for r in final.values() if r == "opus_garble"),
        "opus_degenerate": sum(1 for r in final.values() if r == "opus_degenerate"),
    }}, ensure_ascii=False, indent=2), encoding="utf-8")

# --- D6 part 1: exclusion table + inserts (no view yet) ---
lines = [
    "-- D6 gate2c demote: reversible exclusion table. No question_bank writes.",
    "-- Reverse: TRUNCATE gate2c_demoted;  + restore pre-D6 v_safe_for_beta.",
    "CREATE TABLE IF NOT EXISTS gate2c_demoted (",
    "    id varchar PRIMARY KEY,",
    "    reason text NOT NULL,",
    "    demoted_at timestamptz NOT NULL DEFAULT now()",
    ");",
    "",
]
for qid in sorted(final):
    lines.append(f"INSERT INTO gate2c_demoted (id, reason) VALUES ('{qid}', '{final[qid]}') ON CONFLICT (id) DO NOTHING;")
(BASE / "D6_part1_table.sql").write_text("\n".join(lines) + "\n", encoding="utf-8")

# --- backup of demoted rows (run BEFORE applying view change) ---
ids_sql = ",".join(f"'{q}'" for q in sorted(final))
(BASE / "D6_backup.sql").write_text(
    "\\encoding UTF8\n"
    "\\copy (SELECT id, is_active, correct_answer, quality_review_status, pipeline_metadata "
    f"FROM question_bank WHERE id IN ({ids_sql})) "
    "TO 'C:/Users/husey/kiro2/backend/scripts/quality/_gate2b/D6_backup.tsv' "
    "WITH (FORMAT csv, DELIMITER E'\\t', HEADER)\n",
    encoding="utf-8")

print(f"final demote = {len(final)}  "
      f"(proxy={sum(1 for r in final.values() if r=='proxy_garble')}, "
      f"opus={sum(1 for r in final.values() if r!='proxy_garble')})")
print("written: final_demote_ids.json, D6_part1_table.sql, D6_backup.sql")
print("NEXT: paste pg_get_viewdef output so D6_part2 (view) can be generated exactly.")
