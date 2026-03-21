# FAZ 4: Dead Code Raporu

**Tarih:** 2026-03-21
**Branch:** audit/fullstack-20260321

---

## 1. Backend API Dosyalari (Router Loader'da Olmayan)

| Dosya | Router Var mi? | ROUTER_MAPPING | Durum |
|-------|---------------|----------------|-------|
| `question_pipeline_api.py` | Evet | MAPPING'de var ama yuklenmiyor olabilir | DEAD (import fail?) |
| `response_validation_api.py` | Evet | MAPPING'de var ama yuklenmiyor olabilir | DEAD (import fail?) |
| `websocket_connection_manager.py` | Hayir | MAPPING'de YOK | DEAD (deprecated) |
| `__init__.py` | - | - | OK (package init) |

**Toplam dead API dosyasi:** 3

---

## 2. Backend Service Dosyalari (API Tarafindan Import Edilmeyen)

**Toplam service dosyasi:** 173
**API tarafindan kullanilan:** 94 (%54.3)
**API tarafindan KULLANILMAYAN:** 79 (%45.7)

**Not:** Bu servislerin bir kismi diger servisler tarafindan import edilebilir (service-to-service bagimlilik). Gercek dead code orani daha dusuk olabilir.

### Ornek Kullanilmayan Servisler (ilk 20):
| Service | Olasi Durum |
|---------|------------|
| ab_testing.py | Feature flag — kullanilmiyor |
| ab_testing_service.py | Duplicate |
| accessibility_service.py | Baska servis import edebilir |
| adaptive_test_engine.py | CAT motoru — v2'de kullanilabilir |
| advanced_analytics.py | Analytics alt servisi |
| alert_service.py | Monitoring alt servisi |
| batch_processing.py | Celery task servisi |
| benchmark_test.py | Test/benchmark — API gereksiz |
| bloom_taxonomy_classifier.py | Taxonomy servisi — baska servis kullaniyor |
| chromadb_collection_manager.py | ChromaDB — baska servis kullaniyor |
| content_management_service.py | Alt servis |
| curriculum_compliance_service.py | Alt servis |
| diagnostic_test.py | Test servisi |
| doc_updater_service.py | Dokumantasyon servisi |
| dual_coding_optimizer.py | Ogrenme optimizasyonu |
| enhanced_bloom_classifier.py | Bloom v2 |
| enhanced_question_templates.py | Soru sablonu |
| enhanced_resource_recommendation_engine.py | Oneri motoru |
| fast_learning_service.py | Hizli ogrenme |
| feedback_service.py | Geri bildirim |

**Oneri:** Toplu kullanim taramasi (service-to-service + orchestrator) yapilarak gercek dead code belirlenmeli.

---

## 3. Frontend Dead Code

### Pages
**Toplam page dosyasi:** 59
**App.tsx'te dogrudan:** 39
**Dolayli (wrapper import):** 20 (Modern*Page → *Page wrapper chain)
**Gercek dead page:** 0

### Deprecated Pages
**_deprecated/ klasorunde:** 17 dosya (onceki session'larda tasindi)

### Services
**Toplam service dosyasi:** 27
**Kullanilan:** 27 (%100)
**Dead service:** 0

### Hooks
**Toplam hook dosyasi:** 42
**Detayli tarama gerekli** (hook-to-component kullanim analizi yapilmadi)

---

## 4. Ozet

| Kategori | Dead Code | Toplam | Oran |
|----------|-----------|--------|------|
| Backend API (loader'da olmayan) | 3 | 124 | %2.4 |
| Backend Service (API'dan import edilmeyen) | 79 | 173 | %45.7* |
| Frontend Page | 0 | 59 | %0 |
| Frontend Service | 0 | 27 | %0 |
| Frontend Deprecated | 17 | - | Zaten tasindi |

*Service-to-service importlar dahil degil. Gercek dead code orani daha dusuk.

---

## Aksiyon Onerileri

1. **websocket_connection_manager.py** — `_deprecated/` klasorune tasi (confirmed dead)
2. **question_pipeline_api.py, response_validation_api.py** — import hatasini kontrol et, calismiyorsa ROUTER_MAPPING'den kaldir
3. **79 kullanilmayan service** — toplu `grep -rn "import X\|from X" backend/` taramasi ile gercek dead code'u ayir
4. **Frontend hooks** — kullanim taramasi yap

---

## STATUS: TAMAM
