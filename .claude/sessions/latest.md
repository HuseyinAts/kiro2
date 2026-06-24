## Session Handoff — 2026-06-24 (CC best-practice audit)
**Branch:** feature/self-evolution-optimization
**Son commit:** 54074cc77 chore(rules): lazy-load 4 domain-specific rules via paths: frontmatter (pushed)
**Uncommitted:** ModernOSYMExamInterface.tsx (+22/-22) + 5 untracked audit/sql dosyası — BU SESSION'A AİT DEĞİL, dokunulmadı

### Yapilanlar
- `shanraisshan/claude-code-best-practice` repo tamamı clone+okundu (5 paralel Explore agent ile satır satır)
- Audit: KIRO2 best-practice'lerin ~%95'ini zaten karşılıyor/aşıyor (hooks/permissions/memory/tasks/plan/cross-model/verification)
- Tek gerçek boşluk uygulandı: 4 domain-specific rule'a `paths:` frontmatter (lazy-load) — `windows-hnsw-build`, `case-convention`, `middleware`, `path-naming` (commit 54074cc77)
- `paths:` mekanizması claude-code-guide agent ile RESMİ doküman üzerinden doğrulandı (code.claude.com/docs/en/memory.md)

### Fail Eden Testler
- YOK (config-only değişiklik, kod/test dokunulmadı)

### Engelleyiciler
- YOK

### Sonraki Adimlar (maks 5)
1. (opsiyonel) Agent memory: `memory: project` → code-reviewer/test-runner/data-pipeline-specialist agent'larına ekle
2. (opsiyonel) `settings.json`'a `attribution.commit` ile Co-Authored-By otomasyonu
3. ModernOSYMExamInterface.tsx uncommitted değişikliğinin sahibini/amacını netleştir (bu session'a ait değil)
4. Önceki iş: GitHub Actions kontrol (task #270 pending)

### Kararlar (gelecek session tekrar tartismasin)
- `paths:` bilinen bug'ı (gh #22170/#23478: Read'de enjekte, Write'da güvenilmez DEĞİL) kabul edildi — en kötü ihtimalle eski global-load davranışına düşer, guardrail kaybı YOK. Davranışsal gate'ler (debugging/plan/verification/testing/security/golden-flows) bilerek global bırakıldı.
- `trigger:`/`priority:` frontmatter dekoratiftir — core okumuyor (13 rule de yüklendi). Mevcut 5 rule'da var, dokunulmadı.
- RPI workflow / sound-effect hooks / weather-time demo'ları bilerek atlandı (KISS/YAGNI — KIRO2 zaten aşıyor).
