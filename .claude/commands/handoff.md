---
description: Session handoff - context checkpoint olustur
allowed-tools: Bash(git:*), Read, Write
---

# Handoff: $ARGUMENTS

## 1. Durum Ozeti
- **Aktif gorev:** $ARGUMENTS
- **Son commit:** !`git log -1 --oneline`
- **Branch:** !`git branch --show-current`
- **Degisen dosyalar:**
!`git status --short | head -15`

## 2. Yapilanlar (Son 5 Commit)
!`git log -5 --oneline`

## 3. Bekleyen Isler
<!-- Manuel doldur: Tamamlanmayan gorevler -->
- [ ]

## 4. Kritik Baglamlar (KIRO2 Spesifik)
- authStore.ts kullan (useAuth.ts DEGIL!)
- DB Port: 5434 (5432 degil!)
- Turkce I/i donusumune dikkat

## 5. Onemli Dosyalar (Bu Session)
<!-- Son degistirilen kritik dosyalar -->
!`git diff --name-only HEAD~3 | head -10`

## 6. Kararlar ve Notlar
<!-- Alinan kararlar ve sebepleri -->
| Karar | Sebep |
|-------|-------|
|  |  |

## 7. Sonraki Session Prompt
```
Onceki session'dan devam ediyorum.

1. CLAUDE.md oku
2. progress.md kontrol et
3. Son durum: [ozet]
4. Devam edilecek: $ARGUMENTS

Baslamadan once `/context` calistir.
```

---
*Handoff olusturuldu: !`date +%Y-%m-%d_%H:%M`*
