# 20260514+ NEXT SESSION HANDOFF — Stratified Audit (100 örnek)

**Tarih:** Hazırlandı 13 May 2026, kullanım sonraki oturumda
**Önceki tur:** 20260513 — Asama 1 (demoted exclude) + Asama 2a (fallback exclude) + L5 doc audit + 30-ornek fallback audit

---

## Mevcut durum (13 May 2026 oturum sonu)

- `v_safe_for_beta` = 81,760 satır (Aşama 2a korundu, Yön 3)
- Beta amacı: **kalite testi** (küçük temiz pool yeterli, kullanıcı kararı)
- Aşama 2a temel argüman (Gemini %15-17 DLQ) Bayesian tutarlı, ama spesifik filter (fallback=true) optimal değil

## Sonraki turun amacı

100 örneklik stratified audit ile fallback grubunun kategori-bazlı hata haritasını çıkar. Sonuca göre **kategoriye göre ince filter** karar ver (tüm fallback değil, sadece riskli kategorilerin fallback'i).

## Audit tasarımı

### Stratification

| Strata | Hedef sample | Rationale |
|---|---|---|
| has_diagram=true | 50 | Görsel-bağımlı risk |
| has_diagram=false | 50 | Sadece metin, görsel-bağımsız |

### Kategori dağılımı (her strata içinde dengelenmiş)

| Kategori | Hedef (her strada) | Tahminen oran (fallback evreninde) |
|---|---|---|
| Matematik / Geometri | 15-20 | Yüksek |
| Fizik / Kimya | 10-15 | Yüksek |
| Biyoloji | 5-10 | Orta |
| Edebiyat / Türkçe | 5-10 | Orta |
| Tarih / Sosyal | 5-10 | Orta |
| Coğrafya | 3-5 | Düşük |
| Felsefe / Din | 3-5 | Düşük |

### Sample SQL (sonraki turda çalıştır)

```sql
-- Stratified sample: 50 has_diagram=true + 50 has_diagram=false
WITH stratified AS (
  SELECT 
    id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer,
    pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram' AS has_diagram,
    pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_raw' AS topic_raw,
    subject_area,
    source_book,
    source_page,
    ROW_NUMBER() OVER (
      PARTITION BY pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram'
      ORDER BY RANDOM()
    ) AS rn
  FROM question_bank
  WHERE is_active=true 
    AND quality_review_status='unverified'
    AND pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' = 'fallback'
)
SELECT * FROM stratified WHERE rn <= 50 ORDER BY has_diagram, rn;
```

## Audit yöntemi

1. **Görsel-bağımsız (has_diagram=false, 50 örnek):** Hüseyin metni okuyup matematik/mantık olarak doğrulanabilir mi karar verir.
2. **Görsel-bağımlı (has_diagram=true, 50 örnek):** Hüseyin source_book + source_page üzerinden orijinal kitabı kontrol eder; gerçek doğruluk burada.

## Sayım şablonu (her örnek için)

| Sonuç | Kategori |
|---|---|
| ✅ Net doğru | Cevap = doğru |
| ❌ Net yanlış | Cevap ≠ doğru, kesin |
| 🟡 OCR/duplicate option | Soru yapısal hatalı |
| 🏷️ Konu yanlış ama cevap doğru | Pipeline topic mapping hatası, cevap OK |
| ❓ Şüpheli | Belirsiz, ikinci görüş gerek |

## Karar matrisi (audit sonucuna göre)

### A senaryosu: has_diagram=true hata %30+ → has_diagram=false hata %15-

→ **Hedefli filter (Yön 2 doğrulanmış versiyonu):**
```sql
AND NOT (
  pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' = 'fallback'
  AND (pipeline_metadata::jsonb -> 'ai_extras' ->> 'has_diagram')::boolean = true
)
```
Beta pool: ~99,751 (has_diagram=false fallback geri eklenir)

### B senaryosu: Her iki strata %20+ hata

→ **Aşama 2a koru** (mevcut state). Şu anki defansif yaklaşım optimal.

### C senaryosu: Her iki strata <%15 hata

→ **Tam rollback** (Yön 1). Fallback'ler beta için yeterince güvenli. Beta pool 123,233.

### D senaryosu: Kategori bazlı sapma (örn. matematik %5, edebiyat %40)

→ **Kategori-aware filter:**
```sql
AND NOT (
  pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' = 'fallback'
  AND subject_area IN ('edebiyat', 'tarih', 'sosyal')  -- yüksek hatalı kategoriler
)
```

## Önemli notlar

1. **Selection bias düzeltmesi:** 30-ornek audit'te benim sample'ım matematik/fizik ağırlıklı çıkmış olabilir. Stratified design + kategori-aware sayım bu bias'ı kıracak.

2. **has_diagram confound:** Pipeline'ın has_diagram=true flag'i %30+ yanlış pozitif veriyor (bazı görsel-bağımsız sorular has_diagram=true işaretli). Kitap denetimi sırasında "gerçekten görsel gerekli mi" notu al — pipeline metadata'sı ile karşılaştır.

3. **OCR duplicate option sorunu:** %13 OCR/duplicate beta filter'la çözülmüyor, pipeline-level fix gerekir. Audit sırasında işaretleyerek, sonraki pipeline iyileştirmesi için kanıt biriktir.

4. **IRT calibration:** Şu an aktif değil (1080 manuel seed, son güncelleme 24 Mart). Beta'da %20 yanlış cevap olsa bile IRT bozulması anlamlı düzeye ulaşmaz (50+ yanıt per item gerekli). Yani "yanlış cevap → IRT bozulur" argümanı bu beta için akademik.

## Beklenen süre

- 30 sample audit: ~20 dakika (matematik/fizik) + ~30 dakika (kitap denetimi has_diagram=true)
- 100 sample audit: ~60-90 dakika toplam
- Karar verme + view update: 10 dakika
- RESULT artifact: 15 dakika

**Toplam:** 1.5-2 saat sonraki tur

## Açık sorular (sonraki tura kalan)

| Soru | Önem |
|---|---|
| 100 örnek stratified audit yaparsam fallback'in gerçek hata haritası ne? | Bu turun ana hedefi |
| Kategori-aware filter mı yoksa flat filter mı? | Audit sonrası karar |
| Pipeline-level OCR fix mümkün mü? | Orta vadeli, beta dışı |
| Aşama 3 (pending temiz 2,738 approve) ne zaman? | Düşük risk, ayrı tur |

## Bu turun dersi

**"Daha derin düşün" = perspektif sayısını çoğaltmak.** Bu turda iki kez öneri verdim ve revize ettim. Yorgun karar değil, evolving karar. Sonraki turda yine "ilk gut feel'a güvenme, audit ve katmanları aç" diziplini.

---

## STATUS: HAZIR — sonraki oturum başlangıcında oku
