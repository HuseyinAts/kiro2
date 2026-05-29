## Session Handoff — 2026-05-29 13:45
**Branch:** master | **Son commit:** c433cd434 ci: .venv cache fix (#37)
**Uncommitted:** temiz

### Yapilanlar (bu session)
- **KVKK Faz 2 — 11/11 task TAMAM** → PR #34 master'a merge (`8545927b4`) + container kalıcı rebuild (`docker compose build backend`) + canlı E2E doğrulandı. 15/15 test PASS. Detay: auto-memory `project_kvkk-faz2-shipped`.
- **CI infra onarımı (PR #35/#36/#37, hepsi merged):**
  - Kök neden: Actions dakika **2000/2000 tükenmiş** → startup_failure (ruff değil!). Operatör **$10 limit** açtı.
  - Tüketim azaltma: push/PR başına **~40→6 job** (claude-ci/quality-gates→manuel, deploy→tag-only, security→PR+schedule, backend-test matrix 3→1).
  - Diff-based lint: `quality` job yalnız değişen `backend/**/*.py` (10,870 legacy borç grandfathered).
  - bandit guard fix (#36) + `.venv` cache fix (#37, `rm -rf .venv` + cache path'ten çıkar).
  - **DOĞRULANDI:** workflow_dispatch run → install success → ruff/mypy/bandit/safety **success → quality gate YEŞİL**.

### Fail Eden Testler
- YOK (yeni iş). CI `backend-test` gate'i hâlâ kırmızı olur — AYRI tail (aşağı).

### Engelleyiciler
- **key rotate** teyidi gelmedi (GEMINI_API_KEY AUP leak — operatör, hâlâ açık).

### Sonraki Adimlar (maks 5)
1. **#4 ürün işi:** KVKK Faz B (aydınlatma metni + veri silme/taşıma) VEYA SMTP prod config
2. CI full-green tail (opsiyonel, büyük iş): backend-test `--cov-fail-under=60` (gerçek ~%43) + test pollution bisect; frontend coverage %70
3. GEMINI_API_KEY rotate teyit (operatör)
4. A1 PG restart (shared_buffers 4GB, operatör)
5. Operatör secrets: ANTHROPIC_API_KEY / KUBE_CONFIG (artık manuel/tag-only workflow'lar için)

### Kararlar (gelecek session tekrar tartismasin)
- CI kök neden = Actions dakika; lint/test değil. Detay: auto-memory `project_ci-state`.
- ci.yml tek CI kaynağı; diğer workflow'lar manuel/scheduled.
- Diff-based lint: yeni kod temiz, 10,870 legacy ruff borcu grandfathered.
- `.git/refs/**/desktop.ini` Windows artifact `git pull`'u bozuyor → `find .git -name desktop.ini -delete`.
- PR base = master (clean-main 672K geride). gh CLI yok → GitHub REST API + stored credential ile PR aç/merge.
- Integration test: kök `db_session` BROKEN → inline strict-rollback + `KVKK_VERIFY_DSN` (auto-memory `reference_backend-integration-test-db`).
