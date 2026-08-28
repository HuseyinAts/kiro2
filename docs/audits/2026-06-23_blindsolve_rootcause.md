# blind_solve Bulk — Kök-Neden Audit + Fix (2026-06-23)

## Bağlam
Claude Code'da 2026-06-20/21'de `blind_solve` pool-growth dalgaları (31 wave) çalıştı,
question_bank'te **16.344 soruyu** promote etti (`auto_judged_high` + `blind_solve_wave`
+ `verified_provisional`). v_safe 6.544 → 25.855 (~4x). Bulk = v_safe'in %63'ü.

## Ölçüm (Opus QA, 2 bağımsız örnek: n=50 + n=62 stratified)
- **Servis-temiz ~%50-55** (beta eşiği %95'in çok altında).
- **~%10 yanlış-anahtar** (güçlü, hesapla doğrulanmış: eğim k=7/2 anahtar 9/2; sıralama
  4.=Soner anahtar İlker; denklem x=−2 anahtar −4 [0=0 yerine koyup doğruladım];
  g∘f artan→II&III anahtar yalnız II; soygaz komşuları→yalnız II anahtar hepsi).
- **~%25 degenerate/bozuk** (cevap şıkta yok, iki şık birden doğru, LaTeX-OCR garble).
- Badness 31 wave'e **yaygın** (en kötü 06-20 batch %45 temiz, 06-21 %70, poolA %50) —
  tek wave demote çözmez. Kendi Opus hata payım ~%5-8 (kayıtlı).

## KÖK NEDEN (koddan doğrulandı)
`backend/scripts/quality/_blindsolve/aggregate_wave.py` satır 56-66:
```python
if ans and ans == keys[sid]:      # TEK solver cevabı == stored anahtar
    if conf >= CONF_MIN:           # CONF_MIN=0.80 (self-conf)
        promote.append(sid)
```
Promote kriteri = **tek model cevabı stored'a eşit + öz-confidence≥0.80.** Eksikler:
1. **Tek model** (2-model consensus yok) → tek model stored'la aynı hatayı yapınca yanlış-anahtar promote.
2. **Coherence kontrolü yok** — dup-şık/OCR-prefix/"cevap-şıkta-mı"/figür-görselsiz hiçbiri.
   (Bu kontroller `_gate2b/coherence_gate.py`'de VAR ama _blindsolve import etmemiş.)
3. **Anahtar-doğrulama yok** — stored key'e körü körüne güven (satır 48).
4. **Opus sample-validation yok** (careful Faz A/B/C'de vardı).
5. `conf≥0.80` = 14B overconfidence, anlamsız sinyal.

## FIX — `aggregate_wave_v2.py` (yazıldı 2026-06-23)
Promote için TÜM koşullar:
- **A) coherence-clean**: dup-şık yok + OCR-prefix yok + 5 şık dolu.
- **B) 2-model consensus**: `gemma3.ans == qwen3.ans == stored_key` (üçü aynı, A-E).
- **C) Opus sample-validation kapısı**: her dalgadan ~25 örnek → `opus_wN.txt`;
  precision <%95 ise dalga promote EDİLMEZ.
- Tek-model + self-conf kuralı KALDIRILDI. correct_answer/is_active dokunulmaz.

## RE-GATE PLANI (mevcut 16.344 bulk'u v2'den geçir)
v1 yalnız 1 model çözdü → v2 consensus için **2. modeli bulk'ta çalıştırmak gerekir**:
1. Bulk'un (16.344) sorularını eksik modelle (gemma3 veya qwen3, hangisi v1'de yoksa) blind-solve et. ~7-8 saat GPU (chunk'lı; ollama_blind_solve.py).
2. `aggregate_wave_v2` mantığıyla **v2-pass set** hesapla (coherence + 2-model==stored).
3. Bulk'ta v2-pass OLMAYAN'ları v_safe'ten **demote** (reversible exclusion, gate2c deseni).
   Beklenen: ~%40-50 düşer → v_safe ~17-19K temiz kalır.
4. v2-pass set'ten Opus örneklemle precision teyit (≥%95).

## Disposition
- v2-pass'ı geçemeyenler **silinmez** → "unverified/needs-review"e döner (yargı=zor≠yanlış).
- careful core (~9.500) zaten sağlam, etkilenmez.
- Backup'lar mevcut (`blindsolve_wN_backup`), tüm adımlar geri-alınabilir.

## İlişkili
- Ölçüm görselleri + 112-örnek detayı: bu oturum (Cowork).
- gate2c demote deseni: `_gate2b/D6_*.sql`.
- careful pipeline (referans doğru desen): `_gate2b/gate2c_combined.py` + Opus sample.

---

## GÜNCELLEME (24 Haz 2026): RE-GATE ÖNERİLMİYOR — bulk ~%95 temiz
Re-gate'i çalıştırmadan önce bulk'un gerçek bozuk-oranı **Opus 40-örnek kör-çöz** ile ölçüldü
(v_safe içi blind_solve_wave, self-contained, rastgele md5-salt):
- **38/40 = %95 Opus==stored** (corroborated-temiz).
- 1 kırık (geometri, doğru cevap −8 şıklarda yok → `ccf7f73d` gate2c'ye alındı `no_correct_option_broken`).
- 1 tartışmalı (biyoloji, net yanlış-anahtar değil).

**Sonuç:** bulk zaten ~%93-95 temiz (S160+ ölçümleriyle tutarlı). 2-model **zayıf-consensus**
(gemma3+qwen3 14B) gate'i **zor-ama-doğru** soruları (türev/limit, kombinatorik, log-sistem,
geometri — Opus çözer, 14B çözemez) kitle halinde YANLIŞ-demote eder: beklenen demote ~%30-50,
gerçek bozuk ~%5 → ~%25-45 false-demote = temiz havuzu boşaltır. Bölüm 40-46'daki "%40-50 düşer"
planı **iptal** (bulk "%55 temiz" sanılırken yazılmıştı). Kalan ~%5 için: hedefli Opus-doğrulama
(zayıf 2-model değil), düşük ROI (16K'da %5). Driver banner'ında ⛔ uyarısı eklendi.
