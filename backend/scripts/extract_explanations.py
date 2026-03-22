"""
P6: Explanation Extraction Pipeline
Extract best_answer metadata into explanation field for questions lacking explanations.

Format: "Doğru cevap: {answer} (Güven: %{confidence}, Kaynak: {method})"

Timeout fix: asyncpg single-session while loop timeout sorunu için
psycopg2 + batch 1000 pattern'e dönüştürüldü (fix_explanation_language.py ile aynı yaklaşım).

Usage:
  cd backend
  python scripts/extract_explanations.py --dry-run   # Preview
  python scripts/extract_explanations.py              # Apply
"""

import argparse
import sys

import psycopg2
import psycopg2.extras

sys.path.insert(0, ".")

DB_DSN = "host=localhost port=5434 dbname=kiro2 user=postgres"
BATCH_SIZE = 1000

METHOD_LABELS: dict[str, str] = {
    "bayes_1of1_orig": "Kitap cevap anahtarı",
    "bayes_2of2_orig": "Kitap cevap anahtarı (çapraz doğrulanmış)",
    "bayes_3of4_orig": "Kitap cevap anahtarı (3/4 doğrulama)",
    "bayes_4of4_orig": "Kitap cevap anahtarı (4/4 tam doğrulama)",
    "ai_crop_solve": "AI çözüm analizi",
    "ai_crossval": "AI çapraz doğrulama",
}


def build_explanation(metadata: dict) -> str | None:
    """pipeline_metadata'dan Türkçe açıklama üret."""
    answer = metadata.get("best_answer")
    if not answer:
        return None
    confidence_raw = metadata.get("best_confidence")
    method_key = metadata.get("best_method", "")
    method_label = METHOD_LABELS.get(method_key, method_key)
    if confidence_raw is not None:
        confidence = round(float(confidence_raw) * 100)
        return f"Doğru cevap: {answer} (Güven: %{confidence}, Kaynak: {method_label})"
    return f"Doğru cevap: {answer} (Kaynak: {method_label})"


def main(dry_run: bool = True) -> None:
    print(f"{'[DRY-RUN] ' if dry_run else ''}P6 Explanation Extraction başlıyor...")

    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Özet: method bazında dağılım
    cur.execute("""
        SELECT
            pipeline_metadata->>'best_method' AS method,
            COUNT(*) AS cnt
        FROM question_bank
        WHERE is_active = TRUE
          AND (explanation IS NULL OR explanation = '')
          AND pipeline_metadata->>'best_answer' IS NOT NULL
        GROUP BY 1
        ORDER BY 2 DESC
    """)
    preview_rows = cur.fetchall()
    print("Explanation eksik, best_answer mevcut:")
    for row in preview_rows:
        label = METHOD_LABELS.get(row["method"] or "", row["method"] or "unknown")
        print(f"  {label:>45}: {row['cnt']:,}")

    # Tüm hedef kayıtları çek
    cur.execute("""
        SELECT id, pipeline_metadata
        FROM question_bank
        WHERE is_active = TRUE
          AND (explanation IS NULL OR explanation = '')
          AND pipeline_metadata->>'best_answer' IS NOT NULL
        ORDER BY id
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"\nTotal to update: {total:,}")

    if total == 0 or dry_run:
        if dry_run:
            print("\n[DRY RUN] Değişiklik uygulanmadı.")
            for row in rows[:5]:
                meta = row["pipeline_metadata"]
                new_exp = build_explanation(meta) if meta else None
                print(f"  id={row['id']} → {new_exp!r}")
        cur.close()
        conn.close()
        return

    updated = 0
    skipped = 0
    batch: list[tuple[str, str]] = []

    for row in rows:
        meta = row["pipeline_metadata"]
        new_exp = build_explanation(meta) if meta else None
        if new_exp is None:
            skipped += 1
            continue
        batch.append((new_exp, row["id"]))

        if len(batch) >= BATCH_SIZE:
            psycopg2.extras.execute_batch(
                cur,
                "UPDATE question_bank SET explanation = %s WHERE id = %s",
                batch,
            )
            conn.commit()
            updated += len(batch)
            print(f"  Güncellendi: {updated:,} / {total:,}")
            batch = []

    if batch:
        psycopg2.extras.execute_batch(
            cur,
            "UPDATE question_bank SET explanation = %s WHERE id = %s",
            batch,
        )
        conn.commit()
        updated += len(batch)

    cur.close()
    conn.close()

    print(f"\nTamamlandı: {updated:,} güncellendi, {skipped} atlandı (metadata eksik).")
    print("Doğrulama SQL:")
    print(
        "  SELECT COUNT(*) FROM question_bank "
        "WHERE is_active=TRUE AND (explanation IS NULL OR explanation='');  -- 0 olmalı"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract explanations from pipeline_metadata"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
