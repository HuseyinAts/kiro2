"""is_calibrated bootstrap-flag reset (mirrors irt_reset_bootstrap_flags.py logic), with backup.
Default = DRY-RUN. Pass --apply to execute. Atomic: backup + UPDATE in ONE transaction.
Safety gates: backup count must equal target; post-update TRUE count must equal expected."""
import os, re, sys, argparse, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})

BACKUP = "question_bank_iscalib_reset_backup_20260610"
GUARD = """q.is_calibrated=TRUE
  AND NOT EXISTS (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text AND le.event_type IN ('cat_answer','exam_answer'))
  AND NOT EXISTS (SELECT 1 FROM student_answers sa WHERE sa.question_id::text=q.id::text)"""

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()
def log(*a): print(*a); sys.stdout.flush()
log("is_calibrated RESET  -", datetime.datetime.now().isoformat(), "  MODE:", "APPLY" if args.apply else "DRY-RUN")

with eng.connect() as c:
    total_true = c.exec_driver_sql("SELECT count(*) FROM question_bank WHERE is_calibrated=TRUE").scalar()
    will_reset = c.exec_driver_sql(f"SELECT count(*) FROM question_bank q WHERE {GUARD}").scalar()
    sa_rows    = c.exec_driver_sql("SELECT count(*) FROM student_answers").scalar()
expected_true = total_true - will_reset
log(f"  is_calibrated TRUE su an : {total_true:,}")
log(f"  student_answers satir    : {sa_rows:,}  (0 olmali — guard temiz)")
log(f"  SIFIRLANACAK             : {will_reset:,}")
log(f"  reset sonrasi TRUE kalan : {expected_true:,}  (gercek learning_event destekli)")
if not args.apply:
    log("  [DRY-RUN] degisiklik yok. Uygulamak icin: python /tmp/db_reset_apply.py --apply")
    sys.exit(0)

with eng.begin() as c:
    if c.exec_driver_sql(f"SELECT to_regclass('public.{BACKUP}') IS NOT NULL").scalar():
        raise RuntimeError(f"backup '{BACKUP}' zaten var -> rollback")
    c.exec_driver_sql(f"""CREATE TABLE {BACKUP} AS
        SELECT id, is_calibrated, calibration_sample_size, calibration_quality_score
        FROM question_bank q WHERE {GUARD}""")
    bcount = c.exec_driver_sql(f"SELECT count(*) FROM {BACKUP}").scalar()
    log(f"  backup '{BACKUP}': {bcount:,} satir")
    if bcount != will_reset:
        raise RuntimeError(f"backup {bcount} != target {will_reset} -> rollback")
    updated = c.exec_driver_sql(f"""UPDATE question_bank q
        SET is_calibrated=FALSE, calibration_sample_size=0, calibration_quality_score=0
        WHERE {GUARD}""").rowcount
    new_true = c.exec_driver_sql("SELECT count(*) FROM question_bank WHERE is_calibrated=TRUE").scalar()
    log(f"  updated          : {updated:,}")
    log(f"  yeni TRUE kalan   : {new_true:,}")
    if updated != will_reset or new_true != expected_true:
        raise RuntimeError(f"mismatch updated={updated} new_true={new_true} -> rollback")
log(f"  ✅ COMMIT. is_calibrated reset (backup: {BACKUP}).")
log("  Geri alma: UPDATE question_bank q SET is_calibrated=b.is_calibrated, calibration_sample_size=b.calibration_sample_size,")
log(f"             calibration_quality_score=b.calibration_quality_score FROM {BACKUP} b WHERE b.id=q.id;")
