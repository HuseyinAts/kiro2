# Session Handoff

Mevcut session'in durumunu kaydet ve sonraki session icin hazirla.

## Adimlar (SIRASIYLA)

1. `git status` + `git diff --stat` calistir (gercek durumu gor)
2. `git log --oneline -3` ile son commit'leri al
3. Asagidaki formatta `.claude/sessions/latest.md`'ye yaz (50 satir limit)
4. MEMORY.md session index'e 1 satirlik ozet ekle
5. Pending changes varsa commit et (`chore: session handoff`)
6. Handoff prompt metnini sun

**ONEMLI:** Yeni session acmak MUMKUN DEGIL. Sadece prompt metni ver.

## Format (ZORUNLU — bu yapiyi AYNEN kullan)

```markdown
## Session Handoff — [YYYY-MM-DD HH:MM]
**Branch:** [branch]
**Son commit:** [hash] [mesaj]
**Uncommitted:** [git diff --stat ozeti veya "temiz"]

### Yapilanlar
- [dosya yolu ile madde] (commit hash varsa belirt)
- [dosya yolu ile madde]

### Fail Eden Testler
- [pytest ciktisi — yoksa "YOK"]

### Engelleyiciler
- [varsa, yoksa "YOK"]

### Sonraki Adimlar (maks 5)
1. [en oncelikli]
2. [ikinci]

### Kararlar (gelecek session tekrar tartismasin)
- [neden bu yaklasim secildi — yoksa bos birak]
```

## Anti-pattern'ler
- Dosya yolu OLMADAN "sunu yaptim" yazma — dosya:satir referansi ZORUNLU
- 50 satiri GECME — ozet olmali, transkript degil
- Testleri ATLAMA — fail eden test varsa BELIRT
