# OCR Truncation Root Cause Investigation — RESULT

**Tarih:** 14 May 2026 (Faz 0.8, Session 156)
**Trigger:** C2 audit (50 sample) %24 OCR cut-off oranı tespit etti → Plan v1 OCR truncation acil müdahale gerekiyor sandık
**Yöntem:** 5 hipotez paralel test
**Süre:** ~30 dakika

---

## TL;DR — Şaşırtıcı sonuç

**Gerçek bir OCR truncation YOK.** C2 audit'in %24 cut-off bulgusu **methodology hatasıydı.**

```
ROOT CAUSE: 20260515_next_audit_templates.sql'de
  \copy (SELECT ..., LEFT(question_text, 200) AS question_text, ...)
                     ^^^^^^^^^^^^^^^^^^^^^^^^
  → Sample TSV insan-okunurluk için 200 karaktere TRUNCATE edildi
  → Claude bu truncated TSV'yi okuduğunda gerçek cut-off ile karıştırdı
  → DB'de tüm metinler TAM HAL ile mevcut
```

**Gerçek DB OCR cut-off oranı: %2.15** (167,559 satırın 3,598'i; çoğu legacy_v3'te).

---

## 5 Hipotez Sonuçları

| # | Hipotez | Sonuç | Kanıt |
|---|---|---|---|
| **a** | DB `question_text` VARCHAR limiti | ❌ NOT cause | `text` tipi (unlimited), max actual=2077, p99=878 |
| **b** | `eslesmis_sorucevap.jsonl` truncation | ❌ NOT cause | Sample 5 entry full text ile bitiyor (?, .) |
| **c** | Gemini Flash `max_output_tokens` | ❌ NOT cause | Main OCR config'inde max_output_tokens YOK (Gemini default 8192) |
| **d** | `import_d_dataset.py` manual limit | ❌ NOT cause | `entry.get("text", "")` direct passthrough, no slice |
| **e** | OCR prompt "kısa tut" instructionu | ❌ NOT cause | Prompt full extraction istiyor |

**5/5 hipotez REDDEDİLDİ** — pipeline'da truncation yok.

### Asıl sebep (6. hipotez, sonradan keşfedildi)

**H(f) Audit TSV methodology** — `LEFT(question_text, 200)` SQL function'ı sample TSV'yi 200 karaktere kısaltmış (insan-okunurluk için). Claude bu kısaltılmış TSV'yi gördüğünde gerçek OCR cut-off ile ayırt edemedi.

---

## Doğrulama: 5 "cut-off" entry DB'de

C2 audit'te "ocr cut-off" olarak işaretlediğim 5 entry:

| C2 # | id | TSV son chars (200 limit) | DB son chars (full text) |
|---|---|---|---|
| #2 | ebd6e4ba | "iki başrol oy" | "Serpil hangi yılda doğmuştur?" ✓ |
| #10 | 26335fac | "Bur" | "mekten kaç TL fazla tutmuştur?" ✓ |
| #12 | 8c365bc0 | "sayını" | "işleminin sonucu kaçtır?" ✓ |
| #18 | 9451ced4 | "önc" | "gitme süreleri toplamı kaçtır?" ✓ |
| #20 | e8fdca37 | "He" | "hangisi doğrudur?" ✓ |

**Hepsi DB'de tam halde, tipik soru sonu noktalama (`?`) ile bitiyor.**

---

## Gerçek OCR Cut-Off Oranı (DB-level)

```
Total active question_bank:  167,559
Cut-off (no proper end):       3,598  (%2.15)

Per quality_review_status:
  pending:               2 / 2,775     (%0.07) ← excellent
  unverified no_match:  136 / 38,871   (%0.35) ← v3.5+ residual
  unverified exact:     359 / 25,059   (%1.43) ← Gemini Flash exact
  unverified fallback:  712 / 42,212   (%1.69) ← Gemini Flash fallback
  unverified fuzzy:     971 / 40,245   (%2.41) ← Gemini Flash fuzzy
  legacy_v3:          1,418 / 18,397   (%7.71) ← legacy en kötü
```

**legacy_v3_unaudited** gerçek bir cut-off problemine sahip (%7.71). Diğerleri kabul edilebilir seviyede (<%3).

---

## Plan v1 Üzerindeki Etkiler

### 🔻 Faz 1.10 (Re-OCR cut-off entries) — SCOPE BÜYÜK ÖLÇÜDE AZALDI

**Önceki tahmin:** ~17K satır re-OCR (%24 of 146K Gemini Flash)
**Gerçek:** ~3.6K satır re-OCR (1.6K legacy_v3 + 2K Gemini Flash)
**Cost:** $50-150 → **$15-50** (~%70 düşüş)
**Süre:** 1-2 gün → **<1 gün** (sadece legacy_v3 odaklı)

### 🆕 Yeni anti-pattern rule

**`.claude/rules/audit-methodology.md` (öneri)**

```
Audit sample TSV'leri ÜRETIRKEN:
  ❌ LEFT(question_text, 200) — insan-okunurluk için truncate
  ✅ Full text export, sample size düşür (LIMIT 30 vs 200 char)
  ✅ Veya 2 sütun: question_text_preview (LEFT 200) + question_text_full
  
  Sebep: Sample TSV truncation OCR cut-off ile karışır.
  Yanlış teşhis → yanlış strateji → wasted effort.
```

### 🔄 C2 audit findings revize

C2 audit'te 12 sample "ocr cut-off" işaretlenmişti. Şimdi gerçek dağılım:

| Önceki etiket | Gerçek (DB kontrol sonrası) |
|---|---|
| 12 ocr cut-off (yanlış) | ~%2-4 gerçek cut-off (en fazla 1-2 sample) |
| 5 unclear/ocr cut-off | DB'de tam metin var → re-evaluate gerekiyor |

**Aksiyon:** C2 SCORING.tsv'deki "ocr" işaretlerini DB doğrulama ile yeniden değerlendir. Çoğu `unclear` veya `pass`'a çevrilmeli.

### ✅ Faz 0.6 Convention v3 — IMPORT VALIDATOR hala değerli

Yeni ingest için:
```
if not text.endswith(('?', '.', '!', ')', ']', '"')):
    flag as suspect (review queue)
```

Cut-off rate düşük olsa da gelecek ingest'ler için koruma değerli. Plan v1'deki rolü değişmiyor.

---

## Maliyet Tahmini Revize

| Boyut | Plan v1 (önceki) | Plan v1 (revize) |
|---|---|---|
| Faz 1.10 cost | $50-150 | **$15-50** |
| Faz 1.10 süre | 1-2 gün | **<1 gün** |
| Faz 0.8 süre | 1-2 saat | **30 dk** (tamamlandı, fix gerekmedi) |

**Tasarruf:** ~$50-100 + 1 gün dev.

---

## Çıkarılan Dersler

★ Insight ─────────────────────────────────────
**Audit methodology bias kritik.** Sample sunum şekli (truncated text) → yanlış teşhis → yanlış strateji. Bu sefer 1.5 saatte yakalandı, daha geç olsa $100+ ve 2 gün dev kaybı olurdu.

**Yeni norm:** Audit sample TSV üretiminde **truncate yapma**. Karakter limiti yerine satır limiti (LIMIT 30) tercih et. Veya truncated + full versiyonu paralel sun.

**Karpathy validasyon:** "Önce düşün, varsayım yapma." Eğer C2 audit'te DB'yi doğrudan kontrol etseydim, bu hata 1 saat erken yakalanırdı.
─────────────────────────────────────────────────

---

## Sıradaki adım

1. ✅ Faz 0.8 tamamlandı
2. C2 SCORING.tsv'de "ocr" işaretlerini revize et (~12 sample → re-classify, çoğu unclear/pass)
3. Combined RESULT artifact'ı güncelle (OCR oranı %24 → %2.15)
4. Plan v1'de Faz 1.10 scope/cost güncelle
5. `.claude/rules/audit-methodology.md` yaz (sonraki audit'lerde benzer hatadan kaçınmak için)

---

*Generated by Faz 0.8 investigation. 5 hipotez red edildi, asıl sebep audit methodology'de bulundu.*
