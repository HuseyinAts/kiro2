---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git diff:*)
argument-hint: [commit message]
description: Değişiklikleri stage et ve commit yap
---

## Context
- Current git status: !`git status --short`
- Current diff summary: !`git diff --stat HEAD`

## Task
Commit mesajı ile değişiklikleri kaydet: $ARGUMENTS

## Commit Convention (KIRO2)

Format: `<type>(<scope>): <description>`

### Types
- `feat`: Yeni özellik
- `fix`: Bug düzeltme
- `docs`: Dokümantasyon
- `style`: Format değişikliği (kod değişmez)
- `refactor`: Kod yeniden yapılandırma
- `test`: Test ekleme/düzeltme
- `chore`: Build, CI, tooling
- `perf`: Performans iyileştirme

### Scopes (KIRO2)
- `backend`, `frontend`, `ai`, `db`
- `auth`, `exam`, `content`, `ocr`, `api`

## Örnek Commitler

```
feat(auth): add 2FA support for admin users
fix(exam): resolve timer sync issue
docs(api): update swagger documentation
test(backend): add unit tests for exam service
perf(db): optimize question query with index
```

## Adımlar

1. Değişiklikleri stage et: `git add -A`
2. Status kontrol: `git status`
3. Commit yap: `git commit -m "$ARGUMENTS"`
