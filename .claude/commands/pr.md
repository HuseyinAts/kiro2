---
allowed-tools: Bash(git:*), Bash(gh:*)
description: Pull request oluştur
---

## Context
- Current branch: !`git branch --show-current`
- Commits since main: !`git log main..HEAD --oneline`
- Changed files: !`git diff main --stat`

## Task
GitHub'da Pull Request oluştur.

## Adımlar

1. **Branch'i push et**
```bash
git push origin HEAD
```

2. **PR oluştur**
```bash
gh pr create --fill
```

3. **PR linkini göster**

## PR Template (KIRO2)

```markdown
## Değişiklik Özeti
[Kısa açıklama]

## Değişiklik Tipi
- [ ] feat: Yeni özellik
- [ ] fix: Bug düzeltme
- [ ] refactor: Kod iyileştirme
- [ ] docs: Dokümantasyon
- [ ] test: Test ekleme

## Test Edildi mi?
- [ ] Unit testler geçti
- [ ] Integration testler geçti
- [ ] Manuel test yapıldı

## Checklist
- [ ] Kod lint kontrolünden geçti
- [ ] Type hints eklendi
- [ ] CLAUDE.md güncellendi (gerekirse)
```

## Etiketler
- `backend`, `frontend`, `ai-ml`
- `bug`, `enhancement`, `documentation`
- `P0-critical`, `P1-high`, `P2-medium`
