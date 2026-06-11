"""Post-remediation verification (READ-ONLY)."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":10})
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def s(q): return c.exec_driver_sql(q).scalar()
    print("VERIFY -", datetime.datetime.now().isoformat())
    print("student_answers rows           :", s("SELECT count(*) FROM student_answers"))
    print("student_answers backup rows    :", s("SELECT count(*) FROM student_answers_backup_20260610"))
    print("is_calibrated TRUE             :", s("SELECT count(*) FROM question_bank WHERE is_calibrated=TRUE"))
    print("is_calibrated FALSE            :", s("SELECT count(*) FROM question_bank WHERE is_calibrated=FALSE"))
    print("iscalib reset backup rows      :", s("SELECT count(*) FROM question_bank_iscalib_reset_backup_20260610"))
    print("remaining TRUE response-backed :", s("""SELECT count(*) FROM question_bank q WHERE is_calibrated=TRUE
        AND EXISTS (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text AND le.event_type IN ('cat_answer','exam_answer'))"""))
    print("remaining TRUE w/o response    :", s("""SELECT count(*) FROM question_bank q WHERE is_calibrated=TRUE
        AND NOT EXISTS (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text AND le.event_type IN ('cat_answer','exam_answer'))"""))
    print("irt_method of remaining TRUE   :")
    for r in c.exec_driver_sql("SELECT irt_method, count(*) FROM question_bank WHERE is_calibrated=TRUE GROUP BY 1 ORDER BY 2 DESC").fetchall():
        print("   ", r[0], r[1])
