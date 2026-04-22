---
name: kiro2-skill-index
description: KIRO2'nin tüm skill ve command ekosistemi. Bilinmeyen bir domain'de hangi skill'e bakılacağını bulmak için keşif aracı. .claude/ (canonical) ve .cursor/ (Cursor-port) arasındaki eşleme.
---

# KIRO2 Skill Index — Tam Ekosistem

KIRO2'de şu an **27 skill** mevcut (24 Claude Code + 3 Cursor-only yeni),
**15 slash command** (11 eski + 4 yeni), **5 rule**, **2 hook script**.

Bu dosya bir **keşif aracı**: Kullanıcının isteğine göre hangi skill/command
relevant olduğunu bulmak için tarayarak kullanılır.

## 🔍 Hızlı Arama — Hangi İhtiyaç, Hangi Araç?

### Yeni İş Başlatma

| İhtiyaç | Araç | Yer |
|---|---|---|
| Karmaşık task planlama | **Plan Mode** (Shift+Tab) veya `/plan` | Cursor native |
| Bilinen pattern, hızlı başla | Direkt agent prompt | — |
| Belirsiz yaklaşım var | `/best-of-n` (paralel model) | `.cursor/commands/` |
| Risky experiment | `/worktree` | `.cursor/commands/` |
| Önceki işten devralma | `@Past Chats` | `.cursor/skills/past-chats/` |

### Kod Analizi / Araştırma

| İhtiyaç | Araç | Yer |
|---|---|---|
| Bug / failing test | **debug-bug** skill, `/debug-mode` komutu | Cursor + `.claude/` |
| TDD döngüsü (max 3 iter) | **tdd-loop** skill | Cursor + `.claude/` |
| PR / kod review | **code-review** skill, `/review` komutu | Cursor + `.claude/` |
| 5+ dosyalı audit | **deep-audit** skill (paralel sub-agent) | `.claude/skills/deep-audit/` |
| Derin araştırma | **deep-research** skill | `.claude/skills/deep-research/` |
| Performans analizi | **perf-analysis** skill | `.claude/skills/perf-analysis/` |

### UI / Frontend

| İhtiyaç | Araç | Yer |
|---|---|---|
| Browser'da element seç + iterate | **design-mode** skill | `.cursor/skills/design-mode/` |
| Mockup → implementation | design-mode + Figma MCP | Cursor + MCP |
| Responsive debug | Integrated Browser + Design Mode | Cursor native |

### Güvenlik

| İhtiyaç | Araç | Yer |
|---|---|---|
| OWASP Top 10 checklist | **security-checklist** skill | `.claude/skills/security-checklist/` |
| OWASP güvenlik pattern'ları | **owasp-guide** skill | `.claude/skills/owasp-guide/` |
| Platform özel güvenlik (IDOR, JWT) | **kiro2-specific** skill | Cursor + `.claude/` |
| PR üzerinde otomatik güvenlik review | BugBot ($40/ay ek) | `.cursor/BUGBOT.md` |

### Eğitim Algoritmaları

| İhtiyaç | Araç | Yer |
|---|---|---|
| IRT/FSRS/BKT/ZPD genel | **education-algorithms** skill | Cursor + `.claude/` |
| IRT 3PL detaylı validasyon | **irt-validation** skill | Cursor + `.claude/` |
| FSRS tekrar takvimi | **retrieval-schedule** skill | `.claude/skills/retrieval-schedule/` |
| Öğrenci bilişsel profili | **student-cognitive-profile** skill | `.claude/skills/student-cognitive-profile/` |

### Soru / İçerik

| İhtiyaç | Araç | Yer |
|---|---|---|
| YKS soru üretimi | **yks-generator** skill | Cursor + `.claude/` |
| Soru kalite raporu (multi-dim) | **question-quality-multi** skill | `.claude/skills/question-quality-multi/` |
| Taxonomy etiket doğrulama | **taxonomy-validate** skill | `.claude/skills/taxonomy-validate/` |

### Türkçe NLP

| İhtiyaç | Araç | Yer |
|---|---|---|
| I/ı, UTF-8, tokenizer | **turkish-nlp** skill | Cursor + `.claude/` |

### Session / Context Yönetimi

| İhtiyaç | Araç | Yer |
|---|---|---|
| Commit sonrası checkpoint | **checkpoint** skill | `.claude/skills/checkpoint/` |
| Session kapatma handoff | **handoff** skill, `/handoff` | Cursor + `.claude/` |
| Hızlı durum raporu | **status** skill, `/status` | Cursor + `.claude/` |
| Kalıcı bellek kaydı | **save-memory** skill | `.claude/skills/save-memory/` |
| Önceki chat'e referans | **past-chats** skill, `@Past Chats` | `.cursor/skills/past-chats/` |
| Plan dokümantasyonu | **plan-mode** skill, `.cursor/plans/` | `.cursor/skills/plan-mode/` |

### Ops / Pipeline

| İhtiyaç | Araç | Yer |
|---|---|---|
| DB sorgu çalıştırma | **db-query** skill, `/db` komutu | Cursor + `.claude/` |
| OCR/data pipeline durum | **resume-pipeline** skill | `.claude/skills/resume-pipeline/` |
| Production deployment | **deploy** skill, `/deploy` (manuel) | Cursor + `.claude/` |

## 📋 Tüm Skill'ler (Alfabetik — 27 skill)

| # | Skill | Açıklama | `.claude/` | `.cursor/` |
|---|---|---|---|---|
| 1 | **checkpoint** | Context checkpoint (SESSION_STATE + MEMORY) | ✅ | — |
| 2 | **code-review** | PR/dosya review, OWASP + Boris Cherny | ✅ | ✅ |
| 3 | **db-query** | PostgreSQL sorgu (port 5434, sadece SELECT) | ✅ | — |
| 4 | **debug-bug** | INFRA-FIRST + root cause + TDD fix | ✅ | ✅ |
| 5 | **deep-audit** | Paralel sub-agent sistematik audit (5+ dosya) | ✅ | — |
| 6 | **deep-research** | Codebase + docs + web derinlemesine araştırma | ✅ | — |
| 7 | **deploy** | Production deployment (manuel trigger) | ✅ | — |
| 8 | **design-mode** 🆕 | Browser'da element seç + agent'a hedefle | — | ✅ |
| 9 | **education-algorithms** | IRT/FSRS/BKT/ZPD parametreler ve formüller | ✅ | ✅ |
| 10 | **handoff** | Session handoff (max 50 satır) | ✅ | — |
| 11 | **irt-validation** | IRT 3PL doğrulama, CAT, MLE | ✅ | ✅ |
| 12 | **kiro2-skill-index** | Bu dosya — tüm araçların dizini | — | ✅ |
| 13 | **kiro2-specific** | Platform kuralları (DB port, authStore, Dual Table) | ✅ | ✅ |
| 14 | **owasp-guide** | OWASP güvenlik pattern'ları referansı | ✅ | — |
| 15 | **past-chats** 🆕 | @Past Chats tool'uyla önceki chat'lere referans | — | ✅ |
| 16 | **perf-analysis** | DB + API + memory + CPU performans | ✅ | — |
| 17 | **plan-mode** 🆕 | Plan Mode (Shift+Tab) workflow rehberi | — | ✅ |
| 18 | **question-quality-multi** | OSYM + taxonomy + CLT + readability | ✅ | — |
| 19 | **resume-pipeline** | OCR/data pipeline durumu | ✅ | — |
| 20 | **retrieval-schedule** | FSRS + Retrieval Practice tekrar planı | ✅ | — |
| 21 | **save-memory** | Konuşmayı ~/.claude/memory/'ye kaydet | ✅ | — |
| 22 | **security-checklist** | OWASP Top 10 checklist | ✅ | — |
| 23 | **status** | Hızlı durum raporu (git + memory) | ✅ | — |
| 24 | **student-cognitive-profile** | Öğrenci SOLO/Marzano/VARK profili | ✅ | — |
| 25 | **taxonomy-validate** | Bloom+SOLO+Marzano+Webb DOK tutarlılığı | ✅ | — |
| 26 | **tdd-loop** | Self-correcting TDD fix (max 3 iter) | ✅ | ✅ |
| 27 | **turkish-nlp** | I/ı, UTF-8 NFC, Zemberek, tokenizer | ✅ | ✅ |
| 28 | **yks-generator** | YKS/TYT/AYT/YDT soru üretimi | ✅ | ✅ |

🆕 = Cursor 3.x için yeni eklenen, Cursor-native özelliklere özel

## ⚡ Slash Commands (15 komut)

| Komut | Amaç | Dosya |
|---|---|---|
| `/commit` | Conventional commit oluştur | `.cursor/commands/commit.md` |
| `/pr` | GitHub PR aç | `.cursor/commands/pr.md` |
| `/test` | pytest çalıştır (scope ile) | `.cursor/commands/test.md` |
| `/deploy` | Staging/production deploy | `.cursor/commands/deploy.md` |
| `/review` | Son değişiklikleri review | `.cursor/commands/review.md` |
| `/handoff` | Session kapatma | `.cursor/commands/handoff.md` |
| `/compact` | Context özetleme | `.cursor/commands/compact.md` |
| `/api-endpoint` | Yeni FastAPI endpoint iskeleti | `.cursor/commands/api-endpoint.md` |
| `/db` | Alembic migration işlemleri | `.cursor/commands/db.md` |
| `/status` | Sistem sağlık raporu | `.cursor/commands/status.md` |
| `/lint` | ruff + mypy + eslint | `.cursor/commands/lint.md` |
| `/plan` 🆕 | Plan Mode workflow | `.cursor/commands/plan.md` |
| `/debug-mode` 🆕 | Debug Mode pattern | `.cursor/commands/debug-mode.md` |
| `/best-of-n` 🆕 | Paralel multi-model | `.cursor/commands/best-of-n.md` |
| `/worktree` 🆕 | İzole worktree başlat | `.cursor/commands/worktree.md` |

## 🔗 Kullanım Protokolü — Cursor AI İçin

Cursor AI bir görev aldığında:

1. **Göreve bak:** Hangi kategoriye uyuyor? (kod analizi, güvenlik, UI, algoritma, session)
2. **Yukarıdaki tabloya bak:** En uygun skill/command hangisi?
3. **Cursor port'u var mı?**
   - Varsa `.cursor/skills/<n>/SKILL.md` otomatik yüklenir (Nightly'da)
   - Yoksa `@.claude/skills/<n>/SKILL.md` ile attach iste
4. **Workflow tetikleyici command var mı?** (örn. `/review` → code-review skill)
5. **Emin değilsen:** Kullanıcıya sor, varsayım yapma

## 💡 Yeni Cursor 3.x Özellikleri (Skill'ler İçinde Dağıtılmış)

Cursor 3.x'in getirdiği ana özellikler nerede dokümante:

| Özellik | Nerede öğrenilir |
|---|---|
| **Agents Window** | `.cursor/MIGRATION-NIGHTLY.md` + bu skill'in altı |
| **Plan Mode (Shift+Tab)** | `.cursor/skills/plan-mode/SKILL.md` |
| **Design Mode (⌘+Shift+D)** | `.cursor/skills/design-mode/SKILL.md` |
| **Integrated Browser** | `.cursor/skills/design-mode/SKILL.md` |
| **@Past Chats** | `.cursor/skills/past-chats/SKILL.md` |
| **/worktree** | `.cursor/commands/worktree.md` |
| **/best-of-n** | `.cursor/commands/best-of-n.md` |
| **Debug Mode** | `.cursor/commands/debug-mode.md` |
| **Composer 2** | (model seçimi, skill değil) |
| **Canvases** | (output formatı, skill değil) |
| **Voice Input (Ctrl+M)** | `.cursor/MIGRATION-NIGHTLY.md` §9 |
| **Cloud ↔ Local handoff** | Agents Window özelliği |
| **Tiled Layout** | Agents Window özelliği |

## 📚 Detay İçin Nereye Bakmalı

### Sizin (insan) için
- `.cursor/MIGRATION-NIGHTLY.md` — GUI aksiyonları, kararlar
- `.cursor/plans/README.md` — Plan Mode çıktıları nasıl yönetilir
- `CLAUDE.md` — KIRO2 proje genel talimatları
- `.claude/rules/*.md` — 11 ayrıntılı rule (Session 6-148 dersleri)

### Cursor AI için (runtime)
- `.cursor/rules/` — her prompt'ta yüklenen 5 rule
- `.cursor/skills/` — dinamik yüklenen 12 skill
- `.cursor/commands/` — 15 slash command
- `.cursor/BUGBOT.md` — PR review kuralları
- `.cursor/hooks.json` + `hooks/*.py` — format + shell guard

### Claude Code AI için (runtime)
- `.claude/rules/` — 11 rule
- `.claude/skills/` — 24 skill
- `.claude/commands/` — 23 command
- `.claude/hooks/` — 8 Python hook

## 🔄 Single Source of Truth

Skill'lerin **canonical** versiyonu `.claude/skills/<n>/SKILL.md`'de.
`.cursor/skills/` altındakiler **thin wrapper** — kritik bilgiyi inline
verir, derin içerik için `.claude/`'ya pointer eder.

Bu sayede:
- Bir skill güncellenince sadece `.claude/` tarafı değişir
- Cursor wrapper'ları stable kalır
- İki yerde bakım gerekmez

## 🆕 Yeni Eklenenler (20 Nisan 2026)

Cursor 3.x desteği için eklenen:
- 3 skill: **plan-mode, design-mode, past-chats**
- 4 command: `/plan`, `/debug-mode`, `/best-of-n`, `/worktree`
- 1 dizin: `.cursor/plans/`
- 1 migration doc: `.cursor/MIGRATION-NIGHTLY.md`
- 1 rule güncellemesi: `00-core.mdc`'ye workflow + güvenlik bölümleri
