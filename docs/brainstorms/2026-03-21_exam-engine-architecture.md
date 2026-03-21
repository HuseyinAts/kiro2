# Brainstorm: Exam Engine Architecture
Tarih: 2026-03-21 | Domain: architecture | Perspektifler: Performans, Bakim, Maliyet

## TL;DR
Sinav motorunun en kritik sorunu **`active_sessions` in-memory dict** — horizontal scaling imkansiz, restart'ta tum aktif sinavlar kaybolur (3/3 perspektif hemfikir). `save_answer` her tiklamada SELECT+UPDATE yapiyor (upsert ile yariya iner). `sinav_motoru_service.py` tamamen dead code olarak duplikasyon yaratiyor.

## Top 5 Aksiyon

| # | Aksiyon | Etki | Zorluk | Kaynak |
|---|---------|------|--------|--------|
| 1 | **`active_sessions` dict'i Redis'e tasi** — horizontal scale + restart durability | 5/5 | Orta | 3/3 perspektif |
| 2 | **`save_answer` SELECT+UPDATE -> UPSERT** — her cevap 2 DB round-trip -> 1 | 4/5 | Kolay | Performans + Maliyet |
| 3 | **`sinav_motoru_service.py` sil** — dead code, _refactored da tamamlanmamis | 5/5 | Kolay | Bakim |
| 4 | **`_select_questions` N+1 -> batch query** — 9 konu = 18 sorgu -> 1-2 | 4/5 | Kolay | Performans |
| 5 | **Performance analysis sub-endpoint'lere cache ekle** — ayni sorgu 3x calisiyor | 3/5 | Kolay | Maliyet |

## Konsensus (2+ perspektif)

1. **`active_sessions` stateful singleton** — Performans: horizontal scale imkansiz; Bakim: restart'ta orphan session; Maliyet: tek process'e bagimlilik. Ayni sorun: process-local dict, Redis'e tasinmali.
2. **`save_answer` per-click DB write** — Performans: SELECT+UPDATE 2 round-trip; Maliyet: 120 soru x 100K = saniyede ~3,300 islem. Cozum: UPSERT veya batch flush.
3. **`sinav_motoru_service.py` dead code** — Performans: legacy motor production'da KULLANILMAMALI; Bakim: ayni sinif adi iki dosyada, import kargasasi. Silinmeli.
4. **Tekrarlayan performans analizi** — Performans: `_sonuclari_hesapla` N+1 (120 sorgu); Maliyet: 3 sub-endpoint ayni analizi cache'siz calisiyor.

## Catismalar

| Konu | Taraf A | Taraf B | Onerilen Karar |
|------|---------|---------|----------------|
| Redis session latency | Performans: ~1ms per-op ekler | Maliyet: Redis 7 zaten deployed, kabul edilebilir | Redis'e tasi — 1ms latency vs restart kaybi trade-off net |
| Batch vs per-click save | Performans: UPSERT (tek islem) | Maliyet: batch flush (30sn aralikla) | Hibrit: UPSERT + auto-save interval (zaten mevcut) |

## Perspektif Detaylari

### Performans Mimari

**1. `active_sessions` in-memory dict'i Redis'e tasi**
`OSYMExamEngine.active_sessions` (satir 138) Python dict. 100K concurrent'ta tek process'e bagimli, horizontal scale imkansiz. `get_my_exams` (sinav.py:250) tum dict'i iterate ediyor — O(n) scan.
- Etki: 5/5 | Zorluk: Orta | Risk: Migration sirasinda aktif sinav session kaybi

**2. `_select_questions` N+1 loop'unu tek sorguya indir**
Her konu icin ayri `SELECT ... ORDER BY random() LIMIT n` (osym_exam_engine.py:1092). TYT'de 9 konu = 9-18 sorgu. Ayrica `sinav_motoru_service.py:388`'de `_sonuclari_hesapla` her soru icin tek tek `soru_getir(soru_id)` — 120 soru = 120 DB sorgusu.
- Etki: 4/5 | Zorluk: Kolay | Risk: `ORDER BY random()` buyuk tablolarda yavas — `TABLESAMPLE` dusunulmeli

**3. `save_answer` SELECT+UPDATE -> UPSERT**
Her cevap icin SELECT + UPDATE/INSERT = 2 round-trip (osym_exam_engine.py:586-627). PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` ile tek islem.
- Etki: 4/5 | Zorluk: Kolay | Risk: `ON CONFLICT` constraint dogru tanimlanmali (zaten `uq_student_answer` var)

**Kor nokta:** `asyncio.create_task` ile `_auto_complete_task` her sinav basladiginda 2.75 saat dormant coroutine olusturuyor. 100K session = 100K coroutine. Task referansi TUTULMUYOR — cancel edilemiyor.

**Uyari:** `sinav_motoru_service.py`'yi production'da KULLANMAYIN — tamamen in-memory, DB persistence YOK, circular import riski var.

---

### Bakim/Surdurulebilirlik Mimari

**1. `sinav_motoru_service.py` silinmeli**
Legacy ve refactored versiyon ayni sinif adini (`SinavMotoruServisi`) tanimliyor. Refactored versiyon HICBIR yerde import edilmiyor — tamamlanmamis migration denemesi. Legacy de dead code.
- Etki: 5/5 | Zorluk: Kolay | Risk: Sessizce import edilen uc durum — grep ile dogrula

**2. sinav.py'deki auth+session guard duplikasyonu dependency'ye cikarilmali**
12 endpoint'in 11'inde birebir ayni 8 satirlik pattern: `get_session_data -> 404 -> student_id check -> 403`. ~90 satir saf duplikasyon. Tek `verify_exam_ownership()` dependency'si yeterli.
- Etki: 4/5 | Zorluk: Kolay | Risk: HTTPException propagation testi gerekir

**3. Sinav konfigurasyonlari (148-253) data olarak ayrilmali**
105 satir hardcoded dict (subject distribution, AYT configs, YDT languages) `__init__` icinde. OSYM her yil format degistiriyor — engine koduna dokunmak gerekiyor. Ayri config dosyasina tasinmali.
- Etki: 3/5 | Zorluk: Orta | Risk: Validation'siz config dosyasi runtime hatasi — Pydantic schema gerekir

**Kor nokta:** Sunucu restart'inda in-memory dict bosalir ama DB'deki `in_progress` oturumlar orphan kalir. Kullanici sinavi kaldigi yerden devam edemez, yeni sinav da olusturamaz.

**Uyari:** `sinav_motoru_service_refactored.py`'yi production'a aktarMAyin — sync SQLAlchemy kullaniyor, repo katmani mevcut degil, tamamlanmamis.

---

### Maliyet/Operasyon Mimari

**1. `save_answer` per-click INSERT'u batch'e cevir**
Her cevap icin SELECT + INSERT/UPDATE + COMMIT. 120 soruluk TYT'de 120+ ayri transaction. In-memory'ye yaz (zaten yapiyor), DB flush'i sadece auto-save (30sn) ve exam-complete'te yap.
- Etki: 4/5 | Zorluk: Kolay | Risk: Crash'te max 30sn veri kaybi (kabul edilebilir)

**2. `active_sessions` stateful singleton**
`osym_exam_engine = OSYMExamEngine()` (satir 1444) tum state RAM'de. 2+ worker/pod mumkun degil.
- Etki: 5/5 | Zorluk: Orta | Risk: Redis latency (~1ms) per-operation

**3. `/weaknesses` ve `/study-recommendations` cache'siz**
`analyze_exam_performance`'i tekrar tekrar cagiriyor (exam_performance.py satir 447, 510). 3 endpoint ayri cagirildiginda ayni 7-8 SQL sorgusu 3x calisir.
- Etki: 3/5 | Zorluk: Kolay | Risk: Cache invalidation — sinav tamamlandiktan sonra analiz degismez, TTL yeterli

**Kor nokta:** Storage buyumesi izlenmiyor. 1000 ogrenci x haftada 2 sinav x 120 soru = yilda ~12.5M satir. Retention policy veya cold-storage partition'i planlanmali.

**Uyari:** Exam engine'e AI/LLM cagrisi EKLEMEYIN. Sifir AI maliyeti var (rule-based soru secimi). "Kisisellestirilmis soru secimi icin LLM" 10K kullanicida aylik $1K-10K'ya cikar. IRT/BKT pipeline zaten aktif.

## Kor Noktalar & Uyarilar (Birlesik)

### Kor Noktalar
1. **asyncio dormant coroutine** — 100K concurrent = 100K task, cancel edilemiyor (Performans)
2. **Orphan DB sessions** — restart sonrasi `in_progress` oturumlar kilitli kalir (Bakim)
3. **Storage buyumesi** — yilda ~12.5M satir, retention policy yok (Maliyet)

### Uyarilar
1. `sinav_motoru_service.py`'yi production'da KULLANMAYIN — dead code (Performans)
2. `sinav_motoru_service_refactored.py`'yi aktarMAyin — tamamlanmamis (Bakim)
3. Exam engine'e AI/LLM EKLEMEYIN — gereksiz maliyet (Maliyet)
4. `ORDER BY random()` buyuk tablolarda yavaslar — `TABLESAMPLE` dusunun (Performans)

## Ilgili Dosyalar

| Dosya | Satir | Rol |
|-------|-------|-----|
| `backend/core/osym_exam_engine.py` | 1445 | Ana sinav motoru (DB-backed) |
| `backend/api/sinav.py` | 1337 | Sinav API router |
| `backend/services/sinav_motoru_service.py` | 553 | Legacy motor (DEAD CODE) |
| `backend/services/sinav_motoru_service_refactored.py` | ~500 | Tamamlanmamis migration |
| `backend/services/exam_performance_service.py` | 814 | Performans analiz servisi |
| `backend/models/exam_db.py` | 177 | ORM modelleri (index'ler iyi) |
