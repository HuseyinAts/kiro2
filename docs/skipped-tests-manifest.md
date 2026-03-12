# Skipped Tests Manifest — KIRO2 Backend

**Tarih:** 8 Mart 2026 (Session 80)
**Toplam test dosyası:** 630
**Skip pattern içeren:** 268 (%42.5)

## Genel Bakış

| Metrik | Değer |
|--------|-------|
| Toplam test dosyası | 630 |
| Skip pattern içeren | 268 |
| Module-level `pytest.skip()` | ~230 |
| `pytestmark = skipif` | ~38 |
| Skip oranı | %42.5 |

## Kategori Bazlı Dağılım

### P1 — Hızlı Düzeltilebilir (78 dosya)

| Kategori | Dosya | Root Cause | Çözüm |
|----------|-------|-----------|-------|
| Heavy imports / timeout | 33 | `from main import app` 10+ sn | Lazy import veya ASGITransport fixture |
| Model import hataları | 17 | İmport path değişmiş | İmport path güncelle |
| httpx deprecated | 15 | `AsyncClient(app=app)` yerine `ASGITransport` | Toplu migration |
| SecurityConfig yok | 6 | Config import fail | İmport path kontrol |
| InputValidator yok | 7 | Modül taşınmış/silinmiş | İmport güncelle veya sil |

### P2 — Servis Bağımlılığı (132 dosya)

| Kategori | Dosya | Root Cause | Çözüm |
|----------|-------|-----------|-------|
| RAGService yok | 25 | Servis import fail | Servis var mı kontrol et, yoksa test sil |
| ContentManagementService yok | 24 | Servis import fail | Aynı |
| Fast Learning API yok | 16 | Servis import fail | Aynı |
| BERTurkService yok | 14 | NLP servisi yok | Beklenen skip (external dep) |
| AlertService yok | 9 | Servis import fail | Kontrol et |
| hypothesis yok | 9 | Paket yüklü değil | `pip install hypothesis` veya beklenen skip |
| LearningPathAgent yok | 6 | Agent import fail | Kontrol et |
| YouTubeDiscoveryService yok | 5 | Servis import fail | Kontrol et |
| SecurityManager yok | 5 | Import fail | Kontrol et |
| MultiAgentBlackboard yok | 5 | Import fail | Kontrol et |
| Diğer servis yok | 14 | Çeşitli servisler | Per-file triage |

### P3 — Beklenen / Düşük Öncelik (58 dosya)

| Kategori | Dosya | Root Cause | Çözüm |
|----------|-------|-----------|-------|
| Elasticsearch bağlantısı | 6 | External servis yok | Beklenen (test ortamı) |
| ChromaDB yok | 4 | External servis yok | Beklenen |
| NumPy yok | 4 | Paket eksik | `pip install numpy` |
| FSRSService DB dep | 5 | DB gerekli | Integration test |
| API format değişti | 20 | Eski test, yeni API | Test güncelle veya sil |
| Servis refactor edildi | 6 | DB session pattern değişti | Test güncelle |
| simple_agents removed | 3 | Modül silindi | Test sil |
| Diğer | 10 | Çeşitli | Per-file triage |

## Sonraki Adımlar

### Quick Wins (1-2 saat)
1. **httpx migration** (15 dosya): `AsyncClient(app=app)` → `ASGITransport(app=app)` toplu replace
2. **Import path fix** (17 dosya): Model import hataları — path güncelle
3. **hypothesis install**: `pip install hypothesis` ile 9 test açılır

### Medium Effort (yarım gün)
4. **Heavy imports** (33 dosya): `from main import app` yerine fixture-based lazy import
5. **Servis varlık kontrolü** (50+ dosya): Her servisin hâlâ var olup olmadığını kontrol et, yoksa testleri sil

### Long Term
6. **API format testleri** (20 dosya): Eski test → yeni API format uyumu
7. **Integration test altyapısı**: Redis, Elasticsearch, DB gerektiren testler için test container setup

## Fix/Skip Hedefi

| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| Skip dosya sayısı | 268 | <100 |
| Skip oranı | %42.5 | <%15 |
| Fix/Skip oranı | ~%25 | >%50 |
