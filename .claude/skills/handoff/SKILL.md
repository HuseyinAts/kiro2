# Session Handoff

Mevcut session'in durumunu kaydet ve sonraki session icin hazirla.

## Adimlar

1. SESSION_STATE.md ve MEMORY.md'yi oku (context dogrula)
2. Bu session'da yapilanlari ozetle (commit'ler, degisiklikler, kararlar)
3. Bekleyen isleri listele
4. Bilinen engelleyicileri belirt
5. Dokunulan kritik dosya yollarini listele
6. Sonraki session icin 1-3 somut adim oner
7. `.claude/sessions/latest.md`'ye yaz (formatta)
8. MEMORY.md session index'e ekle
9. Pending changes varsa commit et (message: 'chore: session handoff')
10. Handoff prompt metnini sun

**ONEMLI:** Yeni session acmak MUMKUN DEGIL. Sadece prompt metni ver.

## Format

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
