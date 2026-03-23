---
name: checkpoint
description: Context checkpoint olustur — commit sonrasi veya onemli milestone'da SESSION_STATE.md ve MEMORY.md guncelle
---

# Checkpoint — Progressive Context Save

## Ne Zaman Kullan
- Her commit sonrasi (ZORUNLU)
- Buyuk degisiklik tamamlandiginda
- Compaction oncesi (/compact)
- Session ortasinda context kaybi riski varsa

## Adimlari

### 1. Git Durumu Oku
```bash
git log --oneline -5
git status --short
git diff --cached --stat
```

### 2. Mevcut State Oku
- `.claude/sessions/latest.md` (SESSION_STATE) oku
- Eger bossa veya eskiyse sifirdan olustur

### 3. State Guncelle

SESSION_STATE.md'ye yaz (max 50 satir):

```markdown
# Session State (checkpoint: {TARIH})

## Quick Resume
- **Branch:** {branch}
- **Last commit:** {hash} {mesaj}
- **Uncommitted:** {sayi} files
- **Production:** 77,336 questions

## Bu Session'da Yapilanlar
- {is 1}
- {is 2}
...

## Bekleyen Isler
1. {oncelikli is}
2. {diger is}

## Test Durumu
- Backend: {passed}/{total} passed, {skipped} skipped
- Frontend: tsc {error_count} error

## Son Dokunulan Dosyalar
- {dosya1}
- {dosya2}
```

### 4. MEMORY.md Session Index (Gerekirse)

Session index'e yeni entry ekle — SADECE onemli milestone'larda:
- Yeni feature tamamlandi
- Buyuk bug fix
- Mimari degisiklik

Format: `- Session {N}: {1 satir ozet} (commit \`{hash}\`)`

### 5. Onay Mesaji

```
Checkpoint saved: {commit_hash}
- SESSION_STATE.md guncellendi
- {N} yapilan is, {M} bekleyen is
```

## Kurallar
- SESSION_STATE.md 50 satiri GECMEZ
- Atomic write: gecici dosyaya yaz, sonra rename
- MEMORY.md'ye her checkpoint'te EKLEME — sadece milestone'larda
- Checkpoint session-save hook'unu TETIKLEMEZ (cift yazma onlenir)
