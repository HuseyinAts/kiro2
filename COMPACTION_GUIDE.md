# KIRO2 Context Management Rehberi

## Temel Prensip
**Compaction'a güvenme, aktif yönet!**

## %60 Kuralı
Context %60'a ulaştığında:
1. `/context` ile durumu kontrol et
2. progress.md'ye mevcut durumu kaydet
3. Devam et ama dikkatli ol

## %70 Kuralı
Context %70'e ulaştığında:
1. HEMEN dur
2. `/handoff` komutu çalıştır
3. Git commit at: `WIP: [özet]`
4. `/clear` yap
5. progress.md oku, kaldığın yerden devam et

## Slash Commands

| Komut | Açıklama |
|-------|----------|
| `/api-endpoint X` | Yeni FastAPI endpoint oluştur |
| `/component X` | Yeni React component oluştur |
| `/handoff` | Session handoff hazırla |
| `/checkpoint` | Context checkpoint oluştur |
| `/compact X` | Manuel kompakt sıkıştırma |
| `/quick-status` | Hızlı durum raporu |

## Session Stratejisi
```bash
# Task bazlı session'lar
claude --session=kiro2-backend-auth
claude --session=kiro2-frontend-ui
claude --session=kiro2-database
claude --session=kiro2-debug
```

## Document & Clear Workflow

### Session Başında:
```
progress.md dosyasını oku ve kaldığımız yerden devam et
```

### Çalışırken (her 10-15 prompt):
```
/context
```

### %60-70 arası:
```
Dur. Şu ana kadar yaptıklarımızı, kararları ve sonraki 
adımları progress.md dosyasına kaydet.
```

### Temiz başlangıç:
```
/clear
progress.md dosyasını oku ve devam et
```

## progress.md Şablonu
```markdown
## Aktif Task
[Mevcut çalışılan özellik]

## Tamamlanan
- [x] İş 1
- [x] İş 2

## Sonraki
- [ ] İş 3
- [ ] İş 4

## Kararlar
- Karar 1: Neden
- Karar 2: Neden
```

## Sorun Giderme

### "Exceed max compactions" hatası
1. Esc ile interrupt et
2. `/clear` yap
3. progress.md oku

### Context %100+ gösteriyor
1. Terminal'den: `claude --resume`
2. `/compact` dene
3. Çalışmazsa `/clear`

### CLAUDE.md unutuluyor
Post-Compaction Routine aktif olmalı (CLAUDE.md sonunda var)
