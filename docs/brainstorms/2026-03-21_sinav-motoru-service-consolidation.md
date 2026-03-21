# Brainstorm: sinav_motoru_service.py Konsolidasyon Stratejisi
Tarih: 2026-03-21 | Domain: architecture | Perspektifler: Performans, Bakim, Maliyet

## TL;DR
`sinav_motoru_service.py` (553 satir) tamamen in-memory, DB persistence YOK — 4 tuketici var ama 2'si dead/broken code. `_refactored` versiyonu tamamlanmamis, sifir import. Gercek migrasyon sadece `advanced_reports.py` (5 endpoint) ve `ogretmen_service.py` (4 method) icin gerekli — incremental yaklasimla `osym_exam_engine`'e tasinmali.

## Top 5 Aksiyon

| # | Aksiyon | Etki | Zorluk | Kaynak |
|---|---------|------|--------|--------|
| 1 | **`sinav_motoru_service_refactored.py` sil** — 0 import, dead code | 3/5 | Kolay | 3/3 perspektif |
| 2 | **`websocket_exam.py` import'unu temizle** — router'a kayitli degil, dead code | 3/5 | Kolay | 3/3 perspektif |
| 3 | **`service_dependencies.py` broken import fix** — `SinavMotoruService` sinif adi eslesmesi | 3/5 | Kolay | Bakim + Performans |
| 4 | **`advanced_reports.py` → `osym_exam_engine` migration** — 5 endpoint, `sonuc_getir()` DB-backed'e gec | 4/5 | Orta | 3/3 perspektif |
| 5 | **`ogretmen_service.py` → `osym_exam_engine` migration** — 4 method, teacher panel | 4/5 | Orta | 3/3 perspektif |

## Konsensus (3/3 perspektif)

1. **Incremental migration, big-bang DEGIL** — Tuketicileri teker teker tasi, her adimda test et
2. **`_refactored` hemen silinebilir** — Sifir risk, sifir import, tamamlanmamis migration denemesi
3. **Dead code once temizlenmeli** — websocket_exam + service_dependencies import'lari
4. **In-memory → DB-backed gecis zorunlu** — Restart'ta veri kaybi kabul edilemez
5. **`sinav_motoru_service.py` EN SON silinmeli** — Tum tuketiciler tasindiktan sonra

## Catismalar

| Konu | Taraf A | Taraf B | Onerilen Karar |
|------|---------|---------|----------------|
| Adapter vs dogrudan migration | Bakim: Adapter ile backward compat | Performans: Dogrudan migration daha temiz | Dogrudan — tuketici sayisi az (2 aktif) |
| sinav_motoru_service.py silme zamani | Maliyet: Hemen sil | Bakim: Tuketiciler tasindiktan SONRA sil | Tuketiciler tasindiktan sonra — guvenli |
| ogretmen_service proxy vs rewrite | Maliyet: Proxy (3 satir degisiklik) | Performans: Full rewrite (DB-backed) | Hibrit — once proxy, sonra rewrite |

## Tuketici Haritasi

| Dosya | Method Kullanimi | Durum | Aksiyon |
|-------|-----------------|-------|---------|
| `advanced_reports.py` | `sonuc_getir()` (5 endpoint) | AKTIF | Migration gerekli |
| `ogretmen_service.py` | `ogrenci_sinavlari()`, `sonuc_getir()` (8 cagri) | AKTIF | Migration gerekli |
| `websocket_exam.py` | `oturum_getir()`, `kalan_sure_getir()`, `sinav_tamamla()` | DEAD CODE — router'a kayitli degil | Import temizle |
| `service_dependencies.py` | `SinavMotoruService` import | BROKEN — sinif adi `SinavMotoruServisi` | Import fix/kaldir |

## Perspektif Detaylari

### Performans Mimari

**1. In-memory dict'ler restart'ta kaybolur**
4 Python dict (`self.oturumlar`, `self.cevaplar`, `self.sonuclar`, `self.sinav_gecmisleri`) process restart'inda sifirlanir. 100+ concurrent ogrenci oturumu kaybolur. `osym_exam_engine` zaten Redis L2 + DB persistence kullaniyor — tuketiciler oraya tasinmali.
- Etki: 5/5 | Zorluk: Orta | Risk: Migration sirasinda aktif sinav kaybi

**2. `sonuc_getir()` her cagride yeniden hesaplayarak CPU israf ediyor**
`advanced_reports.py`'deki 5 endpoint her seferinde `sinav_motoru_servisi.sonuc_getir()` cagiriyor. Sonuclar cache'lenmiyor. `osym_exam_engine` zaten `MultiLayerCache` kullaniyor.
- Etki: 3/5 | Zorluk: Kolay | Risk: Cache invalidation timing

**3. websocket_exam.py dead code — gereksiz import chain**
Router'a kayitli degil, hicbir request ulasamaz. Ama module yukleme sirasinda `sinav_motoru_servisi` singleton'u olusturuluyor — gereksiz memory allocation.
- Etki: 2/5 | Zorluk: Kolay | Risk: Sifir

**Kor nokta:** `sinav_motoru_servisi` global singleton — import eden HER module ayni instance'i paylasir. Migration sirasinda partial state inconsistency olusabilir.

**Uyari:** Big-bang migration YAPMAYIN. 553 satirlik servisi tek seferde kaldirir, bir tuketiciyi atlarsiniz → RuntimeError.

---

### Bakim/Surdurulebilirlik Mimari

**1. `sinav_motoru_service_refactored.py` silinmeli**
Sync SQLAlchemy kullaniyor (backend async), repository pattern tamamlanmamis, HICBIR yerde import edilmiyor. Ayni sinif adi (`SinavMotoruServisi`) iki dosyada — import kargasasi riski.
- Etki: 5/5 | Zorluk: Kolay | Risk: Sifir

**2. `service_dependencies.py` broken import**
`SinavMotoruService` (CamelCase, Ingilizce "Service") import ediyor ama gercek sinif adi `SinavMotoruServisi` (Turkce "Servisi"). Bu import HICBIR zaman calismaz — ya fix ya sil.
- Etki: 3/5 | Zorluk: Kolay | Risk: Sifir (zaten broken)

**3. Isimlendirme tutarsizligi**
Legacy: Turkce (`oturum_getir`, `sinav_tamamla`, `SinavMotoruServisi`)
Modern: Ingilizce (`get_session_data`, `complete_exam`, `OSYMExamEngine`)
Migration sonrasi tum API Ingilizce'ye standardize olmali.
- Etki: 3/5 | Zorluk: Orta | Risk: Frontend breaking change

**Kor nokta:** `ogretmen_service.py` teacher panel icin kullaniliyor — migration sirasinda ogretmen dashboard'u test etmek ZORUNLU. Ogretmen hesabi yoksa regression farkedilmez.

**Uyari:** Migration'da Turkce method adlarini BIREBIR koruma — Ingilizce'ye standardize et. Yoksa `sonuc_getir()` + `get_results()` gibi cift method birikiyor.

---

### Maliyet/Operasyon Mimari

**1. Dual motor maintenance maliyeti**
Ayni is mantigi 2 yerde: `sinav_motoru_service.py` (in-memory) ve `osym_exam_engine.py` (DB-backed). Her bug fix'te 2 dosya kontrol etmek gerekiyor. Konsolidasyon bakim maliyetini %50 azaltir.
- Etki: 4/5 | Zorluk: Orta | Risk: Migration effort vs uzun vadeli tasarruf

**2. Dead code infra maliyeti**
`websocket_exam.py` + `_refactored.py` toplam ~1000 satir dead code. Her linting, test collection, IDE indexing'de isleniyor. Silmek developer experience iyilestirir.
- Etki: 2/5 | Zorluk: Kolay | Risk: Sifir

**3. Test maintenance**
`sinav_motoru_service` icin ayri test dosyasi gerekiyor. Konsolidasyon sonrasi tek test suite yeterli olur.
- Etki: 3/5 | Zorluk: Kolay | Risk: Test coverage gap

**Kor nokta:** Migration effort hesabi — advanced_reports.py (5 endpoint) + ogretmen_service.py (4 method) = ~2-4 saat. Bu maliyetin geri donus suresi ~3-4 hafta (haftalik 1 saat bakim tasarrufu).

**Uyari:** Migration'i sprint'e planlayip "sonra yapariz" DEMEYIN. Dead code zamanla daha fazla referans toplar. Simdi 2 aktif tuketici, 3 ay sonra 5 olabilir.

## Kor Noktalar & Uyarilar (Birlesik)

### Kor Noktalar
1. **Ogretmen dashboard regression** — teacher hesabi olmadan test edilemez
2. **Singleton partial state** — migration sirasinda eski+yeni motor parallel calisabilir
3. **Migration effort ROI** — 2-4 saat yatirim, 3-4 hafta geri donus

### Uyarilar
1. Big-bang migration YAPMAYIN — incremental, her adimda test
2. Turkce method adlarini koruma — Ingilizce'ye standardize et
3. "Sonra yapariz" DEMEYIN — dead code referans toplar
4. `_refactored.py`'yi production'a AKTARMAYIN — sync SQLAlchemy, tamamlanmamis

## Onerilen Migration Plani (5 Adim)

```
Adim 1: sinav_motoru_service_refactored.py SIL          [5 dk, sifir risk]
Adim 2: websocket_exam.py import TEMIZLE                 [5 dk, sifir risk]
Adim 3: service_dependencies.py broken import FIX/SIL    [5 dk, sifir risk]
Adim 4: advanced_reports.py → osym_exam_engine MIGRATION  [1-2 saat, orta risk]
Adim 5: ogretmen_service.py → osym_exam_engine MIGRATION  [1-2 saat, orta risk]
Adim 6: sinav_motoru_service.py SIL                       [5 dk, sifir risk — tum tuketiciler tasindi]
```

## Ilgili Dosyalar

| Dosya | Satir | Rol |
|-------|-------|-----|
| `backend/services/sinav_motoru_service.py` | 553 | Legacy motor (in-memory, 4 dict) |
| `backend/services/sinav_motoru_service_refactored.py` | ~500 | Tamamlanmamis migration (DEAD CODE) |
| `backend/core/osym_exam_engine.py` | 1445 | Production motor (DB + Redis backed) |
| `backend/services/advanced_reports.py` | ~300 | Raporlama (5 endpoint, AKTIF tuketici) |
| `backend/services/ogretmen_service.py` | ~250 | Ogretmen paneli (4 method, AKTIF tuketici) |
| `backend/api/websocket_exam.py` | ~200 | WebSocket sinav (DEAD CODE — router yok) |
| `backend/services/service_dependencies.py` | ~50 | Dependency registry (BROKEN import) |
