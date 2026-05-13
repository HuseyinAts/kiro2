# 20260513 — Asama 2a: v4.14e fallback exclude — RESULT

**Tarih:** 13 May 2026 (UTC+3)
**Asama:** 2a/3 (strateji yol haritasindan)
**Status:** KAPANDI ✅

---

## Hedef

v_safe_for_beta'ya savunucu filter eklemek: v4.14e Gemini Flash batch'inden gelen ve `ai_extras->>'topic_match_quality'='fallback'` olan satirlari beta havuzundan dislamak. Bu satirlarda konu eslestirme basarisiz, IRT calibration ve student feedback'i bozma riski yuksek.

## Asama 1'den miras gelen state

- Asama 1 sonunda v_safe_for_beta = 123,233 (demoted exclude)
- Beta havuzu dagilimi:
  - 17,950 approved
  - 105,283 unverified (v4.14e Gemini)
  - 146 edge case
- L3 bulgusu: v4.14e topic match: %39.3 fallback, %37.4 fuzzy, %23.3 exact

## Ön kanıtlar

| Kanit | Kaynak | Yorum |
|---|---|---|
| Gemini Flash %15-17 DLQ | STRATEJI_B_KARAR.md | Yapisal zayiflik dokumantasyonu |
| Konu eslestirme basarisiz | L3.1 sorgu sonucu (canli) | Fallback grubu defansif |
| Spot ornek 5 fallback | L3.4 sorgu sonucu | Konu yanlis ama cevap dogrulugu TEST EDILMEDI |

**UYARI:** "Konu etiketi yanlis = cevap muhtemelen yanlis" hipotezi dogrudan test edilmedi. Bu Asama 1'deki demoted gruptan farkli (orada `tier_f_low_confidence` flag'i ZATEN vardi). Burada body of evidence daha zayif. Defansif yaklasim secildi, geri alinabilir.

## Yapilanlar — kronoloji

| # | Adim | Sonuc |
|---|---|---|
| 1 | Pre-deploy fallback count | 41,473 |
| 2 | Pre-deploy beklenen post-count | 81,760 |
| 3 | Migration dosyasi diske yazildi | backend/migrations/safe_for_beta_exclude_fallback.sql |
| 4 | CREATE OR REPLACE VIEW uygulandi | success |
| 5 | COMMENT ON VIEW eklendi | success |
| 6 | Post-deploy count dogrulama | 81,760 (birebir) |
| 7 | Post-deploy fallback leak | 0 |
| 8 | Post-deploy demoted leak (Asama 1 hala aktif) | 0 |
| 9 | Unfiltered yedek count | 161,028 (degismedi) |
| 10 | Performans (EXPLAIN ANALYZE) | 74.8 ms (Asama 1: 75.9 ms, -1.4%) |
| 11 | Rollback SQL dry-run | 123,233 (Asama 1 state'i) |

## View tanimi (canli, post-deploy)

```sql
CREATE OR REPLACE VIEW v_safe_for_beta AS
SELECT ... FROM v_safe_for_beta_unfiltered
WHERE quality_review_status::text IN ('approved','unverified')
  AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'))
  AND (
    pipeline_metadata IS NULL
    OR NOT (pipeline_metadata::jsonb ? 'ai_extras')
    OR NOT (pipeline_metadata::jsonb -> 'ai_extras' ? 'topic_match_quality')
    OR pipeline_metadata::jsonb -> 'ai_extras' ->> 'topic_match_quality' != 'fallback'
  );
```

## Yeni beta havuzunun dagilimi (81,760)

| Status | Source | n | % |
|---|---|---|---|
| unverified | v4.14e fuzzy | 39,281 | 48.04 |
| unverified | v4.14e exact | 24,529 | 30.00 |
| approved | v3.5+ phase4 | 17,804 | 21.78 |
| approved | other | 146 | 0.18 |

**Approved orani: %14.45 -> %21.96 (oransal +52%).**

## Performans suprizi

Beklenen: +30-50% regresyon (JSONB nested key access pahali). Gercek: -1.4% (iyilesme). Sebep: havuz boyutu kuculmesi (123K -> 82K) JSONB filter maliyetini ofsetledi. Buffer hit+read 1,964 -> 504 (-74%).

## NULL handling

Migration'da 3-yonlu defansif:
1. `pipeline_metadata IS NULL` -> tut
2. `ai_extras` key yok -> tut
3. `topic_match_quality` key yok -> tut
4. Sadece literal `'fallback'` -> dislama

Approved satirlari (ai_extras yok) defansif olarak tutuldu. Sayi parite ile dogrulandi.

## Rollback hazir

Migration dosyasinin yorumunda Asama 1 state'ine donus SQL'i hazir. Dry-run yapildi, 123,233 dondu.

## Acik konular

| Konu | Onem | Sonraki asama |
|---|---|---|
| 81,760 sorunun ne kadari dogru cevapli, bilinmiyor | YUKSEK | Manuel audit 30-100 ornek |
| v4.14e fuzzy (39,281) hala buyuk pay (%48) | YUKSEK | Asama 2b (sadece exact, ~43K) |
| Pending temiz 2,738 hala disarida | ORTA | Asama 3 |
| Fallback'lerin gercekten yanlis cevapli olup olmadigi test edilmedi | YUKSEK | Manuel audit fallback grubunun dogruluk orani |

## Beta icin anlam

- v4.14e fallback satirlari beta'da gosterilmeyecek
- IRT calibration sinyali daha temiz (konu etiketleri tutarli kaynaklardan)
- Beta pool yuzde %33.7 kuculdu ama approved orani %52 arttı
- Gemini Flash yapisal zayifligi hala tam temizlenmedi (fuzzy hala icerdek)

## STATUS: TAMAM
