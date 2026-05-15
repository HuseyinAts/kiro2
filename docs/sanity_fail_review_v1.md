# Sanity-Fail Manuel Review (Faz 4.2)

**Tarih:** 15 May 2026 (Session 160)
**Scope:** Faz 1.4 Sanity checker (Session 158, completed) çıktısının analizi
**Total flagged:** 612 satır
**Status field:** `pipeline_metadata.sanity_flags.{duplicate_options, answer_no_option, audit_date}`

---

## Özet

| Flag tipi | Sayı | % | Eylem |
|---|---:|---:|---|
| `duplicate_options` (non-empty list) | 607 | 99.2% | OCR re-extract veya curator review |
| `answer_no_option=TRUE` | 5 | 0.8% | Manuel düzeltme veya `rejected` |
| BOTH | 0 | 0% | — |

**Toplam etki:** 612 / 167,559 aktif soru = **%0.37 sanity-fail rate** → düşük, ama içerdiği soruların hepsi öğrenciye gösterilemez (duplicate option → 5-şıklı soru efektif 4-şıklı olur).

---

## 1. Duplicate Options Pattern Analizi

OCR farklı seçeneklerin metnini aynı çekmiş. Pattern dağılımı:

| Pair | Sayı | % |
|---|---:|---:|
| **DE** | 197 | 32.4% |
| **CE** | 116 | 19.1% |
| BE | 75 | 12.3% |
| AE | 74 | 12.2% |
| BD | 69 | 11.4% |
| CD | 52 | 8.6% |
| AD | 31 | 5.1% |
| BC | 24 | 4.0% |
| AB | 18 | 3.0% |
| AC | 13 | 2.1% |

### Kritik bulgu

**E ile herhangi bir pair = 462 (%76.1).**

Yani sanity-fail satırların 4'te 3'ünde **E seçeneği başka bir seçeneğin kopyası**. Bu OCR yapısal hatası:

- E genellikle son seçenek, sayfa altında, kesime yakın
- OCR son satırı önceki satırdan kopyalamış olabilir
- Veya boş E için fallback "üstteki satır" değeri atanmış

### Yapısal kök neden (hipotez)

OCR pipeline E seçeneği için **bağımsız çıkarım yerine "son seçenek = bir önceki"** fallback kullanıyor olabilir. Pipeline'da E özel-handling kontrolü yapılmalı.

---

## 2. Subject Distribution

| Subject | Sayı | % |
|---|---:|---:|
| MATEMATIK | 153 | 25.0% |
| TURKCE | 118 | 19.3% |
| FIZIK | 79 | 12.9% |
| KIMYA | 55 | 9.0% |
| TARIH | 41 | 6.7% |
| BIYOLOJI | 38 | 6.2% |
| EDEBIYAT | 37 | 6.0% |
| GEOMETRI | 35 | 5.7% |
| GENEL | 22 | 3.6% |
| SOSYAL | 17 | 2.8% |

**Sayısal ders ağırlıklı:** Matematik + Geometri + Fizik + Kimya = 322 / 612 = **%52.6**

Hipotez: sayısal derslerde E seçeneği uzun matematik ifadesi içeriyor (LaTeX), OCR satır bölme/birleştirme hatalarına daha çok düşüyor.

---

## 3. Exam Type Distribution

| Exam | Sayı | % |
|---|---:|---:|
| TYT | 403 | 65.8% |
| AYT | 209 | 34.2% |

TYT/AYT toplam soru oranı yaklaşık eşit (~85K/77K). TYT %66 fail = TYT'de orantısız fazla. Sebep belirsiz; muhtemelen TYT kitapları (daha eski seriler) daha düşük OCR kalitesinde.

---

## 4. Top Books (top 10)

| Kitap | Sayı |
|---|---:|
| 345 2025 Ayt Matematik Soru Bankası | 41 |
| Bilgi Sarmal Ayt Edebiyat Soru Bankası | 10 |
| Esen Tyt Tarih Soru Bankası | 9 |
| Apotemi Tyt Ayt Kimya 2019-2020 | 8 |
| 345 2025 Tyt Türkçe Soru Bankası | 7 |
| Cap Tyt Konu Anlatımlı Soru Bankası 2024 | 7 |
| Esen Yks Motivasyon Biyoloji | 6 |
| 345 2025 Ayt Biyoloji Soru Bankası | 6 |
| 345 2025 Tyt Sosyal Bilgiler Soru Bankası | 6 |
| Bilgi Sarmalı Tyt Ayt Geometri Soru Bankası | 6 |

**`345 2025` serisi 4 kitap top 10'da** (Matematik, Türkçe, Biyoloji, Sosyal Bilgiler) — toplam 60 fail. Bu serinin OCR pipeline'ı tekrar ele alınmalı (kitap-bazlı pattern olabilir).

---

## 5. Önerilen Aksiyon

### Tier 1 — Bronze pool'dan çıkar (acil, Faz 1.6 öncesi)
- 612 satır → `quality_review_status='rejected'` veya `pending` (Bronze migration filter ekle)
- `bronze_clean` migration zaten sanity-fail satırları hariç tutuyor (Convention v3 §"Kim set eder?" SQL'de `duplicate_options=FALSE` filter)
- **Eylem:** Convention v3 SQL `duplicate_options` field tipini fix et — şu an `bool` cast hatası verir, list olduğu için. Düzeltme:
  ```sql
  AND COALESCE(jsonb_array_length(pipeline_metadata::jsonb -> 'sanity_flags' -> 'duplicate_options'), 0) = 0
  ```

### Tier 2 — OCR pipeline E-seçenek fix (P1, kök neden)
- Pipeline'da E option için bağımsız çıkarım kontrolü
- 462 satır recover potansiyeli (%76.1 sanity-fail'in E pair olanları)
- Test: 50 sample re-OCR'la → kaçı düzeliyor?

### Tier 3 — answer_no_option 5 satır manuel
- Curator UI'da işaret koy
- correct_answer field NULL veya yanlış format → manuel düzeltme

### Tier 4 — 345 2025 serisi audit
- 4 kitap → 60 sanity-fail (top 10'da)
- Seri-bazlı OCR pipeline parametre incele
- Eğer kitap kalitesi düşükse → tüm seriden Bronze pool'a girişi kapat

---

## 6. Bronze Pool Etkisi

Mevcut Bronze proxy pool (Convention v3 hedef): ~80K satır.

- 612 sanity-fail çıkarıldığında: ~79,388 (etki marjinal, %0.77)
- Judge eligible pool azalır ama anlamlı değil
- **Önemli:** sanity-fail rejected/pending'e taşınırsa `v_safe_for_beta` etkilenmez (zaten dahil değildi)

---

## 7. KPI

| Metrik | Değer |
|---|---|
| Toplam Bronze candidate | ~80K |
| Sanity-fail | 612 (%0.77) |
| E-option pattern | 462 (%75.5 of fails) |
| Subjects en çok etkilenen | MATEMATIK (153), TURKCE (118), FIZIK (79) |
| Top book | 345 2025 Ayt Matematik (41) |

---

## 8. Sıradaki Adımlar

1. **Convention v3 SQL fix** (Faz 1.6 prereq) — `duplicate_options` bool cast → array length check
2. **Bronze migration filter doğrula** — Faz 1.6 SQL'i `sanity_fail` satırları hariç tuttuğunu test et
3. **E-option re-OCR pilot** (Tier 2, opsiyonel) — 50 sample test, başarılıysa scale
4. **345 2025 serisi audit** (Tier 4, opsiyonel) — kitap-bazlı OCR kalite incele

---

## 9. Reproducibility

```sql
-- All sanity-fail rows
SELECT id::text, subject_area, source_book, exam_type,
       pipeline_metadata::jsonb -> 'sanity_flags' AS flags
FROM question_bank
WHERE is_active = TRUE
  AND pipeline_metadata::jsonb ? 'sanity_flags';

-- Duplicate pair distribution
SELECT jsonb_array_elements_text(
         pipeline_metadata::jsonb -> 'sanity_flags' -> 'duplicate_options' -> 0
       ) AS letter, COUNT(*)
FROM question_bank
WHERE is_active = TRUE
  AND pipeline_metadata::jsonb ? 'sanity_flags'
GROUP BY letter;
```

---

*Faz 4.2 sanity-fail review v1. Session 160. Tier 1 (Bronze filter fix) Faz 1.6 öncesi yapılmalı.*
