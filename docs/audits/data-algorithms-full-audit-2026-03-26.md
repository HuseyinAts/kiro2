# KIRO2 Data & Algorithms Full Audit Report

**Tarih:** 26 Mart 2026
**Commit:** 48a35f5
**Yontem:** 8 paralel subagent ile kapsamli analiz
**Kapsam:** IRT 3PL, FSRS, CAT/Placement, DAG/ZPD, BKT/YKS, pgvector/Embedding, Orchestrator, d-dataset Pipeline

---

## EXECUTIVE SUMMARY

| Katman | Satir | Skor | Kritik Bulgu |
|--------|-------|------|-------------|
| IRT 3PL Engine | 1,900 | 7.8/10 | Numerik karlilik mukemmel, CTT r_pbis hardcoded |
| FSRS Engine | 3,000+ | 7.1/10 | Turk kulturel faktorler unique, user_item_fsrs migration eksik |
| CAT/Placement | 2,500 | 7.5/10 | Redis session solid, FSRS batch update sessiz basarisizlik |
| DAG/ZPD/LP | 3,800+ | 6.8/10 | topic_prerequisites ve user_theta tablolari BOS |
| BKT/YKS Estimator | 2,900+ | 7.4/10 | 4-algoritma pipeline calisiyor, BKT DB modeli FAZ-2 |
| pgvector/Embedding | 768d, HNSW | 7.5/10 | nomic-embed-text 21ms, index 290MB, batch upsert eksik |
| Orchestrator | 16,864 | 6.5/10 | %60 placeholder/TODO, tool executor bos |
| d-dataset Pipeline | 77,336 soru | 8.6/10 | %100 valid, 13-check validation, Bayesian scoring |

**Genel Skor: 7.3/10 — Algoritma pipeline production-ready, DB integration ve orchestrator eksik**

---

## P0 CRITICAL FINDINGS (Hemen cozulmeli)

### 1. topic_prerequisites ve user_theta Tablolari BOS (DAG/ZPD)
- DAG built-in fallback'e dusuyor (DB'den yuklemiyor)
- user_theta bos → tum ogrenciler CAT ihtiyaci gosteriyor
- ZPD band hesaplamasi default theta=0.0 ile calisiyor
- **Fix:** Migration yaz, CAT sonucu theta persistence implement et

### 2. FSRS Batch Update Sessiz Basarisizlik (CAT)
- CAT → FSRS → Daily Plan zinciri kopuyor
- Exception sadece warning log, kullanici bilgilendirilmiyor
- **Fix:** FSRS batch failure → state recovery + notification

### 3. user_item_fsrs Migration Eksik (FSRS)
- 4 SQL sorgusu hardcoded, migration dosyasinda tanimlanmamis
- Schema degisimi runtime error verir
- **Fix:** Alembic migration yaz, SQLAlchemy model ekle

### 4. Orchestrator %60 Placeholder (Orchestrator)
- _implement_node(), _fix_node() TODO
- tool_executor bos, LLM gateway incomplete
- 37/45 policy validator placeholder ("passed=True")
- **Fix:** Core execution engine'leri implement et

### 5. FSRS Interval Bounds Clamp Yok (FSRS)
- max_interval 36,500 gun (100 yil) hardcoded, check yok
- Cok stabil kart sonsuz interval alabilir
- **Fix:** `max(1, min(round(interval), 365))` clamp ekle

---

## P1 HIGH PRIORITY (Sprint'e alinmali)

### 6. IRT Kalibrasyon Dongusu Pasif (IRT)
- Celery beat scheduled (Pazar 03:00) ama veri yok
- Bootstrap 64K soru parametreleri yazilmis
- **Fix:** Yeni ogrenci verileriyle EM kalibrasyon aktiflesl

### 7. CAT Warm-up Pool Filtre Sorunu (CAT)
- Kalibrasyon pool'u ortaya yakin sorulara oncelik veriyor
- Warm-up sorulari "kolay" olmayabilir
- **Fix:** is_calib_pool AND irt_difficulty < -0.5

### 8. BKT DB Modeli FAZ-2 Bekleme (BKT)
- BKTState.gamification modeli olusturulmadi
- record_answer() pipeline calisiyor ama persist eksik
- **Fix:** FAZ-2 timeline'i uygula

### 9. YKS Puan Tahmini +-20 Puan Hata (YKS)
- Log-normal model kaba, OSYM gercek algoritma kapali kutu
- PUAN_DAGILIM hardcoded sabitler (2019-2024)
- **Fix:** Kernel density estimate veya user feedback

### 10. FSRS-IRT Rating Heuristic Agresif (FSRS)
- 5s→EASY, 30s→HARD — YKS'de %95 GOOD kategorisi
- W[15]/W[16] hard/easy bonus nadiren tetiklenir
- **Fix:** Cohort-based threshold calibration

### 11. Desired Retention Hardcoded 0.90 (FSRS)
- get_optimal_retention_rate() tanimli ama HICBIR YERDE cagrilmiyor
- YKS ogrencileri %95+ retention istiyor
- **Fix:** fsrs_update() → get_optimal_retention_rate() entegre et

### 12. Review Router Hardcoded (Orchestrator)
- _review_router() daima "complete" donuyor, review feedback yok
- **Fix:** Review feedback'e gore "fix" return et

---

## P2 MEDIUM PRIORITY (Sonraki sprint)

### 13. CTT Fallback r_pbis Hardcoded 0.5 (IRT)
- Single-item r_pbis daima 1.0 → fix olarak 0.5
- a parametresi cok konservatif

### 14. Item Exposure Redis'e Tasinmali (IRT)
- Python dict (session basinda reset)
- Adil soru dagilimi icin Redis counter

### 15. Lapse Recovery Leech Detection (FSRS)
- 20+ kez yanlis → forever DURUM_YENIDEN dongusu
- Anki: 10+ lapse → leech flag

### 16. FSRS v6 Service Duplicate (FSRS)
- fsrs_v6_service.py (98 satir) UNUSED
- fsrs_engine.py aktif
- **Fix:** Deprecated'a tasi veya sil

### 17. Placement Session DB Persistence (CAT)
- Placement sonuclari DB'ye yazilmiyor
- Sadece CAT'te kiro2_cat_sessions tablosuna yaziliyor

### 18. theta Cache TTL Tutarsizlik (CAT)
- CAT session TTL 1h, theta cache 5dk
- Frontend 10dk bekleyip retry → theta kaybedilir

---

## ALGORITMA PIPELINE

### record_answer() Akisi (4-Algoritma Entegrasyon)

```
Giris: student_id, topic_id, subject_slug, correct, rating

1. BKT GUNCELLE
   p_L → Bayesian update → p_L_new → mastery status

2. IRT THETA GUNCELLE
   answered_questions → EAP → theta_after, theta_se
   Fallback: p_L → theta lineer donusum

3. FSRS KARTI GUNCELLE
   DB'den FSRSCard → fsrs_update() → due_date

4. ZPD BELIRLE
   p_L → zone() → scaffold_level, hints, difficulty

Cikis: new_p_L, theta, se, fsrs_next_review, zpd_zone
```

### Pipeline: Placement → CAT → IRT EAP → ZPD → FSRS → DAG → LP → YKS

| Adim | Algoritma | Input | Output |
|------|-----------|-------|--------|
| 1 | Placement | Lise turu, 12 soru | theta_0, se_0 |
| 2 | CAT | theta, soru havuzu | theta, se (SE<0.35) |
| 3 | IRT EAP | responses | theta_hat, se |
| 4 | ZPD | theta, se | optimal difficulty band |
| 5 | FSRS | rating, state | due_date, stability |
| 6 | DAG | mastery scores | unlocked topics |
| 7 | LP | theta, mastery, DAG | daily plan |
| 8 | YKS | theta, ders netleri | puan tahmini |

---

## KATMAN DETAY

### 1. IRT 3PL Engine (7.8/10)

| Parametre | Aralik | Durum |
|-----------|--------|-------|
| a (discrimination) | [0.30, 3.00] | np.clip |
| b (difficulty) | [-4.0, 4.0] | Gauss-Hermite |
| c (guessing) | [0.05, 0.40] | L-BFGS-B bounds |
| theta | [-4.0, 4.0] | EAP 201 grid |
| SE threshold | 0.35 | CAT stop |

- 3 katmanli numerik koruma (clipping, log-space, underflow fallback)
- EM + CTT fallback (200+ yanit → EM, 50-199 → CTT)
- Fisher Information: CAT MFI soru secimi
- Test coverage: ICC, EM, recovery, boundary testleri

### 2. FSRS Engine (7.1/10)

| Parametre | Deger | Aciklama |
|-----------|-------|----------|
| W array | 21 element | FSRS v6 (Ye et al., 2024) |
| Stability | 1.0-30+ gun | Hafiza omru |
| Difficulty | 1-10 | Madde zorluk |
| DECAY | -0.5 | Bozunma katsayisi |
| FACTOR | 0.8122 | Stabilite carpani |
| Target R | 0.90 | Hedef retention |

- Turk kulturel faktorler: Ramazan (0.75), sinav stresi (1.35), yaz tatili (0.60)
- 4 state: NEW→LEARNING→REVIEW↔RELEARNING
- 44 unit test, 13 scheduling test, 18 service test
- CAT+FSRS combined_priority_score (0.60 FSRS + 0.40 IRT)

### 3. CAT/Placement (7.5/10)

| Parametre | CAT | Placement |
|-----------|-----|-----------|
| Max items | 20 | 12 |
| SE stop | 0.35 | 0.38 |
| Epsilon | 0.20 | - |
| Max exposure | 0.30 | - |
| ZPD range | [0.40, 0.85] | - |
| Bisection | - | [-4.0, 4.0] |

- Redis session management (~1ms HGETALL)
- Epsilon-greedy MFI (%80 exploitation, %20 exploration)
- Okul turu prior: Fen N(+0.5, 0.9), Meslek N(-0.5, 1.0)
- Auth + ownership verification

### 4. DAG/ZPD/Learning Path (6.8/10)

| Parametre | Deger |
|-----------|-------|
| Node sayisi | ~60 |
| Edge sayisi | ~55 |
| HARD mastery | 0.70 |
| SOFT mastery | 0.40 |
| ZPD band | [theta-0.5, theta+1.0] |
| Cache TTL | 6h (DAG), 5dk (mastery) |

- Kahn O(V+E) topolojik sort + dongu tespiti
- Asimetrik ZPD (Vygotsky: 1:2 asagi:yukari)
- 3-faz daily plan: FSRS review → CAT → Practice
- Production readiness: 4/10 (DB tablolari bos)

### 5. BKT/YKS Estimator (7.4/10)

**BKT 4-Parametre:**
| Param | STEM | Sozel |
|-------|------|-------|
| P(L0) | 0.0 | 0.0 |
| P(T) | 0.10 | 0.05 |
| P(G) | 0.20 | 0.20 |
| P(S) | 0.10 | 0.15 |
| Mastery | 0.80 | 0.85 |

**YKS Puan:**
- OSYM 2024 formulleri (TYT/AYT/SAY/EA/SOZ/DIL)
- Log-normal siralama modeli
- 2,500,000 aday (TYT), 700,000 (SAY)

### 6. Orchestrator (6.5/10)

| Metrik | Deger |
|--------|-------|
| Modul sayisi | 24 |
| Agent sayisi | 7 |
| Policy sayisi | 45 |
| Test sayisi | 71+ |
| Implementation | %40 (60% TODO) |

- LangGraph >=0.2.0, StateGraph + conditional edges
- 18 task type + risk-level matrix
- Tool allowlist/blocklist (guvenlik)
- Quality gates: Lint → TypeCheck → UnitTest → Integration → Security

### 7. pgvector/Embedding (7.5/10)

| Metrik | Deger |
|--------|-------|
| Vector boyut | 768 (nomic-embed-text) |
| Index tipi | HNSW (ivfflat degil) |
| Index boyut | ~290MB |
| Avg query | 21ms |
| Embedding model | nomic-embed-text |
| Prefix | search_document: / search_query: |

- HNSW index: ef_construction=200, m=16
- Cosine similarity (1 - distance)
- Semantic search: soru benzerlik, konu eslestirme
- Batch upsert eksik (tek tek INSERT)
- Re-embedding pipeline yok (model degisiminde)
- Connection pool: pgvector extension async uyumlu

### 8. d-dataset Pipeline (8.6/10)

| Metrik | Deger |
|--------|-------|
| Production soru | 77,336 |
| Quality score (avg) | 99.01 |
| Validation | 100% PASS |
| Kitap sayisi | 405 |
| Image coverage | 75.7% (58,523) |
| Answer sources | 9+ farkli |

- 13-check validation (validate_sample.py)
- Bayesian posterior scoring (cross_validate_answers.py)
- Deterministic UUID (idempotent import)
- v2.0 → v3.5+ version history (17 backup)

---

## AKSIYON PLANI

### IMMEDIATE (Bu hafta)
1. [ ] topic_prerequisites + user_theta migration
2. [ ] FSRS batch update error handling
3. [ ] user_item_fsrs Alembic migration
4. [ ] Interval bounds clamp fix

### SPRINT 1 (2 hafta)
5. [ ] CAT → theta DB persistence
6. [ ] Warm-up pool filtre fix
7. [ ] FSRS desired_retention entegrasyon
8. [ ] fsrs_v6_service.py deprecated'a tasi
9. [ ] Placement session DB persistence
10. [ ] IRT exposure rate Redis'e tasi

### SPRINT 2 (4 hafta)
11. [ ] Orchestrator core implement (tool executor, LLM gateway)
12. [ ] BKT DB modeli (FAZ-2)
13. [ ] YKS puan modeli iyilestirme
14. [ ] FSRS fine-tuning (YKS dataset)
15. [ ] Test coverage artirma

---

## GUCLU YONLER

1. **IRT 3PL numerik karlilik** — 3 katmanli koruma, log-space, underflow guard
2. **FSRS Turk kulturel faktorler** — Ramazan, sinav stresi, aile baskisi (sektorde unique)
3. **4-algoritma pipeline** — BKT→IRT→FSRS→ZPD entegre, error isolation
4. **CAT epsilon-greedy MFI** — %80 exploitation + %20 exploration + exposure control
5. **Placement bisection** — 8-12 soruda theta~+-0.5, okul turu prior
6. **d-dataset %100 valid** — 77,336 soru, 13-check, Bayesian scoring
7. **DAG Kahn topo sort** — O(V+E), dongu tespiti, mastery-based bloklama
8. **Orchestrator mimari** — 45 policy, 7 agent, LangGraph conditional routing
9. **Combined priority score** — FSRS urgency (0.60) + IRT information (0.40)
10. **Deterministic UUID** — uuid5 idempotent import, ON CONFLICT pattern

---

**Rapor Sonu**
**Analiz suresi:** ~8 dakika (8 paralel agent)
**Taranan dosya:** ~100+ algoritma ve veri dosyasi
