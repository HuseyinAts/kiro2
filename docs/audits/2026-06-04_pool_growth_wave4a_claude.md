# Pool Growth Wave-4a — Claude Blind-Solve (qwen pivot çürütüldü)

**Tarih:** 4 Haziran 2026
**Sonuç:** beta `verified_provisional` havuzu **7.760 → 9.329 (+1.569, %20)** — reversible, $0 ek API.

---

## Bağlam: onaylı qwen yolu kalibrasyonda çürüdü

Önceki oturum "no-key Ollama (qwen3:14b)" tasarımını onaylamış (commit `b615d9d7b`),
Wave 4 (9000 aday) hazır ama çözülmemiş bırakmıştı (saatlik limit). Bu oturum:

1. **qwen solver kuruldu + Faz A kalibre edildi** (`ollama_blind_solve.py`, `_calib_fazA/`):
   360 known-good blind-solve → **qwen==DB %61** (A-bias temiz). Branş head-to-head
   (Claude Wave1-3 DB-reconstruct vs qwen):

   | Branş | Claude | qwen | Branş | Claude | qwen |
   |---|---|---|---|---|---|
   | TARIH | 87 | 89 | KİMYA | 71 | 55 |
   | COĞRAFYA | 87 | 68 | TÜRKÇE | 63 | 68 |
   | BİYOLOJİ | 85 | 72 | **MATEMATİK** | **61** | **34** |
   | FİZİK | 78 | 59 | **GEOMETRİ** | **61** | **42** |
   | EDEBİYAT | 76 | 61 | | | |

   **qwen STEM'de çöküyor** (math %34 ≈ rastgele üstü) → qwen-AGREE math'te gürültü.
   think=ON denendi: doğruluk artabilir ama **>6 dk/soru** bu GPU'da = 9000 için günler.

2. **qwen pivot'unun iki gerekçesi de yanlıştı:**
   - "190K token/soru" = başarısız schema yaklaşımının maliyeti. Çalışan workflow zaten
     ~250 tok/soru. **Token duvarı kırılmıştı**; limit Wave 4'ü 9000'e (3×) şişirmekten doldu.
   - "A-bias" yalnız dispute'ları Claude'la TEKRAR çözmede. Wave 1-3 **tek-Claude blind vs
     kitap-anahtarı** (bağımsız) → A-bias yok.

   → **Karar:** qwen birincil çözücü değil. Kanıtlanmış Claude workflow'u 3000-ölçekte tekrarla.

## W4a: kanıtlanmış metot (Wave 1-3 deseni)

- Wave 4 master'ın ilk 3000'i (batch_000–149, ~2850 soru, blindness: batch jsonl'de anahtar YOK).
- **Workflow** (`pool-growth-wave4a`): 150 agent, ≤6 eşzamanlı sıralı dalga, **schema YOK**,
  agent her batch'i blind çözüp `preds_NNN.json`'u **diske yazar** (durable). 150 agent /
  16.3M token / ~47 dk / 327 tool-use. 0 parse hata, 150/150 preds.
- `apply.py` sınıflandırma (3000 tahmin):

  | Sınıf | Sayı | Oran |
  |---|---|---|
  | AGREE (conf≥0.6) | **1.569** | %52.3 |
  | weak_agree | 222 | — |
  | DISPUTE | 798 | %26.6 |
  | UNSOLVABLE | 411 | — |

  **AGREE %52.3 — Wave 1-3 (%51.2/51.1/49.5) ile birebir.** A-bias guard: max bucket C %23.5 (ok),
  solver dağılımı A18/B20/C23/D20/E19 ≈ DB key.

- **Spot-check 5/5 temiz** (TÜRKÇE×2, BİYO, MAT×2 — math conf 0.95/0.99 gerçek-çözüm, dairesel/garble yok).

## Invariant'lar (doğrulandı)

- AGREE 1.569 → `pipeline_metadata.verified_provisional='true'` + `pool_growth_solver=2026_06_04_wave4`.
- DISPUTE 798 → `blind_answer_dispute_solver` (2. sinyal kuyruğu), UNSOLVABLE 411 → `blind_unsolvable_solver`.
- **`correct_answer` / `is_active` / `quality_review_status` DOKUNULMADI** — 1.569 AGREE hâlâ
  `unverified`+`is_active=true`. Yalnız `pipeline_metadata` JSON merge.
- Backup: `question_bank_pool_growth_wave4_backup_20260604` (2.778 satır) → tam rollback.

## Sonraki

- **W4b** (batch 150–299, sonraki ~3000) + **W4c** (300–449) — aynı workflow, ayrı turn (limit güvenliği).
- DISPUTE (798) → farklı-model 3. sinyal / curator. UNSOLVABLE (411) → figür/garble karantinası.
- Kalan unverified evreni Wave 4 sonrası ~52K.
