"""Generate Pool A wave apply SQL from solved rows.
Usage: python apply_wave.py <wave_tag> <solved_json> <keymap_json>
Emits <wave_tag>_apply.tsv (load table) + <wave_tag>_apply.sql (backup + set-based UPDATE).

Promotable = subjOk=Y AND topic in-list AND blind AGREE with stored key AND ans!=X AND conf>=0.80.
Promotable rows: rewrite primary_topic_id + status=auto_judged_high + clear fallback flag.
ALL processed rows: blind_seen=true + category marker. correct_answer/is_active NEVER touched.
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent
TAX = HERE.parent / "_vp_unlock" / "taxonomy.tsv"
RUNDATE = "2026-06-21"

tag = sys.argv[1]
rows = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
keymap = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))

# subject -> {topic_lower: topic_id}  (first id wins, matches build_batches)
name2id = defaultdict(dict)
for line in TAX.read_text(encoding="utf-8").splitlines():
    if line.strip():
        s, t, tid = line.split("|")
        name2id[s].setdefault(t.strip().lower(), tid)

CONF = 0.80
seen = set()
out = []
cats = Counter()
for r in rows:
    rid = r["id"]
    if rid not in keymap or rid in seen:
        continue
    seen.add(rid)
    subj = keymap[rid]["subject"]
    key = keymap[rid]["key"]
    topic_lower = (r.get("topic") or "").strip().lower()
    tid = name2id.get(subj, {}).get(topic_lower)
    subj_ok = r["subjOk"] == "Y"
    agree = r["ans"] == key and r["ans"] != "X"
    promote = bool(subj_ok and tid and agree and r["conf"] >= CONF)
    if promote:
        cat = "promote"
    elif not subj_ok:
        cat = "subject_mismatch"
    elif r["ans"] == "X":
        cat = "unsolvable"
    elif not agree:
        cat = "blind_dispute"
    elif not tid:
        cat = "topic_unresolved"
    else:
        cat = "lowconf"
    cats[cat] += 1
    out.append(
        {
            "id": rid,
            "topic_id": tid if promote else "",
            "promote": "1" if promote else "0",
            "blind_ans": r["ans"],
            "blind_conf": f"{r['conf']:.2f}",
            "cat": cat,
        }
    )

tsv = HERE / f"{tag}_apply.tsv"
with tsv.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["id", "topic_id", "promote", "blind_ans", "blind_conf", "cat"])
    for o in out:
        w.writerow(
            [
                o["id"],
                o["topic_id"],
                o["promote"],
                o["blind_ans"],
                o["blind_conf"],
                o["cat"],
            ]
        )

tsv_posix = str(tsv).replace("\\", "/")
sql = f"""-- Pool A {tag} apply (generated). Reversible. correct_answer/is_active UNTOUCHED.
\\set ON_ERROR_STOP on
BEGIN;
-- 1. backup the exact processed rows
CREATE TABLE IF NOT EXISTS question_bank_poolA_{tag}_backup_{RUNDATE.replace("-", "")} AS
  SELECT * FROM question_bank WHERE id::text IN (SELECT id FROM (VALUES {{IDS}}) v(id));
-- 2. load decisions
CREATE TEMP TABLE _poolA_{tag} (id text, topic_id text, promote text, blind_ans text, blind_conf text, cat text);
\\copy _poolA_{tag} FROM '{tsv_posix}' WITH (FORMAT csv, DELIMITER E'\\t', HEADER true);
-- 3. PROMOTE: rewrite topic + status + clear fallback flag + run marker
UPDATE question_bank q SET
  primary_topic_id = d.topic_id::uuid,
  quality_review_status = 'auto_judged_high',
  pipeline_metadata = (
    jsonb_set(q.pipeline_metadata::jsonb, '{{ai_extras,topic_match_quality}}', '"poolA_retag_verified"')
    || jsonb_build_object('blind_seen', true, 'poolA_wave', 1,
         'verified_provisional', true,
         'poolA_retag_run', '{RUNDATE}', 'blind_solve_answer', d.blind_ans,
         'blind_conf', d.blind_conf::float, 'blind_solve_wave', 'poolA_w1')
  )::json
FROM _poolA_{tag} d
WHERE q.id::text = d.id AND d.promote = '1';
-- 4. ALL processed (incl non-promote): mark seen + category for later 2nd-signal
UPDATE question_bank q SET
  pipeline_metadata = (
    q.pipeline_metadata::jsonb
    || jsonb_build_object('blind_seen', true, 'poolA_wave', 1, 'poolA_cat', d.cat)
  )::json
FROM _poolA_{tag} d
WHERE q.id::text = d.id AND d.promote = '0';
COMMIT;
"""
# embed VALUES list of ids for the backup CTE
ids_values = ",".join(f"('{o['id']}')" for o in out)
sql = sql.replace("{IDS}", ids_values)
(HERE / f"{tag}_apply.sql").write_text(sql, encoding="utf-8")

print(f"{tag}: {len(out)} processed")
for c, n in cats.most_common():
    print(f"  {c:18s} {n:4d} ({100 * n / len(out):.1f}%)")
print(f"  => promotable {cats['promote']} -> new v_safe candidates")
print(f"Wrote {tag}_apply.tsv + {tag}_apply.sql")
