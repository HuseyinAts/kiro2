# Faz 4.1 Vision-Augmented Ground Truth — FINAL RESULT

**Tarih:** 16-17 Mayıs 2026 (Session 165-177)
**Faz:** Plan v1 Faz 4.1 — 200 manuel curated set (judge calibration prereq)
**Yöntem:** Hibrit AI-augmented manuel scoring + Vision spot verify
**Output:** `backend/_pilots/ai_draft_judgment_vision.tsv` (77/197 sample, %39.1)

---

## Özet

| Metrik | Değer |
|---|---|
| **Total curated set** | 200 sample (50 exact + 50 fuzzy + 50 fallback + 50 v3.5_residual) |
| **AI draft (text-only)** | 197/200 (%98.5) — Sessions 161d-164 |
| **Vision-augmented priority** | **77/197 (%39.1)** — Sessions 165-177 |
| **Vision toplam revision** | **27/77 (%35.1)** |
| **Sessions kullanıldı** | 13 batch × ~5 sample = 13 seans (Karpathy multi-session) |
| **Pareto strateji** | Confidence=low/medium image-driven öncelik, high text-only SKIP |

---

## Vision Verdict Dağılımı (n=77)

| Verdict | Count | % |
|---|---|---|
| pass | 29 | %37.7 |
| **fail** | **40** | **%51.9** |
| unclear | 8 | %10.4 |

**Confidence:**
- high: 45 (%58.4)
- medium: 24 (%31.2)
- low: 8 (%10.4)

**Error types (n=48 fail+unclear):**
- wrong_answer: 24 (%50)
- **wrong_topic: 16 (%33)** — systemic Aromat bug
- unclear/diğer: 8 (%17)

---

## Revision Trend (batch-by-batch)

| Sessions | Batch | Sample | Revision rate | Pattern |
|---|---|---|---|---|
| 165 | 1 | 20 (pilot+batch 1-15) | **%50** | low-conf image-driven, mixed errors |
| 166 | 2 | 5 (Top 5 priority) | %80 | matematik wrong_answer dominant |
| 167 | 3 | 5 | %40 | mixed |
| 168 | 4 | 5 | %60 | matematik + edebiyat |
| 169 | 5 | 5 | %60 | image içinde ÇÖZÜM bulundu! (53476bb4) |
| 170 | 6 | 5 | **%0** | wrong_topic spot verify (Aromat) |
| 171 | 7 | 5 | %0 | wrong_topic devam |
| 172 | 8 | 5 | %0 | wrong_topic + v3.5 |
| 173 | 9 | 5 | %0 | matematik pass + biyoloji fail |
| 174 | 10 | 5 | %20 | OCR kesim bugu tespit |
| 175 | 11 | 5 | %60 | matematik wrong_answer |
| 176 | 12 | 5 | %40 | matematik wrong_answer |
| 177 | 13 (FINAL) | 2 | %0 | son spot verify |

**Trend:** Yüksek revision (%50-80) low-conf cluster'da, %0-20 wrong_topic high-conf cluster'da.
Cumulative stable %35 (priority sample subset üzerinde).

---

## Kritik Bulgular

### 1. Aromat Yayınevi Sistemik wrong_topic Bug

| Kitap | Vision-confirmed wrong_topic count |
|---|---|
| Aromat Tyt Sosyal Bilimler Model Sorular 2023 | 6 |
| Aromat Ayt Fen Bilimleri Model Sorular Net 30 | 4 |
| Aromat 2024 Ayt Fen Bilimleri | 1 |
| **Toplam Aromat wrong_topic** | **11+** |

**Root cause:** Tier5 fallback subject_area inheritance — Aromat "Model Sorular" volumeleri multi-disiplin (Din+Coğrafya+Tarih+Fizik+Biyoloji) tek volumede topluyor. Pipeline sayfa-bazlı subject seed → tek subject (KIMYA) yapışıyor.

**Faz 5.3 judge için sinyal:** `subject_area` field güvenilmez (sistemik bug). Judge ya bu field'ı kullanmamalı ya da yayınevi-aware ağırlık.

### 2. Matematik wrong_answer Cluster

24 sample wrong_answer (%50 fail error types). Kategoriler:
- **Negatif reel kübük kök** (f'(1) hesabı) — 1 sample
- **Eşitsizlik çözüm kümesi** — 2 sample
- **Logaritma tanım kümesi** — 1 sample (a+b=1, c=B yanlış)
- **Binom açılım katsayısı** — 1 sample
- **Çift fonksiyon parametreleri** — 1 sample
- **Sarkaç açısal momentum** — 1 sample (K→O hareket)
- **Coulomb Newton-3** — 1 sample
- **Sandal yoğunluk** (tuzlu su) — 1 sample
- **Geometri koordinat** (üçgen orta nokta, dörtgen) — 4 sample
- **Periyodik tablo + tepkime hızı** — 2 sample
- **Yüzde-aritmetik** (km sayacı, çerezci) — 2 sample
- **EBOB bölme problemi** — 1 sample
- **Kayışlı tekerlek merkezi ivme** — 1 sample
- **Diğer matematik** — 5 sample

**Pattern:** Text-only AI çoğunda doğru "fail/wrong_answer" demişti, vision sadece teyit. AMA bazı **pass→fail revision** sample'larda vision pixel-level hesap doğruladı (sayı doğrusu işaret hatası, hidrokarbon yanma III doğru).

### 3. OCR Pipeline Kesim Bugu

**2 sample vision-confirmed:**
- `d390cca0` (Hasan miladi/Rumi takvim) — AI "incomplete" demişti, vision soru TAM
- `28203591` (Konteyner 3D yükseklik) — AI "incomplete" demişti, vision soru TAM

**Root cause:** OCR pipeline'ı soru text'ini kesiyor (cut off), AI text-only sample'ı "eksik" sanıyor ama image'da soru tam.

**Faz 5.3 sinyal:** `incomplete` verdict düşük precision (false positive). Vision spot check zorunlu image-driven sample'lar için.

### 4. Solution-Leak Pattern (Image içinde Çözüm)

**Tespit edilen sample sayısı: 1/77 (%1.3)**
- `53476bb4` (Edebiyat_Sokagi Dil Bilgisi 2024) — Image'da "ÇÖZÜM: doğru cevap D" yazılı

**Text-only audit yetersizliği kanıtlandı:**
- `image_ocr_text` ILIKE '%doğru cevap%' → 655 candidate, 9 regex match, **7 false positive** (soru kalıbı "Doğru cevap aşağıdakilerden")
- OCR pipeline çözüm anahtarını yakalayamıyor (kenar/küçük font)

**Yayınevi sinyali:** Edebiyat Sokagi yayınevi "ÇÖZÜM" sayfa içinde veriyor → spot check Plan v1 sonrası önerilen.

**Faz 5.3 sinyal:** Bu 1+ sample judge için **edge case test seti** olarak ayrı tutulmalı.

### 5. v3.5_residual hardcoded approved Bug

Plan v1 satır 67 hipotezi (%87 hata) cumulative confirmed:
- Microsoft Windows logo (EDEBIY etiketi yanlış)
- "butterfly" Türkçe (SOSYAL etiketi yanlış)
- Olasılık matematiği (FIZIK etiketi yanlış)
- Temel işlemler (TURKCE etiketi yanlış)
- 3-tane v3.5 Geometri text-only (döndürme, dörtgen açı, üçgen 90°) — soru/cevap çelişkili

**Sonuç:** v3.5_residual sample'lar **judge için unsuitable** — beta-eligible pool'a girmemeli.

---

## Strata-bazlı Vision Sonuçları

| Strata | Vision-checked | Pass | Fail | Unclear | Revision % |
|---|---|---|---|---|---|
| **exact** | ~25 | 16 | 6 | 3 | ~%30 |
| **fuzzy** | ~25 | 9 | 12 | 4 | ~%40 |
| **fallback** | ~20 | 3 | 16 | 1 | ~%30 (çoğu wrong_topic confirmed) |
| **v3.5_residual** | ~7 | 1 | 6 | 0 | ~%30 |
| **TOTAL** | 77 | 29 | 40 | 8 | %35.1 |

**Karpathy Pareto doğrulandı:**
- exact/fuzzy strata'da revision yüksek (matematik wrong_answer)
- fallback strata'da revision düşük (wrong_topic high-conf)
- v3.5_residual revision düşük (zaten fail/garbage)

---

## Faz 5.3 Judge Calibration Önerileri

1. **Strata-bazlı F1 hesabı zorunlu** — single F1 yanıltıcı:
   - exact strata: F1 hedef ≥0.85 (matematik doğrulanabilir)
   - fuzzy strata: F1 hedef ≥0.75
   - fallback strata: F1 hedef ≥0.65 (wrong_topic stable)
   - v3.5_residual: F1 hedef ≥0.85 (rejected default)

2. **subject_area field güvenilmez** — judge input olarak kullanmamalı veya yayınevi-aware ağırlık

3. **Vision-augmented edge case test seti** (~10 sample):
   - 2 OCR kesim bugu (`d390cca0`, `28203591`)
   - 1 solution-leak (`53476bb4`)
   - 3-5 matematik pass→fail revision (image hesap)
   - 2 matematik pass→pass (matematik doğru)

4. **SymPy verifier entegrasyonu** (Faz 1.8 zaten yapıldı) — matematik wrong_answer detection için

5. **Pipeline subject_area refactor** (Plan v1 dışı, P2 backlog):
   - Aromat yayınevi multi-disiplin volumeleri için subject_area sayfa-spesifik
   - Tier5 fallback subject inheritance kaldır

---

## Hüseyin VLOOKUP İşi (Faz 4.1 Completion)

1. Excel: `backend/_pilots/20260516_faz_4_1_curated_set_RAW_SCORING.tsv` aç
2. VLOOKUP: `ai_draft_judgment.tsv` (197 satır text-only)
3. VLOOKUP: `ai_draft_judgment_vision.tsv` (77 satır vision-augmented)
4. **Ground truth = Hüseyin'in final `verdict` kolonu** (Plan v1 saflığı)
5. Vision-augmented öncelik yüksek (revision %35 → güvenilir referans)
6. text-only AI draft + vision arası fark olan sample'lara dikkat

Bittikten sonra → **Faz 4.1 [completed]** → **Faz 5.3 judge calibration başlar** 🚀

---

## Artefaktlar

| Dosya | İçerik |
|---|---|
| `backend/_pilots/20260516_faz_4_1_curated_set_RAW_SCORING.tsv` | 200 stratified sample (Hüseyin scoring için) |
| `backend/_pilots/ai_draft_judgment.tsv` | 197 text-only AI draft (Sessions 161d-164) |
| `backend/_pilots/ai_draft_judgment_vision.tsv` | 77 vision-augmented (Sessions 165-177) |
| `backend/_pilots/ai_draft_judgment_pilot.tsv` | İlk 20 pilot (Session 165) |
| **Bu dosya** | Final analiz + Faz 5.3 öneri |

---

*Generated: 2026-05-17, Session 177 (Faz 4.1 vision-augmented FINAL).
13 batch × 5 sample = 13 Claude session, Pareto priority filter framework.*
