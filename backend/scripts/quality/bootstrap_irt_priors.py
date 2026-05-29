"""IRT cold-start bootstrap prior'larını question_bank'a uygula.

Beta öncesi öğrenci yanıtı yok -> gerçek IRT kalibrasyonu imkânsız. Bu script,
``services.irt_bootstrap.difficulty_to_irt`` ile her aktif sorunun difficulty_level
(+ bloom_level) proxy'sinden 3PL prior türetir ve irt_difficulty/discrimination/
guessing kolonlarını günceller. CAT motoru bu kolonları doğrudan okur.

GÜVENLİK:
- Varsayılan = PILOT (dry-run): hiçbir yazma yok, sadece projeksiyon raporu.
- ``--apply``: önce backup tablo, sonra batched UPDATE.
- Sadece gerçek-kalibre OLMAYAN sorular hedeflenir (irt_n_responses < 30 / NULL).
  Gerçek-kalibre olanlar (beta sonrası) KORUNUR.
- irt_method='bootstrap_difficulty_prior' marker -> gerçek kalibrasyon üzerine yazabilir.

Çalıştırma (host):
    python backend/scripts/quality/bootstrap_irt_priors.py            # pilot
    python backend/scripts/quality/bootstrap_irt_priors.py --apply    # uygula
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.irt_bootstrap import difficulty_to_irt

DSN = os.environ.get(
    "KIRO2_DSN",
    "host=localhost port=5434 dbname=kiro2 user=postgres",
)
TARGET_WHERE = "is_active = TRUE AND (irt_n_responses IS NULL OR irt_n_responses < 30)"
BACKUP_TABLE = "question_bank_irt_bootstrap_backup_20260530"
MARKER = "bootstrap_difficulty_prior"
BATCH = 1000


def _band(b: float) -> str:
    if b < -1.5:
        return "<-1.5 (çok kolay)"
    if b < -0.5:
        return "[-1.5,-0.5) kolay"
    if b <= 0.5:
        return "[-0.5,0.5] orta"
    if b <= 1.5:
        return "(0.5,1.5] zor"
    return ">1.5 (çok zor)"


def fetch_targets(cur):
    cur.execute(
        f"SELECT id::text, difficulty_level::text, bloom_level, irt_difficulty "
        f"FROM question_bank WHERE {TARGET_WHERE}"
    )
    return cur.fetchall()


def pilot(rows):
    print(f"\n=== PILOT (dry-run) — hedef satır: {len(rows):,} ===\n")
    before_zero = sum(1 for _, _, _, b_old in rows if b_old == 0.0)
    new_bands = Counter()
    new_bs = []
    for _id, diff, bloom, _b_old in rows:
        p = difficulty_to_irt(diff, bloom)
        new_bs.append(p["b"])
        new_bands[_band(p["b"])] += 1

    print(
        f"ÖNCESİ: b=0.0'da yığılma = {before_zero:,} / {len(rows):,} "
        f"({100 * before_zero / len(rows):.1f}%)"
    )
    mean = sum(new_bs) / len(new_bs)
    var = sum((x - mean) ** 2 for x in new_bs) / len(new_bs)
    print(
        f"SONRASI: b ort={mean:.3f}, std={var**0.5:.3f}, "
        f"benzersiz b değeri={len(set(new_bs))}"
    )
    print("\nSONRASI b-band dağılımı:")
    for band in [
        "<-1.5 (çok kolay)",
        "[-1.5,-0.5) kolay",
        "[-0.5,0.5] orta",
        "(0.5,1.5] zor",
        ">1.5 (çok zor)",
    ]:
        n = new_bands.get(band, 0)
        print(f"  {band:24s} {n:>8,} ({100 * n / len(rows):5.1f}%)")

    print("\nÖrnek 8 dönüşüm (id | difficulty | bloom | b_eski -> a,b,c):")
    for _id, diff, bloom, b_old in rows[:8]:
        p = difficulty_to_irt(diff, bloom)
        print(
            f"  {_id[:8]} | {diff!s:10s} | bloom={bloom} | "
            f"{b_old} -> a={p['a']}, b={p['b']}, c={p['c']}"
        )
    print("\n(Yazma yapılmadı. Uygulamak için --apply.)")


def apply(conn, cur, rows):
    print(f"\n=== APPLY — {len(rows):,} satır güncellenecek ===")
    # 1) Backup
    cur.execute(f"DROP TABLE IF EXISTS {BACKUP_TABLE}")
    cur.execute(
        f"CREATE TABLE {BACKUP_TABLE} AS "
        f"SELECT id, irt_difficulty, irt_discrimination, irt_guessing, irt_method "
        f"FROM question_bank WHERE {TARGET_WHERE}"
    )
    conn.commit()
    cur.execute(f"SELECT COUNT(*) FROM {BACKUP_TABLE}")
    print(f"Backup tablo: {BACKUP_TABLE} ({cur.fetchone()[0]:,} satır)")

    # 2) Batched UPDATE
    done = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        payload = []
        for _id, diff, bloom, _b_old in chunk:
            p = difficulty_to_irt(diff, bloom)
            payload.append((p["a"], p["b"], p["c"], _id))
        cur.executemany(
            "UPDATE question_bank SET irt_discrimination=%s, irt_difficulty=%s, "
            f"irt_guessing=%s, irt_method='{MARKER}', "
            "last_difficulty_update=NOW() WHERE id=%s",
            payload,
        )
        conn.commit()
        done += len(chunk)
        print(f"  {done:,}/{len(rows):,}", end="\r")
    print(f"\n[OK] {done:,} satır güncellendi (marker={MARKER}).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--apply", action="store_true", help="Gerçekten güncelle (varsayılan: pilot)"
    )
    args = ap.parse_args()

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    try:
        rows = fetch_targets(cur)
        if not rows:
            print("Hedef satır yok.")
            return
        if args.apply:
            apply(conn, cur, rows)
        else:
            pilot(rows)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
