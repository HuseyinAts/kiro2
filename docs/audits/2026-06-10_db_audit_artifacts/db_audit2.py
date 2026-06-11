"""KIRO2 DEEP DB PROFILE (values, cross-tabs, coverage, integrity), READ-ONLY.
Runs through backend DATABASE_URL (psycopg2, AUTOCOMMIT). Writes /tmp/db_audit2_output.txt."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})

OUT = "/tmp/db_audit2_output.txt"
fh = open(OUT, "w", encoding="utf-8")
def w(*a): fh.write(" ".join(str(x) for x in a) + "\n")
def hdr(t): w("\n" + "=" * 70); w(t); w("=" * 70)

with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def run(label, sql):
        try:
            rows = c.exec_driver_sql(sql).fetchall()
        except Exception as e:
            w(f"{label}: ERROR {e.__class__.__name__}: {str(e)[:160]}"); return
        if len(rows) == 1 and len(rows[0]) == 1:
            w(f"{label}: {rows[0][0]}")
        else:
            w(f"{label}:")
            for r in rows:
                w("   " + " | ".join("" if v is None else str(v) for v in r))

    w("KIRO2 DEEP PROFILE -", datetime.datetime.now().isoformat())

    # ---- 1. question_bank: default-vs-real on the "0% NULL" columns ----
    hdr("1. question_bank — VALUE checks (is '0% null' real or default?)")
    run("rows total", "SELECT count(*) FROM question_bank")
    run("is_calibrated=true", "SELECT count(*) FROM question_bank WHERE is_calibrated")
    run("irt_calibrated=true", "SELECT count(*) FROM question_bank WHERE irt_calibrated")
    run("is_calib_pool=true", "SELECT count(*) FROM question_bank WHERE is_calib_pool")
    run("irt_a IS NOT NULL (new 3PL set)", "SELECT count(*) FROM question_bank WHERE irt_a IS NOT NULL")
    run("irt_difficulty<>0 OR irt_discrimination<>1 (non-default old set)",
        "SELECT count(*) FROM question_bank WHERE irt_difficulty<>0 OR irt_discrimination<>1")
    run("calibration_sample_size>0", "SELECT count(*) FROM question_bank WHERE calibration_sample_size>0")
    run("irt_n_responses>0", "SELECT count(*) FROM question_bank WHERE irt_n_responses>0")
    run("times_asked>0 (ever served?)", "SELECT count(*) FROM question_bank WHERE times_asked>0")
    run("times_correct>0", "SELECT count(*) FROM question_bank WHERE times_correct>0")
    run("student_success_rate<>0", "SELECT count(*) FROM question_bank WHERE student_success_rate<>0")
    run("exposure_rate<>0", "SELECT count(*) FROM question_bank WHERE exposure_rate<>0")
    run("flag_count>0", "SELECT count(*) FROM question_bank WHERE flag_count>0")
    run("quality_score stats (min/max/avg/zeros)",
        "SELECT min(quality_score), max(quality_score), round(avg(quality_score)::numeric,3), count(*) FILTER (WHERE quality_score=0) FROM question_bank")
    run("difficulty_level distribution", "SELECT difficulty_level, count(*) FROM question_bank GROUP BY 1 ORDER BY 2 DESC")
    run("bloom_level distribution", "SELECT bloom_level, count(*) FROM question_bank GROUP BY 1 ORDER BY 2 DESC")
    run("grade_level distribution", "SELECT grade_level, count(*) FROM question_bank GROUP BY 1 ORDER BY 2 DESC")
    run("metadata_filled_at NOT NULL (pipeline cluster)", "SELECT count(*) FROM question_bank WHERE metadata_filled_at IS NOT NULL")
    run("overlap metadata_filled_at & irt_a both not null", "SELECT count(*) FROM question_bank WHERE metadata_filled_at IS NOT NULL AND irt_a IS NOT NULL")

    # ---- 2. who got the full metadata? cluster identity ----
    hdr("2. Does the 'enriched' cluster line up with quality status / active?")
    run("metadata_filled_at NOT NULL  x quality_review_status",
        "SELECT quality_review_status, count(*) FILTER (WHERE metadata_filled_at IS NOT NULL) AS enriched, count(*) AS total FROM question_bank GROUP BY 1 ORDER BY 2 DESC")
    run("irt_a NOT NULL  x quality_review_status",
        "SELECT quality_review_status, count(*) FILTER (WHERE irt_a IS NOT NULL) AS has_irt_abc, count(*) AS total FROM question_bank GROUP BY 1 ORDER BY 2 DESC")

    # ---- 3. served pool quality by subject / exam ----
    hdr("3. ACTIVE pool quality by subject and exam_type")
    run("by subject_area (active | active_good | active_unreviewed)",
        """SELECT subject_area,
                  count(*) FILTER (WHERE is_active) AS active,
                  count(*) FILTER (WHERE is_active AND quality_review_status IN ('auto_judged_high','bronze_clean')) AS active_good,
                  count(*) FILTER (WHERE is_active AND quality_review_status IN ('unverified','pending')) AS active_unreviewed
           FROM question_bank GROUP BY 1 ORDER BY active DESC""")
    run("by exam_type",
        """SELECT exam_type,
                  count(*) FILTER (WHERE is_active) AS active,
                  count(*) FILTER (WHERE is_active AND quality_review_status IN ('auto_judged_high','bronze_clean')) AS active_good,
                  count(*) FILTER (WHERE is_active AND quality_review_status IN ('unverified','pending')) AS active_unreviewed
           FROM question_bank GROUP BY 1 ORDER BY active DESC""")

    # ---- 4. student_answers deep ----
    hdr("4. student_answers (161,910) — what is actually recorded?")
    run("selected_answer NULL", "SELECT count(*) FROM student_answers WHERE selected_answer IS NULL")
    run("is_correct true/false/null",
        "SELECT count(*) FILTER (WHERE is_correct), count(*) FILTER (WHERE is_correct=false), count(*) FILTER (WHERE is_correct IS NULL) FROM student_answers")
    run("error_type distribution", "SELECT error_type, count(*) FROM student_answers GROUP BY 1 ORDER BY 2 DESC LIMIT 15")
    run("answered_at min/max", "SELECT min(answered_at), max(answered_at) FROM student_answers")
    run("distinct exam_session_id / distinct question_id",
        "SELECT count(DISTINCT exam_session_id), count(DISTINCT question_id) FROM student_answers")
    run("question_id resolves to question_bank?",
        "SELECT count(*) FROM student_answers sa WHERE EXISTS (SELECT 1 FROM question_bank qb WHERE qb.id::text=sa.question_id::text)")
    run("question_id resolves to legacy questions?",
        "SELECT count(*) FROM student_answers sa WHERE EXISTS (SELECT 1 FROM questions q WHERE q.id::text=sa.question_id::text)")
    run("question_id resolves to NEITHER (logical orphan)",
        "SELECT count(*) FROM student_answers sa WHERE NOT EXISTS (SELECT 1 FROM question_bank qb WHERE qb.id::text=sa.question_id::text) AND NOT EXISTS (SELECT 1 FROM questions q WHERE q.id::text=sa.question_id::text)")
    run("backfillable is_correct (selected_answer set, is_correct null, resolves to qb)",
        "SELECT count(*) FROM student_answers sa WHERE sa.selected_answer IS NOT NULL AND sa.is_correct IS NULL AND EXISTS (SELECT 1 FROM question_bank qb WHERE qb.id::text=sa.question_id::text)")

    # ---- 5. duplicates deep ----
    hdr("5. question_bank duplicates — active? cross-subject? near-dup?")
    run("exact dup extra rows that are ACTIVE",
        """WITH g AS (SELECT md5(question_text) h FROM question_bank WHERE question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1)
           SELECT count(*) FROM question_bank qb JOIN g ON g.h=md5(qb.question_text) WHERE qb.is_active""")
    run("normalized dup groups (btrim+lower) vs exact",
        """SELECT (SELECT count(*) FROM (SELECT md5(question_text) FROM question_bank WHERE question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1) a) AS exact_groups,
                  (SELECT count(*) FROM (SELECT md5(lower(btrim(question_text))) FROM question_bank WHERE question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1) b) AS normalized_groups""")
    run("top 10 dup groups (count | subjects | active | statuses)",
        """WITH g AS (SELECT md5(question_text) h, count(*) c FROM question_bank WHERE question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1 ORDER BY c DESC LIMIT 10)
           SELECT g.c, count(DISTINCT qb.subject_area) AS subjects, count(*) FILTER (WHERE qb.is_active) AS active,
                  string_agg(DISTINCT qb.quality_review_status, ',') AS statuses
           FROM g JOIN question_bank qb ON md5(qb.question_text)=g.h GROUP BY g.h, g.c ORDER BY g.c DESC""")

    # ---- 6. control-char disambiguation ----
    hdr("6. control chars EXCLUDING \\n \\t \\r (real corruption signal)")
    run("rows with non-whitespace control char",
        r"SELECT count(*) FROM question_bank WHERE question_text ~ '[\x00-\x08\x0B\x0C\x0E-\x1F]'")
    run("rows with NUL char", "SELECT count(*) FROM question_bank WHERE position(chr(0) in question_text)>0")
    run("rows with newline/tab only (benign)", r"SELECT count(*) FROM question_bank WHERE question_text ~ '[\n\t\r]'")

    # ---- 7. embedding consistency ----
    hdr("7. embedding vs embedding_model consistency")
    run("embedding NOT NULL & model NULL", "SELECT count(*) FROM question_bank WHERE embedding IS NOT NULL AND embedding_model IS NULL")
    run("embedding NULL & model NOT NULL", "SELECT count(*) FROM question_bank WHERE embedding IS NULL AND embedding_model IS NOT NULL")
    run("embedding NOT NULL total", "SELECT count(*) FROM question_bank WHERE embedding IS NOT NULL")

    # ---- 8. question-table family coverage ----
    hdr("8. Question-table family: roles & coverage vs question_bank")
    run("question_math: rows / distinct qid / resolve to qb",
        "SELECT (SELECT count(*) FROM question_math), (SELECT count(DISTINCT question_id) FROM question_math), (SELECT count(*) FROM (SELECT DISTINCT question_id FROM question_math) m WHERE EXISTS (SELECT 1 FROM question_bank qb WHERE qb.id::text=m.question_id::text))")
    run("question_option_rationales: rows / distinct qid / qb-coverage",
        "SELECT (SELECT count(*) FROM question_option_rationales), (SELECT count(DISTINCT question_id) FROM question_option_rationales), (SELECT count(*) FROM (SELECT DISTINCT question_id FROM question_option_rationales) r WHERE EXISTS (SELECT 1 FROM question_bank qb WHERE qb.id::text=r.question_id::text))")
    run("question_kc_mapping: rows / distinct qid / qb-coverage",
        "SELECT (SELECT count(*) FROM question_kc_mapping), (SELECT count(DISTINCT question_id) FROM question_kc_mapping), (SELECT count(*) FROM (SELECT DISTINCT question_id FROM question_kc_mapping) k WHERE EXISTS (SELECT 1 FROM question_bank qb WHERE qb.id::text=k.question_id::text))")
    run("exam_questions: distinct qid / resolve to qb / resolve to legacy",
        "SELECT (SELECT count(DISTINCT question_id) FROM exam_questions), (SELECT count(*) FROM (SELECT DISTINCT question_id FROM exam_questions) e WHERE EXISTS (SELECT 1 FROM question_bank qb WHERE qb.id::text=e.question_id::text)), (SELECT count(*) FROM (SELECT DISTINCT question_id FROM exam_questions) e WHERE EXISTS (SELECT 1 FROM questions q WHERE q.id::text=e.question_id::text))")
    run("osym_questions row count (FK target of student_question_responses)", "SELECT count(*) FROM osym_questions")
    run("student_question_responses row count", "SELECT count(*) FROM student_question_responses")

    # ---- 9. legacy questions table — alive & overlapping? ----
    hdr("9. legacy 'questions' (36,381) — live? overlaps question_bank?")
    run("aktif=true / is_reviewed=true", "SELECT count(*) FILTER (WHERE aktif), count(*) FILTER (WHERE is_reviewed) FROM questions")
    run("created_at min/max", "SELECT min(created_at), max(created_at) FROM questions")
    run("text overlap with question_bank (md5 match)",
        "SELECT count(*) FROM (SELECT DISTINCT md5(question_text) h FROM questions) q WHERE EXISTS (SELECT 1 FROM question_bank qb WHERE md5(qb.question_text)=q.h)")

    # ---- 10. backup tables footprint ----
    hdr("10. Backup tables footprint (size + rows)")
    run("count / total size / total rows",
        """SELECT count(*),
                  pg_size_pretty(COALESCE(sum(pg_total_relation_size(c.oid)),0)),
                  COALESCE(sum(c.reltuples)::bigint,0)
           FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE c.relkind='r' AND n.nspname='public' AND (c.relname LIKE '%backup%' OR c.relname LIKE '%_bak%' OR c.relname LIKE 'soft_fix%')""")

    # ---- 11. tiny subject buckets ----
    hdr("11. Tiny/suspect subject_area buckets")
    run("INGILIZCE/TDE/FEN/GENEL detail (active | statuses)",
        """SELECT subject_area, count(*) AS total, count(*) FILTER (WHERE is_active) AS active,
                  string_agg(DISTINCT quality_review_status, ',') AS statuses
           FROM question_bank WHERE subject_area IN ('INGILIZCE','TDE','FEN','GENEL') GROUP BY 1 ORDER BY 2""")

    w("\n" + "=" * 70); w("DEEP PROFILE COMPLETE", datetime.datetime.now().isoformat()); w("=" * 70)
fh.close()
print(f"WROTE {OUT} ({sum(1 for _ in open(OUT, encoding='utf-8'))} lines)")
