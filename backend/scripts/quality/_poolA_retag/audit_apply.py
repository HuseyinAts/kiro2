"""Apply the open-ended audit results. Reversible, additive + flagging only.
- lowconf_RECOVER (3-way agree book+solve1+solve2) -> PROMOTE (re-tag topic from original wave solve)
- 2signal_CONFIRM -> flag poolA_2signal (strengthen vp)
- answer_DISPUTE -> flag poolA_answer_dispute (book key authoritative, keep)
- wrong_subject -> flag poolA_subject_2nd=<open> (all defensible/adjacent, keep)
correct_answer/is_active NEVER touched."""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent
TAX = HERE.parent / "_vp_unlock" / "taxonomy.tsv"
RUNDATE = "2026-06-21"

keymap = json.loads((HERE / "aud_keymap.json").read_text(encoding="utf-8"))
name2id = defaultdict(dict)
for line in TAX.read_text(encoding="utf-8").splitlines():
    if line.strip():
        s, t, tid = line.split("|")
        name2id[s].setdefault(t.strip().lower(), tid)

# original wave solve topics (for lowconf recover re-tag)
id2topic = {}
for w in ("w1", "w2", "w3"):
    for r in json.loads((HERE / f"{w}_solved.json").read_text(encoding="utf-8")):
        id2topic[r["id"]] = (r.get("topic") or "").strip()


def read_ids(fn):
    return [
        r for r in csv.DictReader((HERE / fn).open(encoding="utf-8"), delimiter="\t")
    ]


recover = read_ids("aud_recover.tsv")
confirm = read_ids("aud_2signal_confirm.tsv")
dispute = read_ids("aud_answer_dispute.tsv")
wrong = read_ids("aud_wrong_subject.tsv")

# build apply rows: (id, action, topic_id, extra)
out = []
recover_ok, recover_skip = 0, 0
for r in recover:
    rid = r["id"]
    subj = keymap[rid]["subject"]
    tid = name2id.get(subj, {}).get(id2topic.get(rid, "").lower())
    if tid:
        out.append((rid, "recover", tid, ""))
        recover_ok += 1
    else:
        recover_skip += 1  # topic not resolvable -> leave unpromoted (conservative)
for r in confirm:
    out.append((r["id"], "confirm", "", ""))
for r in dispute:
    out.append((r["id"], "dispute", "", ""))
for r in wrong:
    out.append((r["id"], "wrong", "", r["open"]))

tsv = HERE / "audit_apply.tsv"
with tsv.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["id", "action", "topic_id", "open_subj"])
    w.writerows(out)

ids_values = ",".join(f"('{o[0]}')" for o in out)
tsv_posix = str(tsv).replace("\\", "/")
sql = f"""-- Pool A open-ended audit apply (generated). Reversible. correct_answer/is_active UNTOUCHED.
\\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS question_bank_poolA_audit_backup_{RUNDATE.replace("-", "")} AS
  SELECT * FROM question_bank WHERE id::text IN (SELECT id FROM (VALUES {ids_values}) v(id));
CREATE TEMP TABLE _aud (id text, action text, topic_id text, open_subj text);
\\copy _aud FROM '{tsv_posix}' WITH (FORMAT csv, DELIMITER E'\\t', HEADER true);
-- RECOVER: promote lowconf (re-tag topic + status + clear fallback + verified_provisional)
UPDATE question_bank q SET
  primary_topic_id = d.topic_id::uuid,
  quality_review_status = 'auto_judged_high',
  pipeline_metadata = (
    jsonb_set(q.pipeline_metadata::jsonb, '{{ai_extras,topic_match_quality}}', '"poolA_retag_verified"')
    || jsonb_build_object('verified_provisional', true, 'poolA_2signal', true,
         'poolA_recover_run', '{RUNDATE}', 'blind_solve_wave', 'poolA_recover')
  )::json
FROM _aud d WHERE q.id::text = d.id AND d.action = 'recover';
-- CONFIRM: strengthen existing promotes (2nd independent signal agreed subject+answer)
UPDATE question_bank q SET
  pipeline_metadata = (q.pipeline_metadata::jsonb || jsonb_build_object('poolA_2signal', true))::json
FROM _aud d WHERE q.id::text = d.id AND d.action = 'confirm';
-- DISPUTE: flag for future 3rd-signal (book key authoritative, stays vp)
UPDATE question_bank q SET
  pipeline_metadata = (q.pipeline_metadata::jsonb || jsonb_build_object('poolA_answer_dispute', true))::json
FROM _aud d WHERE q.id::text = d.id AND d.action = 'dispute';
-- WRONG: record 2nd-signal subject (all defensible/adjacent, kept)
UPDATE question_bank q SET
  pipeline_metadata = (q.pipeline_metadata::jsonb || jsonb_build_object('poolA_subject_2nd', d.open_subj))::json
FROM _aud d WHERE q.id::text = d.id AND d.action = 'wrong';
COMMIT;
"""
(HERE / "audit_apply.sql").write_text(sql, encoding="utf-8")
from collections import Counter

print(f"recover_ok={recover_ok} recover_skip(topic unresolved)={recover_skip}")
print("actions:", dict(Counter(o[1] for o in out)))
print(f"total affected ids: {len(out)}")
