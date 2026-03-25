# Brainstorm: KIRO2 Proje Mimarisi v2 (Guncel Durum)
Tarih: 2026-03-23 | Domain: architecture | Perspektifler: Performans, Bakim, Maliyet

## TL;DR
Session 107-109 ile router standardizasyonu ve algoritma pipeline (BKT->IRT->FSRS->ZPD) baglandi — ancak `record_answer()` icindeki 4 try/except `except Exception` ile susturuluyor, 100K kullanicida binlerce bozuk ogrenci profili demek. En acil: silent failure'lari error seviyesine cikarmak + record_answer'i tek transaction'a almak. Mimari olgunlasti ama teknik borc (models/__init__.py kaos, 11 compose dosyasi, 17 kullanilmayan algoritma) ayni seviyede.

## Onceki Brainstorm'dan (20 Mart) Degisimler

| Sorun (20 Mart) | Durum (23 Mart) | Not |
|------------------|-----------------|-----|
| 4 algoritma silo | DUZELTILDI | Session 108: BKT->IRT->FSRS pipeline |
| IRT kalibre degil (difficulty=0.0) | DUZELTILDI | 64,205 soru bootstrap |
| Router prefix daginilik | DUZELTILDI | Session 107: 33 backend + 75 frontend |
| active_sessions in-memory | KISMEN | L1 cache + Redis L2, ama temizleme yok |
| Core "junk drawer" (186 dosya) | AYNI | Hicbir degisiklik |
| models/__init__.py kaos | AYNI | Pydantic+SQLAlchemy karisik, alias'lar |
| 173 servis dosyasi | AYNI | Hicbir temizlik |
| Modern* wrapper (27 bos) | AYNI | Hicbir temizlik |
| Test coverage ~18% | AYNI | Hicbir ilerleme |

## Top 5 Aksiyon

| # | Aksiyon | Etki | Zorluk | Kaynak |
|---|---------|------|--------|--------|
| 1 | **record_answer() silent failure'lari logger.error + metric counter'a yukselt** — 4 `except Exception` susturuluyor, 100K'da binlerce bozuk profil | 5/5 | Kolay | Maliyet + Performans |
| 2 | **record_answer() DB islemlerini tek transaction'a al** — 4 ayri flush -> 1 commit, DB baglanti suresi ~%60 azalir | 4/5 | Kolay | Maliyet |
| 3 | **_analyze_performance bulk UPDATE** — for dongusunde 120 ayri UPDATE -> tek CASE WHEN bulk | 4/5 | Kolay | Performans |
| 4 | **Docker Compose 11 -> 3** — mvp + dev + test, geri kalan docker/archive/ | 3/5 | Kolay | Maliyet + Bakim |
| 5 | **VersionRedirectMiddleware erken cikis** — `/api/v1/` prefix'i icin 32 kural dongusu atla | 2/5 | Kolay | Performans |

## Konsensus (2+ perspektif hemfikir)

1. **record_answer() pipeline riski** — Maliyet: silent failure binlerce profil bozar; Performans: 4 ayri DB flush gereksiz round-trip. 2/3 perspektif acil oncelik diyor.
2. **Docker Compose fazlaligi** — Maliyet: 11 dosyada hangi deploy aktif belirsiz; Bakim: yanlis compose ile gereksiz servisler aktive olur. 2/3 perspektif.
3. **models/__init__.py en riskli dosya** — Bakim: Pydantic+SQLAlchemy karisik, anlamsiz alias'lar; Maliyet: her yeni model dosyasi kaosu buyutuyor. Ancak duzeltmek 450+ test kirar — dikkatli ilerlenmeli.
4. **Kullanilmayan kod/servis temizligi** — Maliyet: 17 algoritma dosyasi Docker image sisiyor; Bakim: router_loader silent failure. 2/3 perspektif.

## Catismalar

| Konu | Taraf A | Taraf B | Onerilen Karar |
|------|---------|---------|----------------|
| record_answer hata yonetimi | Performans: try/except kalsin, error loglama yeter | Maliyet: partial write riski var, tek transaction ZORUNLU | Maliyet hakli — tek transaction + error counter |
| Redis AOF | Maliyet: AOF kapatin, saatlik RDB snapshot yeter | Performans: session kaybi 1 saat kabul edilemez | Hibrit — AOF everysec (varsayilan), session icin kabul edilebilir |
| models/__init__.py yeniden yapilandirma | Bakim: parcali temizlik, alias'lari deprecated isaretle | Performans: dokunmayin, 450+ test kirar | Bakim hakli — ama adim adim, Session 17 dersi (toplu degisiklik yasak) |

## Perspektif Detaylari

### Performans Mimari

**1. _select_questions N+1 -> tek sorgu**
Her konu icin ayri SELECT, TYT=9 konu=18 sorgu. Tek `SELECT id, subject_area` + Python gruplama ile 1-2 sorguya inir. TTLCache sayesinde sadece ilk sinavda veya 1 saatlik TTL sonrasi calisir.
- Etki: 4/5 | Zorluk: Kolay | Risk: text filtreleri index kullanamaz, birlestirince buyur

**2. _analyze_performance loop UPDATE -> bulk**
120 soruluk TYT = 120 ayri UPDATE execute. `CASE WHEN` bulk UPDATE ile 1'e iner. `times_asked` zaten bulk pattern kullaniyor.
- Etki: 5/5 | Zorluk: Kolay | Risk: SQLAlchemy ORM ile zor, raw SQL gerekebilir

**3. VersionRedirectMiddleware erken cikis**
Modern `/api/v1/` trafigi (%90+) 32 kurali gereksiz tarayarak gecir. `if path.startswith("/api/v1/"): return` ile atla.
- Etki: 2/5 | Zorluk: Kolay | Risk: Sifir

**Kor nokta:** `active_sessions` L1 cache temizlenmiyour — expired/kesilmis oturumlar birikerek memory leak olusturur.
**Uyari:** `_select_questions`'taki `func.length()` ve `func.lower().contains()` computed column'a tasimayin — TTLCache ile zaten nadir calisiyor.

### Bakim Mimari

**1. models/__init__.py Pydantic + SQLAlchemy karisimini ayir**
SQLAlchemy ORM, Pydantic semalari ve Turkce/Ingilizce cift adli enum'lar iç ice. `Student = StudentProfile` gibi anlamsiz alias'lar mevcut.
- Etki: 5/5 | Zorluk: Orta | Risk: 450+ test dosyasindaki import yollari kirilir

**2. router_loader silent failure trap'ini duzelt**
`_load_router()` import hatalarini `logger.warning` ile yutup devam ediyor. 180 router'dan kaci gercekten yuklendi belirsiz. Endpoint sessizce 404 dondugunde kok neden bulmak saatler surebilir.
- Etki: 4/5 | Zorluk: Kolay | Risk: Yok, sadece gorunurluk

**3. dependencies.py token uretim duplikasyonunu temizle**
`create_access_token()` ve `verify_token()` hem burada hem `core/jwt_auth.py`'de var. `get_database_session = get_db` uclu alias "450+ test dosyasi" yorumuyla kilitlenmis.
- Etki: 3/5 | Zorluk: Kolay | Risk: Alias silme test kirar

**Kor nokta:** `App.tsx:452` — `<RevolutionaryDashboard studentId="demo" />` hardcoded string prod route'ta. Admin-only ama demo verisi gosteriyor, gercek veri degil.
**Uyari:** models/__init__.py'yi tek seferde yeniden yapilandirmayin — Session 17 dersi: 3 script 107 dosya bozdu.

### Maliyet Mimari

**1. record_answer() DB islemlerini tek transaction'a al**
4 ayri flush (BKT okuma, FSRS okuma, BKT yazma, FSRS yazma). 100K kullanicida DB baglanti havuzunu bogar. Tek commit'e indirilmeli.
- Etki: 4/5 | Zorluk: Kolay | Risk: FSRS ve BKT flush sirasi onemli, partial write kalabilir

**2. Docker Compose 11 -> 3**
mvp + dev + test. `docker-compose.minimal.yml`'daki HuggingFace + ChromaDB yanlis deploy ile gereksiz maliyet.
- Etki: 3/5 | Zorluk: Kolay | Risk: Sifir teknik risk

**3. Redis AOF tutarsiz kalicllik**
`--appendonly yes --save ""` — AOF her yazida disk I/O, 100K'da CPU %15-30. Session icin saatlik RDB snapshot yeterli olabilir.
- Etki: 3/5 | Zorluk: Kolay | Risk: Crash'te 1 saate kadar session kaybi

**Kor nokta:** `backend/algorithms/` 17 dosyadan cogu uretime bagli degil (`turkish_bionic_reading.py`, `cultural_adaptation_engine.py`, `multi_agent_blackboard.py`). Docker image boyutu ve build suresi sisiyor.
**Uyari:** record_answer()'daki 4 try/except `except Exception` susturuluyor. BKT/FSRS DB yazimsi sessizce basarisiz olursa ogrenci state guncellenmez — **100K'da binlerce bozuk profil, sifir alert.** `logger.error` + metric counter zorunlu.

## Kor Noktalar & Uyarilar (Birlesik)

### Kor Noktalar
1. **record_answer() silent failure** — 4 `except Exception` sessizce yutuyor, ogrenci profili bozulur (Maliyet)
2. **active_sessions L1 memory leak** — expired oturumlar temizlenmiyor (Performans)
3. **17 kullanilmayan algoritma dosyasi** — Docker image sisiyor (Maliyet)
4. **RevolutionaryDashboard hardcoded "demo"** — prod route'ta test verisi (Bakim)
5. **router_loader silent failure** — import hatasi sessizce yutulur, 404 debug zor (Bakim)

### Uyarilar
1. record_answer hatalari SUSTURMAYIN — logger.error + metric counter ZORUNLU (Maliyet)
2. models/__init__.py'yi tek seferde degistirmeyin — adim adim, Session 17 dersi (Bakim)
3. _select_questions text filtrelerini computed column'a tasimayin — TTLCache ile gereksiz (Performans)
4. Microservice'e gecmeyin — <4ms p95, monolith yeterli (20 Mart konsensus)
5. Redis AOF kapatmadan KVKK session persist gereksinimini dogrulayin (Maliyet)

## Ilerleme Ozeti (20 Mart -> 23 Mart)

- 3/9 kritik sorundan 3'u COZULDU (algoritma silo, IRT bootstrap, router prefix)
- 6/9 AYNI (core junk drawer, models kaos, 173 servis, wrapper, test coverage, dead code)
- 1 YENI kritik sorun: record_answer() silent failure (Session 108 ile geldi)
- Genel olgunluk: **MVP'ye yakin ama operasyonel guvenilirlik (observability) eksik**

---
*3 paralel perspektif, Read-based analiz, 2026-03-23*
