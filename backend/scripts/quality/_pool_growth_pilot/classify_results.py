"""
Phase-2 classifier — workflow çift-blind çıktısını DB cevap-anahtarıyla birleştir.

Blindness korundu: workflow correct_answer'ı HİÇ görmedi; karşılaştırma burada.

Girdi:
  - pool_pilot_dblind_results.json  (workflow return: {results:[{id,subject,b1,b2}]})
  - pool_pilot_answers.json          (id -> db correct_answer)
  - pool_pilot_readable.jsonl        (spot-check için tam metin)

Çıktı: konsol özeti + pool_pilot_candidates.json (AGREE_PROMOTE) + spot-check örnekleri.
APPLY YOK — sadece sınıflandırma + insan-onayı materyali.
"""

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
results = json.loads(
    (HERE / "pool_pilot_dblind_results.json").read_text(encoding="utf-8")
)
answers = json.loads((HERE / "pool_pilot_answers.json").read_text(encoding="utf-8"))
fulltext = {
    json.loads(line)["id"]: json.loads(line)
    for line in (HERE / "pool_pilot_readable.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
}

rows = results.get("results", results) if isinstance(results, dict) else results


def classify(r):
    b1, b2 = r["b1"], r["b2"]
    db = (answers.get(r["id"]) or "").strip().upper()
    if b1["letter"] == "PARSE_FAIL" or b2["letter"] == "PARSE_FAIL":
        return "PARSE_FAIL", db
    if b1["solvable"] is False or b2["solvable"] is False:
        return "UNSOLVABLE", db
    if b1["letter"] != b2["letter"]:
        return "SPLIT", db
    # iki blind aynı harfte hemfikir
    if b1["letter"] == db:
        return "AGREE_PROMOTE", db
    return "DISPUTE", db


cats = Counter()
detail = []
for r in rows:
    cat, db = classify(r)
    cats[cat] += 1
    detail.append({**r, "db_answer": db, "category": cat})

n = len(detail)
print(f"=== PİLOT SINIFLANDIRMA (n={n}) ===")
for cat, c in cats.most_common():
    print(f"  {cat:14s} {c:4d}  ({100 * c / n:.1f}%)")

promote = [d for d in detail if d["category"] == "AGREE_PROMOTE"]
dispute = [d for d in detail if d["category"] == "DISPUTE"]
print(f"\nterfi adayı (AGREE_PROMOTE): {len(promote)}")
print(f"dispute (DB hatası şüphesi): {len(dispute)}")

# subject bazında AGREE oranı
print("\n=== subject bazında AGREE_PROMOTE / toplam ===")
by_subj = Counter(d["subject"] for d in detail)
by_subj_agree = Counter(d["subject"] for d in promote)
for s in sorted(by_subj, key=lambda x: -by_subj[x]):
    print(f"  {s:12s} {by_subj_agree[s]:3d}/{by_subj[s]:3d}")

# candidate list (APPLY için, onay sonrası)
(HERE / "pool_pilot_candidates.json").write_text(
    json.dumps([d["id"] for d in promote], ensure_ascii=False), encoding="utf-8"
)


# spot-check materyali: 6 AGREE + 4 DISPUTE, tam metin + cevaplar
def spot(items, k):
    out = []
    for d in items[:k]:
        ft = fulltext.get(d["id"], {})
        out.append(
            {
                "id": d["id"][:8],
                "subject": d["subject"],
                "category": d["category"],
                "blind1": d["b1"]["letter"],
                "blind2": d["b2"]["letter"],
                "db_answer": d["db_answer"],
                "question": (ft.get("question_text") or "")[:400],
                "options": ft.get("options"),
            }
        )
    return out


spotcheck = {"agree_sample": spot(promote, 6), "dispute_sample": spot(dispute, 4)}
(HERE / "pool_pilot_spotcheck.json").write_text(
    json.dumps(spotcheck, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("\npool_pilot_candidates.json + pool_pilot_spotcheck.json yazıldı.")
print("APPLY YOK — insan onayı bekleniyor.")
