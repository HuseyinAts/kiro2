# Session Handoff

Mevcut session'in durumunu kaydet ve sonraki session icin hazirla.

## Adimlar

1. Bu session'da yapilanlari ozetle (commit'ler, degisiklikler, kararlar)
2. Bekleyen isleri listele
3. Bilinen engelleyicileri belirt
4. Dokunulan kritik dosya yollarini listele
5. Sonraki session icin 1-3 somut adim oner
6. Asagidaki formatta `.claude/sessions/latest.md`'ye yaz:

```markdown
## Session Handoff — [YYYY-MM-DD HH:MM]
**Branch:** [branch]
**Son commit:** [hash]

### Yapilanlar
- [madde 1]
- [madde 2]

### Bekleyen
- [madde 1]

### Engelleyiciler
- [varsa]

### Dokunulan Dosyalar
- [dosya yollari]

### Sonraki Adimlar
1. [adim 1]
2. [adim 2]
```

7. 50 satiri gecmesin
8. Memory'yi de guncelle (MEMORY.md session index)
