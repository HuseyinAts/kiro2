"""KIRO2 AUDIT pass 3 — views, id-type consistency, embedding index, staging,
IRT history, user profile, rationale balance. READ-ONLY, AUTOCOMMIT."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
plain = re.sub(r"\+\w+", "", url)
import sqlalchemy as sa
eng = sa.create_engine(plain, connect_args={"connect_timeout": 10})
OUT = "/tmp/db_audit3_output.txt"
fh = open(OUT, "w", encoding="utf-8")
def w(*a): fh.write(" ".join(str(x) for x in a) + "\n")
def hdr(t): w("\n" + "=" * 70); w(t); w("=" * 70)
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def run(label, sql):
        try:
            rows = c.exec_driver_sql(sql).fetchall()
        except Exception as e:
            w(f"{label}: ERROR {e.__class__.__name__}: {str(e)[:140]}"); return
        if len(rows) == 1 and len(rows[0]) == 1:
            w(f"{label}: {rows[0][0]}")
        else:
            w(f"{label}:")
            for r in rows:
                w("   " + " | ".join("" if v is None else str(v) for v in r))
    w("KIRO2 AUDIT PASS 3 -", datetime.datetime.now().isoformat())

    hdr("1. embedding column: type + ANY index?")
    run("embedding column type",
        "SELECT format_type(atttypid, atttypmod) FROM pg_attribute WHERE attrelid='public.question_bank'::regclass AND attname='embedding'")
    run("indexes whose def mentions embedding/hnsw/ivfflat/vector",
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND (indexdef ILIKE '%embedding%' OR indexdef ILIKE '%hnsw%' OR indexdef ILIKE '%ivfflat%' OR indexdef ILIKE '%vector%')")
    run("ALL indexes on question_bank",
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='question_bank' ORDER BY indexname")
    run("pgvector extension installed?", "SELECT extname, extversion FROM pg_extension WHERE extname='vector'")

    hdr("2. ID / PK type consistency audit")
    run("type of every column named 'id'",
        "SELECT data_type, count(*) FROM information_schema.columns WHERE table_schema='public' AND column_name='id' GROUP BY 1 ORDER BY 2 DESC")
    run("question_bank.id / users.id / student_answers.question_id types",
        "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND ((table_name='question_bank' AND column_name='id') OR (table_name='users' AND column_name='id') OR (table_name='student_answers' AND column_name IN ('id','question_id')) OR (table_name='questions' AND column_name='id')) ORDER BY table_name, column_name")
    run("PK columns whose type is character varying (VARCHAR PK — CLAUDE.md note)",
        """SELECT rel.relname, att.attname, format_type(att.atttypid, att.atttypmod) AS typ
           FROM pg_constraint k
           JOIN pg_class rel ON rel.oid=k.conrelid
           JOIN pg_namespace n ON n.oid=rel.relnamespace
           JOIN unnest(k.conkey) WITH ORDINALITY ck(attnum,ord) ON true
           JOIN pg_attribute att ON att.attrelid=k.conrelid AND att.attnum=ck.attnum
           WHERE k.contype='p' AND n.nspname='public' AND format_type(att.atttypid,att.atttypmod) LIKE 'character varying%'
           ORDER BY 1 LIMIT 60""")

    hdr("3. The 7 VIEWS — definitions (what the app serves)")
    run("view list", "SELECT table_name FROM information_schema.views WHERE table_schema='public' ORDER BY 1")
    for v in [r[0] for r in c.exec_driver_sql("SELECT table_name FROM information_schema.views WHERE table_schema='public' ORDER BY 1")]:
        try:
            d = c.exec_driver_sql(f"SELECT pg_get_viewdef('public.{v}'::regclass, true)").scalar()
        except Exception as e:
            d = f"ERR {e}"
        w(f"\n--- VIEW {v} ---"); w(str(d)[:900])

    hdr("4. question_bank_staging (5071) — what is it?")
    run("staging_status distribution", "SELECT staging_status, count(*) FROM question_bank_staging GROUP BY 1 ORDER BY 2 DESC")

    hdr("5. irt_calibration_history (1080) — was IRT ever really run?")
    run("distinct question_id / date range",
        "SELECT count(DISTINCT question_id), min(created_at), max(created_at) FROM irt_calibration_history")
    run("sample columns", "SELECT column_name FROM information_schema.columns WHERE table_name='irt_calibration_history' ORDER BY ordinal_position")

    hdr("6. manual_review_queue (1842)")
    run("decision distribution", "SELECT decision, count(*) FROM manual_review_queue GROUP BY 1 ORDER BY 2 DESC")
    run("status distribution (if any status col)",
        "SELECT column_name FROM information_schema.columns WHERE table_name='manual_review_queue' ORDER BY ordinal_position")

    hdr("7. question_option_rationales (486k) — quality")
    run("is_correct balance", "SELECT is_correct, count(*) FROM question_option_rationales GROUP BY 1")
    run("generated_by distribution", "SELECT generated_by, count(*) FROM question_option_rationales GROUP BY 1 ORDER BY 2 DESC LIMIT 10")
    run("misconception_tag null rate", "SELECT count(*) FILTER (WHERE misconception_tag IS NULL), count(*) FROM question_option_rationales")

    hdr("8. users (75) — who are they?")
    run("role distribution", "SELECT role, count(*) FROM users GROUP BY 1 ORDER BY 2 DESC")
    run("id type sample", "SELECT id FROM users LIMIT 3")
    run("created_at range", "SELECT min(created_at), max(created_at) FROM users")

    hdr("9. is_active vs quality cross (full matrix, re-confirm)")
    run("quality_review_status x is_active x is_public",
        "SELECT quality_review_status, is_active, count(*) FROM question_bank GROUP BY 1,2 ORDER BY 1,2")

    hdr("10. legacy 'questions' aktif/is_reviewed already true — referenced anywhere by FK?")
    run("FKs that REFERENCE questions (legacy)",
        "SELECT conname, conrelid::regclass FROM pg_constraint WHERE contype='f' AND confrelid='public.questions'::regclass")

    w("\n" + "=" * 70); w("PASS 3 COMPLETE", datetime.datetime.now().isoformat()); w("=" * 70)
fh.close()
print(f"WROTE {OUT} ({sum(1 for _ in open(OUT, encoding='utf-8'))} lines)")
