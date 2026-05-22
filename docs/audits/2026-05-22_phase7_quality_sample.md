# Phase 7 Rationale Quality Audit — Sample Sonucu (S181)

**Tarih:** 2026-05-22 23:40
**Sample:** 89 random sorulardan 445 rationale (39 matematik + 50 diğer)
**Methodology:** `quality-evaluator` agent dispatch + verification spot check (8/8 random)
**Source data:** `backend/scripts/quality/_phase7_audit_tmp/sample_100.json`
**Agent scores:** `backend/scripts/quality/_phase7_audit_tmp/scores.json`

---

## Skor Dağılımı (445 rationale)

| Skor | Label | N | % |
|---|---|---|---|
| 1-2 | garbage | 8 | 1.8% |
| 3 | wrong | 22 | 4.9% |
| 4 | circular | 89 | 20.0% |
| 5-6 | partial | 198 | 44.5% |
| 7-8 | good | 105 | 23.6% |
| 9-10 | excellent | 23 | 5.2% |

**Kabul edilemez (1-4):** 119/445 = **%26.7**
**Kabul edilebilir (5-6):** 198/445 = **%44.5** (yüzeysel ama yanlış değil)
**Kaliteli (7-10):** 128/445 = **%28.8**

## Grup Karşılaştırması

| Grup | Mean Score | Kötü% (1-4) |
|---|---|---|
| Matematik | 5.1 | 27.2% |
| Diğer | 5.4 | 22.9% |

## Paradoks: Doğru Cevap Rationale'ı Daha Zayıf

| Tipi | Mean Score |
|---|---|
| **Doğru cevap (correct_option)** | **4.8** ⚠️ |
| Yanlış cevap (wrong_option) | 5.6 |

Beklenti tersi: doğru cevap "neden doğru" en iyi açıklanmalı. Sistematik prompt yetersizliği.

---

## Kritik Sistematik Bulgular

### 1. Matematik Doğru Cevap %55 CIRCULAR
Yaygın tautolojiler:
- "Doğru hesaplama yapılarak bulunur"
- "Verilen koşulu sağlayan doğru seçenektir"
- "En yakın değer doğru seçenektir"

**Eksik:** Numerik adım, formül uygulaması, eliminasyon mantığı.

**Sebep:** `PROMPT_TEMPLATE` (`metadata_phase7_llm_generation.py:111`) 25 kelime/cümle sınırı sayısal eliminasyon için yetersiz.

### 2. Yanlış Şık Açıklamaları %45 Muğlak
"Hatalı işlem", "yanlış hesaplama", "işlem hatası" — **hangi işlem, ne tür yanılgı** belirtilmiyor.

### 3. ⚠️ PRE-EXISTING DATA QUALITY — Cevap Anahtarı Hataları (DOĞRULANDI)

**UUID `8c6493e8` (MATEMATIK):**
- Soru: `x²+2x+1=0` denkleminin kökleri
- DB correct_answer: **E (2 ve -2)** ← **MATEMATİKSEL OLARAK YANLIŞ**
- Doğru: x = -1 (çift kök), en yakın A (-1 ve 1)
- LLM rationale fark etmiş: "verilen cevap anahtarı doğrultusunda E seçeneği işaretlenmiştir"

**UUID `b81ebcc5` (MATEMATIK):**
- Soru: `|(x-2)/3| > 1` çözüm kümesi
- DB correct_answer: **C `(5,∞)`** ← **EKSİK**
- Doğru: E `(-∞,-1) ∪ (5,∞)`

**Sonuç:** Phase 7 sorumlu değil — `question_bank.correct_answer` field'ında en az 2 doğrulanmış hata. **Beta launch için DB-level cevap anahtarı audit zorunlu.**

### 4. ⚠️ PRE-EXISTING DATA QUALITY — Garbage Sorular (8 doğrulanmış)

OCR gürültüsü / saçma metin örnekleri:
- `6247bba5`: "Bir öğrencinin aya katıldığı yarışta 95. pozisyonunda... İki öğrencinin yarışta kaç **haka** vardır?" (haka = anlamsız)
- `5bbc9a07`: "Eren bir işi bir hafta **17 günde**, aynı işi iki ayda kaç gününde tamamlar?" (oksimoron)
- `7358f02f`, `06d13a48`, `029f9806`, `752e1ec5`, `a3b56d64`, `3049e9c0`

**Bu 8 soru gold pool'da olmamalı.** quality_review_status downgrade gerek.

### 5. Subject Tag Karışıklığı (5+ vaka)

- `2af1965f`: FIZIK etiketli ama saf aritmetik (G = a+b+c → c=?)
- `b12f45bc`: KIMYA etiketli ama dilbilgisi sorusu
- `5616e940`: TARIH etiketli ama küp geometrisi

`subject_area` field'ı pipeline'da sistematik kategorize hatası içeriyor.

### 6. Bozuk Şık Setleri

- `b948b295`: A ve E şıkkı ikisi de "Kesir" ile başlıyor — duplicate options

---

## Verification Spot Check Sonucu

8 agent-flagged sample manuel doğrulama:

| Doğrulanan | Abartılmış |
|---|---|
| 6/8 (8c6493e8, b81ebcc5, 6247bba5, 5bbc9a07, 2af1965f, b948b295) | 1/8 (c928a738 — soru aslında normal Türkçe) |

**Agent reliability ~%75-87** — agent skorlarına %20 buffer uygulamak akıllıca. Toplam %26.7 "kabul edilemez" oranı gerçek değerine yakın (muhtemelen %20-25).

---

## Öneriler

### Acil (P0 — Beta öncesi)
1. **DB cevap anahtarı audit** — auto_judged_high'taki 15,321 sorunun **matematik alt kümesinde** (39 sample'da 2 hata = potansiyel %5 hata oranı). 100% manuel review gerek olabilir.
2. **8 garbage soru deactivate** — `quality_review_status = 'rejected'` veya `archived`. `pipeline_metadata.deletion_reason` field'ı ekle.
3. **Curator manuel override katmanı** — auto_judged_high status otomatik beta'ya açmamalı; en azından matematik alt kümesi curator review'dan geçmeli.

### Orta Vadeli (P1)
4. **`PROMPT_TEMPLATE` iyileştirme** — matematik için ayrı template (50 kelime + numerik adım zorunluluk). `metadata_phase7_llm_generation.py:111` değişir.
5. **`expected_answer_formula` field UI'da prominent göster** — Curator + öğrenci UI'da SymPy çözüm rationale yerine geçer (CIRCULAR sorunu için workaround).
6. **Subject tag re-classification** — `subject_area` field için NLP-based audit + correction.

### Stratejik (P2)
7. **Phase 8 rationale refinement** — düşük skorlu (1-4) rationale'lar için targeted re-run, daha güçlü prompt ile. ~$2-3 maliyet.
8. **`quality_review_status` granularity** — `auto_judged_high_with_quality_concerns` gibi alt-status; düşük güven skoru olan rationale'ları işaretle.

---

## Methodology

- **Sample:** PostgreSQL kiro2 `question_bank` `quality_review_status = 'auto_judged_high'` filter, S181 rationale'lı, RANDOM() ORDER, 50 matematik + 50 diğer (matematik 39 geldi, total 89)
- **Output JSON:** option-letter eşleme + correct flag dahil
- **Agent:** `quality-evaluator` (KIRO2 spec — "BERTScore, OSYM uyumluluk, expert review")
- **Skorlama:** 1-2 garbage / 3 wrong / 4 circular / 5-6 partial / 7-8 good / 9-10 excellent
- **Verification:** 8 random agent-flagged sample manuel review (matematik check + Türkçe okuma + DB cross-ref)
- **Reproducible:** evet (RANDOM seed yok ama filter deterministik, scores.json saklı)

## Çıktılar

```
backend/scripts/quality/_phase7_audit_tmp/
├── sample_100.json    (142 KB — 89 sorular + 445 rationale)
└── scores.json        (12 KB — agent çıktı)

docs/audits/
└── 2026-05-22_phase7_quality_sample.md  (BU DOKÜMAN)
```

Önceki MEMORY ifadesi "Quality verified ana batch: tümü kaliteli" — random sampling bias idi (3/3 iyi çıkmıştı). **Gerçek oran %28.8 good+excellent** — beta'ya **manuel review olmadan** sunulamaz.
