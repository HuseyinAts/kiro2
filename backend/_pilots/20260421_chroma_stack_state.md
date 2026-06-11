# ADIM 0 — Chroma yığını (plan F1)

**Tarih:** 2026-04-21  
**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md` §8  
**Durum:** Kısmi tamamlandı — bkz. `.cursor/plans/20260421_chroma_stack_RESULT.md`

## Özet

| Kontrol | Sonuç |
|---------|--------|
| Router mapping | `loader.py`: `semantic_search`, `clustering_api`, `content_recommendation`, `duplicate_detection` → kategori **`search`** |
| Registry | `ROUTER_CATEGORIES` içinde **`search`** anahtarı eklendi (önceden `misc`’e düşüyordu) |
| Python paket | `requirements-minimal.txt` önceden **chromadb içermiyordu** → import başarısız / uyarı; **`chromadb>=0.4.22,<0.6` eklendi** |
| Kalıcılık | `docker-compose.yml`: backend için **`kiro2-vector-db:/app/vector_db`** volume |
| Client türü | Mevcut kod: `chromadb.Client(ChromaSettings(persist_directory=...))` — **embedded**; ayrı Chroma HTTP servisi henüz compose’da yok |

## Sonraki adımlar (§8 checklist)

1. Backend image rebuild sonrası container içinde `python -c "import chromadb; print(chromadb.__version__)"`.
2. `SemanticSearchService.initialize()` veya health endpoint ile smoke.
3. İsteğe bağlı: `chromadb.HttpClient` + `chroma` compose servisi (host `chroma`, port 8000) — dört serviste tekrar kullanım için ortak yardımcı modül.
4. `scripts/test_endpoints.ps1` genişletmesi: auth + search smoke.

## DUR tetikleyicileri

- `chromadb` import hâlâ başarısızsa: Dockerfile / pip cache incele.
- Embedding model indirilemiyorsa: `EmbeddingService` hash fallback ile devam eder; üretim kalitesi için model stratejisi ayrı not.
