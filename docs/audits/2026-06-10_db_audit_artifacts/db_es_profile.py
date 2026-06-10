"""exam_sessions / exam_questions cleanup scoping + FK readiness (READ-ONLY)."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":10})
def hdr(t): print("\n"+"="*60); print(t); print("="*60)
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def run(label, sql):
        try: rows = c.exec_driver_sql(sql).fetchall()
        except Exception as e: print(f"{label}: ERR {e.__class__.__name__}: {str(e)[:90]}"); return
        if len(rows)==1 and len(rows[0])==1: print(f"{label}: {rows[0][0]}")
        else:
            print(f"{label}:")
            for r in rows: print("   "+" | ".join("" if v is None else str(v) for v in r))
    print("exam_sessions/exam_questions PROFILE -", datetime.datetime.now().isoformat())

    hdr("1. FK structure")
    run("FKs REFERENCING exam_sessions (children)",
        "SELECT conname, conrelid::regclass FROM pg_constraint WHERE contype='f' AND confrelid='public.exam_sessions'::regclass")
    run("FKs REFERENCING exam_questions (children)",
        "SELECT conname, conrelid::regclass FROM pg_constraint WHERE contype='f' AND confrelid='public.exam_questions'::regclass")
    run("exam_sessions OWN fks",
        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE contype='f' AND conrelid='public.exam_sessions'::regclass")
    run("exam_questions OWN fks",
        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE contype='f' AND conrelid='public.exam_questions'::regclass")
    run("student_answers OWN fks (FK ekleme oncesi mevcut?)",
        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE contype='f' AND conrelid='public.student_answers'::regclass")

    hdr("2. exam_sessions — test mi? (user/role/email)")
    run("by user",
        """SELECT u.role, u.email, count(*) FROM exam_sessions es JOIN users u ON u.id::text=es.student_id::text
           GROUP BY 1,2 ORDER BY 3 DESC""")
    run("total / distinct users", "SELECT count(*), count(DISTINCT student_id) FROM exam_sessions")
    run("student_id resolves to users?", "SELECT count(*) FROM exam_sessions es WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id::text=es.student_id::text)")

    hdr("3. exam_questions — scope")
    run("total / distinct sessions / distinct questions",
        "SELECT count(*), count(DISTINCT exam_session_id), count(DISTINCT question_id) FROM exam_questions")
    run("exam_session_id resolves to exam_sessions?",
        "SELECT count(*) FROM exam_questions eq WHERE NOT EXISTS (SELECT 1 FROM exam_sessions es WHERE es.id::text=eq.exam_session_id::text)")
    run("question_id resolves to question_bank? (orphan)",
        "SELECT count(*) FILTER (WHERE EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=eq.question_id::text)) AS in_qb, count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=eq.question_id::text)) AS orphan FROM exam_questions eq")

    hdr("4. FK readiness: student_answers.question_id -> question_bank.id")
    run("student_answers rows (0 olmali)", "SELECT count(*) FROM student_answers")
    run("question_bank.id type / student_answers.question_id type",
        "SELECT (SELECT data_type FROM information_schema.columns WHERE table_name='question_bank' AND column_name='id'), (SELECT data_type FROM information_schema.columns WHERE table_name='student_answers' AND column_name='question_id')")
    run("question_bank.id PK var mi?", "SELECT count(*) FROM pg_constraint WHERE contype='p' AND conrelid='public.question_bank'::regclass")
