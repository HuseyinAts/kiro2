# 20260513 — Safe-for-beta wrapper'a demoted exclude eklemek — RESULT

**Tarih:** 13 May 2026 (UTC+3)
**Aşama:** 1/3 (strateji yol haritasından)
**Status:** KAPANDI ✅

---

## Hedef

`v_safe_for_beta`'ya `tier_f_low_confidence_unverified` (demoted) satırları için savunucu filter eklemek. Spot örneklem (5/5'in 2'sinde gözle görülür yanlış cevap) bu grubun beta'ya uygun olmadığını kanıtlamıştı.

## Ön kanıtlar (L1-L3 analizinden)

- `v_safe_for_beta` 161,028 satır (canlı, 22:26 UTC).
- Beta havuzunun anatomisi:
  - 17,950 approved (v3.5+ phase4) — tam doğrulanmış
  - 38,871 unverified-demoted (`tier_f_low_confidence`) — pipeline reddetmiş
  - 107,516 unverified-v4.14e (Gemini Flash) — kalite review yok
- Demoted örnekleminden 5 soru çekildi, 2 tanesinde matematiksel olarak yanlış cevap (örüntü 7. adım = D, DB'de A; tan(4x)=√3 en küçük x = C, DB'de E).
- `v_safe_for_beta` içindeki demoted = 37,795 (38,871 - 1,076 view'ın diğer filter'larıyla zaten elenmiş).

## Yapılanlar — kronoloji

| # | Adım | Sonuç |
|---|---|---|
| 1 | Write yetki smoke test | `write_ok` |
| 2 | Pre-deploy count: demoted_in_view | 37,795 |
| 3 | Pre-deploy beklenen post-count | 123,233 |
| 4 | Migration dosyası diske yazıldı | `backend/migrations/safe_for_beta_exclude_demoted.sql` |
| 5 | CREATE OR REPLACE VIEW uygulandı | success |
| 6 | COMMENT ON VIEW eklendi | success |
| 7 | Post-deploy count doğrulama | 123,233 (beklenen ile birebir) |
| 8 | Post-deploy demoted leak kontrolü | 0 |
| 9 | Unfiltered yedek count | 161,028 (değişmedi) |
| 10 | Performans (EXPLAIN ANALYZE) | 75.9 ms (önce 53.8 ms, +41% kabul edilebilir) |
| 11 | Rollback SQL dry-run | 161,028 (doğru hedef) |
| 12 | Memory #4 + #16 güncellendi | iki replace |

## View tanımı (canlı, post-deploy)

```sql
CREATE OR REPLACE VIEW v_safe_for_beta AS
SELECT ... FROM v_safe_for_beta_unfiltered
WHERE quality_review_status::text = ANY (ARRAY['approved','unverified']::text[])
  AND (pipeline_metadata IS NULL OR NOT (pipeline_metadata::jsonb ? 'demoted_at'));
```

## Yeni beta havuzunun dağılımı (123,233)

| Status | Source | n | % |
|---|---|---|---|
| unverified | v4.14e Gemini Flash | 105,283 | 85.43 |
| approved | v3.5+ phase4 | 17,804 | 14.45 |
| approved | other edge | 94 | 0.08 |
| approved | NULL metadata | 52 | 0.04 |

## NULL handling kararı

`pipeline_metadata::jsonb ? 'demoted_at'` NULL metadata için NULL döner; NOT NULL = NULL → satır eleniyor. WHERE'e `pipeline_metadata IS NULL OR NOT (...)` ekledim → 52 NULL-metadata satır (hepsi approved) korundu. Defansif yaklaşım: NULL = "key yok = demoted değil" yorumuyla.

## Rollback hazır

Tek statement, migration dosyasının yorumunda. Dry-run yapıldı, 161,028 döndü. Beta öncesi her an çalıştırılabilir.

## Önceki turun düzeltmeleri

- "Manual_review_queue → view filter eksik" hipotezi (12 May 2026 önceki tur) **yanlış model** kanıtlandı — queue'daki 1,833 pending'in tamamı `old_question_id IS NULL`, qb'ye referans değil.
- "Pipeline kendi çıktısına güvenmemiş" hipotezi (önceki tur) **yanlış**: pending=2,775'in %98.67'sinde pipeline metadata "anomaly=[]+needs_review=false" diyor. Pending status import default'u.
- "Rename pattern" anlatımı (önceki tur) **yanlış**: ALTER VIEW kullanılmış, rename değil.
- Stale benchmark hatası bu turda **tekrarlanmadı** — beklenen post-count önceden ölçüldü, sonuç birebir eşleşti.

## Açık konular

| Konu | Önem | Sonraki aşama |
|---|---|---|
| 105,283 v4.14e Gemini hâlâ beta'da | YÜKSEK | Aşama 2 (a/b/c varyantları açık) |
| Pending temiz 2,738 hâlâ dışarıda | ORTA | Aşama 3 (toplu approve) |
| Backend code'da `v_safe_for_beta` callsite haritası eksik | DÜŞÜK | Lokal grep gerekli |
| Doc'taki 50+ maddenin yeniden önceliklendirilmesi (L5) | ORTA | Ayrı tur |

## Beta için anlam

- Demoted-low-confidence (tier_f) satırları artık beta'da gösterilmeyecek.
- Yanlış cevap riski %22 daha düşük (38,871/161,028 oran).
- Geri kalan büyük risk: v4.14e Gemini Flash yapısal zayıflığı (STRATEJI_B_KARAR.md'de zaten dokümante).
- IRT calibration bias riski: B-bias artık sadece v4.14e Gemini grubundan gelecek (demoted'ın A+E uçları temizlendi).

---

**Sonraki strateji kararı:** Aşama 3 (pending temiz approve) veya Aşama 2 varyantları için kullanıcı kararı bekleniyor.

## STATUS: TAMAM
