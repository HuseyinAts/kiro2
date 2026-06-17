## Session Handoff — 2026-06-13 (Pool growth: 2-model consensus + Opus validasyonu)
**Branch:** `master`
**Önceki session:** 2026-06-12 (serving-gate + conflict kurtarma — aşağıda "Geçmiş").

### Bu session — servis havuzu 9,913 → **13,831 (+3,918, +%39.5)**
`verified_provisional` havuzunu (3,960 v_safe-uygun) ikinci bağımsız sinyalle doğrulayıp promote ettik. Üç faz, üç backup, hepsi geri-alınabilir. **`correct_answer`/`is_active` hiç değişmedi** (yalnız `quality_review_status` unverified→`auto_judged_high` + provenance metadata).

| Faz | Yöntem | Validasyon | Eklenen | Backup tablosu |
|---|---|---|---|---|
| A | gemma3:12b 2-model consensus (agree) | A-bias ok | +1,908 | `question_bank_gemma3_consensus_backup_20260612` |
| B | qwen3+DB math/geo dispute | **Opus 4.8 60/60** | +1,265 | `question_bank_math_qwen3_promote_backup_20260613` |
| C | qwen3+DB sözel/fen dispute | **Opus 4.8 58/60** | +745 | `question_bank_verbal_promote_backup_20260613` |

### Metodoloji (veri-temelli, kaynaklı belge: `docs/audits/2026-06-13_gemma3_consensus_pool_growth.md`)
- **2. sinyal = gemma3:12b-it-qat** (Google, non-Qwen bağımsızlık; TurkBench Türkçe 71.0 ≈ 27b'nin 73.0; 16GB GPU'ya sığar). Kapsamlı model araştırması: Gemma 4 / gpt-oss / Phi-4 / DeepSeek elendi (Türkçe ölçümsüz ya da sığmıyor).
- **gemma3 yalnız agree'lerde güvenilir** (math'te MA~22≈random). gemma3 confidence metriği **dejenere** (agree/dispute medyan=1.0) → atıldı.
- **Lokal ≤16GB Türkçe-math uzmanı YOK** (veri-kanıtlı, TurkBench MA tablosu). Bağımsız doğrulayıcı = **Opus 4.8, Cowork/Max üzerinden (no-API)**, örneklem-ölçekli: ~150 soru → 3,918 promotion kilitlendi. **Net DB-hatası 0.**
- gemma3 dispute'ları (math + sözel/fen) %96-100 gemma3 hatası, DB doğru — Opus 118/120 örnekte DB'yi doğruladı.

### Scaffolding (not git-tracked: `backend/scripts/quality/`)
`ollama_blind_solve.py` (`--model` bayrağı eklendi), `_pool_growth_gemma3/{export,split,consensus_apply,opus_sample,opus_sample_verbal,analyze_pilot}.py`. **Solver `kiro2-ollama` container'a (`:11434`) bağlanır** — modeli `docker exec kiro2-ollama ollama pull <tag>` ile çek (native Ollama'ya pull `/api/generate`'de "not found" verir — iki instance tuzağı).

### Açık işler (öncelik sıralı)
1. **P1 — kalan unverified havuz:** `verified_provisional` OLMAYAN ~92K unverified/pending. Bunlar hiç blind-solve görmedi → sıfırdan wave (export→gemma3 solve→consensus) gerekir. Servis zaten `v_safe_for_beta` gated → acil değil.
2. **P2 — ~42 figür-bağımlı unsolvable:** gemma3 "UNSOLVABLE" dedi, `unverified` bırakıldı. Multimodal model (gemma3 vision / qwen3-vl) ile re-solve denenebilir.
3. **P2 — eski backlog:** DuelMode/ErrorClusterCard port; `mv_safe_for_beta` matview (~256ms→~3ms); 3,264 mükerrer dedup; json→jsonb (ERTELENDİ, ağır — HNSW rebuild).

### Notlar
- **bash sandbox mount + VM güvenilmez** (bu session VM çökük kaldı) — dosya işlemleri HOST araçları (Read/Write) + kullanıcı PowerShell ile yapıldı.
- DB yazımları MCP (`dbhub-kiro2`) ile, her biri backup'lı. v_safe canlı doğrulandı (13,831).

### Geçmiş (2026-06-12) — özet
Option A serving-gate (`v_safe_for_beta` view), conflict marker kurtarma (Dalga 1/2), subject-switching + Fix 5, HNSW index + embedding %100 kapsama. Detay önceki handoff git history'de.
