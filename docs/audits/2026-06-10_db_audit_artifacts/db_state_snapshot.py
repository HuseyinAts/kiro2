"""CURRENT STATE snapshot + drift detection (READ-ONLY). Writes /tmp/db_state_snapshot.txt.
Captures: table inventory + write-activity (pg_stat), question_bank deep, remediation persistence,
object inventory for diff vs baseline. Used to detect external changes made on other platforms."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":20})
OUT="/tmp/db_state_snapshot.txt"; fh=open(OUT,"w",encoding="utf-8")
def w(*a): fh.write(" ".join(str(x) for x in a)+"\n")
def hdr(t): w("\n"+"="*72); w(t); w("="*72)
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def rows(sql): return c.exec_driver_sql(sql).fetchall()
    def sc(sql): return c.exec_driver_sql(sql).scalar()
    w("CURRENT STATE SNAPSHOT -", datetime.datetime.now().isoformat())

    hdr("A. OVERVIEW")
    w("db size:", sc("SELECT pg_size_pretty(pg_database_size(current_database()))"))
    w("public tables:", sc("SELECT count(*) FROM pg_tables WHERE schemaname='public'"),
      " views:", sc("SELECT count(*) FROM pg_views WHERE schemaname='public'"))
    w("alembic head:", [r[0] for r in rows("SELECT version_num FROM alembic_version")] if sc("SELECT to_regclass('public.alembic_version') IS NOT NULL") else "yok")

    hdr("B. ALL TABLES — rowcount + lifetime ins/upd/del + last analyze  (aktivite = dis degisiklik sinyali)")
    w(f"{'table':52} {'rows':>9} {'ins':>9} {'upd':>9} {'del':>9}  last_auto")
    for r in rows("""SELECT t.relname, t.reltuples::bigint,
                 s.n_tup_ins, s.n_tup_upd, s.n_tup_del, s.last_autoanalyze
               FROM pg_stat_user_tables s JOIN pg_class t ON t.oid=s.relid
               WHERE s.schemaname='public'
               ORDER BY (s.n_tup_ins+s.n_tup_upd+s.n_tup_del) DESC"""):
        la = str(r[5])[:19] if r[5] else ""
        w(f"{r[0]:52} {str(r[1]):>9} {str(r[2]):>9} {str(r[3]):>9} {str(r[4]):>9}  {la}")

    hdr("C. question_bank deep")
    w("total:", sc("SELECT count(*) FROM question_bank"))
    w("is_active T/F:", rows("SELECT is_active, count(*) FROM question_bank GROUP BY 1 ORDER BY 1"))
    w("quality_review_status x is_active:")
    for r in rows("SELECT quality_review_status, is_active, count(*) FROM question_bank GROUP BY 1,2 ORDER BY 1,2"):
        w("   ", r[0], r[1], r[2])
    w("is_calibrated TRUE:", sc("SELECT count(*) FROM question_bank WHERE is_calibrated"))
    w("irt_calibrated TRUE:", sc("SELECT count(*) FROM question_bank WHERE irt_calibrated"))
    w("irt_method (is_calibrated=TRUE):", rows("SELECT irt_method, count(*) FROM question_bank WHERE is_calibrated GROUP BY 1 ORDER BY 2 DESC"))
    w("subject_area:", rows("SELECT subject_area, count(*) FROM question_bank GROUP BY 1 ORDER BY 2 DESC"))
    w("exam_type:", rows("SELECT exam_type, count(*) FROM question_bank GROUP BY 1 ORDER BY 2 DESC"))
    w("image missing:", sc("SELECT count(*) FROM question_bank WHERE question_image_url IS NULL OR question_image_url=''"))
    w("embedding not null:", sc("SELECT count(*) FROM question_bank WHERE embedding IS NOT NULL"))
    w("exact dup extra rows (active):", sc("SELECT COALESCE(sum(c-1),0) FROM (SELECT md5(question_text) h,count(*) c FROM question_bank WHERE is_active AND question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1) t"))

    hdr("D. REMEDIATION PERSISTENCE (R1-R5 + pool cleanup duruyor mu?)")
    w("student_answers rows (R1 -> 0 idi):", sc("SELECT count(*) FROM student_answers"))
    w("exam_sessions rows (R4 -> 0 idi):", sc("SELECT count(*) FROM exam_sessions"))
    w("exam_questions rows (R4 -> 0 idi):", sc("SELECT count(*) FROM exam_questions"))
    w("FK student_answers_question_id_fkey var mi (R5):", sc("SELECT count(*) FROM pg_constraint WHERE conname='student_answers_question_id_fkey'"))
    w("HNSW idx_qb_embedding_hnsw var mi (R3):", sc("SELECT count(*) FROM pg_indexes WHERE indexname='idx_qb_embedding_hnsw'"))
    w("backup tablolari:")
    for r in rows("""SELECT relname, c.reltuples::bigint
                     FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                     WHERE c.relkind='r' AND n.nspname='public'
                       AND relname ~ 'backup|_bak|^soft_fix'
                     ORDER BY relname"""):
        w("   ", r[0], r[1])

    hdr("E. OBJECT INVENTORY (baseline diff icin)")
    w("-- TABLES (alfabetik, baseline ile diff edilecek) --")
    for r in rows("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1"):
        w(r[0])
    w("-- index sayisi:", sc("SELECT count(*) FROM pg_indexes WHERE schemaname='public'"),
      " enum tip:", sc("SELECT count(DISTINCT t.typname) FROM pg_type t JOIN pg_enum e ON e.enumtypid=t.oid JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='public'"))
fh.close()
import sys
print(f"WROTE {OUT} ({sum(1 for _ in open(OUT,encoding='utf-8'))} lines)")
# print key summary to console
for line in open(OUT,encoding="utf-8"):
    if any(k in line for k in ("db size","public tables","alembic head","total:","is_calibrated","irt_calibrated","student_answers rows","exam_sessions rows","exam_questions rows","FK student","HNSW","index sayisi")):
        sys.stdout.write(line)
