# Windows pgvector HNSW Index Build Kuralı

2026-06-12'de eklendi. Kök neden: `question_bank.embedding` (vector 768, 147K dolu)
üzerine HNSW index kurarken **parallel build Windows'ta patladı**:
`could not create shared memory segment "Global/PostgreSQL.xxx": Not enough space`.

## ALTIN KURAL

> **Windows'ta HNSW index build'ini DAİMA tek-thread çalıştır:**
> `SET max_parallel_maintenance_workers = 0;` ÖNCE, sonra `CREATE INDEX`.

## Kök neden

- `dynamic_shared_memory_type = windows` (Windows'ta tek seçenek, değişmez).
- pgvector **parallel** HNSW build'i, worker'lar arası graph için tek bir **DSM
  (dynamic shared memory) segmenti** ister; boyutu ~`maintenance_work_mem`.
- Windows'ta DSM = `CreateFileMapping` → **page-file-backed commit**. RAM + sayfa
  dosyası "commit limit"inden düşülür.
- `shared_buffers` zaten 4GB commit'li. Üstüne `maintenance_work_mem=2GB` ile
  parallel build ~2GB DSM isteyince sistem commit limiti aşıldı → hata.
- `max_parallel_maintenance_workers=0` → worker yok → DSM segmenti **hiç istenmez**
  → build leader'ın **private** belleğinde çalışır → sorunsuz.

**Özet:** RAM yetersizliği DEĞİL; parallel build'in büyük paylaşımlı-bellek
segmentini commit edememesi.

## DOĞRU build (kanıtlanmış)

```sql
SET max_parallel_maintenance_workers = 0;   -- ZORUNLU (Windows)
SET maintenance_work_mem = '1GB';            -- private bellek, DSM değil
CREATE INDEX CONCURRENTLY idx_qb_embedding_hnsw
  ON question_bank USING hnsw (embedding vector_cosine_ops);
```

- 147K vektör için ~birkaç dakika (tek-thread). Tek seferlik iş için kabul edilebilir.
- SET'ler **session-bazlı** — global config'i değiştirme (diğer VACUUM/index parallel kalsın).
- **MCP timeout tuzağı:** `mcp__dbhub-kiro2__execute_sql` ile çalıştırırsan istemci
  ~30-60s'de timeout verir AMA build server'da SÜRER. `pg_stat_progress_create_index`
  ile izle; `indisvalid=true` olunca bitmiştir. Uzun build için `psql` (host) daha temiz.

## REBUILD'DEN KAÇIN (en önemli)

HNSW **insert'leri canlı kabul eder** (IVFFlat'ten farkı). Embedding eklerken:
`UPDATE question_bank SET embedding=... WHERE ...` → yeni değerler **mevcut HNSW
index'ine OTOMATİK eklenir, REBUILD GEREKMEZ.** Tam rebuild yalnız index parametresi
(m, ef_construction) değişirse veya bozulursa gerekir — nadir.

## Arama kalitesi (build değil, query-time)

Recall düşükse servis sorgusunda: `SET hnsw.ef_search = 100;` (varsayılan 40).
Yüksek = daha iyi recall, biraz yavaş.

## İlişkili

- `docs/audits/2026-06-10_full_db_audit.md` §J (R3 HNSW remediation).
- Migration `b2f1a9c7d3e4_add_qb_embedding_hnsw_index.py` (alembic zincirinde applied;
  sync-stamp atladığı için canlıda yoktu → 2026-06-12'de manuel kuruldu).
