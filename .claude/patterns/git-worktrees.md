# Git Worktrees Pattern

> "Birden fazla branch uzerinde ayni anda calisma. Her worktree izole dosya sistemi."

## Konsept

Git worktrees, ayni repo'nun birden fazla checkout'unu saglar:
- Ayni `.git` dizinini paylaşır (space-efficient)
- Her worktree farkli branch'te
- Dosya cakismasi yok

## Kurulum

```bash
# Ana repo
cd c:\Users\husey\kiro2

# Feature worktree olustur
git worktree add ../kiro2-feature-auth feature/auth

# Hotfix worktree olustur
git worktree add ../kiro2-hotfix hotfix/critical-bug

# UI worktree olustur
git worktree add ../kiro2-ui-refactor feature/ui-modernization
```

## Paralel Claude Sessions

```bash
# Terminal 1 - Backend API gelistirme
cd c:\Users\husey\kiro2
claude --session=backend-main

# Terminal 2 - Frontend feature (paralel)
cd c:\Users\husey\kiro2-feature-auth
claude --session=feature-auth

# Terminal 3 - Acil hotfix (paralel)
cd c:\Users\husey\kiro2-hotfix
claude --session=hotfix-critical
```

## Merge Stratejisi

```bash
# Feature tamamlandiginda
cd c:\Users\husey\kiro2

# Feature branch'i merge et
git merge feature/auth --no-ff

# Worktree temizle
git worktree remove ../kiro2-feature-auth

# Branch sil (opsiyonel)
git branch -d feature/auth
```

## KIRO2 Kullanim Senaryolari

### Senaryo 1: Backend + Frontend Paralel
```
kiro2/                    # Backend API gelistirme
kiro2-frontend/           # React component gelistirme
```

### Senaryo 2: Feature + Hotfix
```
kiro2/                    # Ana feature calismasi
kiro2-hotfix/             # Production bug fix
```

### Senaryo 3: Refactor + Tests
```
kiro2/                    # Kod refactor
kiro2-tests/              # Test yazimi (ayni zamanda)
```

## Worktree Yonetimi

```bash
# Mevcut worktree'leri listele
git worktree list

# Worktree bilgisi
git worktree list --porcelain

# Worktree sil
git worktree remove ../kiro2-feature-auth

# Temizlik (silinen branch'lerin worktree ref'lerini temizle)
git worktree prune
```

## Session Eslestirme

| Worktree | Branch | Session | Gorev |
|----------|--------|---------|-------|
| kiro2/ | main | backend-main | Ana gelistirme |
| kiro2-auth/ | feature/auth | feature-auth | Auth modulu |
| kiro2-hotfix/ | hotfix/db-fix | hotfix-db | Acil duzeltme |

## Dikkat Edilecekler

1. **Ayni branch'i iki worktree'de kullanma** - Git buna izin vermez
2. **node_modules**: Her worktree icin ayri `npm install` gerekir
3. **venv**: Python virtual env her worktree'de ayri olustur
4. **DB migration**: Dikkatli ol, ayni DB'yi etkileyebilir

## Best Practices

- Kisa omurlu worktree'ler olustur (feature/hotfix tamamlaninca sil)
- Session adini worktree ile esitle
- Merge oncesi her iki worktree'de testleri calistir
- Duzgun commit message'lari ile traceback kolaylastir
