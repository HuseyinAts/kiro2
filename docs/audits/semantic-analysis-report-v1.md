# KIRO2 Semantik Analiz Raporu v1.0

**Tarih:** 2026-04-10
**Metodoloji:** v6 — Niyet ↔ Gerçekleşme Boşluk Analizi
**Kapsam:** Backend (app/services, core, api), Frontend (pages, hooks, services), Orchestrator
**Detaylı Bulgular:** `docs/audits/findings.md`

---

## 1. Executive Summary

KIRO2 codebase'inin uçtan uca semantik analizi 5 adımda gerçekleştirildi:
- **Kalibrasyon** (2 dosya, 3 agent): %0 false positive, 15 bulgu
- **Statik tarama** (Katman 1): mypy/tsc temiz, 7 exception yutma, 13 auth-siz dosya
- **Agent convergence** (Katman 2, 4 agent): 38 bulgu, güvenlik+veri+domain+frontend
- **Yorumsal** (Katman 3): Config tutarlılığı, orchestrator policy, CLAUDE.md doğrulama
- **Akış izleme** (Adım 4): Sınav + Öğrenme Yolu uçtan uca trace

**Toplam: 87 bulgu — Benzersiz: 80 (21 P0, 28 P1, 31 P2).**

Session 1'de 14 P0 fix uygulandı (commit `f244aae`): auth enforcement (17 endpoint, 11 P0), AYT/YDT total_questions sync, None guard, is_active filter (4 sorgu).
D-01 (TTLCache) review sonrası P0→P1 downgrade (fetch tarafı fixlendi, stale count riski düşük).

### Kalan Risk Profili

| Kategori | P0 | P1 | P2 | En Kritik |
|----------|----|----|----|-----------| 
| Güvenlik (auth) | 0* | 4 | 3 | ~~11 auth-siz endpoint~~ → FIXLENDİ |
| Veri Bütünlüğü | 3 | 3 | 1 | Tablo çatallanması (LP-02, LP-03) |
| Domain/Psikometrik | 0 | 6 | 5 | ZPD hesaplanmıyor (DM-04), BKT formül hatası (DM-01) |
| Sınav Motoru | 4 | 7 | 0 | L1/L2 senkronizasyon bozuk, konu analizi boş, auto-complete kayıp |
| Frontend | 1 | 3 | 3 | DungeonMap hardcoded subject (LP-01/F-01) |
| Config/Docs | 0 | 0 | 9 | CLAUDE.md 3 iddia güncel değil |
| Orchestrator | 0 | 2 | 3 | Policy çelişkileri, %85 stub |

*\*Session 1'de 12 P0 auth+exam bulgusu fixlendi*

---

## 2. P0 Bulgular (Acil — 10 kalan)

| ID | Dosya | Sorun | Önerilen Fix | Effort |
|----|-------|-------|--------------|--------|
| K-B5 | osym_exam_engine.py:1641 | Global singleton `active_sessions` dict — multi-worker'da session izolasyonu bozuk | Redis-backed session store veya DB ExamSession tablosu | M |
| LP-01 | ModernLearningPathPage.tsx:103 | `dungeonSubject='MATEMATIK'` sabit — her ders Matematik haritası | `subject={selectedSubject}` | S |
| LP-02 | orchestrator.py:527 ↔ dungeon.py:215 | Theta iki farklı tablodan okunuyor (`student_abilities` vs `user_theta`) — fog-of-war theta=0.0 | Tek tablo (`student_abilities`) kullan, dungeon API'yi güncelle | M |
| LP-03 | orchestrator.py:541 ↔ bkt_service.py:341 | FSRS due count iki farklı tablodan (`user_item_fsrs` vs `fsrs_cards`) — due count hep 0 | Tablo birleştirme veya cross-reference | M |
| D-01 | osym_exam_engine.py:1248 | TTLCache: Soru ID cache 1h — deaktif soru fetch'te filtrelenir ama count mismatch | TTL kısalt (5-15 dk) veya invalidation hook | S |
| EX-10 | sinav.py:175 ↔ examService.ts:119 | `konu_performanslari` backend'den hiç dönmüyor — konu analizi sayfası her zaman BOŞ | Backend `/complete` response'a `konu_performanslari` ekle | M |
| EX-11 | osym_exam_engine.py:478 | `start_exam()` sadece L1 dict'e bakıyor — restart sonrası session FAIL | `get_session_data()` ile L2 fallback ekle | S |
| EX-12 | osym_exam_engine.py:1608 | `_auto_complete_task` L2'den restore edilmiyor — sınav süresiz IN_PROGRESS | Session load sonrası timer'ı yeniden başlat | M |
| ~~S-01..S-11~~ | ~~vision/yolo/curriculum~~ | ~~17 endpoint auth YOK~~ | ~~FIXLENDİ (commit f244aae)~~ | ~~—~~ |
| ~~K-B2,K-B3,D-02~~ | ~~osym_exam_engine.py~~ | ~~AYT total_questions, None guard, is_active~~ | ~~FIXLENDİ (commit f244aae)~~ | ~~—~~ |

---

## 3. P1 Bulgular (Önemli — 28 adet)

### Güvenlik
| ID | Sorun | Fix |
|----|-------|-----|
| S-12 | curriculum_compliance bulk validate: auth yok + compute-heavy | Auth eklendi (f244aae) ama rate limit gerekli |
| S-15/S-16 | preference_simulation: toplu tahmin/simülasyon auth yok | Auth + rate limit ekle |
| S-17 | vision_api /info: Ollama localhost adresi sızıyor | Auth eklendi (f244aae) |

### Veri Bütünlüğü
| ID | Sorun | Fix |
|----|-------|-----|
| D-03 | dag_service mastery: question_bank JOIN'de is_active filtresi yok | Filter ekle |
| D-04/D-05 | cat_session: theta/XP persist hatası yutulur | `except Exception: pass` → loglama |

### Domain/Psikometrik
| ID | Sorun | Fix |
|----|-------|-----|
| K-A3 | Orchestrator: DAG hata → prereq_blocked=False, öğrenci hazır olmadığı konuya gider | `except` → prereq_blocked=True (güvenli taraf) |
| K-A4 | Mastery: `z=(theta+1.0)/se` — θ=0 → %97.7 mastery | +1.0 kaydırmayı kaldır |
| K-A6 | Theta fetch hata → boş dict → TÜM dersler θ=0.0 → mastery %97.7 | `except` → hata döndür |
| K-B1/EX-06 | TYT=165dk (doğru:135), AYT=210dk (doğru:180) | Süreleri düzelt |
| K-B4/EX-07 | `net=correct-(wrong/4)` — ÖSYM 2023'te ceza kaldırıldı | `net=correct` |
| K-B6/EX-09 | `scaled_score=raw_score` — gerçek YKS ölçekleme yok | Basit ölçekleme formülü |
| DM-01 | BKT wrong-answer: `p_L*(1-p_T)` — Corbett&Anderson'a aykırı | Formülü düzelt |
| DM-02 | IRT parametre validation yok: a=0 veya a=-1 kabul edilir | `__post_init__` clamp ekle |
| DM-03 | ZPD alt sınır 0.40 (hedef 0.15) — düşük yetenek öğrenciye çok kolay soru | Alt sınırı 0.15-0.20'ye düşür |
| DM-04 | ZPD P(correct) hiçbir zaman hesaplanmıyor, sadece difficulty heuristic | Gerçek P(θ) hesaplama ekle |

### Frontend
| ID | Sorun | Fix |
|----|-------|-----|
| F-01 | DungeonMap hardcoded subject (=LP-01) | `subject={selectedSubject}` |
| F-02 | performanceOptimizer.tsx: setInterval temizlenmiyor → memory leak | cleanup fonksiyonu ekle |
| F-03 | fsrsService.ts: VITE_API_URL set edilirse cross-origin | Relative URL enforce |
| LP-05 | /status endpoint exam_type default TYT — AYT öğrenci yanlış ağırlık alır | `_get_user_goal()` sonucunu kullan |
| LP-06 | is_timeout field backend'de yok sayılır | Pydantic modele field ekle |
| LP-07 | Bozuk DAG sessizce kullanılmaya devam eder | Cycle → exception veya empty fallback |

### Orchestrator
| ID | Sorun | Fix |
|----|-------|-----|
| T3-01 | P12 diff limit (20) ↔ Routing limit (50) çelişki | Limitleri eşitle |
| T3-02 | P14 auth blocking ↔ SECURITY task çelişki | Security task'ı P14'ten muaf tut |

---

## 4. Akış Trace Özeti

### Sınav Akışı (16 geçiş noktası — Akış A agent)
- **CLEAN:** ExamType parse (lowercase→enum), doğru tablo (QuestionBankItem), is_active filter (fixed), response_time None guard (fixed), IDOR check tutarlı, auth tüm endpoint'lerde mevcut
- **P0 (4):** Singleton session izolasyonu, `konu_performanslari` eksik (sonuç sayfası boş), `start_exam()` L1-only, auto_complete_task restore yok
- **P1 (4):** TYT/AYT süreleri, 1/4 ceza, abandoned exam cleanup, LGS enum mismatch

### Öğrenme Yolu Akışı (13 geçiş noktası)
- **CLEAN:** BKT→IRT bridge (clamp var), IRT parametreleri (clamp+overflow), cold start default'ları
- **P0 (3 yeni):** Hardcoded DungeonMap subject, theta tablo çatallanması, FSRS tablo çatallanması
- **P1:** prereq_topic_name UUID, exam_type default TYT, is_timeout kaybı, bozuk DAG kullanımı

### Tablo Çatallanması Diyagramı
```
                    Orchestrator (daily API)           Dungeon API
Theta:              student_abilities (INT pk)    ↔    user_theta (TEXT pk)     ← FARKLI TABLO
FSRS:               user_item_fsrs               ↔    FSRSCard/fsrs_cards      ← FARKLI TABLO
Mastery:            kiro2_cat_sessions JOIN qb    ↔    question_bank counts     ← AYNI TABLO ✓
```

---

## 5. Güçlü Yönler

- **QuestionBankItem aliasing** doğru uygulanmış (77,336 prod soru)
- **IRT 3PL parametre sınırları** eksiksiz (a,b,c clamp + overflow koruması)
- **Reward hacking koruması** aktif (0 sahte test, detector testleri çalışıyor)
- **Auth dual model** (cookie + bearer) iyi tasarlanmış
- **Cold start** her tabloda güvenli default'lar
- **Frontend credentials:'include'** büyük ölçüde tamamlanmış (1 istisna: fsrsService health)
- **P0 fix sprint** (Session 1): 12 P0 tek commit'te fixlendi, code review geçti

---

## 6. Sonraki Adımlar

### Acil (P0 — bu hafta)
1. **LP-01:** DungeonMap `subject={selectedSubject}` — 1 satır fix
2. **LP-02/LP-03:** Tablo birleştirme — dungeon API'yi `student_abilities` + `user_item_fsrs` kullanacak şekilde güncelle
3. **EX-10:** `konu_performanslari` backend response'a ekle — konu analizi sayfası hiç çalışmıyor
4. **EX-11/EX-12:** L1/L2 senkronizasyon — `start_exam()` L2 fallback + auto_complete restore
5. **K-B5/EX-05:** `active_sessions` → Redis-backed (veya DB ExamSession)

### Kısa vadeli (P1 — bu sprint)
4. ÖSYM süreleri düzelt (TYT:135, AYT:180)
5. Net hesaplama: `correct - wrong/4` → `correct`
6. Mastery formülü: +1.0 kaydırmayı kaldır
7. ZPD: P(correct) hesaplama ekle
8. BKT wrong-answer formülü düzelt
9. Exception yutma → loglama (cat_session 4x, orchestrator 5x)

### Orta vadeli (P2 — sonraki sprint)
10. CLAUDE.md güncelle (endpoint sayısı, alias, coverage)
11. Orchestrator policy çelişkilerini çöz
12. Frontend memory leak'leri fix (performanceOptimizer interval)

### Metrikler
- **Toplam bulgu:** 86 (22 P0, 32 P1, 32 P2). Benzersiz: ~81
- **Fix edilecek:** 10 P0 + 32 P1 = 42 aksiyon
- **Session 1'de fixlenen:** 12 P0 (auth + exam engine)
- **Toplam coverage:** Analiz ~14 dosya derin, ~132 dosya tarama, 2 akış uçtan uca (22 geçiş noktası)
- **False positive:** %0 (kalibrasyon ile doğrulanmış)
- **Çapraz doğrulama:** 6+ bulgu 2+ agent/katman tarafından onaylandı (★)
- **Agent kullanımı:** 3 kalibrasyon + 4 Katman 2 + 3 Katman 3 + 2 Akış = 12 paralel agent

---

*Bu rapor KIRO2 Semantik Analiz Metodolojisi v6'ya göre hazırlanmıştır.*
*Detaylı bulgular: `docs/audits/findings.md`*
*Metodoloji: `docs/audits/semantic-analysis-methodology-v6.md`*
