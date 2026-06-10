"""student_answers cleanup SCOPING + dependency check (READ-ONLY).
Defines delete-set data-driven; checks child FKs; identifies any rows worth KEEPING."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})
OUT = "/tmp/db_sa_profile_output.txt"
fh = open(OUT, "w", encoding="utf-8")
def w(*a): fh.write(" ".join(str(x) for x in a) + "\n")
def hdr(t): w("\n"+"="*64); w(t); w("="*64)
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def run(label, sql):
        try:
            rows = c.exec_driver_sql(sql).fetchall()
        except Exception as e:
            w(f"{label}: ERROR {e.__class__.__name__}: {str(e)[:120]}"); return
        if len(rows)==1 and len(rows[0])==1: w(f"{label}: {rows[0][0]}")
        else:
            w(f"{label}:")
            for r in rows: w("   " + " | ".join("" if v is None else str(v) for v in r))
    w("student_answers CLEANUP PROFILE -", datetime.datetime.now().isoformat())

    hdr("1. DEPENDENCY: any FK referencing student_answers (child tables)?")
    run("FKs with parent=student_answers",
        "SELECT conname, conrelid::regclass AS child FROM pg_constraint WHERE contype='f' AND confrelid='public.student_answers'::regclass")
    w("(bos = student_answers'a bagli child tablo yok -> satir silmek guvenli)")

    hdr("2. SCOPE: total + classification")
    run("total rows", "SELECT count(*) FROM student_answers")
    run("resolves to question_bank", "SELECT count(*) FROM student_answers sa WHERE EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=sa.question_id::text)")
    run("orphan (not in qb)", "SELECT count(*) FROM student_answers sa WHERE NOT EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=sa.question_id::text)")
    run("is_correct NOT NULL (graded)", "SELECT count(*) FROM student_answers WHERE is_correct IS NOT NULL")
    run("KEEP-candidate = resolves to qb AND is_correct NOT NULL", "SELECT count(*) FROM student_answers sa WHERE sa.is_correct IS NOT NULL AND EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=sa.question_id::text)")
    run("answered 2026-06-09 (today bulk)", "SELECT count(*) FROM student_answers WHERE answered_at::date='2026-06-09'")
    run("answered NOT 2026-06-09 (scattered)", "SELECT count(*) FROM student_answers WHERE answered_at::date<>'2026-06-09'")

    hdr("3. WHO: users behind these answers (via exam_sessions.student_id)")
    run("distinct users + role + count + date range",
        """SELECT u.id, u.role, count(*) AS answers, min(sa.answered_at)::date, max(sa.answered_at)::date
           FROM student_answers sa
           JOIN exam_sessions es ON es.id::text=sa.exam_session_id::text
           JOIN users u ON u.id::text=es.student_id::text
           GROUP BY u.id, u.role ORDER BY answers DESC""")
    run("user email/username if columns exist",
        "SELECT id, role, email FROM users WHERE id::text IN (SELECT DISTINCT es.student_id::text FROM exam_sessions es JOIN student_answers sa ON sa.exam_session_id::text=es.id::text)")

    hdr("4. exam_sessions tied to these answers (clean candidates too?)")
    run("distinct sessions referenced", "SELECT count(DISTINCT exam_session_id) FROM student_answers")
    run("those sessions: status + exam_name sample",
        """SELECT es.status, count(*) FROM exam_sessions es
           WHERE es.id::text IN (SELECT DISTINCT exam_session_id::text FROM student_answers) GROUP BY es.status ORDER BY 2 DESC""")
    run("exam_sessions total rows", "SELECT count(*) FROM exam_sessions")

    hdr("5. proposed DELETE predicate counts (pick one)")
    run("P1: DELETE all student_answers", "SELECT count(*) FROM student_answers")
    run("P2: DELETE where answered_at::date='2026-06-09'", "SELECT count(*) FROM student_answers WHERE answered_at::date='2026-06-09'")
    run("P3: DELETE orphan question_id (not in qb)", "SELECT count(*) FROM student_answers sa WHERE NOT EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=sa.question_id::text)")
    run("P3 KEEP (resolves to qb)", "SELECT count(*) FROM student_answers sa WHERE EXISTS (SELECT 1 FROM question_bank q WHERE q.id::text=sa.question_id::text)")
    w("\nNOT: P3 (orphan sil) en guvenli — gercek soruya baglanani korur. P1 hepsini siler.")
fh.close()
print(f"WROTE {OUT} ({sum(1 for _ in open(OUT, encoding='utf-8'))} lines)")
print(open(OUT, encoding='utf-8').read())
