---
name: turkish-nlp
description: Türkçe string işleme kuralları. I/ı dönüşümü, UTF-8 encoding, NFC normalization, Zemberek. Türkçe içerik üretim/işlenmesinde yüklenir.
---

# Turkish NLP — KIRO2

Türkçe'nin agglutinative morfolojisi ve 4 farklı "i" harfi için kritik kurallar.

## Ne Zaman Yüklenmeli

- Türkçe string karşılaştırma, sıralama, büyük/küçük harf dönüşümü
- Tokenizer veya NLP pipeline değişiklikleri
- Zemberek entegrasyonu
- Kullanıcı input/output'unda Türkçe karakter işleme
- DB collation veya encoding sorunu çözerken

## Kritik Kural: 4 "i" Problemi

Python `.upper()` / `.lower()` Türkçe'de YANLIŞ çalışır:

| Küçük | Büyük | Doğru |
|---|---|---|
| i | İ | Türkçe |
| ı | I | Türkçe |

```python
# YANLIŞ — "istanbul".upper() → "ISTANBUL" (Türkçe değil!)
# DOĞRU
def turkish_upper(text: str) -> str:
    return (text
        .replace('i', 'İ').replace('ı', 'I')
        .replace('ğ', 'Ğ').replace('ü', 'Ü')
        .replace('ş', 'Ş').replace('ö', 'Ö')
        .replace('ç', 'Ç')
        .upper())
```

TypeScript ekvivalent: `.toLocaleUpperCase('tr-TR')` kullan (ama manuel i/ı dönüşümü gerekir).

## UTF-8 + NFC Zorunluluğu

```python
import unicodedata
text = unicodedata.normalize('NFC', user_input)
```

PostgreSQL: `LC_COLLATE = 'tr_TR.UTF-8'` (kiro2 DB bu şekilde kurulu)

FastAPI response: `content-type: application/json; charset=utf-8` middleware

## Tokenizer Uyarısı

Qwen3-8B tokenizer agglutinative morfoloji için extended vocab kullanıyor
(`qwen_extended_vocab/`). BPE tek başına Türkçe için YETERSİZ — "kitaplarımızdan"
gibi ek-ek-ek yapılı kelimeler kötü tokenize olur.

Yeni tokenizer işlemi:
1. `.claude/skills/turkish-nlp/` detaylı rehberi oku
2. Zemberek ile kök doğrulama yap
3. BPE dışı yaklaşımlar (morfeme-aware) değerlendir

## Input Sanitization Template

```python
import re, unicodedata

def sanitize_turkish_input(text: str) -> str:
    text = re.sub(r'<[^>]*>', '', text)  # HTML tag kaldır
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = unicodedata.normalize('NFC', text)
    return text.strip()
```

## Enum Uyarısı (Session 78)

KIRO2 enum'ları Türkçe:
- `SubjectType.MATEMATIK` (MATHEMATICS değil)
- `DifficultyLevel.COK_KOLAY` (VERY_EASY değil)

Test yazarken İngilizce varsayımı yapma — `list(EnumName)` ile gerçek değerleri gör.

## Detaylı Rehber

Zemberek, morfoloji analizi, karşılaştırma, Windows path backslash tuzağı:
- `.claude/skills/turkish-nlp/SKILL.md`

Tokenizer research ve Qwen extended vocab:
- `qwen_extended_vocab/` dizinindeki özel dosyalar
