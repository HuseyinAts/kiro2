"""KIRO2 AUDIT pass 4 — LOGICAL orphan check on FK-less reference columns.
Data-driven: each child.col tested against its real candidate parent(s). READ-ONLY, AUTOCOMMIT."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})
OUT = "/tmp/db_audit4_output.txt"
fh = open(OUT, "w", encoding="utf-8")
def w(*a): fh.write(" ".join(str(x) for x in a) + "\n")

# (child_table, child_col, parent_table, parent_col)  -- candidates confirmed from D section
links = [
 ("kiro2_learning_events","user_id","users","id"),
 ("kiro2_learning_events","question_id","question_bank","id"),
 ("kiro2_learning_events","question_id","questions","id"),
 ("kiro2_learning_events","session_id","kiro2_cat_sessions","id"),
 ("user_item_fsrs","user_id","users","id"),
 ("user_item_fsrs","question_id","question_bank","id"),
 ("user_item_fsrs","question_id","questions","id"),
 ("fsrs_cards","student_id","users","id"),
 ("bkt_states","student_id","users","id"),
 ("bkt_states","topic_id","topic_hierarchy","id"),
 ("bkt_states","topic_id","knowledge_components","kc_id"),
 ("user_theta","user_id","users","id"),
 ("zpd_history","student_id","users","id"),
 ("zpd_history","topic_id","topic_hierarchy","id"),
 ("zpd_history","topic_id","knowledge_components","kc_id"),
 ("student_abilities","student_id","users","id"),
 ("student_abilities","subject_id","subjects","id"),
 ("daily_plans","user_id","users","id"),
 ("chat_sessions","user_id","users","id"),
 ("xp_transactions","topic_id","topic_hierarchy","id"),
 # re-confirm declared-FK-less question links measured loosely before:
 ("student_answers","question_id","question_bank","id"),
 ("exam_questions","question_id","question_bank","id"),
 ("question_kc_mapping","question_id","question_bank","id"),
 ("question_math","question_id","question_bank","id"),
 ("question_option_rationales","question_id","question_bank","id"),
]
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    w("KIRO2 LOGICAL ORPHAN CHECK (FK-less links) -", datetime.datetime.now().isoformat())
    w(f"{'child.col -> parent.col':62} {'nonnull':>9} {'orphans':>9} {'orphan%':>8} {'resolved':>9}")
    w("-"*102)
    for ct, cc, pt, pc in links:
        sql = (f"SELECT count(*) FILTER (WHERE c.{cc} IS NOT NULL) AS nonnull, "
               f"count(*) FILTER (WHERE c.{cc} IS NOT NULL AND NOT EXISTS "
               f"(SELECT 1 FROM {pt} p WHERE p.{pc}::text = c.{cc}::text)) AS orphans "
               f"FROM {ct} c")
        try:
            r = c.exec_driver_sql(sql).fetchone()
            nn, orf = r[0], r[1]
            pct = (100.0*orf/nn) if nn else 0.0
            tag = "  <-- ALL ORPHAN" if nn and orf==nn else ("  <-- partial" if orf else "  OK")
            w(f"{ct+'.'+cc+' -> '+pt+'.'+pc:62} {nn:>9} {orf:>9} {pct:>7.1f}% {nn-orf:>9}{tag}")
        except Exception as e:
            w(f"{ct+'.'+cc+' -> '+pt+'.'+pc:62} ERROR {e.__class__.__name__}: {str(e)[:80]}")
    w("\nNOTE: a link resolving 0 orphans does NOT mean an FK exists — only that current values happen to match.")
fh.close()
print(f"WROTE {OUT} ({sum(1 for _ in open(OUT, encoding='utf-8'))} lines)")
