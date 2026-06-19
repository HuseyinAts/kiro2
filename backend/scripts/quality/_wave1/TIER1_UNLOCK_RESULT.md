# TIER1 UNLOCK — verified_provisional pool, blind-validated, SHIPPED (+1170)

Tarih: 2026-06-19. Lever: wave1'in teşhisi → "3.459 doğrulanmış soru view-bloke; en büyük tek sebep tier1 (1.176)".

## Kanıt (workflow, 100% precision)
- 72-soru stratified (thin-STEM ağırlıklı) blind validation, **3 bağımsız Opus solver/soru, SIRALI 6'lık dalga** (rate-limit-safe; schema YOK, düz-metin parse).
- **PRECISION %100 (72/72), 0 wrong, 0 unsolvable.** 71/72 unanimous. 16 branşın HEPSİ %100 (AYT-Kimya 10/10, Fizik 10/10, Bio 10/10 dahil).
- Sonuç: tier1 dışlaması kör-doğrulanmış içerik için **gereksiz** (eşleştirme-vekili, cevap-doğrulaması süperseder).
- Workflow rate-limit dersi (canlı): 216-ajan 14-paralel+schema → **216/216 server-529**. Düzeltme: schema YOK + 6'lık sıralı dalga → 216/216 OK (12dk, 22M tok). MEMORY pool-growth dersinin tekrarı.

## Uygulama (D8 view, reversible, DB-yazımı YOK)
- D8: `match_tier` tier1 kapısına `OR verified_provisional` eklendi (canlı viewdef'ten birebir; gate2c/fallback/demote/status DOKUNULMADI).
- **v_safe 6.600 → 7.770 (+1.170).** new_tier1_admitted=1.170 = Δ (birebir). leak: gate2c=0, fallback=0, demoted=0.
- Thin AYT fen: Kimya 27→112, Fizik 35→97, Bio 14→57, Tarih 52→95 → **AYT sınav simülasyonu artık mümkün.**
- correct_answer/is_active/status/question_bank DOKUNULMADI (total_active 110.895 + verified_provisional 9.344 değişmedi). Rollback: `D8_rollback.sql` (D7'ye döner).

## ROI
wave1 fresh-solve: 1 oturum → +56. tier1-unlock: 1 workflow + 1 view → **+1.170 (~21×)**, üstelik tam isabetli thin branşlara.

## Sonraki (kalan headroom)
- multi_blocked 2.125 (tier1+başka) — tier1 artık açık, kalan engel (fallback/status) bazılarını kısmen açabilir; ölç.
- fallback 2.115 (kök-çözüm: embedding+topic_hierarchy ile konu re-tag) — orta efor, +unlock +adaptif kalite.
- Artefaktlar: `_wave1/{tier1_validate.csv, tier1_blind/, tier1_keys.csv, compare_tier1.py, tier1_results.json, D8_*.sql}`.
