# Pool Growth Wave-1 — Blind-Solve Verification (re-OCR'sız)

**Tarih:** 3 Haziran 2026
**Hedef:** #1 kaldıraç — 61,482 unverified metin-temiz soruyu kör-çözüp
`verified_provisional` (beta) havuzuna terfi. Re-OCR sıfır.
**Sonuç:** beta havuzu **3,206 → 4,742 (+1,536, %48)** — tam otomatik, reversible.

---

## Yöntem

1. **Aday seçimi (re-OCR'sız filtre):** `is_active=true ∧ quality_review_status='unverified'
   ∧ correct_answer∈{A..E} ∧ 5 şık dolu ∧ word_count≥8 ∧ henüz verified_provisional değil`.
   Evren: **59,426**. Wave-1 örneklemi: `ORDER BY md5(id) LIMIT 3000`.
2. **Körlük yapısal olarak zorlandı:** `master.csv` (cevap-anahtarı dahil) sadece
   `apply.py` tarafından okunur; solver agent'lara verilen `batch_NNN.jsonl` dosyaları
   **cevap-anahtarı içermez** → agent fiziksel olarak DB cevabını göremez.
3. **Solver:** Workflow, 150 batch × 20 soru. Her agent blind çözüp `preds_NNN.json` yazar:
   `{id, answer(A-E|UNSOLVABLE), confidence, reason}`.
4. **Sınıflandırma (`apply.py`):**
   - AGREE (blind==DB ∧ conf≥0.6) → `verified_provisional="true"` + `pool_growth_solver` marker
   - DISPUTE (blind≠DB) → `blind_answer_dispute_solver` (2. sinyal kuyruğu; **correct_answer'a dokunulmaz** — A-bias)
   - UNSOLVABLE → `blind_unsolvable_solver` (karantina adayı)
   - weak_agree (conf<0.6) → flag'lenmez

## Sonuçlar (3000 soru, 0 parse hatası)

| Sınıf | Sayı | Oran |
|---|---|---|
| AGREE (conf≥0.6) | **1,536** | %51.2 |
| weak_agree | 83 | — |
| DISPUTE | 710 | %23.7 |
| UNSOLVABLE | 671 | %22.4 |

**A-bias guard:** solver dağılımı A18/B18/C22/D22/E20 — DB key dağılımıyla (16/20/23/21/20)
örtüşüyor, max bucket %22.4 → **A-bias yok** (bağımsız çözüm kanıtı).

## Invariant'lar (doğrulandı)

- 1,536 AGREE satırı **hâlâ** `quality_review_status='unverified' ∧ is_active=true`.
- `correct_answer`, `is_active`, `quality_review_status` **hiçbiri değişmedi** (yalnız
  `pipeline_metadata` JSON merge).
- Backup: `question_bank_pool_growth_wave1_backup_20260603` (2,917 satır) → tam rollback.
- Beta partial index (`idx_qbank_verified_provisional`) yeni 1,536'yı otomatik kapsar.

## Workflow dersleri (MEMORY ile uyumlu, canlı kanıt)

- **Run-1 (schema'lı, parallel 150):** 144/150 agent "StructuredOutput çağırmadı" + rate-limit
  ile öldü → MEMORY dersi doğrulandı: *schema/StructuredOutput güvenilmez, 16-eşzamanlı 429*.
- **Kurtarma:** durable-deliverable deseni — agent'lar dosya yazdığı için structured-return
  çökse de 16 batch (320 soru) diskte kaldı, pilot doğrulaması bundan yapıldı.
- **Run-2 (schema YOK, 6'lık sıralı dalga):** 134/134 batch sorunsuz, 44 dk, 14.5M token.
- **Tasarım kuralı:** Workflow'da asıl çıktıyı **diske yaz**, structured-return'e bel bağlama;
  eşzamanlılığı ≤6 tut.

## Maliyet duvarı kırıldı

Subagent-başına 20-soru batch'i: ~190K token/soru → ~5K token/agent (~250/soru). Senin
"hafif solver" hedefi workflow içinde, ayrı API kimlik bilgisi olmadan gerçekleşti.

## Sonraki dalgalar

- Kalan aday: ~57,900 (59,426 − 1,536 − weak/dispute/unsolvable çakışmaları hariç).
- Aynı pipeline'ı `LIMIT/OFFSET` ile dalga dalga tekrarla (1000-agent cap → tek run ~3-15K).
- DISPUTE 710 + UNSOLVABLE 671 → ileride farklı-model 3. sinyal / curator.
- **verified_provisional → gold terfisi** ayrı: 2. **farklı-model** kör sinyali gerektirir (A-bias).

## Wave-2 (4 Haz 2026)

Aynı pipeline, wave-1'in 2,917 işlenmiş sorusu dışlandı (`NOT EXISTS wave1_backup`).
3000 yeni aday → **AGREE 1,533 (%51.1) / DISPUTE 707 / UNSOLVABLE 637**, 0 parse hata,
A-bias temiz (A20/B19/C22/D21/E19, max %21.8). beta havuzu **4,742 → 6,275 (+1,533)**.
Backup `question_bank_pool_growth_wave2_backup_20260604` (2,877), 0 invariant ihlali.
1 batch (077) workflow'da düştü → tek Agent ile tamamlandı (150/150). Scriptler
`backend/scripts/quality/_pool_growth_wave2/`.

**Kümülatif (W1+W2):** beta `verified_provisional` 3,206 → **6,275 (+3,069, %96)**.
AGREE oranı iki dalgada %51.2/%51.1 → yöntem kararlı, tekrarlanabilir.

## Wave-3 (4 Haz 2026)

W1+W2 backup'ları dışlandı (`NOT EXISTS wave1 AND NOT EXISTS wave2`). 3000 yeni aday →
**AGREE 1,485 (%49.5) / DISPUTE 696 / UNSOLVABLE 673**, 0 parse hata, A-bias temiz
(max %21.5). beta havuzu **6,275 → 7,760 (+1,485)**. Backup
`question_bank_pool_growth_wave3_backup_20260604` (2,854), 0 invariant ihlali. 150/150
batch, 3 tahmin eksik (ihmal). Scriptler `backend/scripts/quality/_pool_growth_wave3/`.

**Kümülatif (W1+W2+W3):** beta `verified_provisional` 3,206 → **7,760 (+4,554, %142)**.
AGREE oranı 3 dalgada %51.2/%51.1/%49.5 → P3 hedefi (~6,800) aşıldı.

## Dosyalar

`backend/scripts/quality/_pool_growth_wave1/` — export.sql, split.py, apply.py, apply.sql,
master.csv, batches/ (batch_NNN.jsonl + preds_NNN.json). Git-tracked değil (manuel backup).
