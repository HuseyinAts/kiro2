"""DRY-RUN (READ-ONLY) for irt_reset_bootstrap_flags.py — via backend DATABASE_URL.
Reproduces the script's exact detection SQL + measures load-test pollution impact.
NO writes."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})
OUT = "/tmp/db_reset_dryrun_output.txt"
fh = open(OUT, "w", encoding="utf-8")
def w(*a): fh.write(" ".join(str(x) for x in a) + "\n")
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def scalar(sql): return c.exec_driver_sql(sql).scalar()
    w("IRT RESET DRY-RUN (read-only) -", datetime.datetime.now().isoformat())
    w("="*60)
    total_true  = scalar("SELECT COUNT(*) FROM question_bank WHERE is_calibrated=TRUE")
    total_false = scalar("SELECT COUNT(*) FROM question_bank WHERE is_calibrated=FALSE")
    boot        = scalar("SELECT COUNT(*) FROM question_bank WHERE is_calibrated=TRUE AND irt_method='bootstrap_difficulty_prior'")
    hist_total  = scalar("SELECT COUNT(*) FROM irt_calibration_history")
    hist_fake   = scalar("SELECT COUNT(*) FROM irt_calibration_history WHERE standard_error=0 AND convergence_iterations=0")
    hist_del    = scalar("SELECT COUNT(*) FROM irt_calibration_history WHERE standard_error=0 AND convergence_iterations=0 AND log_likelihood=0")
    w(f"MEVCUT: is_calibrated TRUE={total_true:,}  FALSE={total_false:,}")
    w(f"        bunlardan irt_method='bootstrap_difficulty_prior' = {boot:,}")
    w(f"        irt_calibration_history toplam={hist_total:,}  SE=0&iter=0={hist_fake:,}  (silinecek SE=0&iter=0&ll=0={hist_del:,})")

    # EXACT script logic: TRUE & no learning_event(cat/exam) & no student_answers row
    will_reset = scalar("""
        SELECT COUNT(*) FROM question_bank q WHERE q.is_calibrated=TRUE
          AND NOT EXISTS (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text AND le.event_type IN ('cat_answer','exam_answer'))
          AND NOT EXISTS (SELECT 1 FROM student_answers sa WHERE sa.question_id::text=q.id::text)""")
    # Variant: ignore the student_answers guard (only real learning_events protect)
    will_reset_ignore_sa = scalar("""
        SELECT COUNT(*) FROM question_bank q WHERE q.is_calibrated=TRUE
          AND NOT EXISTS (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text AND le.event_type IN ('cat_answer','exam_answer'))""")
    # Protected ONLY by student_answers (load-test junk) — false negatives
    protected_by_sa = scalar("""
        SELECT COUNT(*) FROM question_bank q WHERE q.is_calibrated=TRUE
          AND NOT EXISTS (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text AND le.event_type IN ('cat_answer','exam_answer'))
          AND EXISTS (SELECT 1 FROM student_answers sa WHERE sa.question_id::text=q.id::text)""")
    # Truly response-backed (real learning_events) among is_calibrated TRUE
    real_backed = scalar("""
        SELECT COUNT(*) FROM question_bank q WHERE q.is_calibrated=TRUE
          AND EXISTS (SELECT 1 FROM kiro2_learning_events le WHERE le.question_id::text=q.id::text AND le.event_type IN ('cat_answer','exam_answer'))""")
    w("")
    w(f"SIFIRLANACAK (script'in tam mantigi: yanit yok + student_answers yok): {will_reset:,}")
    w(f"  -> kalan is_calibrated=TRUE: {total_true-will_reset:,}")
    w(f"student_answers (LOAD-TEST) guard'i olmadan sifirlanacak olsa: {will_reset_ignore_sa:,}")
    w(f"  -> SADECE load-test student_answers yuzunden korunan (false negative): {protected_by_sa:,}")
    w(f"gercek learning_event ile destekli (gercekten kalibre sayilabilir): {real_backed:,}")
    w("")
    w("YORUM:")
    w(f"  - Script apply edilirse {will_reset:,} soru is_calibrated=FALSE olur (calibration_task gorebilir).")
    w(f"  - {protected_by_sa:,} soru sadece load-test copu yuzunden TRUE kaliyor -> once student_answers temizlenirse bunlar da reset olur.")
    w(f"  - irt_calibrated (gercek 4PL) zaten 0; bu islem onu degistirmez.")
fh.close()
print(f"WROTE {OUT} ({sum(1 for _ in open(OUT, encoding='utf-8'))} lines)")
print(open(OUT, encoding='utf-8').read())
