"""Blind-solve dalga AGGREGATE v2 — HARDENED gate (kök-neden fix, 2026-06-23).

v1 (aggregate_wave.py) KÖK-NEDEN: tek solver'ın cevabı == stored anahtar AND
self-conf>=0.80 ile promote ediyordu. Sonuç (62-örnek Opus QA): ~%50-55 servis-temiz
(~%10 yanlış-anahtar, ~%25 degenerate/bozuk). Eksik kontroller:
  1) tek model (2-model consensus yok) → tek model stored'la aynı hatayı yapınca
     yanlış-anahtar promote (ölçülen #7 eğim, #14 sıralama, #23 denklem).
  2) coherence/degeneracy kontrolü yok (dup-şık, OCR-prefix, "cevap şıkta mı",
     figür-ama-görselsiz) → degenerate geçiyor.
  3) anahtar-doğrulama yok (stored'a körü körüne güven).
  4) Opus sample-validation yok.
  5) self-conf>=0.80 = 14B overconfidence, anlamsız sinyal.

v2 FIX — promote için TÜM koşullar:
  A) coherence-clean: dup-şık YOK + OCR-prefix YOK + 5 şık dolu.
  B) 2-MODEL CONSENSUS: gemma3.ans == qwen3.ans == stored_key (üçü de aynı, A-E).
     (tek model değil; stored'la 2 bağımsız model aynı anda hemfikir = güçlü.)
  C) Promote ÖNCESİ Opus sample-validation: her dalgadan örnek -> opus_blind.txt;
     precision <%95 ise o dalga promote EDİLMEZ (insan/Opus onayı kapısı).

correct_answer / is_active'e DOKUNMAZ. Sadece quality_review_status + pipeline_metadata.
Tek-model + self-conf kuralı KALDIRILDI.

Kullanım:
  python aggregate_wave_v2.py <N>
  girdi: wave<N>_master.csv (id,key,a,b,c,d,e)  +  w<N>_solved_gemma.json + w<N>_solved_qwen.json
  çıktı: promote_w<N>.json + reject buckets + opus_w<N>.txt/opus_w<N>_key.csv (validation)
         apply_w<N>_v2.sql (Opus onayı SONRASI çalıştırılır)
"""

import csv
import datetime
import json
import random
import re
import sys
from pathlib import Path

D = Path(r"C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve")
ABCDE = ("A", "B", "C", "D", "E")
random.seed(3)


def _load_solved(p: Path) -> dict:
    raw = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("rows", [])
    out = {}
    for s in raw:
        out[s.get("id")] = (str(s.get("ans") or "").strip().upper()[:1])
    return out


def _dup_opts(m) -> bool:
    o = [m.get("a"), m.get("b"), m.get("c"), m.get("d"), m.get("e")]
    return len({x for x in o if x is not None}) < 5


def _ocr_prefix(m) -> bool:
    return any(re.match(r"^[A-Ea-e]\)", str(m.get(k) or "")) for k in ("a", "b", "c", "d", "e"))


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python aggregate_wave_v2.py <N>")
        sys.exit(1)
    n = sys.argv[1]
    master = D / f"wave{n}_master.csv"
    gf = D / f"w{n}_solved_gemma.json"
    qf = D / f"w{n}_solved_qwen.json"
    for p in (master, gf, qf):
        if not p.exists():
            print(f"YOK: {p}")
            sys.exit(1)

    rows = {}
    with master.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            r["key"] = (r.get("key") or "").strip().upper()
            rows[r["id"]] = r

    gemma = _load_solved(gf)
    qwen = _load_solved(qf)

    promote, rej_coherence, rej_consensus = [], [], []
    for sid, m in rows.items():
        g, q, key = gemma.get(sid), qwen.get(sid), m["key"]
        if _dup_opts(m) or _ocr_prefix(m):
            rej_coherence.append(sid)
            continue
        # 2-model consensus + stored: üçü de aynı ve A-E
        if g in ABCDE and g == q and q == key:
            promote.append(sid)
        else:
            rej_consensus.append(sid)
    promote = list(dict.fromkeys(promote))

    # --- Opus validation sample (her dalga için, promote ÖNCESİ kapı) ---
    sample = random.sample(promote, min(25, len(promote)))
    blind = [f"=== OPUS VALIDATION wave{n} — her soru: doğru şık (A-E) ver, anahtar gizli.\n"]
    keyrows = ["id,gemma,qwen,stored"]
    for i, sid in enumerate(sample, 1):
        m = rows[sid]
        blind.append(f"#{i}\n  Q: {m.get('q','(q yok)')}\n  A) {m.get('a')}\n  B) {m.get('b')}\n"
                     f"  C) {m.get('c')}\n  D) {m.get('d')}\n  E) {m.get('e')}\n")
        keyrows.append(f"{sid},{gemma.get(sid)},{qwen.get(sid)},{m['key']}")
    (D / f"opus_w{n}.txt").write_text("\n".join(blind), encoding="utf-8")
    (D / f"opus_w{n}_key.csv").write_text("\n".join(keyrows), encoding="utf-8")
    (D / f"promote_w{n}.json").write_text(json.dumps(promote), encoding="utf-8")

    today = datetime.date.today()
    dt_tbl, dt_flag = today.strftime("%Y%m%d"), today.strftime("%Y-%m-%d")
    ids_sql = ",".join("'" + i + "'" for i in promote)
    apply_sql = (
        f"-- wave{n} v2: promote = coherence-clean AND gemma==qwen==stored (2-model consensus).\n"
        f"-- ÇALIŞTIRMADAN ÖNCE: opus_w{n}.txt'i Opus ile doğrula, precision>=%95 olmalı.\n"
        + ("BEGIN;\n"
           f"CREATE TABLE IF NOT EXISTS question_bank_blindsolve_w{n}v2_backup_{dt_tbl} AS "
           f"SELECT id,quality_review_status,pipeline_metadata FROM question_bank WHERE id::text IN ({ids_sql});\n"
           "UPDATE question_bank SET quality_review_status='auto_judged_high', "
           "pipeline_metadata=(jsonb_set(jsonb_set(coalesce(pipeline_metadata,'{}')::jsonb,"
           f"'{{verified_provisional}}','true'),'{{blind_solve_wave}}','\"{dt_flag}-w{n}v2\"'))::json "
           f"WHERE id::text IN ({ids_sql});\nCOMMIT;\n" if promote else "SELECT 1;  -- 0 promote\n")
    )
    (D / f"apply_w{n}_v2.sql").write_text(apply_sql, encoding="utf-8")

    tot = len(rows)
    print(f"wave{n}: master={tot}  PROMOTE(coherence+2model+stored)={len(promote)} "
          f"({100*len(promote)/tot:.1f}%)  rej_coherence={len(rej_coherence)}  "
          f"rej_consensus={len(rej_consensus)}")
    print(f"-> opus_w{n}.txt ({len(sample)} örnek) DOĞRULA; precision>=%95 ise apply_w{n}_v2.sql çalıştır.")


if __name__ == "__main__":
    main()
