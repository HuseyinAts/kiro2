"""Re-gate AGGREGATE — v2 mantığını TÜM bulk'a uygular (per-wave değil, bütün).

Girdi: master.csv (id,key,a-e,img) + preds_gemma/preds_*.json + preds_qwen/preds_*.json
Mantık (aggregate_wave_v2 ile aynı):
  KEEP  = coherence-clean (dup-şık yok + OCR-prefix yok) AND gemma==qwen==stored (A-E)
  DEMOTE_coherence = dup-şık veya OCR-prefix
  DEMOTE_consensus = coherence OK ama gemma==qwen==stored DEĞİL (tek-model false promote'lar burada düşer)

Çıktı:
  keep_ids.json, demote_ids.json (coherence+consensus)
  opus_keep.txt/opus_keep_key.csv (25 KEEP örnek -> precision teyidi)
  opus_demote.txt/opus_demote_key.csv (25 DEMOTE örnek -> over-demote kontrolü)
  D_regate_demote.sql  (reversible exclusion tablosu + insert; view predicate AYRI eklenir)

DB yazmaz. correct_answer/is_active dokunulmaz.
"""

import csv
import glob
import json
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10_000_000)
random.seed(3)

BASE = Path("C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve/regate")
ABCDE = ("A", "B", "C", "D", "E")


def load_preds(subdir):
    out = {}
    for fp in sorted(glob.glob(str(BASE / subdir / "preds_*.json"))):
        for p in json.loads(Path(fp).read_text(encoding="utf-8")):
            out[p.get("id")] = str(p.get("answer", "")).strip().upper()
    return out


def dup_opts(m):
    o = [m.get("a"), m.get("b"), m.get("c"), m.get("d"), m.get("e")]
    return len({x for x in o if x is not None}) < 5


def ocr_prefix(m):
    return any(re.match(r"^[A-Ea-e]\)", str(m.get(k) or "")) for k in ("a", "b", "c", "d", "e"))


master = {}
with (BASE / "master.csv").open(encoding="utf-8", newline="") as f:
    for rec in csv.reader(f):
        if rec:
            o = json.loads(rec[0])
            o["key"] = str(o.get("key") or "").strip().upper()
            master[o["id"]] = o

gemma = load_preds("preds_gemma")
qwen = load_preds("preds_qwen")
g_missing = [i for i in master if i not in gemma]
q_missing = [i for i in master if i not in qwen]

print(f"master={len(master)}  gemma_solved={len(gemma)} (missing {len(g_missing)})  "
      f"qwen_solved={len(qwen)} (missing {len(q_missing)})")
if g_missing or q_missing:
    print("[!] Eksik pred var — iki modeli de bitir, sonra tekrar çalıştır. (regate YAZILMADI)")
    sys.exit(0)

keep, dem_coh, dem_cons = [], [], []
for sid, m in master.items():
    if dup_opts(m) or ocr_prefix(m):
        dem_coh.append(sid)
        continue
    g, q, key = gemma.get(sid), qwen.get(sid), m["key"]
    if g in ABCDE and g == q and q == key:
        keep.append(sid)
    else:
        dem_cons.append(sid)

demote = dem_coh + dem_cons
n = len(master)
print(f"KEEP={len(keep)} ({100*len(keep)/n:.1f}%)  "
      f"DEMOTE_coherence={len(dem_coh)}  DEMOTE_consensus={len(dem_cons)}  "
      f"-> DEMOTE total={len(demote)} ({100*len(demote)/n:.1f}%)")

(BASE / "keep_ids.json").write_text(json.dumps(keep), encoding="utf-8")
(BASE / "demote_ids.json").write_text(json.dumps(
    {"coherence": dem_coh, "consensus": dem_cons, "all": demote}), encoding="utf-8")


def _sample_blind(ids, fname_txt, fname_key, header):
    s = random.sample(ids, min(25, len(ids)))
    blind = [header + "\n"]
    krows = ["id,gemma,qwen,stored,img"]
    for i, sid in enumerate(s, 1):
        m = master[sid]
        blind.append(f"#{i} [{m.get('subject')}] img={m.get('img')}\n  Q: {m.get('q')}\n"
                     f"  A) {m.get('a')}\n  B) {m.get('b')}\n  C) {m.get('c')}\n  D) {m.get('d')}\n  E) {m.get('e')}\n")
        krows.append(f"{sid},{gemma.get(sid)},{qwen.get(sid)},{m['key']},{m.get('img')}")
    (BASE / fname_txt).write_text("\n".join(blind), encoding="utf-8")
    (BASE / fname_key).write_text("\n".join(krows), encoding="utf-8")


_sample_blind(keep, "opus_keep.txt", "opus_keep_key.csv",
              "=== OPUS KEEP precision: doğru şık ver (A-E). KEEP set'i gerçekten temiz mi?")
_sample_blind(dem_cons, "opus_demote.txt", "opus_demote_key.csv",
              "=== OPUS DEMOTE kontrol: doğru şık ver (A-E). Over-demote mu (aslında doğru mu)?")

ids_sql = ",".join("'" + i + "'" for i in demote)
(BASE / "D_regate_demote.sql").write_text(
    "-- Re-gate demote (reversible). question_bank YAZMAZ; exclusion tablosu.\n"
    "-- Reverse: TRUNCATE blindsolve_regate_demoted; + view'dan AND id NOT IN (...) çıkar.\n"
    "CREATE TABLE IF NOT EXISTS blindsolve_regate_demoted (id varchar PRIMARY KEY, reason text, demoted_at timestamptz DEFAULT now());\n"
    + "\n".join(
        f"INSERT INTO blindsolve_regate_demoted (id,reason) VALUES ('{i}','{r}') ON CONFLICT (id) DO NOTHING;"
        for i, r in ([(x, "coherence") for x in dem_coh] + [(x, "consensus_fail") for x in dem_cons]))
    + "\n\n-- SONRA: v_safe_for_beta'ya canlı pg_get_viewdef'ten 'AND id NOT IN (SELECT id FROM blindsolve_regate_demoted)' ekle (bayrak-grubu DIŞINA, gate2c gibi). Apply sonrası leak=0 doğrula.\n",
    encoding="utf-8")
print(f"yazıldı: keep_ids.json, demote_ids.json, opus_keep.txt(25), opus_demote.txt(25), D_regate_demote.sql")
print("SIRA: opus_keep.txt + opus_demote.txt'i Opus ile doğrula -> KEEP temiz & DEMOTE haklıysa D_regate_demote.sql + view edit uygula.")
