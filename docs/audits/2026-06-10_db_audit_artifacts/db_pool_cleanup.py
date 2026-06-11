"""API-free deterministic pool cleanup (unverified+pending active):
  C) dedup: deactivate non-canonical pool duplicates (keep best-status copy)
  A) strip non-ws control chars from question_text (content preserved)
  B) reject structurally-broken (missing option / answer-option mismatch / all-options-same)
Order C->A->B (dedup on ORIGINAL md5 before strip). Default DRY-RUN; --apply atomic + backup.
NO garble rejection (GATE-1 failed: pool indistinguishable from clean)."""
import os, re, sys, argparse, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+","",url), connect_args={"connect_timeout":20})
POOL = "is_active=TRUE AND quality_review_status IN ('unverified','pending')"
CTRL = r"[\x01-\x08\x0B\x0C\x0E-\x1F]"
BROKEN = ("(option_a IS NULL OR btrim(option_a)='' OR option_b IS NULL OR btrim(option_b)='' "
          "OR option_c IS NULL OR btrim(option_c)='' OR option_d IS NULL OR btrim(option_d)='' "
          "OR (correct_answer='E' AND (option_e IS NULL OR btrim(option_e)='')) "
          "OR (option_a=option_b AND option_b=option_c AND option_c=option_d))")
DEDUP_IDS = """SELECT id FROM (
    SELECT id, quality_review_status st,
      row_number() OVER (PARTITION BY md5(question_text) ORDER BY
        CASE quality_review_status WHEN 'auto_judged_high' THEN 0 WHEN 'human_verified' THEN 0
             WHEN 'bronze_clean' THEN 1 WHEN 'pending' THEN 2 WHEN 'unverified' THEN 3 ELSE 4 END, id) rn
    FROM question_bank WHERE is_active AND question_text IS NOT NULL
      AND md5(question_text) IN (SELECT md5(question_text) FROM question_bank
            WHERE is_active AND question_text IS NOT NULL GROUP BY 1 HAVING count(*)>1)
  ) z WHERE z.rn>1 AND z.st IN ('unverified','pending')"""
BACKUP = "question_bank_pool_cleanup_backup_20260610"
ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args = ap.parse_args()
def log(*a): print(*a); sys.stdout.flush()
log("POOL CLEANUP -", datetime.datetime.now().isoformat(), " MODE:", "APPLY" if args.apply else "DRY-RUN")
with eng.connect() as c:
    n_dedup = c.exec_driver_sql(f"SELECT count(*) FROM ({DEDUP_IDS}) x").scalar()
    n_ctrl  = c.exec_driver_sql(f"SELECT count(*) FROM question_bank WHERE {POOL} AND question_text ~ '{CTRL}'").scalar()
    n_brok  = c.exec_driver_sql(f"SELECT count(*) FROM question_bank WHERE {POOL} AND ({BROKEN})").scalar()
log(f"  C) dedup deaktive edilecek (pool, non-canonical): {n_dedup:,}")
log(f"  A) control-char strip edilecek                  : {n_ctrl:,}")
log(f"  B) yapisal-bozuk reddedilecek                   : {n_brok:,}")
if not args.apply:
    log("  [DRY-RUN] degisiklik yok. --apply ile uygula."); sys.exit(0)
with eng.begin() as c:
    if c.exec_driver_sql(f"SELECT to_regclass('public.{BACKUP}') IS NOT NULL").scalar():
        raise RuntimeError(f"backup '{BACKUP}' zaten var -> rollback")
    # backup pre-state of all affected rows
    c.exec_driver_sql(f"""CREATE TABLE {BACKUP} AS
        SELECT id, question_text, quality_review_status, is_active, 'dedup'::text AS reason FROM question_bank WHERE id IN ({DEDUP_IDS})
        UNION ALL SELECT id, question_text, quality_review_status, is_active, 'control' FROM question_bank WHERE {POOL} AND question_text ~ '{CTRL}'
        UNION ALL SELECT id, question_text, quality_review_status, is_active, 'broken' FROM question_bank WHERE {POOL} AND ({BROKEN})""")
    bcnt = c.exec_driver_sql(f"SELECT count(*) FROM {BACKUP}").scalar()
    log(f"  backup '{BACKUP}': {bcnt:,} satir (overlap ile)")
    # C: dedup (uses ORIGINAL md5)
    d = c.exec_driver_sql(f"UPDATE question_bank SET is_active=false WHERE id IN ({DEDUP_IDS})").rowcount
    # A: strip control chars (only still-active pool rows)
    a = c.exec_driver_sql(f"UPDATE question_bank SET question_text=regexp_replace(question_text,'{CTRL}','','g') WHERE {POOL} AND question_text ~ '{CTRL}'").rowcount
    # B: reject broken
    b = c.exec_driver_sql(f"UPDATE question_bank SET quality_review_status='rejected', is_active=false WHERE {POOL} AND ({BROKEN})").rowcount
    log(f"  C dedup deaktive={d:,}  A strip={a:,}  B reject={b:,}")
    # verify
    rem_ctrl = c.exec_driver_sql(f"SELECT count(*) FROM question_bank WHERE {POOL} AND question_text ~ '{CTRL}'").scalar()
    rem_brok = c.exec_driver_sql(f"SELECT count(*) FROM question_bank WHERE {POOL} AND ({BROKEN})").scalar()
    log(f"  dogrulama: kalan control={rem_ctrl}  kalan broken={rem_brok}  (ikisi de 0 olmali)")
    if rem_ctrl != 0 or rem_brok != 0:
        raise RuntimeError("verify failed -> rollback")
log(f"  ✅ COMMIT. (backup: {BACKUP})")
log(f"  Geri alma: UPDATE question_bank q SET is_active=b.is_active, quality_review_status=b.quality_review_status,")
log(f"             question_text=b.question_text FROM {BACKUP} b WHERE b.id=q.id;")
