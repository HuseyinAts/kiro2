# Tier I Geometri Safety_Blocked Retry — Pilot RESULT (n=20)

**Date:** 2026-05-16 (Session 161b continuation)
**Model:** gemini-2.5-pro
**Safety:** `BLOCK_NONE` × 4 kategori (HARASSMENT, HATE_SPEECH, SEXUALLY_EXPLICIT, DANGEROUS_CONTENT)
**Workers:** 5 (threaded)
**Elapsed:** 1.8 dakika
**Script:** `backend/scripts/tier_i_geometri_retry.py`

## Hedef

Original Tier I apply (Session 159-161, sequential + threaded) sırasında 334 satır
`gemini_error` aldı (`response.text` accessor `finish_reason != STOP` raise). Session 160
finding: 10/10 sample TÜM Geometri kitaplarından (matematiksel şekiller → safety filter).
Hipotez: `safety_settings={...: BLOCK_NONE}` filtreyi devre dışı bırakırsa error oranı düşer.

## Threshold

| Metrik | Hedef | Gerçek | Karar |
|---|---|---|---|
| `gemini_error` rate | ≤%30 | **%45** | ❌ |
| `applied_high` rate | ≥%30 | %20 | ❌ |
| `json_fail` rate | ≤%5 | %5 | ✅ |
| `safety_mode=block_none` audit trail | 100% | **100% (4/4)** | ✅ |

## Stats (n=20)

| Action | Count | % |
|---|---|---|
| gemini_error | 9 | 45.0 |
| applied_high | 4 | 20.0 |
| mid_skip | 3 | 15.0 |
| low_skip | 3 | 15.0 |
| json_fail | 1 | 5.0 |
| **Toplam hata** | **10** | **50.0** |
| **Toplam başarılı** | **10** | **50.0** |

## Karar: NO-GO Production Retry

**Sebep:** Error oranı (%50) threshold'u (%30) aşıyor. Scale-up tahmin: kalan 314 satır →
~63 ek HIGH UPDATE (beklenen 170-240). Marjinal değer, audit trail karmaşıklığı yüksek.

## Bonus: 4 HIGH UPDATE DB'de Kalıcı

Pilot zaten DB'ye yazdı (BACKUP TSV mevcut, rollback gereksiz çünkü HIGH band valid):

| ID prefix | URL set | OCR len | block_none | retry_pass |
|---|---|---|---|---|
| 0065b135 | ✅ | 118 | ✅ | ✅ |
| 0ebdf0c3 | ✅ | 129 | ✅ | ✅ |
| 1fa3ec83 | ✅ | 129 | ✅ | ✅ |
| 2593204f | ✅ | 99 | ✅ | ✅ |

`pipeline_metadata.tier_i_reocr` audit trail:
```json
{
  "date": "2026-05-16",
  "model": "gemini-2.5-pro",
  "substr_pct": <0.70-1.00>,
  "band": "high",
  "ocr_method": "direct_crop",
  "safety_mode": "block_none",
  "retry_pass": 2,
  "prev_image_url": "<original or null>",
  "prev_ocr_text_len": <orig len>
}
```

## Bulgular

### Finding 1: BLOCK_NONE Yetersiz, Derin SDK Sorunu

`response.text` accessor BLOCK_NONE'a rağmen %45 fail. Demek ki `finish_reason != STOP`
durumlarının kaynağı **sadece safety filter değil**:

- `RECITATION` — telif hakkı içerik koruması (BLOCK_NONE'a tabi değil)
- `OTHER` — bilinmeyen iç sebep
- `MAX_TOKENS` — output token limit aşımı
- `BLOCKLIST` — bağımsız content blocklist

Memory'deki "Session 162+ BLOCK_NONE config" planı **eksik teşhis**. Gerçek fix:
```python
# call_gemini patch:
resp = model.generate_content([prompt, img])
# resp.text YERİNE:
if resp.candidates and resp.candidates[0].content.parts:
    raw = resp.candidates[0].content.parts[0].text
else:
    raise GeminiPartialError(finish_reason=resp.candidates[0].finish_reason)
```

### Finding 2: Error Count Drift (Memory → Reality)

| Kaynak | Sayı | Sebep |
|---|---|---|
| Memory handoff | 311 | Handoff tahmini, live count alınmamış |
| awk `$7=="error"` | 346 | TSV kolon escape çakışan satırlar |
| Python `load_error_ids()` | **334** | Strict kolon kontrol, ground truth |

Gerçek scope: **334 satır** (4 apply, 330 kaldı).

### Finding 3: SDK Deprecation Warning

```
FutureWarning: All support for the `google.generativeai` package has ended.
Please switch to the `google.genai` package as soon as possible.
```

Uzun vadeli backlog: `google.genai` migrate (Tier I + judge runner ortak refactor).

## Sonraki Adımlar

**Bu pilot için kapalı:**
- Kalan 330 satır curator pool'a düşer (Faz 3 — manuel review/curation)
- Veya Session 162+ Finding 1 fix ile yeniden denenir

**Faz 5.8 etiketi yeniden tanımlanmalı:**
> ~~Session 162+ `safety_settings=BLOCK_NONE` config~~ →
> Session 162+ `call_gemini` `candidates[0].content.parts[0].text` bypass + safety_settings=BLOCK_NONE birlikte

## Artefaktlar

- Script: `backend/scripts/tier_i_geometri_retry.py`
- RESULT TSV: `backend/_pilots/20260516_tier_i_geometri_retry_apply_RESULT.tsv`
- BACKUP TSV: `backend/_pilots/20260516_tier_i_geometri_retry_BACKUP_apply.tsv`
- Checkpoint: `backend/_pilots/checkpoint_tier_i_geometri.json` (4 ID processed)
