# Context Compact

Mevcut konuşma context'ini özetle ve sıkıştır — önemli bilgiler kaybolmadan
token tüketimini azalt.

## Koru

- **Dosya yolları** — dokunulan her dosya ve konumu
- **Fonksiyon/class isimleri** — özellikle yeni eklenen veya değiştirilen
- **Hatalar** — stack trace'lerin özetleri, error message'lar
- **Kararlar** — "X yerine Y kullanılacak" gibi mimari seçimler
- **Test sonuçları** — passed/failed sayıları, failure türleri
- **Git durumu** — branch, son commit hash, uncommitted dosyalar
- **Açık TODO'lar** — yarım kalan işler

## Sil

- Uzun kod blokları (referans yeterli)
- Tekrarlanan açıklamalar
- Düşünme süreci (ara tartışmalar)
- Daha önce çözülmüş sorunların detayı
- Backtrack edilmiş yolların hikâyesi

## Format

Özet markdown, maksimum 30 satır:

```markdown
## Context Özeti — [TARIH HH:MM]

### Çalışılan Konu
[1-2 cümle]

### Dokunulan Dosyalar
- path/file1.py — [ne yapıldı]
- path/file2.ts — [ne yapıldı]

### Kararlar
1. [karar 1]
2. [karar 2]

### Açık Durumu
- Test: X passed, Y failed
- Git: branch [adı], uncommitted [N dosya]
- Devam eden: [yarım iş]

### Sonraki Adım
[1 cümle]
```

## Ne Zaman Kullanılır

- Context %70+ dolduğunda (Cursor otomatik preCompact uyarısı verebilir)
- Uzun debugging oturumu sonrası
- Dallanmış/dönüş yapmış görevlerde
- `/handoff` öncesi hazırlık olarak

## KIRO2 Özel

`CLAUDE.md`'deki context management threshold ayarları: warning %60, clear %70.
Bu command context'i sıfırlamaz — özetleyip devam ettirir. Sıfırlamak için
yeni chat açman gerekir (`/handoff` sonrası).
