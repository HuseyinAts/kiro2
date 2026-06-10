"""Add FK student_answers.question_id -> question_bank.id (table empty -> instant valid).
Default DRY-RUN; --apply executes. Idempotent (skips if FK exists)."""
import os, re, sys, argparse, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":10})
FK = "student_answers_question_id_fkey"
ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args = ap.parse_args()
def log(*a): print(*a); sys.stdout.flush()
log("add FK student_answers.question_id -", datetime.datetime.now().isoformat(), " MODE:", "APPLY" if args.apply else "DRY-RUN")
with eng.connect() as c:
    rows = c.exec_driver_sql("SELECT count(*) FROM student_answers").scalar()
    exists = c.exec_driver_sql(f"SELECT count(*) FROM pg_constraint WHERE conname='{FK}'").scalar()
    orphan = c.exec_driver_sql("SELECT count(*) FROM student_answers sa WHERE NOT EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=sa.question_id::text)").scalar()
log(f"  student_answers rows={rows:,}  orphan={orphan:,}  FK mevcut={'EVET' if exists else 'HAYIR'}")
if exists:
    log("  FK zaten var. Yapilacak sey yok."); sys.exit(0)
if orphan > 0:
    log(f"  !! ABORT: {orphan} orphan satir var — FK eklenemez (once temizle)."); sys.exit(1)
if not args.apply:
    log(f"  [DRY-RUN] Eklenecek: ALTER TABLE student_answers ADD CONSTRAINT {FK} FOREIGN KEY (question_id) REFERENCES question_bank(id)")
    sys.exit(0)
with eng.begin() as c:
    c.exec_driver_sql(f"ALTER TABLE student_answers ADD CONSTRAINT {FK} FOREIGN KEY (question_id) REFERENCES question_bank(id)")
    ok = c.exec_driver_sql(f"SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='{FK}'").scalar()
    log(f"  ✅ eklendi: {ok}")
log(f"  Geri alma: ALTER TABLE student_answers DROP CONSTRAINT {FK};")
