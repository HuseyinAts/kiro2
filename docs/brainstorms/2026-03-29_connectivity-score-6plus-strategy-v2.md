# Brainstorm v2: Connectivity Skoru 6.0+ Stratejisi (Post-Fix Guncelleme)

Tarih: 2026-03-29 | Domain: architecture | Perspektifler: Performans Muhendisi, Bakim Muhendisi, Maliyet/ROI Analisti

Onceki versiyon: `docs/brainstorms/2026-03-29_connectivity-score-6plus-strategy.md` (v1, pre-fix)

---

## Yonetici Ozeti (TL;DR)

28 commit'lik sprint sonrasi connectivity skoru 3.8/10'dan tahmini **5.3** civarinda yukseldi. Reports backend endpoint'leri dogrulanmadi (7 method 404 donuyor olabilir), Gamification frontend'de hala entegre degil, Recommendation hala %100 mock data donuyor. En kotu durum skoru **5.1** (Reports 0 ise), gercekci **5.3**.

**6.0 hedefi henuz tutmadi.** Ulasmak icin en yuksek ROI aksiyonlar: **(1)** Recommendation mock'u gercek daily-plan + YouTube verisine bagla (+0.24), **(2)** LP v2 facade'a daily summary inject et (+0.18), **(3)** parentService graceful fallback (+0.12), **(4)** FSRS composite index + health metric (performans garantisi). Ilk 3 aksiyon toplam 7-9 saat, tahmini +0.54 skor artisi (5.3 -> 5.8). 6.0'a ulasmak icin Gamification UI entegrasyonu da gerekli.

En kritik risk: `advancedReportsService.ts` URL'leri duzeltildi ama 7 backend endpoint'in gercekten implement edilip edilmedigi HICBIR YERDE test edilmedi. Bu dogrulanmazsa skor tahmini 0.18 puan dusebilir.

---

## 1. Baglam ve Metodoloji

### 1.1 Audit Gecmisi

| Tarih | Rapor | Bulgu | Skor | Notlar |
|-------|-------|-------|------|--------|
| 28 Mart 2026 | deep-connectivity-health-audit | 47 | 4.3/10 | Ilk kapsamli audit |
| 29 Mart 2026 (sabah) | kapsamli-baglanti-sagligi-raporu | 75 | 3.8/10 | 6 paralel Opus agent, guvenlik cezasi |
| 29 Mart 2026 (aksam) | **Bu rapor (v2)** | Guncelleme | **5.1-5.3** | Post-fix, 3 paralel perspektif |

### 1.2 Yapilan Fix'ler (28 Commit Sprint)

Asagidaki fix'ler tamamlandi ve skor hesaplamasina yansitildi:

| Fix | Etkilenen Zincir | Skor Degisimi | Commit |
|-----|-----------------|---------------|--------|
| Ghost table bridge: `user_theta` -> `student_abilities` | LP v2 <-> Daily | 0 -> 5 | `34af68e` |
| Auth enforcement (27 endpoint) | Genel guvenlik cezasi | -0.7 -> 0 | `392858d` |
| Gamification wiring (badge + leaderboard + on_quiz_completed) | Gamification | 2 -> 4 | `392858d` |
| Double XP fix | Gamification | (dahil) | `392858d` |
| Reports URL prefix fix (`/api/v1/`) | Reports | 0 -> 3 (tahmin) | Session 107 |
| DailyPlanPage v2 field'lar (theta_se, zpd_zone, prereq_blocked) | LP Daily | 6 -> 8 | Session 119 |
| ModernLearningPathPage /status fetch + theta/mastery render | LP v2 <-> Daily | (dahil) | Session 119 |
| osym_questions_api raw asyncpg -> SQLAlchemy | Guvenlik | (dahil) | `79538e9` |
| live_session IDOR ownership checks | Guvenlik cezasi | (dahil) | `79538e9` |
| seed_mvp_data hardcoded password -> env var | Guvenlik | (dahil) | `79538e9` |
| konu_map -> _KONU_MAP (F821 fix) | Algoritma | (dahil) | `79538e9` |
| nginx CSP guclendirme | Guvenlik | (dahil) | `79538e9` |
| Dead code cleanup (14 hook, 9 model, 5 API/service) | main.py orphans | 2 -> 4 | `be65c75` |
| is_active filtresi | Veri butunlugu | (dahil) | Onceki |
| Orphan import cleanup (main.py) | main.py -> app/api/ | 2 -> 4 | Sprint |

### 1.3 Metodoloji

3 paralel Opus agent, her biri farkli perspektiften analiz yapti:

- **Performans Muhendisi**: Latency, throughput, DB query count, cache hit orani, index analizi
- **Bakim Muhendisi**: Teknik borc, dependency chain, wrapper karmasikligi, test coverage, import bloat
- **Maliyet/ROI Analisti**: Saat basina skor artisi, minimum effort/maksimum etki, maliyet-fayda

Her agent `docs/audits/2026-03-29_kapsamli-baglanti-sagligi-raporu.md`, onceki brainstorm v1 ve ilgili kaynak dosyalari okudu.

---

## 2. Guncel Skor Tablosu (Post-Fix)

| # | Baglanti Zinciri | Durum | Onceki Skor | Guncel Skor | Degisiklik Nedeni |
|---|------------------|-------|------------|-------------|-------------------|
| 1 | Frontend Auth -> Backend Auth | SAGLAM | 9/10 | 9/10 | Degisiklik yok |
| 2 | Frontend Exam -> Backend Sinav | CALISIYOR | 7/10 | 7/10 | examService 1 yanlis path hala var |
| 3 | Frontend LP -> Backend LP v2 (facade) | KOPUK | 3/10 | 3/10 | Facade hala TODO stub |
| 4 | Frontend LP -> Backend LP Daily | CALISIYOR | 6/10 | 8/10 | v2 field'lar + /status fetch eklendi |
| 5 | LP v2 <-> LP Daily | KISMEN | 0/10 | 5/10 | Ghost table bridge (student_abilities) |
| 6 | Frontend Gamification -> Backend + Event Chain | KISMEN | 2/10 | 4/10 | Backend wiring done, frontend UI eksik |
| 7 | Frontend Reports -> Backend | BELIRSIZ | 0/10 | 3/10 | URL fix yapildi, backend dogrulanmadi! |
| 8 | Frontend Recommendations -> Backend | KOPUK | 1/10 | 1/10 | Hala %100 mock data |
| 9 | Frontend Admin -> Backend | KISMEN | 5/10 | 5/10 | Degisiklik yok |
| 10 | Frontend Parent -> Backend | KISMEN | 5/10 | 5/10 | 4 endpoint hala backend'de yok |
| 11 | Frontend Chat -> Backend | KISMEN | 6/10 | 6/10 | Bionic-reading hala yok |
| 12 | record_answer Pipeline | CALISIYOR | 7/10 | 7/10 | FSRS reps/lapses hala bozuk |
| 13 | Blackboard -> Subscribers | KISMEN | 5/10 | 5/10 | Sync DB riski devam ediyor |
| 14 | Frontend Video -> Backend YouTube | SAGLAM | 9/10 | 9/10 | Degisiklik yok |
| 15 | Frontend AI Chat -> Backend | SAGLAM | 8/10 | 8/10 | Degisiklik yok |
| 16 | Backend -> Orchestrator | DORMANT | 1/10 | 1/10 | %94 dormant (kasitli, dogru) |
| 17 | main.py -> app/api/ | KISMEN | 2/10 | 4/10 | Orphan import cleanup + dead code |

### 2.1 Skor Hesaplama

**Ham ortalama:** (9+7+3+8+5+4+3+1+5+5+6+7+5+9+8+1+4) / 17 = 90/17 = **5.29**

**Guvenlik cezasi:** Onceki raporda -0.7 uygulanmisti (live_session 14 IDOR, main.py crash riski). Bu sprint'te:
- live_session IDOR fix edildi (9 endpoint'e ownership check — 4 host-only, 5 participant)
- Auth enforcement (27 endpoint'e Depends(get_current_user))
- main.py orphan import'lar temizlendi
- **Ceza kaldirildi:** 0

**Belirsizlik marji:** Reports backend dogrulanmadigi icin -0.18 (Reports 3 yerine 0 olursa 87/17 = 5.12)

**Sonuc:** **5.1 (en kotu, Reports 404) — 5.3 (gercekci)**

### 2.2 Skor Degisim Ozeti

```
Baslangic (28 Mart):                    3.8 / 10
  (onceki ham: 76/17=4.47, ceza: -0.70, sonuc: 3.77 ≈ 3.8)

  + Ghost table bridge (LP v2<->Daily): +5/17 = +0.29
  + Guvenlik cezasi kaldirildi:                 +0.70
  + Gamification wiring (2->4):         +2/17 = +0.12
  + LP Daily v2 field'lar (6->8):       +2/17 = +0.12
  + Reports URL fix (0->3):             +3/17 = +0.18 (dogrulanmadi!)
  + Dead code / orphan cleanup (2->4):  +2/17 = +0.12
                                        --------
  Toplam artis:                         +1.53
  3.8 + 1.53 =                          5.33

Dogrulama (tablo bazli):
  Yeni ham: 90/17 = 5.29 (ceza: 0)
  Fark: yuvarlama kaynakli (~0.04)

Guncel tahmini:                         5.1 (Reports 404) — 5.3 (gercekci)
```

---

## 3. Top 5 Aksiyon (Kalan, Etki Sirali)

| # | Aksiyon | Aciklama | Etki | Effort | Tahmini Skor Etkisi | Oneren Perspektifler |
|---|---------|----------|------|--------|---------------------|---------------------|
| 1 | **Recommendation mock -> daily-plan + YouTube adapter** | `recommendationService` her zaman sahte veri donuyor. Mevcut `/api/v1/daily-plan` ciktisini + YouTube search sonuclarini recommendation format'ina map'leyen thin adapter yaz. Yeni backend endpoint gerektirmez, mevcut iki API kaynagini birlestir. | 4/5 | 4-5 saat | Rec: 1->5 (+0.24) | ROI, Performans |
| 2 | **LP v2 facade'a daily summary inject** | Facade `get_student_path` (`backend/agents/learning_path/facade.py:263`) hala TODO stub (skor 3/10). Fix: `facade.py` icinde `LearningPathOrchestrator.get_daily_plan()` cagirarak theta/ZPD/prereq bilgisini path response'una ekle. Frontend'de `useLearningPath.ts` hook'u bu veriyi zaten kabul ediyor. 0 ek DB call — orchestrator'un mevcut ciktisini wrap et. | 3/5 | 2-3 saat | Facade: 3->6 (+0.18) | ROI, Bakim |
| 3 | **FSRS composite index + user_item_fsrs health metric** | `user_item_fsrs(user_id, due_date, state)` composite index yok — LP her yuklendiginde full table scan. Ayrica tablo bos olabilir (hicbir ogrenci FSRS review yapmadiysa), pekistirme sessizce devre disi kalir. Index + `COUNT(*) > 0` health assertion ekle. | 4/5 | 1 saat | Performans garantisi (skor dolayili) | Performans |
| 4 | **parentService 4 eksik endpoint'e graceful fallback** | PDF rapor, bulk islem, onay talebi, detayli istatistik endpoint'leri backend'de implement edilmemis. Frontend'de 404 catch + "Yakin zamanda eklenecek" placeholder donmesi. | 2/5 | 1 saat | Parent: 5->7 (+0.12) | ROI, Bakim |
| 5 | **Orchestrator raw SQL integration test** | `_fetch_thetas_with_se` artik ORM ile `student_abilities` tablosunu kullaniyor ama diger orchestrator fonksiyonlarinda `text(...)` raw SQL var. Schema degisirse compile-time hata VERMEZ. En az 1 integration test zorunlu. | 5/5 | 2 saat | Regresyon onleme (skor koruma) | Bakim, Performans |

**Toplam potansiyel:** +0.54 direkt skor artisi (5.3 -> 5.8) + performans/regresyon garantisi (#3, #5)

**NOT:** 6.0 hedefine ulasmak icin bu 5 aksiyona EK olarak Gamification UI entegrasyonu (4->6, +0.12) ve/veya Exam path fix (7->8, +0.06) gibi ek calisma gerekli.

**Saat basina skor artisi (ROI) sirasi:** #4 (0.12/saat) > #2 (0.07/saat) > #1 (0.05/saat). Etki sirasi farkli: #1 > #2 > #3 > #4 > #5.

**Uygulama sirasi:** #3 (1 saat, bagimsiz) -> #4 (1 saat, bagimsiz) -> #2 (2-3 saat, facade) -> #1 (4-5 saat, recommendation) -> #5 (2 saat, test)

---

## 4. Konsensus (3 Perspektif Hemfikir)

### 4.1 Tam Konsensus (3/3)

1. **Orchestrator canlandirma DEGMEZ**
   - Performans: "35+ yeni DB query, cache invalidation karmasikligi 5x artar"
   - Bakim: "24 dormant modul aktive etmek bakim maliyetini 5x artirir"
   - ROI: "Saat basina skor artisi ~0, effort/etki orani en kotu"
   - **Karar:** %94 dormant = dogru durum. Canlandirma YAPILMAYACAK.

2. **LP facade TODO stub en buyuk teknik borc**
   - Performans: "In-memory cache multi-worker'da tutarsiz, Redis L1'e tasi"
   - Bakim: "Yari-canli stub, yeni gelistirici calisiyor sanir — deprecate veya delege et"
   - ROI: "Daily summary inject ile 0 DB call, 2-3 saatte facade 3->6"
   - **Karar:** Once daily inject (kolay, 2-3 saat), Redis L1 sonraki iterasyonda.

3. **Recommendation mock sessizce gizli — kullanici guveni riski**
   - Performans: "Orchestrator ciktisini adapter'la"
   - Bakim: "UI'da mock etiketi yok, kullanici gercek oneri aldigini saniyor"
   - ROI: "Daily-plan + YouTube adapter, yeni backend gerektirmez"
   - **Karar:** Ya mock etiketi ekle (gecici, 30dk) ya da gercek veriye bagla (kalici, 4-5 saat).

### 4.2 Cogunluk Konsensus (2/3)

4. **Reports backend dogrulanmadi** (ROI + Bakim)
   - URL fix yapildi ama 7 endpoint'in calisip calismadigini kimse test etmedi
   - Skor tahmini 0.18 puan dusebilir
   - **Karar:** Docker up + curl ile 7 endpoint'i test et (15 dk).

5. **Frontend-only fix'ler kalici cozum DEGIL** (Bakim + ROI)
   - parentService graceful fallback gecici — backend endpoint yazilmali
   - Reports URL fix gecici — backend implement edilmeli
   - **Karar:** Gecici fix'leri JIRA/issue olarak izle, ayri session'da backend yaz.

---

## 5. Catismalar

| Konu | Taraf A | Taraf B | Analiz | Onerilen Karar |
|------|---------|---------|--------|----------------|
| **Facade: Redis L1 mi, daily inject mi?** | Performans: Redis L1 ile multi-worker tutarlilik + restart guvenli. Circuit breaker sart. | ROI: Daily summary inject 0 infra, 2-3 saat, hemen uygulanabilir. | Redis L1 ideal ama infra gerektirir (Redis zaten var, ama serialize/deserialize + TTL + circuit breaker). Daily inject sifir risk. | **Once daily inject (2-3 saat), Redis L1 sonraki iterasyon (4-5 saat)** |
| **FSRS index: simdi mi, sonra mi?** | Performans: Simdi ekle, `CREATE INDEX CONCURRENTLY` ile risk yok. Tablo buyuyunce migration cok daha zor. | Bakim: Tablo henuz kucuk, kullanici az, gereksiz optimizasyon. | Tablo kucukken index olusturmak milisaniye surer. Buyuyunce saatler alabilir ve downtime riski olusur. | **Simdi ekle (1 saat, sifir risk)** |
| **Recommendation: adapter mi, yeni backend mi?** | ROI: Mevcut daily-plan + YouTube API'yi adapter ile recommendation format'ina map'le. Yeni endpoint gerektirmez. | Performans: Orchestrator ciktisini adapter'la — daha zengin veri, oncelik skoru dahil. | Her iki kaynak da mevcut ve calisiyor. Adapter her ikisini de tuketebilir. | **Adapter + YouTube mix birlesimi (her iki kaynak)** |
| **Bionic-reading: client mi, backend mi?** | Bakim: Client-side regex (2 saat, %80 cozum). Backend gerektirmez. | Performans: Backend endpoint (tam cozum, Turkce hece kurallari dogru). | Client-side yeterli baslangic. Turkce hece riski dusuk (kelime ilk yarisi bold, hece siniri degil). | **Client-side once (2 saat), backend sonra (ihtiyac olursa)** |

---

## 6. Perspektif Detaylari

### 6.1 Performans Muhendisi

**Analiz edilen dosyalar:**
- `docs/audits/2026-03-29_kapsamli-baglanti-sagligi-raporu.md`
- `docs/brainstorms/2026-03-29_connectivity-score-6plus-strategy.md`
- `backend/app/services/learning_path_orchestrator.py` (satir 510-554, `_fetch_thetas_with_se` + `_fetch_fsrs_due_counts`)

**Oneriler:**

1. **`_fetch_fsrs_due_counts` icin composite index**
   - `user_item_fsrs` tablosunda `(user_id, due_date, state)` composite index yok
   - LP sayfasi her yuklendiginde bu sorgu calisir — full table scan
   - Ogrenci sayisi 1K+ olunca 50ms -> 2s+ cikar
   - Fix: `CREATE INDEX CONCURRENTLY idx_fsrs_user_due_state ON user_item_fsrs(user_id, due_date, state)`
   - **Etki:** 4/5 | **Zorluk:** Kolay | **Risk:** `CONCURRENTLY` kullanilmazsa tablo kilitlenir

2. **LP orchestrator N+1 sorgu problemi**
   - `_fetch_thetas_with_se` (1 query) + `_fetch_fsrs_due_counts` (1 query) + `_fetch_topic_row` (konu basina 1 query)
   - TYT icin 8 ders x topic lookup = ~10+ DB roundtrip
   - Tek CTE/JOIN ile 1-2 sorguya indirilebilir
   - **Etki:** 3/5 (simdilik kullanici az, 100+ concurrent'ta bottleneck) | **Zorluk:** Orta | **Risk:** ORM'den raw SQL'e geciste Turkce NFC riski

3. **Facade in-memory cache -> Redis L1**
   - `facade.py` `get_student_path` in-memory dict kullaniyor
   - Gunicorn multi-worker'da ayni ogrenci farkli worker'dan farkli path gorebilir
   - Redis L1 (TTL=60s) ile tek kaynak saglanir, restart'ta veri kaybolmaz
   - **Etki:** 5/5 | **Zorluk:** Orta | **Risk:** Redis down = LP kirilir; circuit breaker ZORUNLU

**Kor nokta:** `user_item_fsrs` tablosu bos olabilir. Hicbir ogrenci FSRS review yapmadiysa, `_fetch_fsrs_due_counts` her zaman bos donecek ve LP orchestrator pekistirme onerileri sessizce devre disi kalir. `SELECT COUNT(*) FROM user_item_fsrs` > 0 assertion'i health metric olarak ekle.

**Uyari:** Orchestrator'un 24 dormant modulunu performans icin canlandirMAyin. Satir 519-529'daki `_fetch_thetas_with_se` zaten ORM ile calisiyor ve yeterli. Dormant modulleri aktive etmek 35+ yeni DB query ekler, cache invalidation karmasikligi 5x artar, olculebilir skor artisi ~0.

### 6.2 Bakim Muhendisi

**Analiz edilen dosyalar:**
- `docs/audits/2026-03-29_kapsamli-baglanti-sagligi-raporu.md`
- `docs/brainstorms/2026-03-29_connectivity-score-6plus-strategy.md`
- `frontend/src/pages/ModernLearningPathPage.tsx` (ilk 80 satir — import analizi)

**Oneriler:**

1. **LP v2 facade TODO stub'ini temizle veya deprecate et**
   - Facade `get_student_path` backend'de TODO stub olarak duruyor, frontend kismen bagli
   - "Yari-canli" durum en tehlikeli teknik borc tipi: yeni gelistirici facade'i calisiyor sanip uzerine kod yazar, runtime'da sessizce bos doner
   - Ya daily endpoint'e delege et (brainstorm Top 5 #2 ile uyumlu), ya da acikca `@deprecated` isaretle ve frontend'den referansini kes
   - **Etki:** 4/5 | **Zorluk:** Orta | **Risk:** Facade'i silen PR, import chain'deki 12+ dosyayi kirar — `deprecation-guard.md` kontrol listesi ZORUNLU

2. **ModernLearningPathPage import/dependency bloat kontrolu**
   - Dosyanin ilk 32 satiri 20+ import iceriyor: `LeaguePanel`, `DuelMode`, `ProductiveFailureFlow`, `StudyPlannerWidget`, `ErrorClusterCard`...
   - Bunlarin cogu Session 102-111'de eklenen ama henuz backend'e baglanmamis UI bilesenleri
   - Kullanilmayan veya mock-backed import'lar bundle size ve cognitive load artiriyor
   - `React.lazy` ile lazy boundary'e tasinmali
   - **Etki:** 3/5 | **Zorluk:** Kolay | **Risk:** Lazy boundary yanlis konulursa Suspense fallback UX bozar

3. **Orchestrator raw SQL bagimliligi integration test'e bagla**
   - `user_theta` ghost table fix yapildi, `_fetch_thetas_with_se` artik ORM ile `StudentAbility` kullaniyor
   - Ama diger fonksiyonlarda (`_fetch_fsrs_due_counts`, `_fetch_topic_row`) hala `text(...)` raw SQL var
   - Schema degisikliklerinde compile-time hata VERMEZ — sessizce bos donebilir
   - En az 1 integration test yazilmali (`student_abilities` + `user_item_fsrs` tablolarina karsi)
   - **Etki:** 5/5 | **Zorluk:** Orta | **Risk:** Test ortaminda DB schema senkronizasyonu (alembic head) atlanirsa false-green

**Kor nokta:** `recommendationService` singleton her zaman mock data donuyor ama UI'da "mock" etiketi yok. Kullanici gercek oneri aldigini saniyor. Bu bir guven sorunu — teknik borctan once cozulmeli.

**Uyari:** Facade ve orchestrator duzeltmeleri ayni session'da yapilirsa, her ikisi de LP v2 import chain'ini etkiler. Sirali yapin, paralel degil — aksi halde merge conflict ve circular dependency riski yuksek.

### 6.3 Maliyet/ROI Analisti

**Analiz edilen dosyalar:**
- `docs/brainstorms/2026-03-29_connectivity-score-6plus-strategy.md`
- `docs/audits/2026-03-29_kapsamli-baglanti-sagligi-raporu.md`
- `frontend/src/services/advancedReportsService.ts` (271 satir, 7 method)

**Oneriler:**

1. **Recommendation mock -> daily-plan + YouTube adapter**
   - `recommendationService` her zaman sahte veri donuyor
   - Mevcut `/api/v1/daily-plan` ciktisini + YouTube search sonuclarini recommendation format'ina map'leyen thin adapter yaz
   - Yeni backend endpoint gerektirmez — mevcut iki API kaynagini frontend'de birlestir
   - **Etki:** 4/5 | **Zorluk:** Orta | **Skor etkisi:** Recommendations 1->5 (+0.24) | **ROI:** 0.05 puan/saat

2. **LP v2 facade'a daily summary inject et**
   - Facade `get_student_path` hala TODO stub (skor 3/10)
   - Mevcut daily endpoint ciktisini (theta, ZPD, prereq) facade response'una ekle
   - 0 DB call, 1 ek HTTP istegiyle mevcut endpoint ciktisini wrap et
   - **Etki:** 3/5 | **Zorluk:** Kolay | **Skor etkisi:** LP facade 3->6 (+0.18) | **ROI:** 0.07 puan/saat

3. **parentService 4 eksik endpoint'e graceful fallback**
   - PDF rapor, bulk islem, onay talebi, detayli istatistik endpoint'leri backend'de yok
   - Frontend'de 404 catch + "Yakin zamanda eklenecek" placeholder donmesi
   - **Etki:** 2/5 | **Zorluk:** Kolay | **Skor etkisi:** Parent 5->7 (+0.12) | **ROI:** 0.12 puan/saat

**Kor nokta:** `advancedReportsService.ts` URL'leri duzeltilmis (`/api/v1/reports/...`) ama bu endpoint'lerin backend'de gercekten implement edilip edilmedigini KIMSE dogrulamadi. 7 method var:
- `GET /api/v1/reports/exam/{id}/advanced`
- `GET /api/v1/reports/exam/{id}/irt-analysis`
- `GET /api/v1/reports/exam/{id}/zpd-recommendations`
- `GET /api/v1/reports/exam/{id}/learning-style-analysis`
- `GET /api/v1/reports/exam/{id}/osym-ets-comparison`
- `POST /api/v1/reports/exam/{id}/generate-pdf`
- `GET /api/v1/reports/download/{filename}`

Hepsi 404 donuyor olabilir — Reports skoru 0->3 degil 0->0 kalir ve tahmini skor 0.18 duser.

**Uyari:** Recommendation mock'unu degistirirken, mevcut mock'a bagli frontend component'ler (response shape) kirilabilir. Adapter'in mock ile AYNI INTERFACE'i dondurmesi zorunlu, yoksa UI crash olur.

---

## 7. Kor Noktalar (Birlesmis Liste)

| # | Kor Nokta | Kapsam | Tespit Eden | Oncelik |
|---|-----------|--------|-------------|---------|
| 1 | **Reports backend dogrulanmadi** | advancedReportsService.ts 7 method — backend'de implement edilmis mi bilinmiyor. URL fix yapildi ama endpoint'ler 404 donuyor olabilir. | ROI Analisti | P0 — 15 dk dogrulama |
| 2 | **user_item_fsrs bos olabilir** | Hicbir ogrenci FSRS review yapmadiysa, pekistirme onerileri sessizce devre disi. Orchestrator FSRS'i "sifir vadesiz" yorumlar. | Performans | P1 — health metric ekle |
| 3 | **Recommendation mock gizli** | UI'da mock oldugu belli degil. Kullanici gercek kisisel oneri aldigini saniyorken statik sahte veri goruyor. Guven riski. | Bakim, ROI | P1 — mock etiketi veya gercek veri |
| 4 | **Facade multi-worker tutarsizlik** | Gunicorn worker'lar arasi in-memory cache paylasimi YOK. Ayni ogrenci farkli worker'dan farkli ogrenme yolu gorebilir. | Performans | P2 — Redis L1 ile cozulur |
| 5 | **ModernLearningPathPage 20+ import** | Cogu Session 102-111'de eklenen mock-backed UI bilesenleri. Bundle size + cognitive load artiriyor. | Bakim | P2 — React.lazy |
| 6 | **parentService backend SIFIR** | 4 endpoint'in sadece frontend'de degil, backend'de de implement edilmesi lazim. Graceful fallback gecici cozum. | Bakim (v1) | P2 — ayri session |

---

## 8. Uyarilar (Birlesmis Liste)

| # | Uyari | Kaynak | Neden |
|---|-------|--------|-------|
| 1 | Orchestrator 24 dormant modulu canlandirMAyin | 3/3 Perspektif | 5x bakim + 35+ DB query, skor artisi ~0 |
| 2 | Facade + orchestrator fix'leri SIRALI yapin | Bakim | Her ikisi de LP v2 import chain'ini etkiler, paralelde merge conflict |
| 3 | Recommendation adapter AYNI INTERFACE dondurmeli | ROI | Mock'a bagli component'ler response shape degisirse crash olur |
| 4 | Reports backend'i ONCE test edin | ROI | 7 endpoint 404 olabilir, skor tahmini 0.18 kayar |
| 5 | Paralel API call'a dikkat | ROI (v1) | Ayni sayfada 2+ yeni fetch = UX latency riski |
| 6 | Rush commit yapmayin | Bakim | NFC normalizasyon, Turkce hece, TypeScript strict mode riskleri |
| 7 | Frontend-only fix'ler kalici cozum DEGIL | Bakim, ROI | Backend eksiklikleri ayri session'da ele alinmali |

---

## 9. Skor Projeksiyon Tablosu

### 9.1 Aksiyon Bazli Projeksiyon

Hesaplama: Mevcut ham 90/17=5.29. Her aksiyon zincir skorunu arttirir, artis = delta/17.

| Senaryo | Aksiyonlar | Effort | Tahmini Skor | Hesaplama |
|---------|-----------|--------|-------------|-----------|
| **Mevcut** | Sprint fix'leri tamamlandi | 0 saat | **~5.3** | 90/17=5.29, Reports dogrulanmazsa 87/17=5.12 |
| **Quick Wins** | #4 (parent 5->7) + #2 (facade 3->6) | 3-4 saat | **~5.6** | (90+2+3)/17=95/17=5.59 |
| **Hedef** | + #1 (recommendation 1->5) | 7-9 saat | **~5.8** | (95+4)/17=99/17=5.82 |
| **Genisletilmis** | + Gamification UI (4->6) + Exam fix (7->8) | 12-15 saat | **~6.0** | (99+2+1)/17=102/17=6.0 |
| **Agresif** | + Reports backend (3->7) + Chat bionic (6->8) | 20-25 saat | **~6.5** | (102+4+2)/17=108/17=6.35 |
| **Maksimum** | + Orchestrator (1->4) + Blackboard (5->7) + FSRS fix (7->8) | 35+ saat | **~7.0** | (108+3+2+1)/17=114/17=6.71 |

### 9.2 Zincir Bazli Projeksiyon (17 zincir)

| # | Zincir | Mevcut | Quick Wins | Hedef | Genisletilmis | Agresif | Maksimum |
|---|--------|--------|-----------|-------|--------------|---------|----------|
| 1 | Auth | 9 | 9 | 9 | 9 | 9 | 9 |
| 2 | Exam | 7 | 7 | 7 | **8** | 8 | 8 |
| 3 | LP v2 facade | 3 | **6** | 6 | 6 | 6 | 6 |
| 4 | LP Daily | 8 | 8 | 8 | 8 | 8 | 8 |
| 5 | LP v2<->Daily | 5 | 5 | 5 | 5 | 5 | 5 |
| 6 | Gamification | 4 | 4 | 4 | **6** | 6 | 6 |
| 7 | Reports | 3 | 3 | 3 | 3 | **7** | 7 |
| 8 | Recommendations | 1 | 1 | **5** | 5 | 5 | 5 |
| 9 | Admin | 5 | 5 | 5 | 5 | 5 | 5 |
| 10 | Parent | 5 | **7** | 7 | 7 | 7 | 7 |
| 11 | Chat | 6 | 6 | 6 | 6 | **8** | 8 |
| 12 | record_answer | 7 | 7 | 7 | 7 | 7 | **8** |
| 13 | Blackboard | 5 | 5 | 5 | 5 | 5 | **7** |
| 14 | Video | 9 | 9 | 9 | 9 | 9 | 9 |
| 15 | AI Chat | 8 | 8 | 8 | 8 | 8 | 8 |
| 16 | Orchestrator | 1 | 1 | 1 | 1 | 1 | **4** |
| 17 | main.py | 4 | 4 | 4 | 4 | 4 | 4 |
| | **TOPLAM** | **90** | **95** | **99** | **102** | **108** | **114** |
| | **ORTALAMA** | **5.29** | **5.59** | **5.82** | **6.00** | **6.35** | **6.71** |

### 9.3 Zaman-Skor Grafigi

```
Skor
7.0 |                                                    * Maksimum (35+ saat)
6.5 |                                    * Agresif (20-25 saat)
6.0 |                      * Genisletilmis (12-15 saat) <-- HEDEF
5.8 |              * Hedef (7-9 saat)
5.6 |       * Quick Wins (3-4 saat)
5.3 | * Mevcut
5.1 | (en kotu — Reports 404)
    |_____|_____|_____|_____|_____|_____|_____|
    0     5    10    15    20    25    30    35 saat
```

**Onemli:** 6.0 hedefine ulasmak icin Top 5 aksiyonlar YETMEZ. Gamification UI entegrasyonu ve Exam path fix gibi ek calisma da gerekli (Genisletilmis senaryo).

---

## 10. Onceki Brainstorm (v1) ile Karsilastirma

| v1 Aksiyon | v1 Oncelik | Durum | v2 Notlari |
|-----------|-----------|-------|------------|
| LP Daily endpoint'ini LP v2 sayfasina wire'la | #1 | YAPILDI (Session 119) | +0.29 gerceklesti |
| DailyPlanPage v2 field'lar ekle | #2 | YAPILDI (Session 119) | +0.12 gerceklesti |
| Recommendation mock'u gercek veriye bagla | #3 | BEKLIYOR | v2'de #1, degisiklik yok |
| parentService 404 graceful fallback | #4 | BEKLIYOR | v2'de #4, degisiklik yok |
| chatService bionic-reading client-side | #5 | BEKLIYOR | v2'de oncelik dusuruldu (dusuk ROI) |
| user_theta ghost table fix | Kor nokta | YAPILDI (3 dosya migrate) | En kritik fix, +0.29 skor etkisi |
| Orchestrator canlandirma | Anti-pattern | YAPILMAYACAK | 3/3 perspektif hemfikir: degmez |

### Yeni Aksiyonlar (v2'de eklenen)

| Aksiyon | v2 Oncelik | Kaynak | v1'de Neden Yoktu |
|---------|-----------|--------|-------------------|
| FSRS composite index + health metric | #3 | Performans | Performans perspektifi v1'de yoktu |
| Orchestrator raw SQL integration test | #5 | Bakim | Ghost table fix sonrasi ortaya cikti |
| LP facade daily inject (v1'de "merge" olarak onerilmisti) | #2 | ROI | v1'de daha agresif "merge" onerildi, v2 daha pragmatik |

---

## 11. Uygulama Yol Haritasi

### Faz 1: Dogrulama (30 dk)
- [ ] Reports backend 7 endpoint'i curl ile test et
- [ ] Skor tahminini guncelle (Reports 3 mi 0 mi?)
- [ ] `user_item_fsrs` tablosunda veri var mi kontrol et

### Faz 2: Quick Wins (3-4 saat)
- [ ] FSRS composite index migration yaz (#3)
- [ ] LP v2 facade'a daily summary inject (#2)
- [ ] parentService graceful fallback (#4)

### Faz 3: Ana Aksiyon (4-5 saat)
- [ ] Recommendation adapter yaz (#1)
- [ ] Mock interface uyumlulugunu dogrula
- [ ] Frontend component'leri test et

### Faz 4: Kalite Guvenceleri (2 saat)
- [ ] Orchestrator integration test yaz (#5)
- [ ] ModernLearningPathPage lazy import refactor
- [ ] Full regression test

### Faz 5: 6.0 Hedefi (ayni veya sonraki session — ZORUNLU)
- [ ] Gamification UI entegrasyonu — badge/XP gosterimi (4->6, +0.12, **6.0 hedefi icin GEREKLI**)
- [ ] Exam path fix — examService.ts yanlis path duzeltme (7->8, +0.06)

### Faz 6: Gelecek Iterasyon (ayri session, 6.5 hedefi)
- [ ] Facade Redis L1 migration
- [ ] Reports backend implement (3->7, +0.24)
- [ ] parentService 4 backend endpoint implement (kalici cozum)
- [ ] Bionic-reading backend (gerekirse)
- [ ] FSRS reps/lapses fix (record_answer pipeline, 7->8, +0.06)

---

## 12. Risk Matrisi

| Risk | Olasilik | Etki | Azaltma |
|------|----------|------|---------|
| Reports backend 404 | Yuksek | Skor -0.18 | Faz 1'de dogrula |
| Recommendation adapter interface uyumsuzluk | Orta | UI crash | Mock interface'i birebir kopyala |
| Facade import chain kirilmasi | Orta | 12+ dosya etkilenir | deprecation-guard.md kontrol listesi |
| FSRS tablo bos, pekistirme devre disi | Yuksek | Sessiz ozellik kaybi | Health metric + assertion |
| Redis down -> LP kirilir | Dusuk | LP tamamen erisilemez | Circuit breaker + in-memory fallback |
| N+1 query bottleneck (100+ concurrent) | Dusuk (simdilik) | LP 2s+ yuklenme | CTE/JOIN refactor |

---

## 13. Basari Kriterleri

| Kriter | Hedef | Olcum |
|--------|-------|-------|
| Connectivity skoru | >= 6.0 (102/17) | Audit raporu tekrari |
| Reports backend durumu | Dogrulanmis | curl 7 endpoint |
| Recommendation gercek veri | Mock kaldirilmis | Frontend test |
| LP facade TODO | Daily inject veya deprecated | Kod inceleme |
| FSRS index | Olusturulmus | `\di user_item_fsrs*` |
| Integration test | >= 1 orchestrator test | pytest -k orchestrator |
| Regresyon | 0 yeni bug | Full test suite PASS |

---

## Kaynaklar

- Audit raporu: `docs/audits/2026-03-29_kapsamli-baglanti-sagligi-raporu.md`
- Onceki brainstorm (v1): `docs/brainstorms/2026-03-29_connectivity-score-6plus-strategy.md`
- Backend kaynak: `backend/app/services/learning_path_orchestrator.py`
- Frontend kaynak: `frontend/src/pages/ModernLearningPathPage.tsx`
- Reports service: `frontend/src/services/advancedReportsService.ts`
- Agent ciktilari: 3 paralel Opus agent (Performans, Bakim, ROI)
