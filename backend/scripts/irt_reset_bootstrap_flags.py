"""
IRT Bootstrap Flag Reset
========================
bootstrap_irt_params.py 64,225 soruya is_calibrated=TRUE koydu.
Bu YANLIŞ — o değerler sahte (standard_error=0, iterations=0).
calibration_task.py is_calibrated=FALSE olanları arıyor.
→ Gerçek kalibrasyon ASLA çalışmıyor.

Bu script sahte bayrakları düzeltiyor.

Çalıştırma:
  python scripts/irt_reset_bootstrap_flags.py --dry-run
  python scripts/irt_reset_bootstrap_flags.py
"""
import argparse
import sys
import psycopg2

DB = dict(host="localhost", port=5434, dbname="kiro2",
          user="postgres", password="changeme_strong_password_here")

# Sahte kalibrasyon tespiti:
# Gerçek EM-3PL → standard_error > 0, convergence_iterations > 0
# Bootstrap    → standard_error = 0, convergence_iterations = 0
DETECT_FAKE_SQL = """
SELECT COUNT(*) FROM question_bank q
WHERE q.is_calibrated = TRUE
  AND EXISTS (
    SELECT 1 FROM irt_calibration_history h
    WHERE h.question_id = q.id
      AND h.standard_error = 0
      AND h.convergence_iterations = 0
  );
"""

# Direkt basit kriter: is_calibrated=TRUE ama hiç learning_event yok
# (Bootstrap yapıldı, öğrenci yanıtı yok → kesinlikle sahte)
DETECT_NO_RESPONSES_SQL = """
SELECT COUNT(*) FROM question_bank q
WHERE q.is_calibrated = TRUE
  AND NOT EXISTS (
    SELECT 1 FROM kiro2_learning_events le
    WHERE le.question_id::text = q.id::text
  )
  AND NOT EXISTS (
    SELECT 1 FROM student_answers sa
    WHERE sa.question_id::text = q.id::text
  );
"""

RESET_SQL = """
UPDATE question_bank
SET
    is_calibrated = FALSE,
    calibration_sample_size = 0,
    calibration_quality_score = 0
WHERE is_calibrated = TRUE
  AND NOT EXISTS (
    SELECT 1 FROM kiro2_learning_events le
    WHERE le.question_id::text = id::text
  )
  AND NOT EXISTS (
    SELECT 1 FROM student_answers sa
    WHERE sa.question_id::text = id::text
  );
"""

CLEAN_FAKE_HISTORY_SQL = """
DELETE FROM irt_calibration_history
WHERE standard_error = 0
  AND convergence_iterations = 0
  AND log_likelihood = 0;
"""


def main(dry_run: bool):
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    print("=" * 60)
    print("IRT BOOTSTRAP FLAG RESET")
    print("=" * 60)

    # Mevcut durum
    cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calibrated = TRUE;")
    total_true = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calibrated = FALSE;")
    total_false = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM irt_calibration_history;")
    hist_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM irt_calibration_history WHERE standard_error=0 AND convergence_iterations=0;")
    hist_fake = cur.fetchone()[0]

    print(f"\nMEVCUT DURUM:")
    print(f"  question_bank is_calibrated=TRUE  : {total_true:,}")
    print(f"  question_bank is_calibrated=FALSE : {total_false:,}")
    print(f"  irt_calibration_history toplam    : {hist_total:,}")
    print(f"  irt_calibration_history SAHTE     : {hist_fake:,}  (SE=0, iter=0)")

    # Sıfırlanacak miktar
    cur.execute(DETECT_NO_RESPONSES_SQL)
    will_reset = cur.fetchone()[0]
    print(f"\nSIFIRLANACAK (yanıt yok + is_calibrated=TRUE): {will_reset:,}")

    if dry_run:
        print(f"\n[DRY RUN] Değişiklik yapılmadı.")
        print(f"  Uygulamak için: python scripts/irt_reset_bootstrap_flags.py")
        conn.close()
        return

    # Uygula
    print(f"\nUYGULANIYOR...")

    cur.execute(RESET_SQL)
    reset_count = cur.rowcount
    print(f"  ✅ {reset_count:,} soru → is_calibrated=FALSE yapıldı")

    cur.execute(CLEAN_FAKE_HISTORY_SQL)
    hist_del = cur.rowcount
    print(f"  ✅ {hist_del:,} sahte kalibrasyon geçmişi silindi")

    conn.commit()

    # Son durum
    cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calibrated = TRUE;")
    new_true = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM question_bank WHERE is_calibrated = FALSE;")
    new_false = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM irt_calibration_history;")
    new_hist = cur.fetchone()[0]

    print(f"\nYENİ DURUM:")
    print(f"  question_bank is_calibrated=TRUE  : {new_true:,}  (gerçekten kalibre)")
    print(f"  question_bank is_calibrated=FALSE : {new_false:,} (kalibrasyon bekliyor)")
    print(f"  irt_calibration_history toplam    : {new_hist:,}")

    print(f"\n✅ Calibration task artık {new_false:,} soruyu görebilir.")
    print(f"   Veri birikince: python scripts/irt_calibration_runner.py --dry-run")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
