---
name: deep-research
description: Konu hakkında derinlemesine araştırma yapar. Codebase analizi, dokümantasyon taraması ve pattern keşfi için kullanılır. Araştırma sonuçları ana context'e özet olarak döner.
context: fork
agent: Explore
model: sonnet
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

# Deep Research: $ARGUMENTS

Bu skill, belirtilen konu hakkında kapsamlı araştırma yapar ve bulgularını özetler.

## Araştırma Protokolü

### Adım 1: Dosya Keşfi
- Glob ile ilgili dosyaları bul: `**/*$ARGUMENTS*`
- İlgili pattern'leri ara: `*.py`, `*.ts`, `*.md`
- Config dosyalarını kontrol et

### Adım 2: Kod Analizi
```
Aranacak Pattern'ler:
- Class tanımları: class.*$ARGUMENTS
- Function tanımları: def.*$ARGUMENTS / function.*$ARGUMENTS
- Import'lar: import.*$ARGUMENTS / from.*$ARGUMENTS
- Kullanım yerleri: $ARGUMENTS\(
```

### Adım 3: Dokümantasyon Taraması
- README dosyalarını oku
- Docstring'leri analiz et
- Comment'leri incele
- API dokümantasyonunu kontrol et

### Adım 4: Dependency Analizi
- Bu modülü kullanan dosyaları bul
- Bu modülün kullandığı dependency'leri listele
- Circular dependency kontrolü yap

### Adım 5: Web Araştırması (Gerekirse)
- Resmi dokümantasyon
- Stack Overflow çözümleri
- GitHub issues/discussions

## Çıktı Formatı

Araştırma sonuçlarını şu formatta raporla:

```markdown
## Araştırma: $ARGUMENTS

### Bulunan Dosyalar
| Dosya | Satır | Açıklama |
|-------|-------|----------|
| path/to/file.py | 42 | Ana implementasyon |

### Önemli Pattern'ler
- Pattern 1: Açıklama
- Pattern 2: Açıklama

### Dependencies
- Upstream: [bu modülü kullananlar]
- Downstream: [bu modülün kullandıkları]

### Öneriler
1. Öneri 1
2. Öneri 2

### Kaynaklar
- [Kaynak 1](url)
- [Kaynak 2](url)
```

## KIRO2 Spesifik Kurallar

- **Türkçe Desteği**: Araştırma sonuçlarını Türkçe yaz
- **IRT/FSRS/ZPD**: Bu algoritmalara özel dikkat göster
- **Boris Cherny Standards**: Kod kalitesi notlarını dahil et
- **Type Hints**: Type annotation kullanımını raporla

## Örnek Kullanım

```
/deep-research OAuth implementation
/deep-research IRT parametreleri
/deep-research video player component
/deep-research Zemberek NLP entegrasyonu
```

## Notlar

- Bu skill izole context'te çalışır (context: fork)
- Ana context'e sadece özet döner
- Sonnet model kullanılır (kalite öncelikli)
- Read-only araçlar kullanılır (güvenli)
