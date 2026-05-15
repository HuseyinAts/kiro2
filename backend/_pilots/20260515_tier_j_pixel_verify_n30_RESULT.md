# Tier J Pre-Audit — Pixel-Verify n=30 RESULT

**Tarih:** 15-16 May 2026 (Session 161)
**Method:** Claude Opus 4.7 (1M context) multimodal — 30 PNG image + qtext + image_ocr_text yan yana karşılaştırma
**Sample:** Random seed=42, drift<0.85 olan satırlardan (substantive_drift + severe_drift + moderate_drift karışık)
**Source:** `_pilots/20260515_tier_j_pixel_sample_GEOMETRI.tsv`

---

## 1. Verdict Kategorileri

| Kategori | Anlam | Tier J yön |
|---|---|---|
| `format_only` | qtext ve image_ocr semantik aynı, sadece LaTeX vs Unicode rendering farkı | 🟡 NO-OP (Tier J apply LaTeX'i Unicode'a çevirir, UI render kaybı) |
| `image_ocr_better` | qtext'te içerik hatası var, image_ocr image'a uyumlu | ✅ GAIN |
| `qtext_better` | image_ocr'da yeni hata var (Tier I OCR introduced), qtext doğru | ❌ LOSS |
| `both_wrong` | Hiçbiri image'a uymuyor | curator queue |
| `unclear` | Image okunamaz | manuel review |

---

## 2. 30 Sample Detay (sıralı)

| # | id | drift | Verdict | Ne oldu? |
|---|---|---:|---|---|
| 1 | db904600 | 0.83 | `format_only` | LaTeX `$[AD]\perp[BC]$` vs Unicode `[AD] ⊥ [BC]` |
| 2 | 26446d2a | 0.60 | `format_only` | Aynı içerik, LaTeX/Unicode |
| 3 | 08675020 | 0.44 | **image_ocr_better** | qtext eksik `|AC|=x cm` satırı + bozuk `\perp` (`AB ot BC`) |
| 4 | fe29d62d | 0.36 | `format_only` | `\widehat{}` vs Unicode `͡` |
| 5 | 5cdc1837 | 0.33 | `format_only` | Aynı |
| 6 | 541749ca | 0.33 | `format_only` | Aynı |
| 7 | 4c940d5d | 0.73 | `format_only` | Aynı |
| 8 | 301d21e9 | 0.30 | **image_ocr_better** | qtext "AD⊥BE", image+ocr "AB⊥BE" (segment hatası) |
| 9 | fcf1e4d1 | 0.59 | `format_only` | Aynı |
| 10 | 20a2fe4f | 0.28 | **image_ocr_better** | qtext "[CA teğet, A noktası çemberde", ocr "[CA çembere A noktasında teğet" (image word order match) |
| 11 | e948b157 | 0.55 | **qtext_better** | ocr Alan'a `\widehat{ENG}` eklemiş, image düz `Alan(ENG)` |
| 12 | fdfe4dd1 | 0.61 | **image_ocr_better** | qtext `|DC|=5` ❌, image `|DC|=√5`, ocr `|DC|=√5` ✅ |
| 13 | bdf36019 | 0.72 | **image_ocr_better** | qtext bozuk LaTeX `^ ext{o}` (parse fail), ocr Unicode `°` |
| 14 | 1b1a1155 | 0.43 | `format_only` | Aynı |
| 15 | cccc15ae | 0.75 | `format_only` | LaTeX `\parallel` vs `//` |
| 16 | 8fbd91c8 | 0.83 | **image_ocr_better** | qtext "BD⊥EC", image+ocr "EC⊥CB" (segment) |
| 17 | 0b8a0f66 | 0.18 | **image_ocr_better** | qtext "AB⊥AD" ❌, image "AB⊥AC", ocr "AB⊥AC" ✅ |
| 18 | 0aa793d0 | 0.62 | `format_only` | `\text{DEFG}` vs `DEFG` |
| 19 | 1d08c6cf | 0.33 | `format_only` | Aynı |
| 20 | 4a5834a8 | 0.35 | **image_ocr_better** | qtext "[DF]∥[AB]" ❌, image+ocr "[DF]⊥[AB]" (∥ vs ⊥, KRITIK) |
| 21 | 4f6b5732 | 0.53 | `format_only` | Aynı |
| 22 | ae1091b0 | 0.39 | **image_ocr_better** | qtext "|EFI|=6" italic-I OCR hatası, ocr "|EF|=|FC|=6" ✅ image |
| 23 | d079b8ba | 0.71 | **image_ocr_better** | qtext "m(ABC)=45°" ❌, image+ocr "m(ABC)<45°" (= vs <, **KRITIK** matematik) |
| 24 | 08f55cce | 0.28 | `format_only` | Aynı |
| 25 | c407cb48 | 0.50 | **image_ocr_better** | qtext "[AB]∥[BC]" ❌, image+ocr "[AB]⊥[BC]" (paralel vs dik, **KRITIK**) |
| 26 | 4472a963 | 0.28 | `format_only` | Aynı |
| 27 | f6e48f8c | 0.58 | **image_ocr_better** | qtext "m(EDC')=α" ❌, image+ocr "m(EB'C)=α" (nokta etiketleri) |
| 28 | ded93d26 | 0.54 | **qtext_better** | ocr italic I yanlış okumuş `IAEI` vs qtext doğru `|AE|` |
| 29 | f3d1b0ac | 0.53 | `format_only` | Aynı |
| 30 | 8ee0778d | 0.50 | `format_only` | Aynı |

---

## 3. Toplu Skor

| Kategori | n | % |
|---|---:|---:|
| `format_only` | **16** | **53.3%** |
| `image_ocr_better` | **12** | **40.0%** |
| `qtext_better` | **2** | **6.7%** |
| `both_wrong` | 0 | 0% |
| `unclear` | 0 | 0% |
| **TOPLAM** | **30** | **100%** |

**Net Tier J value (per row):**
- Gain: 12/30 (40%)
- Loss (qtext degradation): 2/30 (7%)
- LaTeX-to-Unicode degradation: 16/30 (53%) — UI render quality kaybı

---

## 4. KRİTİK BULGULAR

### 4.1 Drift_sim format'a hassas, content'e değil

`substring_overlap` algoritması **LaTeX vs Unicode rendering farkını drift olarak gösteriyor**. 30 sample'ın %53'ü pure formatting drift. Buna göre **drift_sim METRİK GÜVENİLMEZ** — gerçek qtext kalitesi ölçmek için format-aware similarity gerekir.

### 4.2 Tier I gerçekten qtext düzeltebileceği fırsatlar var (%40)

12 satırda Tier I'ın image_ocr_text'i, legacy qtext'teki gerçek hataları tespit ediyor:
- **2 KRİTİK matematik anlam hatası** (= vs < / ∥ vs ⊥) — cevabı tamamen değiştirir
- **6 segment/nokta etiketi hatası** (AD vs AB, EDC' vs EB'C, AB⊥AD vs AB⊥AC, BD⊥EC vs EC⊥CB, ...)
- **2 italic-I OCR hatası** (|EFI| vs |EF|=|FC|)
- **1 √ kayıp** (|DC|=5 vs |DC|=√5)
- **1 bozuk LaTeX** (`^ ext{o}` parse fail)

### 4.3 Blind Tier J YASAK

Net etki:
- 40% gain (12 row qtext fix)
- 60% loss (16 row LaTeX → Unicode + 2 row ocr typo)
- **NET NEGATIVE** — beta UI render quality düşer, sadece içerik fix sayısı küçük

---

## 5. Smart Tier J — 3 Olası Strateji

### Strateji A: Heuristic Filter (hızlı, low-risk)

Sadece qtext'te bozuk LaTeX pattern olan satırlarda Tier J apply:

```python
# Tier J apply candidate filter
def is_qtext_broken(qtext: str) -> bool:
    patterns = [
        r"\\perp ot",        # broken \perp split
        r"\^ ?ext\{",        # \\text{} mangled
        r"\\widehat\{[^}]{0,1}\}",  # empty/short widehat
        r"[^a-zA-Z]I[^a-zA-Z]",     # italic-I as letter
        r"AB ot",            # any "X ot Y" perpendicular
    ]
    return any(re.search(p, qtext) for p in patterns)
```

Tahmin: 1,254 GEOMETRI drift satırının ~%20-30'u broken LaTeX bulunur (~250-380 satır). Bunlarda Tier J yüksek güvenlikle uygulanabilir.

### Strateji B: Format-Aware Re-Audit

Audit script revize: similarity hesabı önce LaTeX → Unicode normalize, sonra karşılaştır. Gerçek "content drift" bucket'ı çıkarır:

```python
def normalize_latex_to_unicode(s):
    s = re.sub(r"\$([^$]*)\$", r"\1", s)  # strip $
    s = re.sub(r"\\perp", "⊥", s)
    s = re.sub(r"\\parallel", "∥", s)
    s = re.sub(r"\\sqrt\{?(\w+)\}?", r"√\1", s)
    # ...
    return s

# True content drift = format_normalized_substr_overlap < 0.85
```

Bu ayıkla → format_only false positive'leri düşer, gerçek hata satırları öne çıkar.

### Strateji C: Judge-Based (en güvenli, daha pahalı)

Drift>0.30 satırları **Faz 5+6 judge pipeline**'a ver. Judge "qtext mı ocr mı doğru, hangisini sakla" karar versin.
- Cost: 1,254 × $0.02 = ~$25 ek
- Doğruluk: en yüksek (Opus+Pro double check)
- Hız: 1.5h paralel

### Önerilen: Strateji B → A → C

1. Önce **B (format-aware re-audit)** çalıştır → gerçek content drift count netleşir
2. Eğer sadece ~50-100 content drift varsa → Strateji A heuristic + manuel review
3. Eğer 200+ content drift varsa → Strateji C judge pipeline'da işle

---

## 6. Toplam Round 1 + 2 + 3 = n=42

Tüm pixel-verify sessionlarını birleştir:

| Round | n | URL | image_ocr image-uyum | qtext image-uyum |
|---|---:|---:|---:|---:|
| Round 1 (Tier I postaudit, geometri) | 7 | 7/7 | 7/7 | 5/7 (2 substantive) |
| Round 2 (non-geometri spot-check) | 5 | 5/5 | 4/5 (1 minor KIMYA) | 5/5 |
| Round 3 (Tier J pre-audit, geometri drift) | 30 | (URL audit yapılmadı) | 28/30 effective (16 format + 12 better) | 16/30 effective (16 format + 2 better) |
| **TOPLAM** | **42** | **12/12 ✅** (Round 1+2 audit) | image_ocr çoğunlukla doğru | qtext geometri'de %30-40 hatalı |

---

## 7. Sıradaki Adımlar (revize)

1. ✅ Bu RESULT commit
2. **Strateji B: format-aware re-audit script** — `tier_j_qtext_audit_v2.py` (~30 dk)
3. **B sonrası karar**: gerçek content drift sayısı → A veya C strateji seçimi
4. Eğer content drift >100 → **Faz 4.1 (200 manuel curated set)** önceliğe gir, judge pipeline tüm Bronze'a hizmet eder

---

## 8. Lessons Learned

1. **substring_overlap LaTeX/Unicode farkına HASSAS** — drift>0.30 olmasına rağmen %53'ü format farkı, gerçek anlam aynı
2. **Tier I image_ocr Unicode → blind apply LaTeX kaybı = beta UI render quality düşer** — sadece broken qtext varsa value
3. **Geometri ZORLU OCR target** — segment etiketleri, perpendicular/parallel sembolleri, √ ve fraction'lar yanlış okunabilir; legacy pipeline %40 hatalı, Pro re-OCR çok daha iyi
4. **Karpathy "Önce Düşün" kanıtı** — Tier J pre-audit drift>0.30 için %72.6 dedi, ama %40'ı gerçek gain. Apply öncesi pixel-verify Tier H rollback dersini doğruladı (sample bias yok ama metrik bias var)
5. **2 KRİTİK matematik hatası** (sample 23, 25) — = vs <, ∥ vs ⊥ — cevabı tamamen değiştirir. qtext kullanan beta öğrenci YANLIŞ cevap görür. Tier J'in gerçek değeri burada

---

*Round 3 — Tier J pre-audit pixel-verify, n=30 GEOMETRI sample, Claude Opus 4.7 multimodal.*
