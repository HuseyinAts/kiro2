# Stratified Audit RESULT — 100 örnek + Approved mini-audit

**Tarih:** 14 May 2026 (audit yapımı), 15 May 2026 (RESULT yazımı, gecikmeli)
**Önceki tur:** [20260513_fallback_audit_30_RESULT.md](20260513_fallback_audit_30_RESULT.md)
**Önceki tur'un handoff'u:** [20260514_NEXT_SESSION_HANDOFF_stratified_audit.md](20260514_NEXT_SESSION_HANDOFF_stratified_audit.md)
**Yazan:** Claude (Sonnet 4.6 / Opus 4.7) — 15 May session, audit ham verisi Hüseyin tarafından paylaşıldı

---

## Özet (TL;DR)

Pool'un **hiçbir alt-kümesi beta'ya hazır değil.** 100-örnek stratified audit
+ 30-örnek approved mini-audit toplamı %61 hata gösteriyor. **En şok edici
bulgu: `quality_review_status='approved'` etiketi %87 hata oranıyla
geliyor** — yani "approved" hiçbir gerçek kalite garantisi vermiyor.

Bu RESULT artifact'ı, 13 May 30-örnek audit'in (fallback grubu için
%67-73 doğru) gösterdiği "fallback en kötü" hipotezini **çürütüyor**:
fallback değil olanlar (exact/fuzzy) da %76-84 hatalı, ve `approved`
hepsinden daha kötü.

---

## Audit metodolojisi

### Sample tasarımı

**100-örnek stratified (5×20):**
- exact|true (has_diagram=true, topic_match_quality=exact): 25
- exact|false: 25
- fuzzy|true: 25
- fuzzy|false: 25
- (fallback için ayrı, yapılmadı — 13 May 30-örnekle birleşti)

**30-örnek approved mini-audit:**
- random sample, `quality_review_status='approved' AND is_active=true`
- Reproducible seed: `md5(id::text || 'audit-20260514-approved')`

**Doğrulama yöntemi:**
- Görsel-bağımsız: Hüseyin metni okuyup matematik/mantık doğruluk
- Görsel-bağımlı: source_book + source_page üzerinden orijinal kitap kontrolü
- 5 örnek sanity check Hüseyin tarafından gözle doğrulandı (5/5 bozuk → metodoloji güvenilir)

### Disk artefaktları

| Dosya | Beklenen | Gerçek |
|---|---|---|
| `20260514_stratified_audit_100_RAW.tsv` | Mevcut | **YOK** (handoff'taki "diskte mevcut" iddiası yanlış) |
| `20260514_stratified_audit_100_SCORING.tsv` | Mevcut | **YOK** |
| `20260514_audit_exact_true.tsv` | Mevcut | **YOK** |
| `20260514_audit_fuzzy_false.tsv` | Mevcut | **YOK** |
| `20260514_audit_fuzzy_true.tsv` | Mevcut | **YOK** |

⚠ **Audit ham verisi diskte yok.** Bu RESULT, 15 May handoff dokümanındaki
sayılara dayanıyor. Gelecek audit'ler **mutlaka** ham TSV'leri commit etmeli.

---

## Sonuçlar — alt-küme bazında

### 100-örnek stratified

| Strata | n | Hata | Dominant hata türü |
|---|---|---|---|
| exact \| true | 25 | **%84** | missing_diagram |
| fuzzy \| true | 25 | **%76** | missing_diagram |
| exact \| false | 25 | %44 | wrong_answer |
| fuzzy \| false | 25 | %40 | wrong_answer |
| **TOPLAM** | **100** | **%61** | mixed |

### 30-örnek approved mini-audit

| Sub-pool | n | Hata | Notlar |
|---|---|---|---|
| approved (v3.5 phase4 sub-set) | 30 | **%87** | "Kalite filtresi" sıfır anlam ifade ediyor |

### Hata türü dağılımı (100+30 = 130 örnek)

| Tür | Yaklaşık sayı | % | Düzeltilebilirlik |
|---|---|---|---|
| missing_diagram (has_diagram=true + image_url=null) | 40+1 | **%32** | Pipeline-fix (image persist mantığı) |
| ocr (bozuk metin) | 14+20 | **%26** | Pipeline-fix (re-OCR) veya manuel |
| wrong_answer | 8+5 | **%10** | Manuel curator veya LLM rerun |
| Diğer (konu yanlış, duplicate option, …) | — | bakiye | Karışık |

---

## Smoking gun — "approved" yalanı

15 May Claude session araştırması, **`approved` etiketinin manuel onay
süreci olmadığını** kanıtladı:

```python
# backend/scripts/import_d_dataset.py:212  (commit 877cb44c, 4 Mart 2026, Hüseyin Ateş)
"quality_review_status": "approved",
```

Bu literal string `import_d_dataset.py` her satıra hardcoded yazıyor.
77,336 d-dataset satırı v3.5 import'unda otomatik `approved` etiketlendi.
**"Manuel review queue", "expert review", "human-in-the-loop" — hiçbiri
olmadı.**

DB schema default'u `'pending'` (add_question_bank_tables.sql:122),
import script override ediyor.

Hüseyin'in 3 hipotezinden:
- ❌ (a) v3.5 manuel kriteri zayıf → **YANLIŞ**, hiç manuel kriter yok
- ✅ (b) Pipeline otomatik atadı, insan değerlendirmesi yok → **DOĞRU**
- ❌ (c) v4.14e sıvıştırdı → **YANLIŞ**, sorun Mart'tan beri orada

---

## 13 May audit ile çelişki

13 May 30-örnek fallback audit'i (`20260513_fallback_audit_30_RESULT.md`):
- 15 doğrulanabilir örnekte: 10 doğru, 1 yanlış, 2 OCR duplicate, 1 şüpheli, 1 konu yanlış
- "Net doğruluk oranı (doğrulanabilir grupta): %67-73"

14 May 100-örnek stratified audit:
- exact/fuzzy (fallback DEĞİL) gruplar da %40-84 hatalı
- approved (en "güvenli" kabul edilen) %87 hatalı

**Çelişkinin olası açıklamaları:**

1. **Sample bias (13 May):** 30-örnek küçük, 15'i doğrulanabilirdi
   (yarısı görsel). Bu alt-set'in tesadüfen iyi çıkması olası.
2. **Strata farkı:** 13 May fallback'i kontrol etti; 14 May exact/fuzzy
   (fallback DEĞİL) kontrol etti. Beklenmedik şekilde fallback değil
   olanlar daha kötü görünüyor.
3. **`has_diagram` farkı:** 13 May 50% görsel-bağımlı (doğrulanamadı).
   14 May yarısı `has_diagram=true` (kitap denetimi yapıldı, missing_diagram dominant).

**Sonuç:** 13 May'in "fallback en kötü" hipotezi yanlış. **Aşama 2a
(fallback exclude) gereksiz olabilir** — pool zaten her yerden kötü.

---

## Stratejik implikasyonlar

| Strateji | 14 May audit ışığında durum |
|---|---|
| Beta'yı `v_safe_for_beta` ile açmak | ❌ Kritik risk — %61-87 hatalı pool |
| `approved` filter'a güvenmek | ❌ Yalan — manuel onay yok |
| `fallback` exclude (Aşama 2a) | ⚠ Etkisiz — geri kalan da kötü |
| Mevcut "pipeline-fix" yaklaşımı | ⚠ Tek başına yeterli değil |
| Manuel curator (X1) | ✅ Beta için zorunlu |
| Yeni `human_verified` status | ✅ Gerekli (gerçek temiz pool için) |

---

## Sonraki adımlar (15 May Claude oturumunda alınanlar)

1. ✅ `import_d_dataset.py:212` hardcoded literal kaldırıldı (D1)
2. ✅ 17,950 yanlış approved satırı → `legacy_v3_unaudited` (D2)
3. ✅ `human_verified` status değeri tanımlandı, convention belgelendi (A6, D3)
4. ✅ `v_safe_for_beta` view yeniden tanımı — `approved` artık güvenli sayılmıyor (D4)
5. ⏳ 3 servis dosyası (osym_exam_engine, cat_session, placement_service) audit + güncelleme (D5)
6. ⏳ Sonraki audit turları (C1-C3) Hüseyin tarafından elle

## Açık konular (sonraki oturuma kalan)

- `missing_diagram` flag güvenilirliği (C1): %32 dominant hata — pipeline-fix mümkün mü?
- `wrong_answer` Mat/Geometri konsantrasyonu (C2)
- Approved'da 30 örnek tekrar audit (C3): %87 hata istikrarlı mı?
- LLM-as-judge prototype kalibrasyonu için minimum manuel curated set boyutu
