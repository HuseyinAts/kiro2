---
name: code-review
description: PR ve kod kalitesi incelemesi yapar. OWASP güvenlik kontrollerini, Boris Cherny standartlarını ve KIRO2 coding conventions'ı uygular. Security, performance ve maintainability odaklı.
context: fork
agent: code-reviewer
model: opus
allowed-tools: Read, Grep, Glob, Bash
skills: security-checklist
---

# Code Review: $ARGUMENTS

Bu skill, belirtilen dosya veya PR'ı kapsamlı olarak inceler.

## İnceleme Protokolü

### 1. Güvenlik Kontrolü (OWASP Top 10)

| Kontrol | Açıklama | Öncelik |
|---------|----------|---------|
| SQL Injection | Parameterized query kullanımı | P0 |
| XSS | Input sanitization, output encoding | P0 |
| CSRF | Token validation | P1 |
| Auth Bypass | Authentication/Authorization | P0 |
| Sensitive Data | Hardcoded secrets, logging | P0 |
| Security Misconfig | Default credentials, debug mode | P1 |
| Injection | Command injection, path traversal | P0 |
| Insecure Deserialization | Pickle, eval kullanımı | P1 |
| Vulnerable Components | Outdated dependencies | P2 |
| Insufficient Logging | Audit trail eksikliği | P2 |

### 2. Boris Cherny Standards

```
✅ KONTROL EDİLECEKLER:
- Type hints ZORUNLU (Python/TypeScript)
- Async I/O kullanımı (blocking calls)
- Pydantic validation
- Turkish UTF-8 encoding
- Exit code kullanımı (0, 2, diğer)

❌ YASAK PATTERN'LER:
- assert True / ASSERT_TRUE(true)
- echo Success / print("Success")
- pass # placeholder
- # pragma: no cover (gerekçesiz)
- return None # stub
```

### 3. KIRO2 Coding Conventions

```python
# DOGRU
from backend.core.config import settings
from frontend.src.store.authStore import useAuthStore  # store DEGIL stores!

# YANLIS
from backend.core.config import Settings  # lowercase 'settings'
from frontend.src.stores.authStore import useAuthStore  # stores YANLIS!
```

### 4. Performans Kontrolü

- [ ] N+1 query problemi
- [ ] Unnecessary database calls
- [ ] Missing indexes
- [ ] Large payload responses
- [ ] Missing caching
- [ ] Blocking I/O in async context

### 5. Test Coverage

- [ ] Unit test var mı?
- [ ] Edge case'ler kapsanıyor mu?
- [ ] Mock kullanımı uygun mu?
- [ ] Assertion'lar anlamlı mı?

### 6. Maintainability

- [ ] Fonksiyon boyutu (max 50 satır önerilir)
- [ ] Cyclomatic complexity
- [ ] Code duplication
- [ ] Clear naming
- [ ] Docstring/comment kalitesi

## Çıktı Formatı

```markdown
## Code Review: $ARGUMENTS

### Özet
- Dosya sayısı: X
- Toplam satır: Y
- Sorun sayısı: Z (P0: a, P1: b, P2: c)

### Güvenlik Sorunları (P0)
| Dosya | Satır | Sorun | Öneri |
|-------|-------|-------|-------|
| ... | ... | ... | ... |

### Kod Kalitesi Sorunları (P1)
...

### İyileştirme Önerileri (P2)
...

### Onay Durumu
- [ ] Güvenlik: ✅/❌
- [ ] Performans: ✅/❌
- [ ] Test Coverage: ✅/❌
- [ ] Code Style: ✅/❌

### Sonuç
🟢 ONAY / 🟡 KÜÇÜK DÜZELTME / 🔴 MAJOR REVIZYON
```

## Komut Örnekleri

```bash
# Tek dosya inceleme
/code-review backend/api/auth.py

# Dizin inceleme
/code-review backend/services/

# PR inceleme (PR numarası)
/code-review PR#123

# Son commit inceleme
/code-review HEAD
```

## Otomatik Checks

Review başlamadan önce şunlar otomatik çalıştırılır:

```bash
# Python
ruff check $FILES --select=E,F,W,S,B
mypy --ignore-missing-imports $FILES

# TypeScript
npx tsc --noEmit
npx eslint $FILES
```

## KIRO2 Spesifik Kontroller

### IRT Parametreleri
```python
# Geçerli aralıklar
difficulty: [-4.0, 4.0]
discrimination: [0.2, 4.0]
guessing: [0.0, 0.35]
upper_asymptote: [0.0, 1.0]
```

### Database Port
```python
# DOGRU
DATABASE_PORT = 5434

# YANLIS
DATABASE_PORT = 5432  # KIRO2'de 5434 kullanılıyor!
```

### Auth Store
```typescript
// DOGRU - store dizini
import { useAuthStore } from '@/store/authStore';

// YANLIS - stores dizini
import { useAuthStore } from '@/stores/authStore';
```

## Notlar

- Bu skill Opus model kullanır (kritik kararlar)
- İzole context'te çalışır
- Güvenlik sorunları P0 öncelikli
- Exit code 2 döndürülürse: BLOCKING ERROR
