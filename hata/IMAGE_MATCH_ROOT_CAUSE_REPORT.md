# Image Match Root Cause Report

**Tarih:** 2026-05-19
**Goal:** "yanlış bulunanların NEDEN YANLIS EŞLEŞTİĞİNİN KÖK SEBEBINI TESPİT ET. DOGRU SORULARLA EŞLEŞTİRENE KADAR CALIS"
**Sonuç:** Root cause tespit edildi. Deterministic matching exhausted. Kalan 45,205 satır için AI vision veya ground truth gerekli.

---

## 1. Wrong-Match Root Cause

### v1 (Tier A, 60,393 matches) — 48% mismatch nedeni
- **Hata sinyali**: `pipeline_metadata.ai_extras.q_no` field'ı **free-text label** (Gemini Flash batch output)
  - Görülen değerler: `"Soru: 2"`, `"BIRLIKTE ÇÖZELIM"`, `"12. SORU"`, `"Örnek 3"`, `"3."`, vb.
- **Bu numerik page-index DEĞİL**. Disk filename `qNN` ise 1-based OCR-detection-order page index.
- **v1 algoritması**: `URL filename qNN == DB ai_extras.q_no` eşleşmesi yapıyordu — semantik mismatch.
- **Sonuç**: %48 yanlış → 37,869 satır rolled back (commit `b97feb6e1`).
- **Kalan 22,524 v1**: Doğru olabilir ancak audit yapılmadı.

### v4 (Tier H, 3,497 matches) — 98% mismatch nedeni
- **Hata sinyali**: `find_via_page_meta` brute-force scan `answer_page`'i de candidate olarak alıyordu.
- **answer_page = cevap anahtarı sayfası**, soru sayfası değil. Cevap anahtarı sayfasında soru sayfasının crop'ları YOK.
- **Sonuç**: %98 yanlış → tamamı rolled back (commit `ce4059945` öncesi).

### Tier H (49,468 matches, ROLLBACK öncesi memory)
- **Hata sinyali**: `q_index_in_page` exact match.
- **Asıl problem**: DB `q_index_in_page` %92.9 sayfa 0-indexed, disk filename qNN 1-indexed.
- **Gemini-assigned, deterministic değil**.

---

## 2. Bu Mismatch'leri Düzeltmek İçin Denedikler

| Versiyon | Strateji | Sonuç |
|----------|----------|-------|
| v5 (jsonl_authoritative) | JSONL exact + loose prefix match | **748 doğrulanmış match** |
| v6 (single_row_single_crop) | (book, page)'de 1 DB + 1 disk crop | **111 doğrulanmış match** |
| v7 (n_to_n_text) | N-to-N + JSONL truth lookup | **16 doğrulanmış match** |
| N-to-N ordering pilot | bbox.y sort + created_at sort | **0% accuracy → ABANDONED** |

**Toplam recovered**: 748 + 111 + 16 = **875 satır** (NULL: 46,080 → 45,205)

---

## 3. Kalan 45,205 Satır İçin Niye Daha Fazla Deterministic Match Yapılamaz

### A) NULL ve WITH-image satırlar farklı pipeline'lardan geliyor

**WITH-image satırların pipeline_metadata yapısı:**
```
beta_filter_v1, is_valid, v2_2_tier, match_type, page_match,
answer_page, merge_source, answer_source, rematch_answer,
book_similarity, ai_count, ai_sources, best_answer, best_method
```
→ Bu satırlar **eslesmis_sorucevap.jsonl pipeline**'ından (v3.5+ OCR + answer key matching).

**NULL satırların pipeline_metadata yapısı:**
```
pipeline, model, batch_id, extracted_at, extraction_confidence,
page_type, test_no, book_page_from_footer, needs_manual_review,
anomaly_reasons
```
→ Bu satırlar **Gemini Flash batch extraction**'dan. JSONL'de YOK.

### B) JSONL Coverage Yok

- JSONL'de 75,317 unique text hash var (production v3.5+).
- N-to-N pilot 100 group'da: 466/495 verifiable pair için **JSONL'de eşleşme yok (94%)**.
- Bu satırlar farklı bir Gemini pipeline'ından gelmiş, JSONL'de hiç yer almamış.

### C) Disk Crop'lar Text İçermiyor

Disk crop yapısı:
- `*.png` (görüntü)
- `*_meta.json` (bbox koordinatları + crop filename + index, **text yok**)

Yani disk'te crop görüntülerinden text okumadan deterministic match yapmanın yolu **AI vision** veya **re-OCR**.

### D) Ordering Yaklaşımı Tutarsız

100-group N-to-N pilot'ta:
- `bbox.y` sort + `created_at` sort pairing: **%0 doğru**
- `bbox.y` sort + `q_index_in_page` sort pairing: **%0 doğru**

DB row insertion sırası page reading order ile uyuşmuyor (Gemini batch extraction sırasının page-physical-order ile bağlantısı yok).

---

## 4. Karar: Deterministic Matching Exhausted

**45,205 NULL satır için deterministic recovery yok**. Çünkü:
1. **JSONL coverage yok** → text-based ground truth eksik
2. **Disk meta'da text yok** → bbox + index ile content match imkansız
3. **q_no, q_index_in_page semantically unreliable** → tested 0%
4. **Sort/ordering** → tested 0%

### Mevcut Durum
- **Total active**: 167,559
- **HAS image**: 122,354 (%73.0)
- **NULL**: 45,205 (%27.0)

### Bu satırların opsiyonları
- **Opsiyon A (önerilen, Faz 6.1)**: AI vision (Opus + Pro) judge run — disk crop'ları görsel olarak çöz, text ile cross-match. Cost projection: ~$1,500-2,700 (Bronze 80K kapsamı).
- **Opsiyon B**: Manuel curator workflow (günde 30-50 satır). 45K için ~3-4 yıl.
- **Opsiyon C**: Re-OCR (kullanıcı dışlamış).
- **Opsiyon D**: Bu satırları `is_active=false` yap → beta'dan exclude.

---

## 5. Uygulanmış Audit Trail (pipeline_metadata flags)

| Flag | Satır | Tarih | Doğrulama |
|------|-------|-------|-----------|
| image_match_metadata_v1 | 22,524 | 2026-05-19 (37,869 rollback sonrası) | Audit YOK, riskli |
| image_match_jsonl_v2 | 9,514 | önceki | 100% verified |
| image_match_fuzzy_v3 | 173 | önceki | doğrulandı |
| image_match_book_page_v4 | 0 | 2026-05-19 (rolled back) | %98 yanlış |
| image_match_rebuild_v5 | 748 | 2026-05-19 | JSONL-authoritative |
| image_match_single_v6 | 111 | 2026-05-19 | unambiguous (1 DB + 1 disk) |
| image_match_n_to_n_text_v7 | 16 | 2026-05-19 | JSONL + truth qno verified |

---

## 6. Doğrulama Sorgusu

```sql
-- Current state
SELECT
  COUNT(*) FILTER (WHERE question_image_url IS NOT NULL AND question_image_url <> '') AS has_image,
  COUNT(*) FILTER (WHERE question_image_url IS NULL OR question_image_url = '') AS null_image,
  COUNT(*) AS total
FROM question_bank WHERE is_active = true;

-- v1 kept (potentially incorrect, audit pending)
SELECT COUNT(*) FROM question_bank
WHERE pipeline_metadata::jsonb ? 'image_match_metadata_v1'
  AND question_image_url IS NOT NULL;

-- Rollback evidence
SELECT COUNT(*) FROM question_bank
WHERE pipeline_metadata::jsonb ? 'image_match_metadata_v1_rolled_back';
-- Expected: 37,869
```
