"""Create HNSW index on question_bank.embedding (vector_cosine_ops), ONLINE (CONCURRENTLY).
Default = DRY-RUN. Pass --apply to build. Idempotent; detects existing/invalid index."""
import os, re, sys, argparse, datetime
url = (os.environ.get("DATABASE_URL") or os.environ.get("ASYNC_DATABASE_URL") or "")
import sqlalchemy as sa
eng = sa.create_engine(re.sub(r"\+\w+", "", url), connect_args={"connect_timeout": 10})
IDX = "idx_qb_embedding_hnsw"
ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args = ap.parse_args()
def log(*a): print(*a); sys.stdout.flush()
log("HNSW INDEX BUILD -", datetime.datetime.now().isoformat(), " MODE:", "APPLY" if args.apply else "DRY-RUN")

# CONCURRENTLY requires autocommit (no transaction block)
with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
    emb = c.exec_driver_sql("SELECT count(*) FILTER (WHERE embedding IS NOT NULL), count(*) FROM question_bank").fetchone()
    log(f"  embedding dolu/toplam: {emb[0]:,}/{emb[1]:,}")
    idxs = c.exec_driver_sql("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='question_bank'").fetchall()
    hnsw = [r[0] for r in idxs if 'hnsw' in r[1].lower()]
    log(f"  mevcut HNSW index: {hnsw or 'YOK'}")
    inv = c.exec_driver_sql("SELECT cl.relname FROM pg_index i JOIN pg_class cl ON cl.oid=i.indexrelid JOIN pg_class t ON t.oid=i.indrelid WHERE t.relname='question_bank' AND i.indisvalid=false").fetchall()
    if inv:
        log(f"  !! INVALID index var: {[r[0] for r in inv]} -> once DROP INDEX CONCURRENTLY ile temizle")
    if hnsw and not inv:
        log("  Zaten gecerli HNSW index var. Yapilacak bir sey yok."); sys.exit(0)
    if not args.apply:
        log(f"  [DRY-RUN] Olusturulacak: CREATE INDEX CONCURRENTLY {IDX} ... USING hnsw (embedding vector_cosine_ops)")
        log("  Uygulamak icin: python /tmp/db_hnsw_create.py --apply"); sys.exit(0)

    try:
        c.exec_driver_sql("SET maintenance_work_mem='256MB'")
    except Exception as e:
        log(f"  (maintenance_work_mem ayarlanamadi: {e.__class__.__name__} — devam)")
    log("  HNSW build basliyor (147K vektor — birkac dakika surebilir, lutfen bekle)...")
    t0 = datetime.datetime.now()
    c.exec_driver_sql(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {IDX} ON question_bank USING hnsw (embedding vector_cosine_ops)")
    dt = (datetime.datetime.now()-t0).total_seconds()
    valid = c.exec_driver_sql(f"SELECT i.indisvalid FROM pg_index i JOIN pg_class cl ON cl.oid=i.indexrelid WHERE cl.relname='{IDX}'").scalar()
    size = c.exec_driver_sql(f"SELECT pg_size_pretty(pg_relation_size('{IDX}'))").scalar()
    log(f"  ✅ index '{IDX}' olusturuldu  valid={valid}  size={size}  sure={dt:.0f}s")
    log(f"  Geri alma: DROP INDEX CONCURRENTLY IF EXISTS {IDX};")
