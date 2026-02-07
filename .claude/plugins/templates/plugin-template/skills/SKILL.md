---
name: example-skill
description: Example skill demonstrating skill integration
user-invocable: true
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
  - example-tool
---

# Example Skill

Bu skill, KIRO2 Claude Code plugin sistemi için örnek bir skill tanımıdır.

## Kullanım

```
/example-skill
```

Veya otomatik olarak ilgili konularda aktive olur.

## Özellikler

### Dosya Analizi

Bu skill dosyaları analiz edebilir:

1. Python dosyalarını oku
2. Pattern'leri ara
3. Sonuçları raporla

### Örnek Workflow

```
1. Kullanıcı skill'i çağırır
2. Skill gerekli dosyaları okur
3. Analiz yapar
4. Sonuçları formatlar
5. Kullanıcıya sunar
```

## Konfigürasyon

Skill şu parametrelerle yapılandırılabilir:

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| verbose | false | Detaylı çıktı |
| format | text | Çıktı formatı |
| max_files | 10 | Maksimum dosya sayısı |

## Bağımlılıklar

Bu skill şu tool'ları kullanır:

- `Read`: Dosya okuma
- `Grep`: Pattern arama
- `Glob`: Dosya bulma
- `example-tool`: Plugin tool

## Örnekler

### Temel Kullanım

```
User: /example-skill
Claude: Analiz başlatılıyor...
```

### Parametreli Kullanım

```
User: /example-skill --verbose --format=markdown
Claude: Detaylı analiz markdown formatında...
```

## Hata Durumları

| Hata | Çözüm |
|------|-------|
| Dosya bulunamadı | Path'i kontrol et |
| İzin hatası | Permissions kontrol et |
| Timeout | max_files değerini düşür |

## Notlar

- Bu skill `context: fork` ile çalışır, ana context'i etkilemez
- Sonuçlar ana conversation'a özet olarak döner
- Tool kullanımı izin gerektirmez (allowed-tools'da tanımlı)
