---
name: save-memory
description: Konuşmayı özetler ve kalıcı belleğe kaydeder. Önemli kararları, TODO'ları ve öğrenilen dersleri ~/.claude/memory/memories.md dosyasına yazar.
user-invocable: true
context: fork
disable-model-invocation: true
allowed-tools:
  - Read
  - Edit
  - Glob
---

# Memory Saver: $ARGUMENTS

Bu skill, mevcut konuşmayı özetler ve kalıcı belleğe kaydeder.
SADECE kullanıcı tarafından tetiklenebilir.

## Bellek Dosyası

```
~/.claude/memory/
├── memories.md       # Ana bellek dosyası
├── decisions.md      # Önemli kararlar
├── lessons.md        # Öğrenilen dersler
└── todos.md          # Açık TODO'lar
```

## Kaydetilecek Bilgiler

### 1. Önemli Kararlar
- Mimari kararlar ve gerekçeleri
- Teknoloji seçimleri
- Trade-off analizi sonuçları

### 2. Öğrenilen Dersler
- Hata çözümleri
- Performans optimizasyonları
- Best practice keşifleri

### 3. Açık TODO'lar
- Tamamlanmamış görevler
- Gelecekte yapılacaklar
- Technical debt

### 4. Bağlam Bilgisi
- Hangi dosyalar üzerinde çalışıldı
- Hangi sorunlar çözüldü
- Mevcut durum

## Çıktı Formatı

### memories.md'ye Eklenecek
```markdown
## [${DATE}] - $ARGUMENTS

### Oturum Özeti
[Konuşmanın kısa özeti]

### Önemli Kararlar
- **Karar**: [karar açıklaması]
  - **Gerekçe**: [neden bu karar alındı]
  - **Alternatifler**: [değerlendirilen diğer seçenekler]

### Yapılan Değişiklikler
- [dosya1.py]: [değişiklik açıklaması]
- [dosya2.ts]: [değişiklik açıklaması]

### Açık TODO'lar
- [ ] [todo item 1]
- [ ] [todo item 2]

### Öğrenilen Dersler
- [ders 1]
- [ders 2]

### Sonraki Adımlar
1. [adım 1]
2. [adım 2]

---
```

## Kayıt Kuralları

### KAYDET ✅
- Mimari kararlar
- Bug çözümleri
- Performans iyileştirmeleri
- Konfigürasyon değişiklikleri
- API tasarımları
- Veritabanı şema değişiklikleri

### KAYDETME ❌
- API keys, passwords, tokens
- Kişisel bilgiler
- Geçici debug kodları
- Hassas iş verileri
- Credential bilgileri

## Örnek Kullanım

```bash
# Genel özet
/save-memory "Authentication refactoring tamamlandı"

# Belirli bir karar
/save-memory "PostgreSQL yerine Redis cache tercih edildi"

# Sprint özeti
/save-memory "Sprint 3 tamamlandı - video player entegrasyonu"
```

## KIRO2 Spesifik Notlar

### IRT/FSRS/ZPD
Bu algoritmalara ait kararlar özellikle detaylı kaydedilmeli:
- Parametre seçimleri
- Kalibrasyon sonuçları
- Performans metrikleri

### Türkçe NLP
Zemberek ve BERTurk ile ilgili:
- Encoding sorunları ve çözümleri
- Tokenization kararları
- Morfolojik analiz optimizasyonları

### Database
- Migration geçmişi
- Index optimizasyonları
- Query performans notları

## Otomatik Tagging

Kayıtlara otomatik tag eklenir:
- `#backend` / `#frontend`
- `#bugfix` / `#feature` / `#refactor`
- `#database` / `#api` / `#ui`
- `#performance` / `#security`
- `#irt` / `#fsrs` / `#zpd`

## Bellek Okuma

Önceki kayıtları okumak için doğrudan dosyaları okuyun:
```bash
# Ana bellek dosyası
cat ~/.claude/memory/memories.md

# Sadece kararlar
cat ~/.claude/memory/decisions.md

# Sadece dersler
cat ~/.claude/memory/lessons.md

# Sadece TODO'lar
cat ~/.claude/memory/todos.md
```

## Dosya Konumları

```
~/.claude/memory/memories.md    # Ana bellek
~/.claude/memory/decisions.md   # Sadece kararlar
~/.claude/memory/lessons.md     # Sadece dersler
~/.claude/memory/todos.md       # Sadece TODO'lar
```

## Notlar

- Bu skill izole context'te çalışır
- Kullanıcı onayı olmadan tetiklenmez
- Hassas bilgiler ASLA kaydedilmez
- Her kayıt tarih damgalıdır
- Mevcut içerik KORUNARAK append edilir
