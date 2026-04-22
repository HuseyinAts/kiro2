# Session Handoff

Mevcut Cursor session'ını kapatmadan önce state'i kaydet, sonraki session için
context hazırla.

## Adımlar

### 1. Git Durumu Topla

```bash
git branch --show-current
git log -1 --oneline
git log -5 --oneline
git status --short | head -15
git diff --stat HEAD
```

Bu bilgileri aşağıdaki özete dahil et.

### 2. `progress.md` Güncelle

`progress.md` dosyasının en üstüne yeni session entry'si ekle:

```markdown
## Session [TARIH] - [KISA_BASLIK]

**Durum:**
- Branch: [branch-adi]
- Son commit: `[hash] [mesaj]`
- Uncommitted: [N dosya]

**Yapılan:**
1. [iş 1]
2. [iş 2]
3. [iş 3]

**Yarım Kalan (sonraki session):**
- [bekleyen iş 1]
- [bekleyen iş 2]

**Blokajlar:**
- [varsa engel]

**Sonraki Oturum Başlangıcı:**
- [1 cümlelik hatırlatma]
```

### 3. `.claude/sessions/latest.md` (Claude Code uyumluluğu)

Eğer mevcutsa bu dosyayı da güncelle. Format `CLAUDE.md`'deki session handoff
checklist ile aynı:

- ✅ Completed (yapılanlar)
- ⏳ Remaining (bekleyenler)
- 🔧 State (Docker/Redis/PG durumu)
- ⚠️ Known Issues (sorunlar)

### 4. Uncommitted Değişiklikleri Karar Ver

Eğer `git status` uncommitted dosyalar gösteriyorsa:

- **Temiz kalmalı** → kullanıcıya göster, commit/stash öner
- **Commit** → `/commit` komutunu öner
- **Geçici stash** → `git stash save "handoff: [tarih]"` öner

### 5. Sonraki Session İçin Kickstart Prompt

Kullanıcıya kopyalanabilir tek blok ver:

```
Önceki session'dan devam ediyorum.
progress.md'nin en üstündeki [Session TARIH] entry'sini oku.
Devam edilecek: [YARIM_KALAN_IŞLER]
```

## Önemli Kural

Cursor'da yeni chat açmak session'ı bitirmez ama context'i sıfırlar. `progress.md` ve
`latest.md` bu geçişte state taşır. Handoff olmadan yeni chat açarsan önceki kararlar
kaybolur.

## Context Yönetimi (CLAUDE.md'den)

KIRO2 workflow'unda context warning threshold %60, clear %70. `/compact` komutu
ile kısaltabilir veya `/handoff` ile session kaydı yapıp yeni chat aç.
