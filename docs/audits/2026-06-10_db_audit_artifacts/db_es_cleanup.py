"""exam_sessions/exam_questions test cleanup (delete 323 test sessions -> CASCADE exam_questions).
Default DRY-RUN; --apply executes. Atomic + backups. Safety: matched!=total -> abort; post-counts verified."""
import os, re, sys, argparse, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":10})
EMAILS = "('test@kiro2.com','admin@kiro2.com','ogrenci@kiro2.com','beta01@kiro2.com')"
MATCH = f"EXISTS (SELECT 1 FROM users u WHERE u.id::text=es.student_id::text AND u.email IN {EMAILS})"
ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args = ap.parse_args()
def log(*a): print(*a); sys.stdout.flush()
log("exam cleanup -", datetime.datetime.now().isoformat(), " MODE:", "APPLY" if args.apply else "DRY-RUN")
with eng.connect() as c:
    es_total = c.exec_driver_sql("SELECT count(*) FROM exam_sessions").scalar()
    es_match = c.exec_driver_sql(f"SELECT count(*) FROM exam_sessions es WHERE {MATCH}").scalar()
    eq_total = c.exec_driver_sql("SELECT count(*) FROM exam_questions").scalar()
log(f"  exam_sessions total/test-match: {es_total:,}/{es_match:,}")
log(f"  exam_questions total (CASCADE silinecek): {eq_total:,}")
if es_total != es_match:
    log(f"  !! ABORT: test-disi exam_session var ({es_total-es_match}) — silinmiyor."); sys.exit(1)
if not args.apply:
    log("  [DRY-RUN] degisiklik yok. --apply ile uygula."); sys.exit(0)
with eng.begin() as c:
    for b in ("exam_sessions_backup_20260610","exam_questions_backup_20260610"):
        if c.exec_driver_sql(f"SELECT to_regclass('public.{b}') IS NOT NULL").scalar():
            raise RuntimeError(f"backup '{b}' zaten var -> rollback")
    c.exec_driver_sql("CREATE TABLE exam_sessions_backup_20260610 AS SELECT * FROM exam_sessions")
    c.exec_driver_sql("CREATE TABLE exam_questions_backup_20260610 AS SELECT * FROM exam_questions")
    bes = c.exec_driver_sql("SELECT count(*) FROM exam_sessions_backup_20260610").scalar()
    beq = c.exec_driver_sql("SELECT count(*) FROM exam_questions_backup_20260610").scalar()
    log(f"  backup exam_sessions={bes:,}  exam_questions={beq:,}")
    if bes != es_total or beq != eq_total: raise RuntimeError("backup count mismatch -> rollback")
    deleted = c.exec_driver_sql(f"DELETE FROM exam_sessions es USING users u WHERE u.id::text=es.student_id::text AND u.email IN {EMAILS}").rowcount
    es_rem = c.exec_driver_sql("SELECT count(*) FROM exam_sessions").scalar()
    eq_rem = c.exec_driver_sql("SELECT count(*) FROM exam_questions").scalar()
    log(f"  deleted exam_sessions={deleted:,}  remaining es={es_rem:,}  eq(cascade)={eq_rem:,}")
    if es_rem != 0 or eq_rem != 0: raise RuntimeError(f"remaining es={es_rem} eq={eq_rem} != 0 -> rollback")
log("  ✅ COMMIT. exam_sessions+exam_questions temizlendi (backup'lar mevcut).")
log("  Geri alma: INSERT INTO exam_sessions SELECT * FROM exam_sessions_backup_20260610; sonra exam_questions ayni sekilde.")
