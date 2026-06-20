"""Blind-solve dalga AGGREGATE adimi.
Workflow ciktisi (kor cevaplar) + wave<N>_master.csv (key) -> apply_w<N>.sql + flag_seen_w<N>.sql

Kullanim:
  1) Workflow'u calistir, donen {"rows":[{"id","ans","conf"},...]} sonucunu su dosyaya YAZ:
       w<N>_solved.json
  2) python aggregate_wave.py <N>

Uretir:
  apply_w<N>.sql      -> AGREE (ans==key) AND conf>=0.80 promote: backup tablo + status + vp flag
  flag_seen_w<N>.sql  -> bu dalgada export edilen TUM adaylar blind_seen=true (dalgalar disjoint kalir)

correct_answer / is_active'e DOKUNMAZ. Sadece quality_review_status + pipeline_metadata.
apply_w20.sql yapisiyla BIREBIR ayni (dogrulandi 2026-06-21).
"""

import csv
import datetime
import json
import sys
from pathlib import Path

D = Path(r"C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve")
CONF_MIN = 0.80


def _inlist(ids) -> str:
    return ",".join("'" + i + "'" for i in ids)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "usage: python aggregate_wave.py <N>  (wave<N>_master.csv + w<N>_solved.json okur)"
        )
        sys.exit(1)
    n = sys.argv[1]
    master = D / f"wave{n}_master.csv"
    solved_f = D / f"w{n}_solved.json"
    for p in (master, solved_f):
        if not p.exists():
            print(f"YOK: {p}")
            sys.exit(1)

    keys, order = {}, []
    with master.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            keys[r["id"]] = (r["key"] or "").strip().upper()
            order.append(r["id"])

    solved = json.loads(solved_f.read_text(encoding="utf-8"))
    if isinstance(solved, dict):
        solved = solved.get("rows", [])

    promote, seen_solved, agree = [], set(), 0
    for s in solved:
        sid = s.get("id")
        ans = (s.get("ans") or "").strip().upper()[:1]
        conf = float(s.get("conf") or 0)
        if sid not in keys:
            continue
        seen_solved.add(sid)
        if ans and ans == keys[sid]:
            agree += 1
            if conf >= CONF_MIN:
                promote.append(sid)
    promote = list(dict.fromkeys(promote))  # dedup, order-stable

    today = datetime.date.today()
    dt_tbl, dt_flag = today.strftime("%Y%m%d"), today.strftime("%Y-%m-%d")

    if promote:
        apply_sql = (
            "BEGIN;\n"
            f"CREATE TABLE IF NOT EXISTS question_bank_blindsolve_w{n}_backup_{dt_tbl} AS "
            f"SELECT id,quality_review_status,pipeline_metadata FROM question_bank "
            f"WHERE id::text IN ({_inlist(promote)});\n"
            "UPDATE question_bank SET quality_review_status='auto_judged_high', "
            "pipeline_metadata=(jsonb_set(jsonb_set(coalesce(pipeline_metadata,'{}')::jsonb,"
            f"'{{verified_provisional}}','true'),'{{blind_solve_wave}}','\"{dt_flag}-w{n}\"'))::json "
            f"WHERE id::text IN ({_inlist(promote)});\n"
            "COMMIT;\n"
        )
    else:
        apply_sql = (
            f"-- wave{n}: 0 promote (conf>={CONF_MIN} AGREE yok). no-op.\nSELECT 1;\n"
        )
    (D / f"apply_w{n}.sql").write_text(apply_sql, encoding="utf-8")

    flag_sql = (
        "UPDATE question_bank SET pipeline_metadata=(jsonb_set("
        "coalesce(pipeline_metadata,'{}')::jsonb,'{blind_seen}','true'))::json "
        f"WHERE id::text IN ({_inlist(order)});\n"
    )
    (D / f"flag_seen_w{n}.sql").write_text(flag_sql, encoding="utf-8")

    rate = (100 * agree / len(seen_solved)) if seen_solved else 0
    print(
        f"solved={len(seen_solved)}/{len(order)}  agree={agree} (%{rate:.1f})  "
        f"promote(conf>={CONF_MIN})={len(promote)}  -> apply_w{n}.sql + flag_seen_w{n}.sql "
        f"(backup _w{n}_backup_{dt_tbl})"
    )


if __name__ == "__main__":
    main()
