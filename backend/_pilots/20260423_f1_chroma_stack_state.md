# F1 — Chroma yığını durum özeti (ADIM 0)

**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md` §8  
**Tarih:** 2026-04-23  

## Tek head

- `alembic heads` → `billing_subscriptions_mvp_20260423` (tek head).

## Chroma operasyon

- Checklist: `docs/operations/chroma_operational_checklist_20260423.md`
- Tohum script: `backend/scripts/chroma_seed_kiro2_questions.py`
- Merge gate ile ilişkili golden’lar: GF38 / GF37 / GF47 / GF152 + GF150 (matris).

## Sonraki (F1 çıktısı için)

- [ ] `docker compose` profili ile vektör süreç + volume doğrulama logu  
- [ ] Ingest idempotent tekrar koşusu (iki kez seed → tutarlı sayım)  
- [ ] Bu dosyanın `_RESULT.md` eşi: gerçek koşu tarihi + embedding model + `chroma_connection_mode`
