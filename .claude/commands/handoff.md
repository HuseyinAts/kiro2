---
description: Session handoff - context checkpoint olustur
allowed-tools: Bash(git:*), Bash(python:*), Read, Write
---

# Handoff: $ARGUMENTS

## Task
Session state'i kaydet ve sonraki session icin context hazirla. Otomatik + manuel.

## Adimlar

### 1. Otomatik State Kaydet
```bash
python C:/Users/husey/kiro2/.claude/hooks/session-save.py
```

### 2. Git Durumu
- **Son commit:** !`git log -1 --oneline`
- **Branch:** !`git branch --show-current`
- **Degisen dosyalar:**
!`git status --short | head -15`

### 3. Son 5 Commit
!`git log -5 --oneline`

### 4. Bekleyen Isler
$ARGUMENTS varsa aktif gorevi belirt, yoksa TaskList'ten in_progress olanlari listele.

### 5. CLAUDE.local.md Guncelle
Asagidaki formatta CLAUDE.local.md'nin "GUNCEL DURUM" bolumunu guncelle:

```markdown
## GUNCEL DURUM (Tarih - Session N)

**Proje:** pytest X passed, Y skipped, Z failures
**Branch:** branch-adi | **Commit:** `hash`
**Production:** eslesmis_sorucevap.jsonl = X soru (vN.N)

### Son Session Yapilan
1. [is 1]
2. [is 2]
3. [is 3]

### Sonraki Adimlar
1. [adim 1]
2. [adim 2]
```

### 6. Sonraki Session Prompt
Kopyala-yapistir hazir prompt olustur:

```
Onceki session'dan devam ediyorum.
.claude/SESSION_STATE.md'yi oku ve context'i restore et.
Devam edilecek: $ARGUMENTS
```

---
*Handoff olusturuldu: !`date +%Y-%m-%d_%H:%M`*
