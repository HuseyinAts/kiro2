"""
S1 - Backfill soru_hash for question_bank.

Idempotent: WHERE soru_hash IS NULL ile calisir, kesinti sonrasi tekrar
calistirilirsa kaldigi yerden devam eder.

Hash formulu (M1 SUPERSEDED ile birebir):
    MD5(LOWER(TRIM(question_text)) || '|' || option_a || '|' || option_b
        || '|' || option_c || '|' || option_d || '|' || COALESCE(option_e, ''))

Batch: 5000 satir/tx. Her batch kendi transaction'i, AccessExclusive lock
sadece batch suresi kadar tutulur (~ms).

Calistirma:
    docker exec kiro2-backend python /app/scripts/backfill_soru_hash.py
"""

import os
import sys
import time

import psycopg2

BATCH_SIZE = 5000

UPDATE_SQL = """
    UPDATE question_bank
    SET soru_hash = MD5(
        LOWER(TRIM(question_text)) || '|' ||
        option_a || '|' || option_b || '|' || option_c || '|' || option_d || '|' ||
        COALESCE(option_e, '')
    )
    WHERE id IN (
        SELECT id FROM question_bank
        WHERE soru_hash IS NULL
        LIMIT %s
    );
"""


def get_dsn():
    """Backend DATABASE_URL ornek: postgresql+asyncpg://user:pass@host:port/db
    psycopg2 '+asyncpg' driver suffix'ini anlamaz, soyup birakiyoruz."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL env not set", file=sys.stderr)
        sys.exit(1)
    return url.replace("+asyncpg", "").replace("+psycopg", "")


def main():
    dsn = get_dsn()
    print("[backfill] connecting to db...")

    conn = psycopg2.connect(dsn)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM question_bank WHERE soru_hash IS NULL;")
            initial_null = cur.fetchone()[0]
        conn.commit()

        print(f"[backfill] starting: {initial_null} rows to fill, batch={BATCH_SIZE}")
        if initial_null == 0:
            print("[backfill] nothing to do, exiting")
            return

        total_done = 0
        batch_num = 0
        t0 = time.time()

        while True:
            batch_num += 1
            t_batch = time.time()

            with conn.cursor() as cur:
                cur.execute(UPDATE_SQL, (BATCH_SIZE,))
                affected = cur.rowcount
            conn.commit()

            total_done += affected
            elapsed = time.time() - t_batch

            print(
                f"[backfill] batch {batch_num:>3}: {affected:>5} rows in {elapsed:.2f}s "
                f"-> total {total_done}/{initial_null} ({100*total_done/initial_null:.1f}%)",
                flush=True,
            )

            if affected == 0:
                break

            time.sleep(0.05)

        total_elapsed = time.time() - t0
        print(f"[backfill] DONE: {total_done} rows in {total_elapsed:.1f}s ({batch_num} batches)")

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM question_bank WHERE soru_hash IS NULL;")
            still_null = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT soru_hash) FROM question_bank WHERE soru_hash IS NOT NULL;")
            distinct_hashes = cur.fetchone()[0]
        conn.commit()

        print(f"[backfill] verify: still_null={still_null}, distinct_hashes={distinct_hashes}")

        if still_null > 0:
            print(f"[backfill] WARNING: {still_null} rows still NULL", file=sys.stderr)
            sys.exit(2)

    except KeyboardInterrupt:
        print("\n[backfill] interrupted, current batch already committed", file=sys.stderr)
        conn.rollback()
        sys.exit(130)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
