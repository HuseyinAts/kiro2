---
name: turkish-nlp
description: Türkçe doğal dil işleme kuralları. I/ı dönüşümü, UTF-8 encoding, Zemberek entegrasyonu. Türkçe içerik işlenirken otomatik yüklenir.
user-invocable: false
context: fork
allowed-tools: Read, Grep, Glob
---

# Turkish NLP Skill - KIRO2

Türkçe doğal dil işleme için kritik kurallar ve best practices.

## Türkçe I/ı Problemi (KRİTİK)

Türkçe'de 4 farklı "i" harfi vardır. Yanlış dönüşüm ciddi bug'lara yol açar.

| Küçük | Büyük | Türkçe | İngilizce |
|-------|-------|--------|-----------|
| i | İ | i ↔ İ | i ↔ I |
| ı | I | ı ↔ I | - |

### Python Fonksiyonları

```python
def turkish_upper(text: str) -> str:
    """Türkçe büyük harf dönüşümü"""
    return (text
        .replace('i', 'İ')
        .replace('ı', 'I')
        .replace('ğ', 'Ğ')
        .replace('ü', 'Ü')
        .replace('ş', 'Ş')
        .replace('ö', 'Ö')
        .replace('ç', 'Ç')
        .upper())

def turkish_lower(text: str) -> str:
    """Türkçe küçük harf dönüşümü"""
    return (text
        .replace('İ', 'i')
        .replace('I', 'ı')
        .replace('Ğ', 'ğ')
        .replace('Ü', 'ü')
        .replace('Ş', 'ş')
        .replace('Ö', 'ö')
        .replace('Ç', 'ç')
        .lower())

def turkish_casefold(text: str) -> str:
    """Case-insensitive karşılaştırma için"""
    return turkish_lower(text)
```

### TypeScript Fonksiyonları

```typescript
function turkishUpper(text: string): string {
  return text
    .replace(/i/g, 'İ')
    .replace(/ı/g, 'I')
    .toLocaleUpperCase('tr-TR');
}

function turkishLower(text: string): string {
  return text
    .replace(/İ/g, 'i')
    .replace(/I/g, 'ı')
    .toLocaleLowerCase('tr-TR');
}

function turkishCompare(a: string, b: string): number {
  return a.localeCompare(b, 'tr-TR');
}
```

## UTF-8 Encoding (ZORUNLU)

### PostgreSQL

```sql
CREATE DATABASE kiro2
WITH ENCODING = 'UTF8'
LC_COLLATE = 'tr_TR.UTF-8'
LC_CTYPE = 'tr_TR.UTF-8'
TEMPLATE = template0;

-- Türkçe sıralama
SELECT * FROM questions ORDER BY content COLLATE "tr_TR.UTF-8";
```

### FastAPI Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware

class UTF8Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            if 'charset' not in content_type:
                response.headers['content-type'] = f'{content_type}; charset=utf-8'
        return response
```

## Zemberek Entegrasyonu

```python
from zeyrek import MorphAnalyzer

analyzer = MorphAnalyzer()

def validate_turkish_word(word: str) -> dict:
    """Türkçe kelime doğrulama ve analiz"""
    analyses = analyzer.lemmatize(word)
    if not analyses:
        return {'valid': False, 'error': 'Kelime sözlükte bulunamadı'}
    
    best_analysis = analyses[0]
    return {
        'valid': True,
        'lemma': best_analysis[1],  # Kök form
        'pos': best_analysis[0],     # Part of speech
    }

# Örnek: validate_turkish_word('kitaplarımızdan')
# {'valid': True, 'lemma': 'kitap', 'pos': 'Noun'}
```

## Türkçe Karakterler

```python
TURKISH_CHARS = set('ğüşıöçĞÜŞİÖÇ')

def contains_turkish(text: str) -> bool:
    return any(c in TURKISH_CHARS for c in text)

def validate_turkish_content(content: str) -> bool:
    """İçeriğin Türkçe olduğunu doğrula"""
    if not contains_turkish(content):
        raise ValueError('İçerik Türkçe karakter içermelidir')
    return True
```

## Input Sanitization

```python
import re

def sanitize_turkish_input(text: str) -> str:
    """Güvenli Türkçe input temizleme"""
    # HTML tag'lerini kaldır
    text = re.sub(r'<[^>]*>', '', text)
    # Script injection önle
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    # Unicode normalize
    import unicodedata
    text = unicodedata.normalize('NFC', text)
    return text.strip()
```

## Doğrulama Kontrol Listesi

- [ ] Tüm string karşılaştırmalarında turkish_casefold kullan
- [ ] Büyük/küçük harf dönüşümlerinde turkish_upper/lower kullan
- [ ] Veritabanı tr_TR.UTF-8 collation ile oluşturuldu
- [ ] API response'larında charset=utf-8 header var
- [ ] Kullanıcı inputları sanitize ediliyor
- [ ] Zemberek ile kelime doğrulama yapılıyor (gerekirse)
