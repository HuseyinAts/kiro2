---
name: security-rules
description: KIRO2 guvenlik kurallari ve kisilamalar
trigger: always
priority: critical
paths:
  - "backend/**/*.py"
  - "frontend/src/**/*.ts"
  - "frontend/src/**/*.tsx"
  - "**/.env.example"
  - "docker/**"
  - "docker-compose*.yml"
---

# Security Rules - KIRO2 Standards

## KRITIK GUVENLIK KURALLARI

### YASAK KOMUTLAR (Exit Code 2 ile Engellenir)

```bash
# Dosya sistemi yikimi
rm -rf /
rm -rf *
rm -rf .

# Veritabani yikimi
DROP TABLE
DROP DATABASE
TRUNCATE TABLE
DELETE FROM table_name  # WHERE olmadan

# Git tehlikeli islemler
git push --force origin main
git push --force origin master
git reset --hard HEAD~

# Secrets aciklama
cat .env
echo $API_KEY
echo $PASSWORD
```

### KORUNAN YOLLAR

Bu yollara erisim ENGELLENIR:

- `/etc/`, `/usr/`, `/bin/`, `/sbin/`
- `C:\Windows`, `C:\Program Files`
- `~/.ssh/`, `~/.aws/`, `~/.config/`
- `.env` dosyalari (`.env.example` haric)

## SECRETS YONETIMI

### ASLA YAPMA

- NEVER hardcode API keys, passwords, tokens
- NEVER commit .env files
- NEVER log sensitive data
- NEVER expose secrets in error messages

### DOGRU KULLANIM

```python
# DOGRU - Environment variable
import os
API_KEY = os.environ.get("API_KEY")

# YANLIS - Hardcoded
API_KEY = "<BURAYA-DUZ-METIN-ANAHTAR>"  # YASAK!
```

## INPUT VALIDATION

### SQL Injection Onleme

```python
# DOGRU - Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# YANLIS - String concatenation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # TEHLIKE!
```

### XSS Onleme

```typescript
// DOGRU - Escaped output
<div>{escapeHtml(userInput)}</div>

// YANLIS - Direct HTML
<div dangerouslySetInnerHTML={{__html: userInput}} />  // TEHLIKE!
```

## AUTHENTICATION & AUTHORIZATION

### JWT Token Kurallari

- Token suresi: maksimum 24 saat
- Refresh token: 7 gun
- Token'lar httpOnly cookie'de saklanmali
- HTTPS zorunlu (production)

### RBAC (Role-Based Access Control)

```python
# Her endpoint'te rol kontrolu
@router.get("/admin/users")
async def get_users(current_user: User = Depends(get_admin_user)):
    ...
```

## RATE LIMITING

| Endpoint Tipi | Limit |
|---------------|-------|
| Login | 5/dakika |
| API Genel | 100/dakika |
| File Upload | 10/dakika |
| Admin | 50/dakika |

## LOGGING KURALLARI

### ASLA LOGLAMA

- Passwords
- API keys
- Credit card numbers
- Personal identification numbers
- Full JWT tokens

### GUVENLI LOGLAMA

```python
# DOGRU
logger.info(f"User {user_id} logged in")

# YANLIS
logger.info(f"User logged in with password: {password}")  # YASAK!
```

## KIRO2 SPESIFIK GUVENLIK

### Ogrenci Verileri (KVKK/GDPR)

- Ogrenci verileri sifrelenmeli
- Veri silme hakki desteklenmeli
- Veri tasima hakki desteklenmeli
- Minimal veri toplama prensibi

### YKS Soru Guvenligi

- Sorular sifrelenerek saklanmali
- Soru ID'leri tahmin edilemez olmali (UUID)
- Soru erisim loglari tutulmali

## GUVENLIK KONTROL LISTESI

Her PR oncesi kontrol et:

- [ ] Hardcoded secrets yok mu?
- [ ] SQL injection riski yok mu?
- [ ] Input validation yapildi mi?
- [ ] CORS dogru yapilandi mi?
- [ ] Rate limiting aktif mi?
- [ ] Sensitive data loglanmiyor mu?
- [ ] Authentication/Authorization var mi?
