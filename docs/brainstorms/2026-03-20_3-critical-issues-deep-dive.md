# Brainstorm: 3 Kritik Sorun Deep Dive — IRT Kalibrasyon, Algoritma Silo, Scope Temizligi
Tarih: 2026-03-20 | Domain: architecture | Perspektifler: Performans, Bakim, Maliyet

## TL;DR
IRT heuristik bootstrap ~8 saatte yapiilabilir ve "adaptif ogrenme" vaadini hemen acar (difficulty_level enum -> irt_difficulty toplu UPDATE). Dead code temizligi (Revolutionary 8,965 satir + 5 orphan backend 5,600 satir) guvenli. Algoritma orkestrasyon 3-4 hafta surer ve 0 ogrenci verisiyle test edilemez — MVP sonrasina birakilmali.

## Top 5 Aksiyon

| # | Aksiyon | Etki | Zorluk | Sure | Kaynak |
|---|---------|------|--------|------|--------|
| 1 | **IRT heuristik bootstrap** — difficulty_level enum -> irt_difficulty toplu UPDATE + calibration_confidence=0.3 flag | 5/5 | Kolay | ~8 saat | Performans + Maliyet |
| 2 | **Revolutionary frontend temizligi** — 18 component + 3 test = 8,965 satir -> _deprecated/ | 5/5 | Kolay | ~4 saat | Bakim |
| 3 | **26 Modern* wrapper kaldirma** — App.tsx'te direkt import, wrapper'lari _deprecated/ | 4/5 | Kolay | ~6 saat | Bakim |
| 4 | **5 orphan backend router+servis cikarma** — revolutionary, sequential_reasoning, preference_simulation, bloom_taxonomy + router'lari | 4/5 | Orta | ~8 saat | Bakim |
| 5 | **FSRS state persistence ekleme** — stability=None ile cagriliyor, her seferinde sifirdan -> DB'ye kart state yazma | 4/5 | Orta | ~12 saat | Performans |

**Toplam tahmini sure: ~38 saat (1 hafta yoGun calisma)**

## Konsensus (3/3 perspektif hemfikir)

1. **IRT bootstrap HEMEN yapilmali** — CAT fiilen rastgele soru seciyor (tum difficulty=0.0), ~8 saat yeterli
2. **Algoritma orkestrasyon simdi YAPILMAMALI** — 3-4 hafta, 0 ogrenci verisinde test edilemez, MVP gecikir
3. **Dead code guvenle temizlenebilir** — Revolutionary 0 import, 8,965 satir; toplam 36 dosya ~9 saat

## Catismalar

| Konu | Taraf A | Taraf B | Karar |
|------|---------|---------|-------|
| BKT->IRT veri akisi | Performans: "Kolay, 0 ek DB" | Maliyet: "MVP gecikir" | Performans hakli — `initial_theta = logit(p_L)` tek satir |
| Modern* wrapper silme | Bakim: "26 wrapper sil" | Maliyet: "aktif route" | Bakim hakli — route yonlendirilip wrapper deprecate |
| FSRS cultural multiplier | Performans: "30x aralik, A/B test sart" | Maliyet: "multiplier=1.0 ile cik" | Her ikisi — MVP'de devre disi, sonra A/B test |

## Perspektif Detaylari

### 1. Performans Muhendisi

**IRT Cold Start Felaketi:** question_bank modelinde 77,336 sorunun tamami irt_difficulty=0.0, is_calibrated=False. IRT modeli select_next_item_cat() bilgi fonksiyonuyla soru secer — ama tum difficulty=0.0 oldugunda secim fiilen RASTGELE.

**Silo Pipeline:** bkt_service.py:record_answer() 4 algortimayi seri cagiriyor AMA:
- BKT: 2 DB round-trip
- IRT: lazy import, caller DB'den veri cekmeli (3. round-trip)
- FSRS: stability=None ile cagriliyor — her seferinde sifirdan
- ZPD: saf hesaplama

BKT sonucu (new_p_L) IRT theta'ya GECMIYOR. FSRS'ye de gecmiyor.

**FSRS Cultural Multiplier:** 8 hardcoded carpan worst case 0.61x, best case 1.73x — 30x aralik.

**Oneriler:**
1. IRT bootstrap: success_rate > 0 olanlari logit donusumle toplu UPDATE — Etki 5/5, Kolay
2. Pipeline birlestirme: 4 round-trip -> 2 — Etki 4/5, Orta
3. BKT->IRT tek-yonlu veri akisi: initial_theta = logit(p_L) — Etki 3/5, Kolay

**Kor nokta:** FSRS state persistence yok — stability=None ile cagriliyor, tekrar zamanlama anlamsiz.
**Uyari:** Cultural multiplier'lari A/B test olmadan production'a tasima.

### 2. Bakim Muhendisi

**Revolutionary Frontend:** 18 component, 7,325 satir + 1,640 satir test = 8,965 satir dead code. 0 aktif import.

**Modern* Wrapper'lar:** 26 wrapper, her biri 9-14 satir (sadece re-export). 3 katmanli zincir mevcut.

**Backend Nis Servisler:** 6 servis 3,477 satir + 5 router 2,123 satir + test 1,043 satir. Router registry'de SADECE cultural_adaptation_api kayitli. Diger 5 router register edilmemis — HTTP ile erisilemez.

**Oneriler:**
1. 26 wrapper kaldirma — Etki 4/5, Kolay
2. Revolutionary 18 comp + 3 test -> _deprecated/ — Etki 5/5, Kolay
3. 5 orphan backend router+servis cikarma — Etki 4/5, Orta

**Temizlik sirasi:** Revolutionary (0 bagimlilik) -> Wrapper'lar (mekanik) -> Backend orphan (yolo ayirmak gerekir)

**Kor nokta:** yolo_question_detector orphan DEGIL — ocr_api.py:41 ve unified_ocr_service.py:689 lazy import ile cagiriyor.
**Uyari:** Toplu silme scripti KULLANMAYIN — 2-3 pilot, sonra tamam.

### 3. Maliyet/Fizibilite Analisti

**IRT Heuristik Bootstrap:** difficulty_level enum -> logit mapping. 1 script + 1 migration = ~8 saat. Gercek EM/MCMC: min 500 ogrenci x 50+ soru = 25K response, MVP ile 3-6 ay sonra.

**Dead Code:** Revolutionary 19 + deprecated 17 = 36 dosya silinebilir. ~9 saat.

**Algoritma Orkestrasyon:** 12-15 dosya degisikligi + yeni DB migration + integration test = 3-4 hafta. MVP 1+ ay gecikir.

**Oneriler:**
1. IRT bootstrap HEMEN — Etki 5/5, Kolay, ~8 saat
2. Dead code temizligi SIMDI — Etki 3/5, Kolay, ~9 saat
3. Orkestrasyon YAPMAYIN (simdi) — MVP oncelikli

**Kor nokta:** IRT bootstrap hem FSRS'i de acar — FSRS card difficulty IRT'ye bagli olmali.
**Uyari:** Orkestrasyon refactoring'ine BASLAMAYIN — 0 verisiyle test edilemez.

## Kor Noktalar & Uyarilar (Birlesik)

### Kor Noktalar
1. **FSRS state persistence yok** — stability=None ile cagriliyor, tekrar zamanlama anlamsiz (Performans, P0)
2. **yolo_question_detector silmeyin** — OCR pipeline aktif kullanyor (Bakim, P1)
3. **IRT bootstrap FSRS'i de acar** — iki sistemi birden calistirir (Maliyet, P1)
4. **BKT sonucu IRT theta'yi etkilemiyor** — record_answer() icinde gecilmiyor (Performans, P2)

### Uyarilar
1. Cultural multiplier'lari A/B test olmadan production'a tasimayin (Performans)
2. Toplu wrapper silme scripti KULLANMAYIN — pilot yapin (Bakim)
3. Algoritma orkestrasyon refactoring'ine BASLAMAYIN — MVP once (Maliyet)
4. yolo_question_detector dead code sanip silmeyin (Bakim)

## Uygulama Sira Onerisi

```
Hafta 1: IRT Bootstrap + Revolutionary Temizlik
  - Gun 1: IRT heuristik script + test + migration (~8 saat)
  - Gun 2: Revolutionary 18 comp -> _deprecated/ (~4 saat)
  - Gun 2: FSRS cultural_multiplier=1.0 default (~2 saat)

Hafta 2: Wrapper + Backend Temizlik
  - Gun 3-4: 26 Modern* wrapper pilot (3 dosya) + tamami (~6 saat)
  - Gun 5: 5 orphan backend router/servis (yolo haric) (~8 saat)

Hafta 3: FSRS State + Minimal Pipeline
  - Gun 6-7: FSRS card state DB persistence (~12 saat)
  - Gun 7: BKT->IRT tek satir baglanti: initial_theta = logit(p_L) (~2 saat)

MVP Sonrasi (500+ ogrenci verisi):
  - Gercek IRT EM/MCMC kalibrasyon
  - FSRS cultural multiplier A/B test
  - Tam algoritma orkestrasyon
```

---
*3 paralel perspektif (Performans, Bakim, Maliyet), Read-based analiz, 2026-03-20*
