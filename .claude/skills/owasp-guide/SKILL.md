---
name: owasp-guide
description: OWASP güvenlik standartları rehberi
user-invocable: false
allowed-tools:
  - Read
---

# OWASP Security Guide Skill

Bu skill, OWASP güvenlik standartlarına uygun kod yazımı için referans sağlar.
Code Review ve Security Checklist skill'leri tarafından kullanılır.

## Injection Prevention

### SQL Injection

**Kural:** ASLA string concatenation ile SQL sorgusu oluşturma.

```python
# ✅ DOĞRU - Parameterized Query (SQLAlchemy)
from sqlalchemy import text

query = text("SELECT * FROM users WHERE email = :email")
result = db.execute(query, {"email": user_email})

# ✅ DOĞRU - ORM kullanımı
user = session.query(User).filter(User.email == user_email).first()

# ❌ YANLIŞ - String interpolation
query = f"SELECT * FROM users WHERE email = '{user_email}'"  # TEHLIKE!
```

### Command Injection

**Kural:** Kullanıcı girdisini shell komutlarına ASLA doğrudan geçirme.

```python
# ✅ DOĞRU - subprocess with list
import subprocess
subprocess.run(["ls", "-la", directory], check=True)

# ✅ DOĞRU - shlex.quote
import shlex
safe_input = shlex.quote(user_input)

# ❌ YANLIŞ - shell=True ile kullanıcı girdisi
subprocess.run(f"ls {user_input}", shell=True)  # TEHLIKE!
```

### XSS (Cross-Site Scripting)

**Kural:** Kullanıcı girdisini HTML'e yazmadan önce MUTLAKA escape et.

```typescript
// ✅ DOĞRU - React otomatik escape eder
<div>{userInput}</div>

// ✅ DOĞRU - Manuel escape
import { escape } from 'lodash';
<div>{escape(userInput)}</div>

// ❌ YANLIŞ - dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{__html: userInput}} />  // TEHLIKE!
```

## Authentication Best Practices

### Password Hashing

```python
# ✅ DOĞRU - bcrypt veya argon2
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ❌ YANLIŞ - MD5, SHA1, SHA256 (salt'sız)
import hashlib
hashlib.md5(password.encode()).hexdigest()  # ZAYIF!
```

### JWT Token Management

```python
# ✅ DOĞRU - Kısa ömürlü access token
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 dakika
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 gün

def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# ❌ YANLIŞ - Çok uzun token ömrü
ACCESS_TOKEN_EXPIRE_DAYS = 365  # 1 yıl - ÇOK UZUN!
```

### Session Management

```python
# ✅ DOĞRU - Güvenli session cookie
response.set_cookie(
    key="session_id",
    value=session_id,
    httponly=True,      # JavaScript erişemez
    secure=True,        # Sadece HTTPS
    samesite="strict",  # CSRF koruması
    max_age=3600        # 1 saat
)
```

## Data Protection

### Encryption at Rest

```python
# ✅ DOĞRU - Fernet symmetric encryption
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data: str, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_sensitive_data(encrypted: bytes, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted).decode()
```

### Key Management

```python
# ✅ DOĞRU - Environment variable'dan al
import os
SECRET_KEY = os.environ["SECRET_KEY"]

# ❌ YANLIŞ - Hardcoded key
SECRET_KEY = "my-super-secret-key-12345"  # ASLA!
```

## Input Validation

### Pydantic Validation

```python
from pydantic import BaseModel, EmailStr, constr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=128)
    username: constr(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')

    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

### File Upload Validation

```python
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_file(file: UploadFile) -> bool:
    # Extension check
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension not allowed: {ext}")

    # Size check
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size} bytes")

    # Magic bytes check (optional)
    return True
```

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Login - strict
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    ...

# API - moderate
@router.get("/api/questions")
@limiter.limit("100/minute")
async def get_questions(request: Request):
    ...
```

## Security Headers

```python
from fastapi.middleware.cors import CORSMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kiro2.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

## Logging Best Practices

### Ne Loglanmalı

```python
# ✅ DOĞRU - Güvenlik olayları
logger.warning(f"Failed login: user_id={user_id}, ip={ip}, reason={reason}")
logger.info(f"Password changed: user_id={user_id}")
logger.error(f"Unauthorized access attempt: endpoint={path}, user_id={user_id}")
```

### Ne Loglanmamalı

```python
# ❌ YANLIŞ - Hassas veriler
logger.info(f"User {user_id} logged in with password: {password}")  # YASAK!
logger.debug(f"API key used: {api_key}")  # YASAK!
logger.info(f"Credit card: {card_number}")  # YASAK!
```

## KIRO2 Spesifik Kurallar

### Öğrenci Verileri

```python
# Veri maskeleme
def mask_student_data(student: dict) -> dict:
    return {
        "id": student["id"],
        "name": student["name"][:1] + "***",
        "email": mask_email(student["email"]),
        # Hassas alanlar dahil edilmez
    }
```

### YKS Soru Erişimi

```python
# Rate limiting
@limiter.limit("10/minute")
async def get_question(question_id: UUID):
    # Erişim logu
    logger.info(f"Question accessed: id={question_id}, user={user_id}")
    ...
```

## Referanslar

- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [KVKK Rehberi](https://kvkk.gov.tr/)
