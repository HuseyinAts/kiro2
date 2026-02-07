---
name: security-checklist
description: OWASP tabanlı güvenlik kontrol listesi
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Security Checklist Skill

Bu skill, kod incelemesi sırasında OWASP tabanlı güvenlik kontrollerini uygular.
Code Review skill'i tarafından otomatik olarak yüklenir.

## OWASP Top 10 (2021) Kontrol Listesi

### A01:2021 - Broken Access Control
- [ ] Her endpoint'te authentication kontrolü var mı?
- [ ] Role-based access control (RBAC) uygulanmış mı?
- [ ] Horizontal privilege escalation koruması var mı?
- [ ] Vertical privilege escalation koruması var mı?
- [ ] CORS policy doğru yapılandırılmış mı?

**Kontrol Pattern'leri:**
```python
# DOĞRU
@router.get("/admin/users")
async def get_users(current_user: User = Depends(get_admin_user)):
    ...

# YANLIŞ - Authentication yok
@router.get("/admin/users")
async def get_users():
    ...
```

### A02:2021 - Cryptographic Failures
- [ ] Hassas veriler şifreleniyor mu (at rest)?
- [ ] HTTPS kullanılıyor mu (in transit)?
- [ ] Güncel şifreleme algoritmaları kullanılıyor mu?
- [ ] Şifreleme anahtarları güvenli saklanıyor mu?
- [ ] Password hashing için bcrypt/argon2 kullanılıyor mu?

**Kontrol Pattern'leri:**
```python
# DOĞRU
from passlib.hash import bcrypt
hashed = bcrypt.hash(password)

# YANLIŞ - MD5/SHA1 zayıf
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()
```

### A03:2021 - Injection
- [ ] SQL Injection koruması var mı?
- [ ] NoSQL Injection koruması var mı?
- [ ] Command Injection koruması var mı?
- [ ] LDAP Injection koruması var mı?
- [ ] XPath Injection koruması var mı?

**Kontrol Pattern'leri:**
```python
# DOĞRU - Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# YANLIŞ - String concatenation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### A04:2021 - Insecure Design
- [ ] Threat modeling yapılmış mı?
- [ ] Security requirements tanımlanmış mı?
- [ ] Rate limiting uygulanmış mı?
- [ ] Input validation kapsamlı mı?

### A05:2021 - Security Misconfiguration
- [ ] Debug mode kapalı mı (production)?
- [ ] Default credentials değiştirilmiş mi?
- [ ] Error mesajları detay içermiyor mu?
- [ ] Security headers doğru yapılandırılmış mı?

**Kontrol Pattern'leri:**
```python
# DOĞRU - Production
DEBUG = False
ALLOWED_HOSTS = ["example.com"]

# YANLIŞ - Production'da debug açık
DEBUG = True
```

### A06:2021 - Vulnerable and Outdated Components
- [ ] Bağımlılıklar güncel mi?
- [ ] Bilinen güvenlik açıkları taranmış mı?
- [ ] Kullanılmayan bağımlılıklar kaldırılmış mı?

### A07:2021 - Identification and Authentication Failures
- [ ] Strong password policy var mı?
- [ ] Multi-factor authentication destekleniyor mu?
- [ ] Session yönetimi güvenli mi?
- [ ] Brute force koruması var mı?

### A08:2021 - Software and Data Integrity Failures
- [ ] CI/CD pipeline güvenli mi?
- [ ] Kod imzalama kullanılıyor mu?
- [ ] Deserialization güvenli mi?

### A09:2021 - Security Logging and Monitoring Failures
- [ ] Güvenlik olayları loglanıyor mu?
- [ ] Log'lar yeterli detay içeriyor mu?
- [ ] Alerting yapılandırılmış mı?

**Kontrol Pattern'leri:**
```python
# DOĞRU - Güvenlik olayını logla
logger.warning(f"Failed login attempt for user {user_id} from {ip}")

# YANLIŞ - Hassas veri loglama
logger.info(f"User logged in with password {password}")  # YASAK!
```

### A10:2021 - Server-Side Request Forgery (SSRF)
- [ ] URL validation yapılıyor mu?
- [ ] Whitelist yaklaşımı kullanılıyor mu?
- [ ] Internal network erişimi engelleniyor mu?

## KIRO2 Spesifik Kontroller

### Öğrenci Verileri (KVKK/GDPR)
- [ ] Öğrenci verileri şifreleniyor mu?
- [ ] Veri silme hakkı destekleniyor mu (right to erasure)?
- [ ] Veri taşıma hakkı destekleniyor mu (data portability)?
- [ ] Minimal veri toplama prensibi uygulanıyor mu?
- [ ] Consent mekanizması var mı?

### YKS Soru Güvenliği
- [ ] Sorular şifreli saklanıyor mu?
- [ ] Soru ID'leri tahmin edilemez mi (UUID)?
- [ ] Soru erişim logları tutuluyor mu?
- [ ] Rate limiting aktif mi (soru çekme)?

### API Güvenliği
- [ ] JWT token süresi uygun mu (<24 saat)?
- [ ] Refresh token mekanizması güvenli mi?
- [ ] API key rotation planı var mı?

## Otomatik Tarama Komutları

```bash
# Bandit - Python security linter
bandit -r backend/ -f json -o bandit-report.json

# Safety - Dependency vulnerability check
safety check --json > safety-report.json

# Semgrep - Pattern-based security scanning
semgrep --config=auto backend/
```

## Sonuç Formatı

Security checklist kontrolü sonucunda şu format kullanılır:

```json
{
  "passed": true,
  "checks": {
    "owasp_a01": {"status": "pass", "findings": []},
    "owasp_a03": {"status": "warn", "findings": ["SQL query in line 42"]},
    "kiro2_kvkk": {"status": "pass", "findings": []}
  },
  "total_findings": 1,
  "severity": "low"
}
```
