# Data & Algorithms Deep Audit Report

**Tarih:** 2026-03-28
**Concern'ler:** Orchestrator (LangGraph), Algorithms (IRT/FSRS/BKT/ZPD), d-dataset Pipeline, Embedding+Vector+NLP
**Agent sayisi:** 4 (paralel)
**Toplam bulgu:** 15 P0, 23 P1, 36 P2 = **74 bulgu**

---

## P0 — Hemen Fix (15 bulgu)

### Orchestrator (3)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| O1 | graph.py:159+282 | LoopGuardrail TANIMLI ama graph'a BAGLANMAMIS — sonsuz dongu riski | `guardrail.check(state)` quality_check node'a ekle |
| O2 | graph.py:109 | `MemorySaver()` import fail durumunda None — `None()` TypeError | `MemorySaver() if MemorySaver else None` guard |
| O3 | graph.py:283-285 | "blocked" status quality_check'e geciyor, tum gate'ler bosuna calisir | Early-return: `if state["status"] == "blocked": return state` |

### Algorithms — IRT/FSRS/BKT/ZPD (4)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| AL1 | fsrs_service.py:246-269 | FSRS batch review race condition — `SELECT FOR UPDATE` yok, concurrent write kayip | `FOR UPDATE` ekle veya Redis lock |
| AL2 | cat_session.py:408-562 | submit_answer'da duplicate question_id kontrolu yok — replay saldirisi | `if question_id in answered_ids: raise` |
| AL3 | algorithms/irt_model.py:22 | Broken import `from core.irt_validators` — ModuleNotFoundError | Dead code — `_archived/` dizinine tasi |
| AL4 | fsrs_engine.py:302 | FSRS YENIDEN state'te stability guncelleme eski `state.stability` kullanir | `new.stability` kullan |

### d-dataset Pipeline (3)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| DD1 | eslesmis_sorucevap.jsonl | 74 farkli field semasi — canonical schema ENFORCE edilmiyor | Schema normalization pass ekle |
| DD2 | eslesmis_sorucevap.jsonl:29567,53238,63220 | 3 kayit answer not in options — seceneklerde olmayan cevap | Sil veya duzelt, hard reject rule |
| DD3 | eslesmis_sorucevap.jsonl | 919 kayit UPPERCASE confidence_level (LOW/HIGH) — validation bypass | `.lower()` normalize ekle |

### Embedding + Vector + NLP (5)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| E1 | alembic/004:181-184 | HNSW index YANLIS tabloda (`question_embeddings`) — production `question_bank.embedding`'de seqscan | `question_bank(embedding)` uzerinde index olustur |
| E2 | models/question_bank.py | `embedding` kolonu SQLAlchemy model'de YOK — autogenerate kolonu silebilir | `embedding = mapped_column(Vector(768), nullable=True)` ekle |
| E3 | agents/question_classifier.py:204,249 | Embedding oncesi NFC normalization yok — ayni metin farkli vector | `unicodedata.normalize("NFC", ...)` ekle |
| E4 | agents/question_classifier.py:227 | Turkish `.lower()` — "I"→"i" (yanlis), "I"→"ı" olmali | Turkish-safe lowercase |
| E5 | agents/question_classifier.py:158 | Model mismatch — `MiniLM-L12-v2` (384d) vs production `nomic-embed-text` (768d) | Ayni model kullan veya dokumante et |

---

## P1 — Sprint Icinde Fix (23 bulgu)

### Orchestrator (5)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| O4 | routing.py:362-396 | 8 specialist agent routing'de tanimli ama factory'de YOK | Fallback mapping veya implement |
| O5 | llm_gateway.py:325 | Cost limit asilinca RuntimeError — ucuz model'e fallback yok | Sonnet→haiku fallback |
| O6 | policy_engine.py:487-535 | Policy routing_rules, routing.py agent isimleriyle UYUMSUZ | Sync et |
| O7 | graph.py:349-352 | Review router DAIMA "complete" donuyor — review asla fix tetiklemiyor | Review logic implement et |
| O8 | self_improvement.py:326 | Self-improvement engine graph'a BAGLANMAMIS | Wire et veya import kaldir |

### Algorithms (8)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| AL5 | irt_engine.py:75-84 | IRT a/b/c parametre validation YOK — a<0, c>1 kabul ediliyor | `__post_init__` clamp ekle |
| AL6 | irt_engine.py:231-237 | ZPD filtresi [0.40,0.85] — CLAUDE.md [0.15,0.85] diyor, tutarsiz | Senkronize et |
| AL7 | turkish_optimized_fsrs.py:429 | FSRS retrievability exponential decay — production power-law, uyumsuz | Dead code — arsivle |
| AL8 | algorithms/ (4 dosya) | Dual FSRS implementasyonu — farkli formuller, farkli parametre sayilari | `_archived/` dizinine tasi |
| AL9 | turkish_zpd_maarif_system.py:398 | ZPD hesaplama `current_level*0.3` — theta=0 icin ZPD=0 (paradoks) | Minimum floor ekle veya arsivle |
| AL10 | cat_session.py:455-475 | DB'den cekilemeyen soruya default a=1,b=0,c=0.25 — theta saptirir | Warning log + EAP'den cikar |
| AL11 | irt_engine.py | ItemParams constructor'da parametre validation yok | `__post_init__` ekle |
| AL12 | placement_service.py:430 | Placement sonucu SADECE Redis'te (TTL 300s) — DB'ye persist edilmiyor | `user_theta` tablosuna UPSERT |

### d-dataset Pipeline (4)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| DD4 | import_d_dataset.py:211 | quality_score=None → 0.0 coercion — unscored vs bad ayirt edilemez | Sentinel deger (-1) veya bool kolon |
| DD5 | validate_sample.py:515-526 | 111MB JSONL full memory load (~1.2GB RAM) | Streaming/generator pattern |
| DD6 | backups/ | v3.5 backup YOK — en son v3.4 (76,527) mevcut | Hemen backup olustur |
| DD7 | validate_sample.py:42 | PASS_THRESHOLD 95% — CLAUDE.md "100% PASS" diyor | 1.0 yap veya CRITICAL_THRESHOLD=0 ekle |

### Embedding + Vector + NLP (6)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| E6 | question_crud_api.py:931 + photo_ask_service.py:135 | Embedding dimension validation yok — 768 != gelen boyut kontrolu | `len(embedding) != 768` check |
| E7 | (yok) | Soru text guncellendikten sonra embedding re-generate edilmiyor — stale vector | Update'te `embedding = NULL` set et |
| E8 | (yok) | Query embedding cache yok — ayni sorgu her seferinde Ollama'ya gidiyor | Redis cache + TTL |
| E9 | question_classifier.py:186-191 | Model yuklenemezse sessiz fallback — health check'te gorunmuyor | Health sub-check ekle |
| E10 | turkish_bionic_reading.py:104 | Zemberep `.lower()` Turkish-safe degil | Turkish lowercase |
| E11 | generate_embeddings.py:144 | Text 2000 char'a truncate — uzun sorularda kalite kaybi | Log + limit review |

---

## P2 — Teknik Borc (36 bulgu)

### Orchestrator (12)

| # | Dosya | Aciklama |
|---|-------|----------|
| O9 | metrics_collector.py:345-348 | `field()` non-dataclass'ta — calismiyor |
| O10 | routing.py:503-507 | Qwen endpoint hardcoded `localhost:8080` |
| O11 | llm_gateway.py:76 + cost_tracker.py:30 | Duplicate pricing table — farki format |
| O12 | cost_tracker.py + graph.py | CostTracker mevcut ama graph'a BAGLANMAMIS |
| O13 | graph.py:168-290 | State dict in-place mutation — parallel node eklenirse race condition |
| O14 | resource_manager.py:296 | `_monitoring_loop` metodu TANIMLANMAMIS — AttributeError |
| O15 | resource_manager.py:320-326 | `_trigger_callback` TANIMLANMAMIS |
| O16 | graph.py:170,214 | iteration implement+fix'te 2x arttirilir — efektif 5 dongu (10/2) |
| O17 | llm_gateway.py:289-320 | DEFAULT_CONFIGS'te codex-cli ve qwen EKSIK |
| O18 | agents.py:277-292 | JSON parse error → success=True (DocumentWriter) |
| O19 | llm_gateway.py:121-125 | API key missing → opaque runtime error (validate() cagrilmiyor) |
| O20 | learning_loop.py:501-568 | LinUCBBandit numpy yoksa AttributeError |

### Algorithms (8)

| # | Dosya | Aciklama |
|---|-------|----------|
| AL13 | irt_calibrator.py:209 | EM E-step'te gereksiz r_k hesaplama (uzerine yazilir) |
| AL14 | algorithms/ (4 dosya) | Dead code — irt_model, turkish_optimized_fsrs, zpd_maarif, irt_morfoloji |
| AL15 | irt_engine.py + fsrs_engine.py | Production algoritmalar icin birim test EKSIK |
| AL16 | irt_engine.py:156 | EAP norm_factor underflow threshold 1e-300 (cok dusuk) |
| AL17 | fsrs_engine.py:306-307 | YENIDEN state puan<IYI durumunda stability GUNCELLENMEZ |
| AL18 | cat_session.py:630-650 | Learning events INSERT'te ON CONFLICT yok — duplicate risk |
| AL19 | yks_estimator.py:289-298 | AYT puan formulu basitlestirilmis — ±50 puan sapma |
| AL20 | algorithms/irt_model.py:189 | YKS predicted score naif lineer: `300 + theta*66.67` |

### d-dataset Pipeline (7)

| # | Dosya | Aciklama |
|---|-------|----------|
| DD8 | pipeline.py:152-158 | 7 hardcoded Windows path |
| DD9 | cross_validate_answers.py:763 | Output overwrite without backup |
| DD10 | cross_validate_answers.py:168-186 | Duplicate key: last wins silently |
| DD11 | import_d_dataset.py:292 | `ON CONFLICT DO NOTHING` — guncelleme yansimaz |
| DD12 | import_d_dataset.py:338 | 77K row full memory load |
| DD13 | scripts/ (98 dosya) | Cogu stale — archive yok |
| DD14 | eslesmis_sorucevap.jsonl | 2,348 low confidence kayit production'da |

### Embedding + Vector + NLP (9)

| # | Dosya | Aciklama |
|---|-------|----------|
| E12 | 004:185 | HNSW ef_search set edilmemis (default 40) |
| E13 | question_crud_api.py:951 + photo_ask_service.py:148 | f-string SQL — fragile pattern |
| E14 | question_crud_api.py:959 | Triple CAST(:emb AS vector) — CTE kullan |
| E15 | reasoning_models.py:355 | `problem_embedding` ARRAY(Float), Vector degil |
| E16 | generate_embeddings.py:157-164 | String-based vector serialization — native binding kullan |
| E17 | photo_ask_service.py:27 | Hardcoded Ollama URL — merkezi config yok |
| E18 | question_classifier.py:186 | Model auto-download — Docker read-only FS'de fail |
| E19 | (yok) | Embedding coverage monitoring yok — NULL% bilinmiyor |
| E20 | generate_embeddings.py:42-60 | Ollama API retry logic yok |

---

## Konsensus (2+ agent hemfikir)

| Konu | Agent'lar | Guvenilirlik |
|------|-----------|-------------|
| **Dead code backend/algorithms/** | Algorithms + Orchestrator | YUKSEK — 4 dosya production'da kullanilmiyor |
| **Turkish .lower() bozuklugu** | Embedding + Algorithms | YUKSEK — question_classifier, bionic_reading |
| **FSRS dual implementation** | Algorithms + Embedding | YUKSEK — fsrs_engine.py (production) vs turkish_optimized_fsrs.py (dead) |
| **NFC normalization eksik** | Embedding + d-dataset (pozitif) | ORTA — classifier'da eksik, pipeline'da OK |
| **Placement/CAT data persist** | Algorithms (placement Redis-only) + Orchestrator (graph state) | ORTA — session verisi kaybolabilir |
| **Parameter bounds validation** | Algorithms (IRT) + Embedding (dimension) | ORTA — hem IRT hem embedding tarafinda eksik |

---

## Oncelikli Aksiyon Plani

### Faz 1 — Acil (Bu hafta)
1. **HNSW index question_bank'a** (E1): 77K row seqscan → ~21ms HNSW
2. **FSRS race condition fix** (AL1): `SELECT FOR UPDATE` veya distributed lock
3. **CAT replay guard** (AL2): duplicate question_id reject
4. **3 bozuk cevap sil** (DD2): answer not in options
5. **LoopGuardrail wire** (O1): sonsuz dongu onleme

### Faz 2 — Sprint (Bu ay)
6. **embedding kolonu model'e ekle** (E2): autogenerate DROP onleme
7. **Placement DB persist** (AL12): Redis TTL sonrasi veri kaybi
8. **ZPD aralik senkronize** (AL6): [0.40,0.85] vs [0.15,0.85]
9. **confidence_level normalize** (DD3): 919 kayit validation bypass
10. **v3.5 backup olustur** (DD6): disaster recovery
11. **Quality gate 95%→100%** (DD7): CLAUDE.md ile tutarli

### Faz 3 — Teknik Borc (Sonraki sprint)
12. **Dead code arsivle** (AL14): algorithms/ 4 dosya
13. **8 specialist agent implement/map** (O4): routing dead-end
14. **Schema normalization** (DD1): 74 farkli schema → canonical
15. **Embedding cache** (E8): Redis TTL ile sorgu cache
16. **Production algoritma testleri** (AL15): irt_engine + fsrs_engine unit test

---

## Metrikler

| Kategori | P0 | P1 | P2 | Toplam |
|----------|----|----|----|----|
| Orchestrator (LangGraph) | 3 | 5 | 12 | 20 |
| Algorithms (IRT/FSRS/BKT/ZPD) | 4 | 8 | 8 | 20 |
| d-dataset Pipeline | 3 | 4 | 7 | 14 |
| Embedding + Vector + NLP | 5 | 6 | 9 | 20 |
| **TOPLAM** | **15** | **23** | **36** | **74** |

---

## Pozitif Bulgular

- d-dataset NFC normalization %100 temiz
- Import script idempotent (deterministic UUID + ON CONFLICT)
- UTF-8 encoding tutarli
- Bayesian cross-validation iyi kalibre edilmis
- generate_embeddings.py prefix kullanimi dogru (`search_document:`)
- question_crud_api.py NFC + prefix kullanimi dogru
- fsrs_engine.py FSRS v6 power-law decay dogru implement edilmis
- IRT 3PL formulu matematiksel olarak dogru
- EAP theta estimation quadrature ile implement — yakinsama garanti

---

*Audit by: 4 parallel agents (Claude Opus 4.6)*
*Rapor: docs/audits/2026-03-28_data_algorithms_deep_audit.md*
