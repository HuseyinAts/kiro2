"""Deterministic structural triage of the unverified+pending active pool (READ-ONLY, no API).
Counts ONLY unambiguous structural defects (safe to reject). Turkish-char absence is
INFORMATIONAL only (cheap-filter trap guard). Semantic correctness is NOT judged here."""
import os, re, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":15})
POOL = "is_active=TRUE AND quality_review_status IN ('unverified','pending')"
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    def s(label, where):
        n = c.exec_driver_sql(f"SELECT count(*) FROM question_bank WHERE {POOL} AND ({where})").scalar()
        print(f"  {label:52} {n:>7,}")
        return n
    print("POOL TRIAGE (unverified+pending, active) -", datetime.datetime.now().isoformat())
    total = c.exec_driver_sql(f"SELECT count(*) FROM question_bank WHERE {POOL}").scalar()
    print(f"  {'TOPLAM havuz':52} {total:>7,}")
    print("\n-- KESIN yapisal kusurlar (offline reddedilebilir) --")
    d_opt   = s("eksik sik (option_a..d NULL/bos)",
                "option_a IS NULL OR btrim(option_a)='' OR option_b IS NULL OR btrim(option_b)='' OR option_c IS NULL OR btrim(option_c)='' OR option_d IS NULL OR btrim(option_d)=''")
    d_ans   = s("cevap-sik uyumsuz (correct_answer bos siga isaret)",
                "(correct_answer='A' AND (option_a IS NULL OR btrim(option_a)='')) OR (correct_answer='B' AND (option_b IS NULL OR btrim(option_b)='')) OR (correct_answer='C' AND (option_c IS NULL OR btrim(option_c)='')) OR (correct_answer='D' AND (option_d IS NULL OR btrim(option_d)='')) OR (correct_answer='E' AND (option_e IS NULL OR btrim(option_e)=''))")
    d_short = s("cok kisa metin (<15 char)", "length(btrim(question_text)) < 15")
    d_ctrl  = s("non-ws control char (gercek bozulma)", r"question_text ~ '[\x01-\x08\x0B\x0C\x0E-\x1F]'")
    d_repl  = s("U+FFFD replacement char", "position(chr(65533) in question_text) > 0")
    d_same  = s("tum siklar ayni (a=b=c=d)", "option_a=option_b AND option_b=option_c AND option_c=option_d")
    # exact duplicate within pool
    d_dup = c.exec_driver_sql(f"""SELECT COALESCE(sum(c-1),0) FROM
        (SELECT md5(question_text) h, count(*) c FROM question_bank WHERE {POOL} AND question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1) t""").scalar()
    print(f"  {'birebir mukerrer (fazlalik satir)':52} {d_dup:>7,}")
    # union of certain defects
    certain = c.exec_driver_sql(f"""SELECT count(*) FROM question_bank WHERE {POOL} AND (
        option_a IS NULL OR btrim(option_a)='' OR option_b IS NULL OR btrim(option_b)='' OR option_c IS NULL OR btrim(option_c)='' OR option_d IS NULL OR btrim(option_d)=''
        OR (correct_answer='E' AND (option_e IS NULL OR btrim(option_e)=''))
        OR length(btrim(question_text))<15
        OR question_text ~ '[\\x01-\\x08\\x0B\\x0C\\x0E-\\x1F]'
        OR position(chr(65533) in question_text)>0
        OR (option_a=option_b AND option_b=option_c AND option_c=option_d))""").scalar()
    print(f"\n  {'>> KESIN-kusurlu (union, dedup haric)':52} {certain:>7,}  (%{100.0*certain/total:.1f})")
    print(f"  {'>> yapisal TEMIZ (LLM bekler)':52} {total-certain:>7,}  (%{100.0*(total-certain)/total:.1f})")
    print("\n-- BILGI (reddetme kriteri DEGIL — ucuz-filtre tuzagi) --")
    s("Turkce-char yok (ASCII/math olabilir)", "question_text !~ '[çğıöşüÇĞİÖŞÜ]'")
    s("gorsel-bagimli ama image_url yok", "(question_text ILIKE '%sekil%' OR question_text ILIKE '%grafik%' OR question_text ILIKE '%gorsel%') AND (question_image_url IS NULL OR question_image_url='')")
    print("\n-- status kirilimi --")
    for r in c.exec_driver_sql(f"SELECT quality_review_status, count(*) FROM question_bank WHERE {POOL} GROUP BY 1 ORDER BY 2 DESC").fetchall():
        print(f"  {r[0]:52} {r[1]:>7,}")
