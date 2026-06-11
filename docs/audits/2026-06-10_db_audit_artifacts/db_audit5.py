"""KIRO2 AUDIT pass 5 — ROOT-CAUSE forensics (data-driven), READ-ONLY, AUTOCOMMIT.
(A) is_calibrated=TRUE composition: bootstrap-fake vs real vs no-history.
(B) student_answers 161K origin: id formats, session/user linkage, time clustering, value fingerprints."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})
OUT = "/tmp/db_audit5_output.txt"
fh = open(OUT, "w", encoding="utf-8")
def w(*a): fh.write(" ".join(str(x) for x in a) + "\n")
def hdr(t): w("\n" + "=" * 70); w(t); w("=" * 70)
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def run(label, sql):
        try:
            rows = c.exec_driver_sql(sql).fetchall()
        except Exception as e:
            w(f"{label}: ERROR {e.__class__.__name__}: {str(e)[:120]}"); return
        if len(rows) == 1 and len(rows[0]) == 1: w(f"{label}: {rows[0][0]}")
        else:
            w(f"{label}:")
            for r in rows: w("   " + " | ".join("" if v is None else str(v) for v in r))
    w("KIRO2 ROOT-CAUSE FORENSICS -", datetime.datetime.now().isoformat())

    hdr("A. is_calibrated=TRUE (82,530) — what set it? (bootstrap vs real vs synthetic)")
    run("is_calibrated TRUE total", "SELECT count(*) FROM question_bank WHERE is_calibrated")
    run("of those: has calib_history with se=0 & iter=0 (BOOTSTRAP signature)",
        """SELECT count(*) FROM question_bank q WHERE q.is_calibrated AND EXISTS
           (SELECT 1 FROM irt_calibration_history h WHERE h.question_id::text=q.id::text
            AND h.standard_error=0 AND h.convergence_iterations=0)""")
    run("of those: has calib_history with se>0 (REAL EM signature)",
        """SELECT count(*) FROM question_bank q WHERE q.is_calibrated AND EXISTS
           (SELECT 1 FROM irt_calibration_history h WHERE h.question_id::text=q.id::text AND h.standard_error>0)""")
    run("of those: NO calib_history row at all (pure flag set, no record)",
        """SELECT count(*) FROM question_bank q WHERE q.is_calibrated AND NOT EXISTS
           (SELECT 1 FROM irt_calibration_history h WHERE h.question_id::text=q.id::text)""")
    run("of those: has ANY real learning_event (cat/exam) — i.e. response-backed",
        """SELECT count(*) FROM question_bank q WHERE q.is_calibrated AND EXISTS
           (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text
            AND le.event_type IN ('cat_answer','exam_answer'))""")
    run("irt_method distribution for is_calibrated=TRUE",
        "SELECT irt_method, count(*) FROM question_bank WHERE is_calibrated GROUP BY 1 ORDER BY 2 DESC")
    run("irt_calibrated (the SEPARATE 4PL flag) TRUE count", "SELECT count(*) FROM question_bank WHERE irt_calibrated")
    run("irt_calibration_history total rows + se=0/iter=0 share",
        "SELECT count(*), count(*) FILTER (WHERE standard_error=0 AND convergence_iterations=0) FROM irt_calibration_history")

    hdr("B. student_answers (161,910) — origin fingerprints")
    run("sample student_answers.question_id (10)", "SELECT DISTINCT question_id FROM student_answers LIMIT 10")
    run("sample question_bank.id (5)", "SELECT id FROM question_bank LIMIT 5")
    run("distinct exam_session_id", "SELECT count(DISTINCT exam_session_id) FROM student_answers")
    run("exam_session_id resolves to exam_sessions?",
        "SELECT count(*) FROM (SELECT DISTINCT exam_session_id FROM student_answers) s WHERE EXISTS (SELECT 1 FROM exam_sessions e WHERE e.id::text=s.exam_session_id::text)")
    run("those exam_sessions -> distinct student/user (try student_id then user_id)",
        "SELECT count(DISTINCT student_id) FROM exam_sessions WHERE id::text IN (SELECT DISTINCT exam_session_id::text FROM student_answers)")
    run("answered_at by DAY (top 15 — bulk = load-test runs)",
        "SELECT answered_at::date, count(*) FROM student_answers GROUP BY 1 ORDER BY 2 DESC LIMIT 15")
    run("response_time_seconds stats (min/max/avg/stddev)",
        "SELECT min(response_time_seconds), max(response_time_seconds), round(avg(response_time_seconds)::numeric,1), round(stddev(response_time_seconds)::numeric,1) FROM student_answers")
    run("selected_answer distribution", "SELECT selected_answer, count(*) FROM student_answers GROUP BY 1 ORDER BY 2 DESC")
    run("answer_changes / time_to_first_answer stats",
        "SELECT round(avg(answer_changes)::numeric,2), round(avg(time_to_first_answer)::numeric,2), count(*) FILTER (WHERE answer_changes=0) FROM student_answers")
    run("rows per exam_session (min/max/avg)",
        "SELECT min(n), max(n), round(avg(n)::numeric,1) FROM (SELECT exam_session_id, count(*) n FROM student_answers GROUP BY 1) t")
    run("question_id format: how many are 36-char UUID vs other",
        "SELECT count(*) FILTER (WHERE question_id ~ '^[0-9a-fA-F-]{36}$') AS uuid_like, count(*) FILTER (WHERE question_id !~ '^[0-9a-fA-F-]{36}$') AS other FROM student_answers")

    hdr("C. exam_sessions (323) — are they real or test?")
    run("exam_sessions columns", "SELECT column_name FROM information_schema.columns WHERE table_name='exam_sessions' ORDER BY ordinal_position")

    w("\n" + "=" * 70); w("FORENSICS COMPLETE", datetime.datetime.now().isoformat()); w("=" * 70)
fh.close()
print(f"WROTE {OUT} ({sum(1 for _ in open(OUT, encoding='utf-8'))} lines)")
