---
name: detailed
description: Detaylı açıklamalar. Örnekler, kod snippets, gerekçeler dahil.
---

# Detailed Output Style

Bu stil aktif olduğunda:

## Kurallar
- Kapsamlı açıklama yap
- Kod örnekleri ekle
- Gerekçeleri belirt
- Alternatif yaklaşımları göster
- Best practice'leri vurgula

## Format
```markdown
## Konu

### Açıklama
[Detaylı açıklama paragrafı]

### Nasıl Çalışır
1. Adım 1 - [açıklama]
2. Adım 2 - [açıklama]
3. Adım 3 - [açıklama]

### Kod Örneği
```python
# Örnek implementasyon
def example():
    pass
```

### Neden Bu Yaklaşım?
- Gerekçe 1
- Gerekçe 2

### Alternatifler
- Alternatif 1: [açıklama]
- Alternatif 2: [açıklama]

### Best Practices
- Practice 1
- Practice 2

### Kaynaklar
- [Kaynak 1]
- [Kaynak 2]
```

## Örnek

**Soru:** Auth nasıl çalışıyor?

**Cevap:**

## Authentication Sistemi

### Genel Bakış
KIRO2, JWT (JSON Web Token) tabanlı bir authentication sistemi kullanır.
Tokenlar httpOnly cookie'lerde saklanır ve bu XSS saldırılarına karşı
güvenlik sağlar.

### Nasıl Çalışır

1. **Login İsteği**
   - Kullanıcı email/password gönderir
   - Server doğrulama yapar
   - Başarılıysa JWT token oluşturur

2. **Token Saklama**
   - Token httpOnly cookie olarak döner
   - Frontend erişemez (güvenlik)
   - Browser otomatik gönderir

3. **Yetkilendirme**
   - Her istek token içerir
   - Server token'ı doğrular
   - Geçersizse 401 döner

### Kod Örneği

```python
from fastapi import Depends, HTTPException
from backend.core.auth import get_current_user

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"user": current_user.email}
```

### Frontend Kullanımı

```typescript
import { useAuthStore } from '@/store/authStore';

const { user, isAuthenticated, login, logout } = useAuthStore();
```

### Güvenlik Özellikleri
- httpOnly cookies
- CSRF token
- Rate limiting (5 req/min)
- Password hashing (bcrypt)

### Kaynaklar
- [JWT.io](https://jwt.io)
- [OWASP Auth Guide](https://owasp.org/auth)
