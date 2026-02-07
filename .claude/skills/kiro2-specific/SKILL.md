---
name: kiro2-specific
description: KIRO2 YKS hazırlık platformunun özel gereksinimleri, IRT/FSRS/ZPD validasyonu ve Türkçe dil kuralları. Platform spesifik kod yazarken otomatik yüklenir.
user-invocable: false
allowed-tools: Read, Grep, Glob
---

# KIRO2 Platform Skills

## Genel Bakış
KIRO2 YKS hazırlık platformunun özel gereksinimleri ve doğrulama kuralları.

## Teknoloji Stack
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL + Redis
- **Frontend**: React 18 + TypeScript + Zustand + Next.js
- **AI/ML**: IRT, FSRS, ZPD, Zemberek, BERTurk

## Kritik Kurallar

### Auth Store (P0 - KRİTİK)
```
❌ ASLA useAuth.ts kullanma
✅ HER ZAMAN authStore.ts kullan
```

### Veritabanı
- **Port**: 5434 (standart 5432 değil!)
- **Encoding**: UTF-8 (tr_TR.UTF-8)
- **ORM**: SQLAlchemy 2.0+

### API Endpoint'leri
| Servis | Port | URL |
|--------|------|-----|
| Backend | 8000 | http://localhost:8000 |
| Frontend | 3001 | http://localhost:3001 |
| PostgreSQL | 5434 | localhost:5434 |
| Redis | 6379 | localhost:6379 |

---

## Doğrulama Gereksinimleri

### IRT Parametreleri (P0)
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Zorluk (b) | [-4.0, 4.0] | Logit ölçeği, 0 = ortalama |
| Ayırt edicilik (a) | [0.2, 4.0] | Pozitif, tipik: 1.0-1.5 |
| Şans (c) | [0.0, 0.35] | 5 şıklı MCQ için ~0.20 |

**Uyumsuzluk Kuralı**: Düşük ayırt edicilik (<0.4) + Aşırı zorluk (|b|>3) = GEÇERSİZ

```python
from pydantic import BaseModel, Field, model_validator

class IRTParameters(BaseModel):
    difficulty: float = Field(..., ge=-4.0, le=4.0)
    discrimination: float = Field(..., ge=0.2, le=4.0)
    guessing: float = Field(default=0.2, ge=0.0, le=0.35)
    
    @model_validator(mode='after')
    def validate_consistency(self):
        if self.discrimination < 0.4 and abs(self.difficulty) > 3.0:
            raise ValueError('Düşük ayırt edicilik ile aşırı zorluk uyumsuz')
        return self
```

### FSRS Parametreleri (P0)
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Stabilite | [0.1, 3650] | Gün cinsinden (max 10 yıl) |
| Zorluk | [0.0, 10.0] | Kart zorluğu |
| Hatırlanabilirlik | [0.0, 1.0] | Olasılık |

**Formül**: `R(t) = e^(-t/S)` (S = stabilite, t = geçen gün)

### ZPD Bölgeleri (P0)
| Bölge | Başarı Tahmini | Açıklama |
|-------|----------------|----------|
| TOO_EASY | > 85% | Öğrenme potansiyeli düşük |
| **OPTIMAL** | **15% - 85%** | **İdeal öğrenme bölgesi** |
| TOO_HARD | < 15% | Hayal kırıklığı riski |

```python
from enum import Enum

class ZPDZone(str, Enum):
    TOO_EASY = "too_easy"
    OPTIMAL = "optimal"
    TOO_HARD = "too_hard"

def classify_zpd(success_prob: float) -> ZPDZone:
    if success_prob > 0.85:
        return ZPDZone.TOO_EASY
    elif success_prob < 0.15:
        return ZPDZone.TOO_HARD
    return ZPDZone.OPTIMAL
```

---

## Türkçe Dil Kuralları (P0 - KRİTİK)

### I/ı Dönüşümü
Türkçe'de 4 farklı "i" harfi var (İngilizce'de 2):

| Küçük | Büyük | Türkçe | İngilizce |
|-------|-------|--------|-----------|
| i | İ | i↔İ | i↔I |
| ı | I | ı↔I | - |

### Python Fonksiyonları
```python
def turkish_upper(text: str) -> str:
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
    return (text
        .replace('İ', 'i')
        .replace('I', 'ı')
        .replace('Ğ', 'ğ')
        .replace('Ü', 'ü')
        .replace('Ş', 'ş')
        .replace('Ö', 'ö')
        .replace('Ç', 'ç')
        .lower())
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

### UTF-8 Zorunlu
```sql
-- PostgreSQL
CREATE DATABASE kiro2
  WITH ENCODING = 'UTF8'
  LC_COLLATE = 'tr_TR.UTF-8'
  LC_CTYPE = 'tr_TR.UTF-8';
```

---

## YKS Sınav Tipleri

### Geçerli Dersler
| Sınav | Dersler |
|-------|---------|
| TYT | Türkçe, Matematik, Geometri, Tarih, Coğrafya, Felsefe, Din, Fizik, Kimya, Biyoloji |
| AYT-SAY | Matematik, Geometri, Fizik, Kimya, Biyoloji |
| AYT-EA | Matematik, Geometri, Edebiyat, Tarih, Coğrafya |
| AYT-SÖZ | Edebiyat, Tarih, Coğrafya, Felsefe, Din, Psikoloji, Sosyoloji, Mantık |
| YDT | İngilizce, Almanca, Fransızca, Arapça, Rusça |

### Soru Format Doğrulama
```python
class YKSQuestion(BaseModel):
    exam_type: Literal["TYT", "AYT-SAY", "AYT-EA", "AYT-SOZ", "YDT"]
    subject: str
    content: str = Field(..., min_length=10, max_length=5000)
    options: list[str] = Field(..., min_length=5, max_length=5)
    correct_answer: Literal["A", "B", "C", "D", "E"]
```

---

## Güvenlik Kuralları

### Rate Limiting
| Endpoint | Limit | Gerekçe |
|----------|-------|---------|
| /auth/login | 5/dakika | Brute force önleme |
| Genel API | 100/dakika | Normal kullanım |
| AI işlemleri | 10/dakika | Maliyet kontrolü |

### SQL Injection Önleme
```python
# YANLIŞ
query = f"SELECT * FROM users WHERE email = '{email}'"

# DOĞRU
from sqlalchemy import text
result = session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)

# EN İYİ - ORM
user = session.query(User).filter(User.email == email).first()
```

---

## Performans Hedefleri

| Metrik | Hedef | Kritik |
|--------|-------|--------|
| p50 response | < 100ms | < 200ms |
| p95 response | < 300ms | < 500ms |
| p99 response | < 500ms | < 1000ms |
| Error rate | < 0.1% | < 1% |
