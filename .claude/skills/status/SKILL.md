# Status Check

Hizli durum raporu - codebase kesfetmeden mevcut bilgiyi kullan.

## Adimlar

1. Memory dosyalarini oku: `memory/MEMORY.md` ve `memory/sessions.md`
2. Son 3 git commit'i kontrol et: `git log --oneline -3`
3. Degistirilmis dosyalari goster: `git status --short`
4. Asagidaki formatta ozet sun:

```
## Durum Raporu
- **Branch:** [branch]
- **Son commit:** [hash] [mesaj]
- **Degisen dosyalar:** [sayi]
- **Son session:** [session ozeti]
- **Bekleyen isler:** [liste]
- **Engelleyiciler:** [varsa]
```

5. Sonraki 1-3 adimi oner
6. Codebase kesfetme, sadece git + memory bilgisini kullan
