# Tier F — Root Cause Analizi + Asymmetric Threshold Çözümü

**Tarih:** 15 May 2026 (Session 158)
**Tetikleyici:** Faz 1.5 audit "%30.05 missing, hedef <%5 SAĞLANMADI"
**Yöntem:** Karpathy adım adım kök neden + asymmetric threshold solution

## ADIM 1: Evren-Level Kategori Profil (14,817 missing)

| Kategori | n | % | Anlam |
|---|---|---|---|
| **D_match_failed** | **14,672** | **%99.0** | Disk+OCR VAR, script match etmedi |
| C_no_page_ocr | 135 | %0.9 | Page OCR'lanmamış |
| A_no_book_dir | 10 | %0.1 | Kitap dir eksik |
| B_no_page_disk | 0 | %0.0 | Page disk'te yok |

**Kök neden**: Pipeline-fix script'lerimin **threshold kalitesi**, OCR/disk eksikliği değil.

## ADIM 2: D_match_failed Similarity Bucket (50 sample)

| sim bucket | n | % | Yorum |
|---|---|---|---|
| **0.50-0.70** | **32** | **%64** | **Tier D threshold 0.70 reddetti** |
| 0.30-0.50 | 6 | %12 | Borderline |
| <0.30 | 12 | %24 | Gerçek farklı sorular veya OCR çok bozuk |

**Kök neden detay**: CAP, Aromat, Bilgi Sarmal, C1CELL kitaplarında OCR kalitesi düşük → text similarity %50-70 bucket'a düşüyor.

## ADIM 3: Asymmetric Threshold Stratejisi

**Hipotez**: Key match (`ocr_crops`'ta `(book, page, q_no)` AYNEN var) **güçlü sinyal**. Text similarity sadece güvence. Düşük sim bile match doğru olabilir.

**Strateji**:
- **F1 (key match exists)**: sim >= 0.50 (gevşek)
- **F2 (page fallback)**: REDDEDİLDİ (D2 zaten Tier D'de yaptık)

## ADIM 4: Pilot 100 Sample Doğrulama

| Bucket | ok | unclear | Worst case accuracy |
|---|---|---|---|
| 0.50-0.60 | 40 | 9 | %82 |
| 0.60-0.70 | 42 | 8 | %84 |
| **Toplam** | **82** | **17** | **%83 worst / ~%92 realistic** |

**Unclear case'ler 2 kategori:**
1. **OCR error** (~50%): match doğru, OCR text bozuk (Barış→Başak, AF⊥LC→AF⊥EC, |DE|=2√3→√3)
2. **Math template repetition** (~50%): aynı sayfada aynı şablon farklı sayılar (x²-4 vs x²+4, C(-4,4) vs C(-4,-4))

Text-only ile ayırmak imkansız. Pipeline_metadata.tier_f_match.similarity field ile judge'a sinyal verilir.

## ADIM 5: Apply Sonucu

| Metrik | Pre-Tier-F | Post-Tier-F | Δ |
|---|---|---|---|
| image_url (aktif) | 77,243 | **84,684** | **+7,441** |
| Aktif coverage | %46.1 | **%50.54** | +%4.4 |
| has_diagram missing | 14,817 | **7,376** | -7,441 |
| **missing %** | **%30.05** | **%14.96** | **-%15.09** |

**Tier toplam:**
- Tier C: 16,440 | Tier D: 13,741 | Tier E: 4,315 | Tier F: 7,441 = **41,937 pipeline-fix kümülatif**

## ADIM 6: Hedefin Hâlâ Sağlanmadığı Bölge (7,376)

| Kategori | n | % | Çözüm önerisi |
|---|---|---|---|
| sim_below_0.50 | 5,021 | %68 | Çok bozuk OCR — Faz 1.10 Re-OCR adayı |
| no_key_match | 1,367 | %19 | ocr_crops yanlış soru_no atadı — page-level Tier G? |
| no_qno | 977 | %13 | OCR başlık yakaladı, q_no yok — Tier E2 gevşek threshold |
| no_page_ocr | 11 | %0.1 | Page hiç OCR'lanmamış — manual review |

## Karpathy Notu — Plan v1 Revize

**Pipeline-fix matematik sınırı**: %14.96 missing kabul edilebilir bound.

**<%5 hedefi için yol:**
1. **Faz 1.10 Re-OCR (Gemini Pro)**: 5,021 sim<0.50 satır → muhtemelen ~3,500 kurtarılır (%70 success rate). Missing: %14.96 → ~%7-8
2. **Tier G page-level sim<0.50 fallback (yüksek risk)**: 977 no_qno + 1,367 no_key_match için page-level best sim (judge filter). Marjinal.
3. **Curator UI (Faz 3)**: Kalan ~3,000 satır manual. <%2 ulaşılabilir.

**Realistik final hedef**: pipeline-fix + Re-OCR sonrası **%7-8 missing**, sonra curator ile **<%5**.

---

*Asymmetric threshold + defansif flag pattern = Karpathy "Önce Düşün, Cerrahi Müdahale" uygulaması.*
*Script: `backend/scripts/tier_f_recovery.py`, Pilot TSV: `_pilots/20260515_tier_f_pilot_RESULT.tsv`*
