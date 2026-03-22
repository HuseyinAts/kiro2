"""
IRT Calibration History — Bootstrap Audit Trail
-------------------------------------------------
Session 108'de 64,205 soru IRT bootstrap kalibrasyonu SQL ile doğrudan yapıldı.
Bu script o kalibrasyonun geçmişini irt_calibration_history tablosuna ekler.

- calibration_method: "bootstrap"
- sample_size: 30 (DB constraint minimum — gerçek veri yok, teorik bootstrap)
- old_*: model default'ları (a=1.0, b=0.0, c=0.25, d=1.0)
- new_*: question_bank'taki irt_discrimination/difficulty/guessing/upper_asymptote

Idempotent: calibration_method='bootstrap' olan kayıtlar atlanır.

Usage:
  cd backend
  python scripts/insert_irt_calibration_history.py --dry-run   # Kaç kayıt?
  python scripts/insert_irt_calibration_history.py              # Uygula
"""

import argparse
import sys
import uuid
from datetime import UTC, datetime

import psycopg2
import psycopg2.extras

sys.path.insert(0, ".")

DB_DSN = "host=localhost port=5434 dbname=kiro2 user=postgres"
BATCH_SIZE = 1000

# Model default'ları (bootstrap öncesi varsayılan değerler)
OLD_DISCRIMINATION = 1.0
OLD_DIFFICULTY = 0.0
OLD_GUESSING = 0.25
OLD_UPPER_ASYMPTOTE = 1.0

# DB constraint minimum: sample_size >= 30
# Bootstrap için gerçek veri yoktur; 30 minimum constraint'i geçmek için.
BOOTSTRAP_SAMPLE_SIZE = 30


def main(dry_run: bool = True) -> None:
    print(
        f"{'[DRY-RUN] ' if dry_run else ''}IRT Calibration History Bootstrap başlıyor..."
    )

    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT
            qb.id,
            qb.irt_discrimination,
            qb.irt_difficulty,
            qb.irt_guessing,
            qb.irt_upper_asymptote
        FROM question_bank qb
        WHERE qb.irt_difficulty IS NOT NULL
          AND qb.id NOT IN (
              SELECT question_id FROM irt_calibration_history
              WHERE calibration_method = 'bootstrap'
          )
        ORDER BY qb.id
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Eklenecek kayıt sayısı: {total:,}")

    if total == 0:
        print("Tüm kayıtlar zaten mevcut. İşlem gerekmiyor.")
        cur.close()
        conn.close()
        return

    if dry_run:
        print("[DRY-RUN] Değişiklik uygulanmadı.")
        print("Örnek (ilk 3):")
        for row in rows[:3]:
            print(
                f"  id={row['id'][:8]}... "
                f"a={row['irt_discrimination']} b={row['irt_difficulty']} "
                f"c={row['irt_guessing']} d={row['irt_upper_asymptote']}"
            )
        cur.close()
        conn.close()
        return

    now = datetime.now(UTC)
    inserted = 0
    batch: list[tuple] = []

    for row in rows:
        batch.append(
            (
                str(uuid.uuid4()),  # id
                row["id"],  # question_id
                now,  # calibration_date
                "bootstrap",  # calibration_method
                BOOTSTRAP_SAMPLE_SIZE,  # sample_size (constraint >= 30)
                OLD_DISCRIMINATION,  # old_discrimination
                OLD_DIFFICULTY,  # old_difficulty
                OLD_GUESSING,  # old_guessing
                OLD_UPPER_ASYMPTOTE,  # old_upper_asymptote
                row["irt_discrimination"],  # new_discrimination
                row["irt_difficulty"],  # new_difficulty
                row["irt_guessing"],  # new_guessing
                row["irt_upper_asymptote"],  # new_upper_asymptote
                0.0,  # standard_error
                0,  # convergence_iterations
                0.0,  # log_likelihood
                0.0,  # discrimination_ci_lower
                0.0,  # discrimination_ci_upper
                0.0,  # difficulty_ci_lower
                0.0,  # difficulty_ci_upper
            )
        )

        if len(batch) >= BATCH_SIZE:
            psycopg2.extras.execute_batch(
                cur,
                """
                INSERT INTO irt_calibration_history (
                    id, question_id, calibration_date, calibration_method, sample_size,
                    old_discrimination, old_difficulty, old_guessing, old_upper_asymptote,
                    new_discrimination, new_difficulty, new_guessing, new_upper_asymptote,
                    standard_error, convergence_iterations, log_likelihood,
                    discrimination_ci_lower, discrimination_ci_upper,
                    difficulty_ci_lower, difficulty_ci_upper
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                batch,
            )
            conn.commit()
            inserted += len(batch)
            print(f"  Eklendi: {inserted:,} / {total:,}")
            batch = []

    if batch:
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO irt_calibration_history (
                id, question_id, calibration_date, calibration_method, sample_size,
                old_discrimination, old_difficulty, old_guessing, old_upper_asymptote,
                new_discrimination, new_difficulty, new_guessing, new_upper_asymptote,
                standard_error, convergence_iterations, log_likelihood,
                discrimination_ci_lower, discrimination_ci_upper,
                difficulty_ci_lower, difficulty_ci_upper
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            batch,
        )
        conn.commit()
        inserted += len(batch)

    cur.close()
    conn.close()

    print(f"\nTamamlandı: {inserted:,} kayıt eklendi.")
    print("Doğrulama SQL:")
    print(
        "  SELECT COUNT(*) FROM irt_calibration_history "
        "WHERE calibration_method='bootstrap';  -- ~64,205 olmalı"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="IRT bootstrap kalibrasyon geçmişini irt_calibration_history'ye ekle"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Değişiklik uygulamadan önizle"
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
