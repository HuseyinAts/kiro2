# Post-Fix Audit — Faz 1.5 RESULT

**Tarih:** 15 May 2026 (Session 158)
**Sample:** 30 random satır (md5 hash seed, reproducible)
**Plan v1 hedef:** missing_diagram dilimi < %5

## TL;DR

**Hedef SAĞLANMADI**: missing_diagram dilimi şu an **%30.05** (hedef <%5).
Pipeline-fix etkisi büyük (49,313 → 14,817, %70 düşüş) ama yetersiz.

## DB durumu (Session 158 post-fix)

| Kategori | n |
|---|---|
| has_diagram=true, image_url=NULL | **14,817** (missing) |
| has_diagram=true, image_url=var | 34,496 (pipeline-fix sonrası) |
| has_diagram=true toplam | 49,313 (audit baseline ile aynı) |
| **Missing dilimi** | **%30.05** |

### Tier dağılımı (pipeline-fix katkı)

| Tier | n | Session |
|---|---|---|
| Tier A/B (legacy populate) | 59,187 | <Session 157 |
| Tier C (exact_match) | 16,440 | Session 157 |
| Tier D (page_match_other_q) | 13,741 | Session 158 |
| Tier E (q_no orphan) | 4,315 | Session 158 |
| **Toplam pipeline-fix katkı (C+D+E)** | **34,496** | |

Aktif image_url coverage: %35.3 (pre-Tier C) → **%46.1 (post-Tier E)**

## 30 sample dağılımı

| Kategori | n | % |
|---|---|---|
| VALID_QNO | 23 | 77% |
| TRAILING_DOT | 4 | 13% |
| OTHER_INVALID | 3 | 10% |

**VALID_QNO no_match analizi (23/30):**
Bu satırların q_no DB'de geçerli sayısal, ama pipeline-fix yakalamadı. Nedenler:
- `ocr_crops/results.jsonl`'de `(book, page)` anahtarı yok → page hiç OCR'lanmamış
- Disk'te `crops/<book>/_pNNNN_qNN.png` yok → crop generation atlanmış
- Text similarity <0.70 → OCR text bozuk veya farklı segment

**Etkilenen kitaplar (sample içinden):**
- CAP-2023-AYT-Matematik AL, CAP-2022-2023-TYT-Matematik
- Bilgi Sarmal series (2022-2024 Tyt/Ayt)
- Aromat (2023-2024 Matematik, Fizik, Fen Bilimleri)
- C1CELL-2024-TYT-AYT-Geometri/Matematik
- Esen Ayt Fizik, Esen Apt Ayt Fizik 2025
- Aktif Ogrenme 2025 Tyt Fizik
- 345 Tyt/Ayt Geometri 2025

Bu kitaplar OCR pipeline'ında **eksik crop** veya **eksik page index** durumu.

## TRAILING_DOT no_match (4/30, %13)

Bunlar Tier E1a-c'nin kıramadığı satırlar — q_no parse edildi ama:
- E1a: disk'te `_pNNNN_qNN.png` yok
- E1b: ocr_crops'ta `(book, page, qno)` key match yok
- E1c: page best similarity <0.70

Yine kitap-bazlı eksiklik.

## OTHER_INVALID no_match (3/30, %10)

`KILAVUZ SORU`, `Örnek: 6` gibi template başlığı OCR'lanmış. q_no yok, Tier E2 yakalamadı çünkü page-level sim <0.70. Bu satırlar muhtemelen **gerçek bir soru numarası olmayan kitap içi örnek/açıklama**.

## Karar

Plan v1 hedef "<%5 missing" **bu pipeline-fix dalgasıyla sağlanamaz**. Sebep:
- Pipeline-fix'in matematik sınırı: ocr_crops + disk içinde **mevcut crop'larla** match yapabilir
- ~14,817 satır için disk'te ya crop yok ya ocr_text yok → pipeline-fix'in ulaşamayacağı bölge

**Bu satırlar için yol:**
1. **Faz 1.10 Re-OCR (Gemini Pro)**: ~3.6K cut-off satırı kurtarabilir
2. **Kitap-bazlı OCR re-run**: CAP, Aromat, C1CELL, Bilgi Sarmal serileri için crop generation tekrarı (ayrı iş, scope)
3. **Curator manual review**: kalan ~11K satır (3.6K dışında) Faz 3'e (Curator UI) defer
4. **Judge classification**: Faz 5 judge bu satırları "image-uncertain" olarak işaretler, beta'da skip

## Karpathy notu

Plan v1 "missing <%5" iddiası **bu pipeline dalgası tek başına yeterli değildi**. Gerçek hedef revize edilmeli:
- **Pipeline-fix alone**: ~%30 missing kabul edilir
- **+ Re-OCR (Faz 1.10)**: ~%27-28 hedef
- **+ Curator (Faz 3)**: gerçek <%5 hedefi (uzun vadeli)

Plan v1 bu bulgu ile güncellenmeli (Faz 1.5 hedefi sadece pipeline-fix etki ölçer, %5 hedef <Faz 3+Curator sonrası>).

---

*Audit script: dynamic SQL (md5 seed reproducible).*
*Sample: 30 random rows from `is_active=TRUE AND has_diagram=true AND image_url IS NULL`.*
