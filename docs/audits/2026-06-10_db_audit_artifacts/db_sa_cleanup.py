"""student_answers LOAD-TEST cleanup (P1: delete all test-account rows), with backup.
Default = DRY-RUN. Pass --apply to execute. Atomic: backup + delete in ONE transaction.
Safety gates: aborts if matched!=total, if backup count!=total, or if remaining!=0."""
import os, re, sys, argparse, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})

BACKUP = "student_answers_backup_20260610"
EMAILS = "('test@kiro2.com','admin@kiro2.com','ogrenci@kiro2.com','beta01@kiro2.com')"
MATCH_PRED = f"""EXISTS (SELECT 1 FROM exam_sessions es JOIN users u ON u.id::text=es.student_id::text
              WHERE es.id::text=sa.exam_session_id::text AND u.email IN {EMAILS})"""
DELETE_SQL = f"""DELETE FROM student_answers sa USING exam_sessions es, users u
  WHERE sa.exam_session_id::text=es.id::text AND es.student_id::text=u.id::text AND u.email IN {EMAILS}"""

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true", help="execute (default = dry-run)")
args = ap.parse_args()

def log(*a): print(*a); sys.stdout.flush()
log("student_answers CLEANUP (P1)  -", datetime.datetime.now().isoformat(), "  MODE:", "APPLY" if args.apply else "DRY-RUN")

# ---- pre-checks (read-only, separate connection) ----
with eng.connect() as c:
    total   = c.exec_driver_sql("SELECT count(*) FROM student_answers").scalar()
    matched = c.exec_driver_sql(f"SELECT count(*) FROM student_answers sa WHERE {MATCH_PRED}").scalar()
log(f"  total rows        : {total:,}")
log(f"  test-account match: {matched:,}")
if total != matched:
    log(f"  !! ABORT: matched ({matched:,}) != total ({total:,}) -> test-disi satir olabilir, silinmiyor.")
    sys.exit(1)
if not args.apply:
    log("  [DRY-RUN] degisiklik yok. Uygulamak icin: python /tmp/db_sa_cleanup.py --apply")
    sys.exit(0)

# ---- APPLY (atomic: eng.begin() commits on clean exit, rolls back on exception) ----
with eng.begin() as c:
    if c.exec_driver_sql(f"SELECT to_regclass('public.{BACKUP}') IS NOT NULL").scalar():
        raise RuntimeError(f"backup tablosu '{BACKUP}' zaten var (uzerine yazma yok) -> rollback")
    c.exec_driver_sql(f"CREATE TABLE {BACKUP} AS SELECT * FROM student_answers")
    bcount = c.exec_driver_sql(f"SELECT count(*) FROM {BACKUP}").scalar()
    log(f"  backup '{BACKUP}': {bcount:,} satir")
    if bcount != total:
        raise RuntimeError(f"backup count {bcount} != total {total} -> rollback")
    deleted = c.exec_driver_sql(DELETE_SQL).rowcount
    remaining = c.exec_driver_sql("SELECT count(*) FROM student_answers").scalar()
    log(f"  deleted          : {deleted:,}")
    log(f"  remaining        : {remaining:,}")
    if remaining != 0:
        raise RuntimeError(f"remaining {remaining} != 0 -> rollback")
log(f"  ✅ COMMIT. student_answers temizlendi (backup: {BACKUP}).")
log("  Geri alma: INSERT INTO student_answers SELECT * FROM " + BACKUP + ";")
