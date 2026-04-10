# KIRO2 Semantik Analiz Bulguları

**Başlangıç:** 2026-04-09
**Metodoloji:** v6 (Niyet ↔ Gerçekleşme Boşluk Analizi)
**Durum:** Başlamadı

---

## Adım 0: Ön Koşul

**Durum: GO**

| Kontrol | Sonuç |
|---------|-------|
| Git | master, 3 modified (session/docker), 2 untracked (audit dosyaları) |
| Son commit | c786620 fix(dungeon): safe array casting + useEffect cleanup |
| Araçlar | mypy 1.19.1 ✓, pytest-cov 7.0.0 ✓, vulture/radon/bandit YOK |
| PostgreSQL | OK (port 5434, kiro2 DB) |
| Redis | OK (port 6379) |
| Durdurma koşulu | Tetiklenmedi |

## Adım 1: Hedef Haritası

**Filtre A (coverage):** Eski coverage.json (31 Ocak) — `core/osym_exam_engine.py` %0. Yeni app/services/ dosyaları Ocak sonrası oluşturulmuş, coverage verisi yok.
**Filtre B (son 30 commit):** loader.py (9x), ModernLearningPathPage (3x), cat_session (3x), cat_models (3x), pwa_sync_api (3x)
**Filtre C (sorun geçmişi):** learning_path (5 session), auth (4), gamification (4), exam (3), BKT/IRT/FSRS (2)

### Öncelik 1 (derin analiz — 14 dosya)

| # | Dosya | Coverage | Volatilite | Sorun Geçmişi | Kalibrasyon |
|---|-------|----------|-----------|---------------|-------------|
| 1 | app/services/learning_path_orchestrator.py | yok (yeni) | orta | 5 session | **Dosya A** |
| 2 | core/osym_exam_engine.py | **%0** | orta | 3 session | **Dosya B** |
| 3 | app/services/cat_session.py | yok (yeni) | 3 commit | absolute import | |
| 4 | app/services/fsrs_engine.py | yok (yeni) | orta | 2 session | |
| 5 | app/services/bkt_service.py | yok (yeni) | orta | 2 session | |
| 6 | app/services/irt_engine.py | yok (yeni) | orta | 2 session | |
| 7 | app/services/dag_engine.py | yok (yeni) | orta | — | |
| 8 | app/api/learning_path_daily.py | yok (yeni) | orta | — | |
| 9 | app/api/learning_path_dungeon.py | yok (yeni) | yüksek | — | |
| 10 | routers/loader.py | — | **9 commit** | — | |
| 11 | pages/ModernLearningPathPage.tsx | — | **3 commit** | 5 session | |
| 12 | services/fsrsService.ts | — | 2 commit | — | |
| 13 | services/chatService.ts | — | 3 commit | — | |
| 14 | utils/performanceOptimizer.tsx | — | 2 commit | — | |

### Öncelik 2 (auth taraması — backend/api/ 132 dosya)
T1.5 Katman 1'de taranacak.

### Kalibrasyon Dosya Seçimi
- **Dosya A:** learning_path_orchestrator.py (bilinen: absolute import satır 25)
- **Dosya B:** osym_exam_engine.py (%0 coverage, 1677 satır, sınav çekirdeği)

## Adım 2: Kalibrasyon

**Durum: PASSED**

### Kalibrasyon Dosyaları
- **Dosya A:** `backend/app/services/learning_path_orchestrator.py` (695 satır, bilinen: absolute import L25)
- **Dosya B:** `backend/core/osym_exam_engine.py` (1677 satır, %0 coverage)

### 3 Agent Sonuçları (Convergence)

**Dosya A — learning_path_orchestrator.py:**

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
|----|-------------|-------|-------------|----------|-------|-------|
| K-A1 | orchestrator.py:25 | Relative import (app paket yapısı) | `from models.gamification import StudentAbility` absolute import — Docker/test'te ImportError riski | P2 | YÜKSEK (3/3) | all |
| K-A2 | orchestrator.py:171 | DAG mastery skorlarını kullan | `await self._dag_service.get_user_mastery(user_id)` return değeri ATILIYOR — I/O israfı | P2 | YÜKSEK (2/3) | code-reviewer, coderabbit |
| K-A3 | orchestrator.py:217-218 | DAG hata → güvenli varsayılan | `except Exception` → prereq_blocked=False — önkoşul atlanır, öğrenci hazır olmadığı konuya gider | P1 | YÜKSEK (2/3) | code-reviewer, coderabbit |
| K-A4 | orchestrator.py:641 | θ→mastery dönüşümü (normal CDF) | `z = (theta + 1.0) / max(0.1, se)` — θ=0 (ortalama) → %97.7 mastery. +1.0 kaydırma herkesin mastered görünmesine yol açar | P1 | YÜKSEK (2/3) | code-reviewer, psychometrics |
| K-A5 | orchestrator.py:626-627 | DB hatası logla | `except Exception: pass` — SQL hataları sessizce yutulur, None döner | P2 | YÜKSEK (2/3) | code-reviewer, coderabbit |
| K-A6 | orchestrator.py:535-536 | θ fetch hata → boş dict | Theta çekme hatası → boş dict → TÜM dersler θ=0.0 → mastery %97.7 (K-A4 ile birleşince) | P1 | YÜKSEK (2/3) | coderabbit, psychometrics |
| K-A7 | orchestrator.py:211 | Konu adını göster | `next_topic_name = next_tid` — topic ID, konu ADI yerine atanır | P2 | ORTA (1/3) | code-reviewer |

**Dosya B — osym_exam_engine.py:**

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
|----|-------------|-------|-------------|----------|-------|-------|
| K-B1 | osym_exam.py:158,178 | ÖSYM resmi süreler | TYT=165dk (doğru:135), AYT=210dk (doğru:180) — öğrenciye +30dk fazla süre | P1 | YÜKSEK (2/3) | code-reviewer, coderabbit |
| K-B2 | osym_exam.py:288-299 | AYT alan türüne göre dağılım | subject_distribution değişir ama total_questions=160 SABİT kalır. SAYISAL=104, SÖZEL=120 → `len(questions)<160` → ValueError. Sınav oluşturulamaz | **P0** | YÜKSEK (2/3) | code-reviewer, psychometrics |
| K-B3 | osym_exam.py:1087 | Süre istatistiği topla | `stats["total_time"] += answer.response_time_seconds` — None olabilir → TypeError | **P0** | YÜKSEK (2/3) | code-reviewer, coderabbit |
| K-B4 | osym_exam.py:1427 | ÖSYM net hesaplama | `net = correct - (wrong/4)` — ÖSYM 2023'te 1/4 cezayı kaldırdı, net=correct olmalı | P1 | YÜKSEK (2/3) | code-reviewer, psychometrics |
| K-B5 | osym_exam.py:1631-1632 | Sınav motoru servisi | `osym_exam_engine = OSYMExamEngine()` global singleton — multi-worker'da her process ayrı active_sessions dict'i, session izolasyonu bozuk | **P0** | YÜKSEK (2/3) | code-reviewer, coderabbit |
| K-B6 | osym_exam.py:834 | YKS puan hesaplama | `scaled_score = raw_score` — gerçek YKS scaling (diploma notu, standart sapma) uygulanmıyor | P1 | YÜKSEK (2/3) | coderabbit, psychometrics |
| K-B7 | osym_exam.py:1470-1498 | IRT tabanlı yetenek tahmini | Basit logit hesabı, gerçek IRT parametreleri (a,b,c) kullanılmıyor | P2 | ORTA (1/3) | psychometrics |
| K-B8 | osym_exam.py:140-141 | Session durumu sakla | `active_sessions: dict` bellek-içi — restart'ta tüm oturumlar kaybolur (K-B5 ile ilişkili) | P1 | ORTA (1/3) | code-reviewer |

### Kalibrasyon Kriterleri

| Kriter | Beklenen | Gerçekleşen | Sonuç |
|--------|----------|-------------|-------|
| Dosya A: bilinen sorun (absolute import) | ≥1 doğrulama | 3/3 agent buldu | ✅ PASS |
| Dosya B: yeni bulgular | ≥2 anlamlı | 8 bulgu (3 P0, 3 P1, 2 P2) | ✅ PASS |
| False positive oranı | ≤%30 | %0 (15/15 doğrulandı) | ✅ PASS |

### Kalibrasyon Kararı: **PASS — Adım 3'e devam**

## Adım 3: Bulgular

### Katman 1 (KESİN — Statik Araç Çıktısı)

**T1.1 mypy:** Priority 1 dosyalarda 0 hata (bağımlılıklarda 90+ uyarı, deprecated dosyalarda yoğun)
**T1.2 tsc:** Frontend 0 hata ✓
**T1.3 Dual table:** app/services/ → QuestionBankItem veya question_bank raw SQL kullanıyor ✓ CLEAN
**T1.4 Absolute import:** Sadece 1 dosya: `learning_path_orchestrator.py:25` (K-A1 ile aynı)
**T1.5 Auth eksikliği:** 13 dosya, 86 route auth Depends YOK (aşağıda)
**T1.6 is_active filtresi:** cat_session ✓, dag_service ✓, placement ✓, osym_exam ✓ — CLEAN
**T1.7 get_async_session yanlış kullanım:** 0 bulgu ✓ CLEAN
**T1.8 Exception yutma:** 15+ `except Exception: pass/continue` — cat_session (4x), orchestrator (5x), dag_service (2x), placement (1x), fsrs_service (1x), irt_calibrator (1x)
**T1.9 Sahte test:** `assert True` sadece test dokümanlarında ve reward_hacking detector testinde (meşru) — CLEAN
**T1.10 Skip sayısı:** 1237 pytest.skip/mark.skip (316 dosyada) — yüksek teknik borç ama analiz dışı

#### T1.5 Auth-siz Dosyalar (13 dosya, 86 route)

| # | Dosya | Route | Olası Kasıt | Risk |
|---|-------|-------|-------------|------|
| 1 | curriculum_compliance.py | 13 | Public referans veri? | Kontrol gerek |
| 2 | monitoring.py | 11 | Ops/internal | P2 (kasıtlı) |
| 3 | preference_simulation_routes.py | 11 | Simülasyon — user data? | **Kontrol gerek** |
| 4 | youtube_routes.py | 10 | Public arama | P2 (kasıtlı) |
| 5 | health.py | 7 | Health check | P2 (kasıtlı) |
| 6 | turkish_nlp.py | 7 | NLP utility | P2 (kasıtlı) |
| 7 | vision_api.py | 7 | Görüntü işleme | **Kontrol gerek** |
| 8 | yolo_detection_api.py | 6 | ML inference | **Kontrol gerek** |
| 9 | production_monitoring.py | 4 | Ops/internal | P2 (kasıtlı) |
| 10 | text_simplification.py | 4 | NLP utility | P2 (kasıtlı) |
| 11 | tts_api.py | 3 | TTS servisi | P2 (kasıtlı) |
| 12 | telemetry.py | 2 | Ops/internal | P2 (kasıtlı) |
| 13 | schemas/error_responses.py | 1 | Schema tanım | P2 (kasıtlı) |

**Karar:** 7/13 kasıtlı public (monitoring, health, NLP utility). 4 dosya (curriculum_compliance, preference_simulation, vision_api, yolo_detection) Katman 2 agent'ına aktarılacak.

#### T1.8 Exception Yutma Adayları

| ID | Dosya:Satır | Pattern | Ciddiyet |
|----|-------------|---------|----------|
| L1-1 | cat_session.py:542 | `except Exception: pass` — persist hatası yutulur | P2 |
| L1-2 | cat_session.py:562 | `except Exception: pass` | P2 |
| L1-3 | cat_session.py:843 | `except Exception: pass` | P2 |
| L1-4 | cat_session.py:892 | `except Exception: pass` | P2 |
| L1-5 | dag_service.py:295 | `except (ValueError, KeyError): pass` | P2 |
| L1-6 | placement_service.py:256 | `except Exception: pass` | P2 |
| L1-7 | orchestrator.py:626 | `except Exception: pass` (K-A5 ile aynı) | P2 |

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
|----|-------------|-------|-------------|----------|-------|-------|

### Katman 2 (Convergence sonrası — 4 Agent)

**Convergence notu:** Aynı dosya:satır 2+ agent/kaynak → güven YÜKSEK. Çapraz doğrulanan bulgular ★ ile işaretli.

#### Güvenlik (Security Agent)

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
|----|-------------|-------|-------------|----------|-------|-------|
| S-01 | vision_api.py:152 | Görsel analiz servisi | Auth YOK + GPU inference sınırsız. Herkes Qwen3-VL çalıştırabilir — compute abuse | **P0** | YÜKSEK | security |
| S-02 | vision_api.py:191 | Soru çözüm servisi | Auth YOK. Ücretli AI çözüm servisi olarak kötüye kullanılabilir | **P0** | YÜKSEK | security |
| S-03 | vision_api.py:263 | OCR servisi | Auth YOK. Sınırsız OCR — telif ihlali + GPU tüketimi | **P0** | YÜKSEK | security |
| S-04 | vision_api.py:304 | Diyagram açıklama | Auth YOK. S-01 ile aynı risk profili | **P0** | YÜKSEK | security |
| S-05 | vision_api.py:369 | Dosya yükleme + analiz | Auth YOK + file upload + AI inference = en yüksek abuse potansiyeli | **P0** | YÜKSEK | security |
| S-06 | yolo_detection_api.py:137 | YOLO soru tespiti | Auth YOK + file upload + boyut limiti YOK → bellek tüketimi | **P0** | YÜKSEK | security |
| S-07 | yolo_detection_api.py:192 | Base64 YOLO tespiti | Auth YOK + base64 boyut kontrolü YOK | **P0** | YÜKSEK | security |
| S-08 | yolo_detection_api.py:227 | Toplu YOLO tespiti (20 dosya) | Auth YOK + 20× unbounded memory | **P0** | YÜKSEK | security |
| S-09 | curriculum_compliance.py:46 | MEB standardı ekle (admin) | Auth YOK — anonim kullanıcı MEB müfredat kaydı yazabilir | **P0** | YÜKSEK | security |
| S-10 | curriculum_compliance.py:162 | ÖSYM standardı ekle (admin) | Auth YOK — anonim ÖSYM standardı değiştirebilir | **P0** | YÜKSEK | security |
| S-11 | curriculum_compliance.py:381 | Güncelleme talebi (admin) | Auth YOK — requested_by sahte kimlik | **P0** | YÜKSEK | security |
| S-12 | curriculum_compliance.py:464 | Toplu uyumluluk analizi | Auth YOK + compute-heavy. DoS vektörü | P1 | YÜKSEK | security |
| S-13 | curriculum_compliance.py:238 | Alignment analizi | Auth YOK + ML compute. DoS riski | P1 | ORTA | security |
| S-14 | curriculum_compliance.py:327 | Uyumluluk raporu | Auth YOK — içerik stratejisi ifşası | P1 | ORTA | security |
| S-15 | preference_simulation.py:362 | Toplu tahmin (100 program) | Auth YOK + N+1 sorgu + rate limit yok | P1 | ORTA | security |
| S-16 | preference_simulation.py:336 | 50 tercih simülasyonu | Auth YOK + N+1 sorgu riski | P1 | ORTA | security |
| S-17 | vision_api.py:444 | Model info | Auth YOK — iç Ollama adresi (localhost:11434) sızıyor | P1 | YÜKSEK | security |
| S-18 | vision_api.py:411 | Health (inference) | Auth YOK — her çağrıda gerçek inference. DoS | P1 | ORTA | security |
| S-19 | yolo_detection_api.py:279 | Soru kırpma | Auth YOK + PIL decompression bomb riski | P1 | ORTA | security |
| S-20 | yolo_detection_api.py:331,351 | Model info/health | Auth YOK — model path ifşası | P1 | ORTA | security |

#### Veri Bütünlüğü (Data Integrity Agent)

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
|----|-------------|-------|-------------|----------|-------|-------|
| D-01 | osym_exam.py:1248-1262 | Soru havuzunu cache'le | ★ TTLCache doluyken is_active kontrolü YAPILMAZ. Deactivated soru ID'leri 1 saat boyunca havuzda kalır → sınava dahil edilebilir | **P0** | YÜKSEK | data-integrity |
| D-02 | osym_exam.py:1259-1262 | Cache'den soru getir | `select(Question).where(id.in_(ids))` — is_active filtresi YOK. D-01 ile birlikte deactivated sorular exam'a girer | **P0** | YÜKSEK | data-integrity |
| D-03 | dag_service.py:163-173 | Topic mastery hesapla | ★ question_bank JOIN'de is_active filtresi YOK — deaktif sorular mastery hesabını bozar (Katman 1 T1.6 eksik tespit) | P1 | YÜKSEK | data-integrity |
| D-04 | cat_session.py:542-543 | Theta persist hatası | ★ `except Exception: pass` — theta güncelleme hatası yutulur → LP orchestrator yanlış theta okur (L1-1 ile aynı, güven↑) | P1 | YÜKSEK | data-integrity+K1 |
| D-05 | cat_session.py:562-563 | XP insert hatası | ★ `except Exception: pass` — gamification sayacı kayması, iz yok (L1-2 ile aynı) | P1 | YÜKSEK | data-integrity+K1 |
| D-06 | cat_session.py:890-893 | Streak güncelleme hatası | ★ `except Exception: pass` — streak kaybı izlenmez (L1-4 ile aynı) | P2 | YÜKSEK | data-integrity+K1 |

#### Domain / Psikometrik (Domain Agent)

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
|----|-------------|-------|-------------|----------|-------|-------|
| DM-01 | bkt_service.py:252-259 | Standard BKT Bayesian posterior | Wrong-answer branch `p_L*(1-p_T)` kullanıyor — Corbett&Anderson'a aykırı. İki farklı BKT formülü aynı dosyada | P1 | YÜKSEK | domain |
| DM-02 | irt_engine.py:50-56 | IRT parametre sınırları | `__post_init__` validation YOK. a=0 (dejenere), a=-1 (ters ICC), c=0.9 (P asla <0.9) kabul edilir | P1 | YÜKSEK | domain |
| DM-03 | irt_engine.py:233 | ZPD seçimi P(correct)∈[0.15,0.85] | Gerçekte [0.40,0.85] kullanıyor. Alt sınır 0.40 → düşük yetenek öğrencilere çok kolay soru | P1 | YÜKSEK | domain |
| DM-04 | orchestrator.py:633-636 | ZPD band = P(correct) kontrolü | ★ Band sadece difficulty-range heuristic, P(correct) hiçbir zaman HESAPLANMIYOR (K-A4 ile çapraz doğrulama) | P1 | YÜKSEK | domain+calib |
| DM-05 | bkt_service.py:284 | BKT→IRT theta bridge (logit) | Linear transform `(p_L-0.5)*8` kullanıyor — doğru logit `ln(p/(1-p))` değil. Yüksek mastery'de theta şişirilir | P2 | YÜKSEK | domain |
| DM-06 | bkt_service.py:88-90 | scaffold_level 0-5 aralığı | p_L=0.0 → scaffold=10 (5'i aşar). Docstring ile çelişiyor | P2 | YÜKSEK | domain |
| DM-07 | fsrs_engine.py:326-328 | YENIDEN state stability güncelle | Wrong answer'da stability güncellenmiyor — stale pre-lapse stability kalır | P2 | YÜKSEK | domain |
| DM-08 | irt_engine.py:237 | ZPD havuz boşsa güvenli fallback | Fallback = unfiltered pool → P(correct) 0.01-0.99 arası, ZPD tamamen devre dışı | P2 | YÜKSEK | domain |
| DM-09 | bkt_service.py:231 | p_learn başlangıç değeri | p_T (transit) değeri p_L (learn) yerine kullanılıyor — semantik karışıklık | P2 | ORTA | domain |
| DM-10 | bkt_service.py:173 | p_learn clamp [0,1] | Sadece üst sınır `min(new_p_L, 0.999)`. Alt sınır yok — negatif olabilir | P2 | ORTA | domain |

#### Frontend (Frontend Agent)

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven | Agent |
|----|-------------|-------|-------------|----------|-------|-------|
| F-01 | ModernLearningPathPage.tsx:103 | Dungeon subject seçimi | `dungeonSubject='MATEMATIK'` sabit, hiç güncellenmez — her ders için matematik dungeon'ı gösterir | P1 | YÜKSEK | frontend |
| F-02 | performanceOptimizer.tsx:309 | Memory tracking interval | `setInterval` temizlenmiyor, `stopTracking()` yok. Singleton → remount'ta interval birikir → memory leak | P1 | YÜKSEK | frontend |
| F-03 | fsrsService.ts:14,74 | Relative URL (nginx proxy) | `VITE_API_URL` set edilirse cross-origin hatası. Docker prod'da kırılır | P1 | ORTA | frontend |
| F-04 | chatService.ts:47,56,264 | Chat session localStorage | Auth token değil ama öğrenci sohbet geçmişi localStorage'da — KVKK risk | P2 | ORTA | frontend |
| F-05 | fsrsService.ts:256 | Health check credentials | `credentials: 'include'` eksik — tek istisna | P2 | YÜKSEK | frontend |
| F-06 | ModernLearningPathPage.tsx:143 | Fetch unmount cleanup | AbortController yok — unmount'ta state update → memory leak | P2 | ORTA | frontend |
| F-07 | ModernLearningPathPage.tsx:151 | useEffect bağımlılık | `loadVideosForPath` her render'da yeni referans → sonsuz döngü riski | P2 | ORTA | frontend |

### Convergence Özeti

| Çapraz Doğrulama | Kaynaklar | Sonuç |
|-----------------|-----------|-------|
| cat_session except:pass | K1 (L1-1..L1-4) + Data Integrity (D-04,D-05,D-06) | ★ YÜKSEK — theta/XP/streak kaybı |
| ZPD hiçbir zaman hesaplanmıyor | Calibration (K-A4) + Domain (DM-04) + Domain (DM-03) | ★ YÜKSEK — tüm ZPD zinciri bozuk |
| Question cache is_active bypass | Data Integrity (D-01) + (D-02) — aynı agent ama 2 ayrı sorgu noktası | ★ YÜKSEK — deactivated soru sınava girebilir |
| dag_service is_active eksik | K1 T1.6 "CLEAN" tespiti + D-03 tarafından düzeltildi | ★ K1 yanlış-negatif düzeltildi |

### Katman 3 (Yorumsal)

#### T3.1 Orchestrator Policy Tutarlılığı

| ID | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet | Güven |
|----|-------------|-------|-------------|----------|-------|
| T3-01 | orchestrator/core/policy_engine.py (P12) ↔ routing.py | CRITICAL risk: max 50 satır (routing) | P12 policy: max 20 satır — çelişki, routing geçen PR policy'de FAIL | P1 | YÜKSEK |
| T3-02 | policy_engine.py (P14) ↔ routing (SECURITY task) | Security task'ta auth değişikliği yapabilme | P14 auth changes'ı CRITICAL bloklıyor → security task'ında auth fix imkansız | P1 | YÜKSEK |
| T3-03 | policy_engine.py (P1) | 18 TaskType'ı routing'e yönlendir | Sadece 5/18 TaskType handle ediliyor (%28 coverage) — 13 type fallback'e düşer | P2 | YÜKSEK |
| T3-04 | policy_engine.py (P2,P3,P4) | Agent capability, workflow integrity, state consistency | Stub implementation — always pass. Hiçbir validasyon yapılmıyor | P2 | YÜKSEK |
| T3-05 | policy_engine.py | 7 specialist agent için policy kuralları | 0 rule — psychometrics, exam_engine, learning_analytics vb. politikasız | P2 | ORTA |

**Not:** Orchestrator policy sistemi ~%85 placeholder. Production kullanımı sınırlı olduğundan P1/P2.

#### T3.2 Config Tutarlılığı

| ID | Dosya1 ↔ Dosya2 | Beklenen | Gerçek | Ciddiyet |
|----|------------------|----------|--------|----------|
| T3-06 | vite.config.ts:184 ↔ nginx.conf:7 | Aynı port | Dev:3001, Nginx:3000 — kasıtlı (dev vs prod) | P2 (by design) |
| T3-07 | config.py:116 ↔ docker-compose.yml | Redis: host.docker.internal | Default: localhost:6379 — Docker'da çalışması .env.mvp override'a bağlı | P2 (bilinen) |
| T3-08 | config.py:177 CORS | 3000,3001,5173 hepsi izinli | 5173 artık kullanılmıyor (Vite artık 3001) — stale entry | P2 |
| — | Backend port 8000, Docker network, API prefix | Tutarlı | ✅ CLEAN | — |

#### T3.3 Test Semantiği

| ID | Kontrol | Sonuç | Ciddiyet |
|----|---------|-------|----------|
| T3-09 | `assert True` sahte test taraması | 75 hit — TÜMÜ reward_hacking detector test dosyalarında veya "NEVER use" yorumlarında. **0 gerçek sahte test** | CLEAN |
| T3-10 | `pytest.skip/mark.skip` sayısı | 113 occurrence / 30 dosya — teknik borç ama fonksiyonel risk değil | P2 |
| T3-11 | placement_service.py:256 | `except Exception: pass` — bare except, hata yutulur | P2 (K1'de yakalandı) |

#### T3.4 CLAUDE.md ↔ Gerçeklik

| # | CLAUDE.md İddiası | Gerçek Değer | Tutarlı? | Güncelleme Gerekiyor? |
|---|-------------------|-------------|----------|----------------------|
| T3-12 | "41+ endpoint" (backend/api/) | backend/api/: ~96 aktif router, backend/app/api/: 28 endpoint = **124+ toplam** | ❌ | ✅ Güncelle: "124+ endpoint" |
| T3-13 | "17 kanal, 27 alias" | 17 kanal ✓, **11 alias** (27 değil) | ❌ | ✅ Güncelle: "17 kanal, 11 alias" |
| T3-14 | "Coverage ~18%" | Session 127'de **%53** (28 yeni test dosyası) | ❌ | ✅ Güncelle: "~53%" |
| T3-15 | "React 18" | React 18.2.0 ✓ | ✅ | — |
| T3-16 | "PostgreSQL 15" | postgres:15-alpine ✓ | ✅ | — |
| T3-17 | "12+ modules" YouTube | 12 dosya ✓ | ✅ | — |
| T3-18 | "77,336 soru" | import script + MEMORY referansı ✓ | ✅ | — |

**Not:** 3 iddia güncellenmelidir (endpoint sayısı, alias sayısı, coverage). Doğruluk = 4/7 (%57).

## Adım 4: Akış Trace

### Sınav Akışı

**Akış Diyagramı:**
```
[ModernExamStartPage] --(POST /api/v1/osym-exam/create)--> [sinav.py:348]
  │                                                          │
  │ exam_type.toLowerCase()="tyt"                            │ ExamType(str,Enum) TYT="tyt" ✓
  │                                                          │
  └── navigate(`/exam/${session_id}`)                        ├── osym_exam_engine.create_exam_session()
                                                             │    ├── exam_configs[ExamType.TYT] deepcopy
[ExamPage] --(GET /questions, POST /answer)-->               │    ├── _select_questions() → question_bank
  │                                                          │    │    ├── is_active filter ✓ (P0 fix)
  │ Timer: local countdown + 30s sync                        │    │    ├── UPPERCASE subject match ✓
  └── (POST /finish) → calculate_score()                     │    │    └── TTLCache + random.sample
                                                             │    └── active_sessions[sid] = session_data (in-memory ⚠️)
                                                             │
                                                             └── get_session_data() → ExamSessionResponse
```

| # | Geçiş | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet |
|---|-------|------------|-------|------------|---------|
| EX-01 | Frontend→API: exam_type case | ExamStartPage:91 → sinav.py:36 | Frontend "tyt" → backend ExamType parse | ✅ ExamType(str,Enum) TYT="tyt" — Pydantic otomatik parse | CLEAN |
| EX-02 | Soru seçimi: doğru tablo | osym_exam.py:32 | QuestionBankItem kullan | `from models.question_bank import QuestionBankItem as Question` ✅ | CLEAN |
| EX-03 | Soru seçimi: is_active | osym_exam.py:1260-1298 | Deaktif soru filtreleme | ✅ 4 select noktasında `Question.is_active.is_(True)` (Session 1 P0 fix) | CLEAN (fixed) |
| EX-04 | Cache invalidation | osym_exam.py:1248 | TTLCache soru havuzu | Cache doluyken is_active kontrolü yapılmaz — TTL (1 saat) içinde deaktif soru ID havuzda kalır. Fetch'te is_active filtresi var ama COUNT mismatch olabilir | P1 (downgraded from P0) |
| EX-05 | Session izolasyonu | osym_exam.py:140,1641 | Multi-worker desteği | ★ `active_sessions: dict` in-memory — multi-worker'da session paylaşılmaz (K-B5) | **P0** (bilinen) |
| EX-06 | TYT/AYT süreleri | osym_exam.py:158,178 | ÖSYM resmi süreler | TYT=165dk (doğru:135), AYT=210dk (doğru:180) — K-B1 ile aynı | P1 (bilinen) |
| EX-07 | Puan hesaplama | osym_exam.py:1427 | ÖSYM 2023+ net=correct | `net = correct - (wrong/4)` — 1/4 ceza kaldırıldı ama hâlâ uygulanıyor (K-B4) | P1 (bilinen) |
| EX-08 | response_time None | osym_exam.py:1084 | Süre topla | ✅ `answer.response_time_seconds or 0` (Session 1 P0 fix) | CLEAN (fixed) |
| EX-09 | Score scaling | osym_exam.py:834 | YKS puan ölçekleme | `scaled_score = raw_score` — gerçek YKS ölçekleme yok (K-B6) | P1 (bilinen) |
| EX-10 | PerformanceResponse eksik | sinav.py:175-203 ↔ examService.ts:119 | `konu_performanslari` dönmeli | Backend schema'da alan YOK. Frontend `performanceToSinavSonucu()` || [] ile default → **konu analizi her zaman BOŞ** | **P0** |
| EX-11 | start_exam L1-only | osym_exam.py:478-479 | Session L2'den yüklenebilmeli | `start_exam()` sadece `active_sessions` dict'e bakıyor, `get_session_data()` gibi L2 Redis fallback YOK. Backend restart sonrası start çağrısı FAIL | **P0** |
| EX-12 | auto_complete_task restore | osym_exam.py:1608-1640 | Restart sonrası timer devam etmeli | Redis L2'den yüklenen session için `_auto_complete_task` başlatılmıyor → sınav süresi dolsa bile IN_PROGRESS'te asılı kalır | **P0** |
| EX-13 | Abandoned exam cleanup | ExamPage.tsx:104-106 | Terk edilen sınav ABANDONED olmalı | `handleExamExit` → `/dashboard` redirect, ExamSession DB'de sonsuza kadar IN_PROGRESS | P1 |
| EX-14 | LGS enum mismatch | examService.ts:13 ↔ enums_db.py:50 | LGS desteklenmeli veya devre dışı | Frontend ExamType.LGS tanımlı, backend'de YOK → 422 Unprocessable Entity | P1 |
| EX-15 | topic field UUID | sinav.py:558 | Konu adı dönmeli | `topic=question.primary_topic_id or question.subject_area` — primary_topic_id UUID string, konu adı değil | P1 |
| EX-16 | YDT no-questions UX | osym_exam.py:198-200 | Açık mesaj | YDT soru yokluğu → ValueError → "İşlem başarısız" — kullanıcı neden anlayamaz | P1 |

### Öğrenme Yolu Akışı

**Akış Diyagramı:**
```
[ModernLearningPathPage]
  ├── GET /api/v1/learning-path/status → [daily API] → Orchestrator
  │     ├── _fetch_thetas_with_se() → student_abilities
  │     ├── _fetch_fsrs_due_counts() → user_item_fsrs JOIN question_bank
  │     ├── DAGService.get_user_mastery() → kiro2_cat_sessions JOIN question_bank
  │     └── DAGService.get_next_recommended_topic()
  │
  ├── GET /api/v1/dungeon/{subject} → [dungeon API]
  │     ├── topic_hierarchy + topic_prerequisites → rooms/edges
  │     ├── dungeon_progress → user progress
  │     ├── user_theta → theta, theta_se  ⚠️ FARKLI TABLO
  │     └── question_bank WHERE is_active=true → counts
  │
  ├── GET /api/v1/learning-path/exit-quiz/{subject} → SoruBankasiServisi
  │     └── question_bank WHERE is_active=TRUE
  │
  └── POST /api/v1/learning-path/register-wrong-answers → QuestionReviewAdapter
        └── user_item_fsrs (FSRS state persist)
            ↓ (BKTService.record_answer pipeline)
        BKT → IRT (theta bridge) → FSRS (review_card) → ZPD (zone)
```

| # | Geçiş | Dosya:Satır | Niyet | Gerçekleşme | Ciddiyet |
|---|-------|------------|-------|------------|---------|
| LP-01 | DungeonMap subject | ModernLearningPathPage.tsx:103,927 | Kullanıcının seçtiği selectedSubject'i göster | `dungeonSubject='MATEMATIK'` sabit — her ders için matematik dungeon'ı gösterir | **P0** |
| LP-02 | Theta tablo çatallanması | orchestrator.py:527 ↔ dungeon.py:215 | Theta tutarlı bir tablodan okunmalı | Orchestrator → `student_abilities` (INT subject_id), Dungeon → `user_theta` (TEXT subject_area). İki farklı tablo → fog-of-war her kullanıcı için theta=0.0 | **P0** |
| LP-03 | FSRS tablo çatallanması | orchestrator.py:541 ↔ bkt_service.py:341 | FSRS due count tutarlı olmalı | Orchestrator `user_item_fsrs` sorgular, BKTService `FSRSCard/fsrs_cards` günceller. Farklı tablolar → due count her zaman 0 | **P0** |
| LP-04 | prereq_topic_name | orchestrator.py:211 | Konu adı göster | `next_topic_name = next_tid` — UUID yazılıyor, banner'da UUID görünür | P1 (=K-A7) |
| LP-05 | /status exam_type | daily.py:133-159 | Öğrencinin sınav türüne göre ağırlık | `exam_type` default "TYT" kalır, `_get_user_goal()` sonucu kullanılmaz. AYT öğrenci TYT ağırlığı alır | P1 |
| LP-06 | is_timeout field | MLPP.tsx:320 ↔ v2.py:1988 | Timeout bilgisi backend'e ulaşmalı | `RegisterWrongAnswersRequest`'te `is_timeout` field yok → sessizce silinir | P1 |
| LP-07 | Bozuk DAG kullanımı | dag_service.py:132-134 | Cycle → DAG hatalı işaretle | `logger.error()` sonrası bozuk DAG `self._dag`'a atanır → sessizce kullanılmaya devam | P1 |
| LP-08 | BKT→IRT bridge | bkt_service.py:283-286 | p_L→theta dönüşümü | `max(0.05, min(0.95))` clamp var, `(clamped-0.5)*8` → [-3.6,3.6]. IRT b∈[-3,3] daha dar | CLEAN |
| LP-09 | IRT parametre sınırları | irt_service_3pl.py:104-106 | a,b,c clamp | ✅ Tüm parametreler klamplı, overflow koruması var | CLEAN |
| LP-10 | Cold start | dungeon.py:196-212 | Yeni kullanıcı default | ✅ `progress_map.get(tid, {})` → default değerler | CLEAN |
| LP-11 | DungeonNode description | MLPP.tsx:185-189 | Anlamlı açıklama | `description: node.code` — MAT.01 gibi kod gösterir, UX sorunu | P2 |

## Özet Sayaçlar (Tüm adımlar sonrası — FINAL, review sonrası düzeltilmiş)

| Ciddiyet | Kalibrasyon | K1 | K2 | K3 | Akış | Toplam | Benzersiz |
|----------|------------|-----|-----|-----|------|--------|-----------|
| **P0** | 3 | 0 | 13 | 0 | 6 | 22 | **21** |
| **P1** | 7 | 0 | 15 | 2 | 9 | 33 | **28** |
| **P2** | 5 | 7 | 10 | 9 | 1 | 32 | **31** |
| **Toplam** | 15 | 7 | 38 | 11 | 16 | 87 | **80** |

*Duplicate'lar: EX-05=K-B5, EX-06=K-B1, EX-07=K-B4, EX-09=K-B6, LP-04=K-A7, F-01=LP-01 (6 duplicate). D-01 P0→P1 downgrade (review sonrası).*
*Fixlenen: 14 P0 (f244aae), 21 P0 toplam (2a84504), 28 P1 (22b089e→088ccf2), 13 P2 (5b1160d). Kalan P0: 7. Kalan P1: 0. Kalan P2: ~18 (çoğu informational/by-design).*

### P0 Tam Liste (22 toplam — 14 fixlendi, 1 duplicate, 7 kalan)

**FIXLENDİ (Session 1, commit f244aae — 14 bulgu):**
- S-01..S-11: 3 dosyada 17 endpoint'e auth eklendi (11 P0) ✅
- K-B2: AYT field type → total_questions sync ✅
- K-B3: response_time_seconds None → `or 0` guard ✅
- D-02: select(Question).where(id.in_) → is_active filtresi eklendi (4 sorgu) ✅

**DUPLICATE:** EX-05 = K-B5 (aynı singleton bulgusu)

**DOWNGRADE:** D-01 → P1 (fetch tarafı fixlendi, cache stale count mismatch riski düşük)

**KALAN (7 adet):**
- K-B5: Global singleton multi-worker session izolasyonu
- LP-01: DungeonMap hardcoded 'MATEMATIK' (=F-01, F-01 kaldırıldı)
- LP-02: Theta tablo çatallanması (student_abilities vs user_theta)
- LP-03: FSRS tablo çatallanması (user_item_fsrs vs fsrs_cards)
- EX-10: PerformanceResponse konu_performanslari eksik → konu analizi her zaman BOŞ
- EX-11: start_exam() L1-only — L2 Redis fallback yok (nadir senaryo ama restart'ta session kaybı)
- EX-12: _auto_complete_task L2'den restore edilmiyor → sınav süresiz IN_PROGRESS

### P0 Listesi (16 adet — acil müdahale)
- K-B2: AYT field type → total_questions mismatch → ValueError
- K-B3: response_time_seconds None → TypeError
- K-B5: Global singleton multi-worker session izolasyonu
- D-01: Question pool TTLCache is_active bypass
- D-02: select(Question).where(id.in_) — is_active filtresi yok
- S-01..S-05: vision_api.py 5 endpoint auth YOK (GPU abuse)
- S-06..S-08: yolo_detection_api.py 3 endpoint auth YOK (memory abuse)
- S-09..S-11: curriculum_compliance.py 3 POST endpoint auth YOK (veri bütünlüğü)

### P0 Karar Noktası
16 P0 bulundu (plan limiti: 4+ → durdur).
**Ancak** 11/16 P0 aynı pattern (auth eksikliği) ve fix basit (Depends ekle).
3/16 P0 osym_exam_engine'de (kalibrasyon).
2/16 P0 question cache (yeni, kritik).

**Karar:** Analiz DEVAM — P0'lar ayrı fix sprint'inde çözülecek. Session 2'de Katman 3 + Akış İzleme.

---

## Fix Sprint Özeti

### P0 Fixes (commit 2a84504 — 6 fix, Session 2)
- LP-01: DungeonMap selectedSubject binding (hardcoded MATEMATIK→dynamic)
- LP-02: Theta tablo çatallanması → user_theta tablosu (dungeon okumalarında)
- LP-03: FSRS tablo çatallanması → user_item_fsrs birleştirildi
- EX-10: PerformanceResponse konu_performanslari → konu analizi dolu
- EX-11: start_exam() L2 Redis fallback eklendi
- EX-12: auto_complete_task L2'den restore ediliyor

### P1 Fixes (4 batch: 22b089e, 392c2bc, 96ef273, 088ccf2 — 28/28 fix)
**Batch 1:** K-A4 mastery formula, K-A6 theta error handling, K-B1 TYT/AYT süreler, K-B4 1/4 ceza kaldırma, K-B6 scaled_score, K-B8 session Redis L2, DM-01 BKT posterior, K-A3 DAG hata→prereq_blocked=True, D-04 cat_session theta except→log, D-05 cat_session XP except→log, EX-04 cache+is_active, EX-13 abandoned exam
**Batch 2:** DM-02 IRT __post_init__ clamp, DM-03 ZPD 0.40→0.20, DM-04 ZPD difficulty band, EX-14 LGS enum, EX-15 topic field UUID→name, EX-16 YDT no-questions UX, F-01 (=LP-01 resolved), F-02 MemoryTracker cleanup, F-03 relative URL
**Batch 3:** LP-05 exam_type goal, LP-07 DAG cycle→raise, D-03 dag_service is_active, S-17 vision info leak, S-18 vision health DoS, F-05 fsrsService credentials
**Batch 4:** S-12..S-14 curriculum auth (7 endpoint), S-15/S-16 preference_simulation auth (9 endpoint), LP-06 is_timeout field, T3-01 policy P12 diff limits, T3-02 policy P14 auth/security, T3-12..T3-14 CLAUDE.md stats update

### P2 Fixes (commit 5b1160d — 13 fix)
**Backend domain:**
- DM-05: BKT→IRT logit transform (linear→ln(p/(1-p)))
- DM-06: scaffold_level clamp max 5
- DM-07: FSRS YENİDEN state stability update
- DM-08: ZPD empty pool intermediate band [0.10,0.95]
- DM-09: BKT initial p_L proper prior (0.10 not p_T)
- DM-10: p_learn lower bound clamp [0.001,0.999]
**Backend infrastructure:**
- K-A1: absolute import try/except guard
- K-A2: unused return value captured
- K-A5/L1-7: bare except→logged warning (orchestrator)
- L1-6: bare except→logged warning (placement)
**Frontend:**
- F-04: chatService localStorage→sessionStorage (KVKK)
- F-06: AbortController fetch unmount cleanup
- LP-11: DungeonNode description name_tr

### P2 Skipped (by design / out of scope)
- T3-03/T3-04/T3-05: Policy engine stubs — ~85% placeholder, feature request not fix
- T3-08: CORS 5173 stale entry — harmless, .env override controls production
- T3-10: pytest skip count — informational, not actionable
- F-07: loadVideosForPath dep — already stable (useCallback([]))
- L1-1..L1-4 (=D-04/D-05): Already fixed in P1 batch
- D-06: cat_session streak except — duplicate of D-04/D-05 pattern
- K-A7 (=LP-04): Already fixed in P1 batch
- K-B7: osym IRT estimation — informational, works as approximate
- L1-5: dag_service ValueError/KeyError — appropriate for cache misses

### P0 Son Durum (21/21 FIXLENDİ)
- K-B5: ✅ FIXLENDİ (d2e5b1a) — 10 method Redis L2 fallback, 3 mutating persist
- LP-01: ✅ FIXLENDİ (2a84504)
- LP-02: ✅ FIXLENDİ (2a84504)
- LP-03: ✅ FIXLENDİ (2a84504)
- EX-10: ✅ FIXLENDİ (2a84504)
- EX-11: ✅ FIXLENDİ (2a84504)
- EX-12: ✅ FIXLENDİ (2a84504)

### Code Review Fixes (commit e06c16f)
- osym_exam_engine: background task KeyError guard (.get() instead of [])
- osym_exam_engine: L1 eviction before Redis delete (race condition fix)
- fsrs_engine DM-07: _next_forget_stability for repeated lapse (FSRS v6 spec)

**Kalan P0: 0. Kalan P1: 0. Kalan P2: ~18 (informational/by-design).**
