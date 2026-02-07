# Requirements Document - Security Validation Hooks Sistemi

## Introduction

Bu spec, Daisy Stanton'ın hooks system expertise'ine göre tasarlanmış güvenlik doğrulama hook'larını tanımlar. PreToolUse hook'ları ile SQL injection, secret exposure, XSS gibi güvenlik açıkları otomatik tespit edilir. OWASP Top 10 standartlarına uygun olarak %95 güvenlik açığı önlenir.

## Glossary

- **SQL Injection**: Veritabanı sorgularına zararlı kod enjeksiyonu
- **Secret Exposure**: API key, password gibi hassas bilgilerin kodda bulunması
- **XSS**: Cross-Site Scripting saldırısı
- **CSRF**: Cross-Site Request Forgery
- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability checker
- **OWASP**: Open Web Application Security Project

## Requirements

### Requirement 1: SQL Injection Detection Hook

**User Story:** As a security engineer, I want SQL injection açıklarının otomatik tespit edilmesini, so that database güvenliği sağlansın.

#### Acceptance Criteria

1. **REQ-1.1** WHEN SQL query yazıldığında, THE PreToolUse Hook SHALL string concatenation ile query oluşturulup oluşturulmadığını kontrol eder
2. **REQ-1.2** WHEN raw SQL tespit edildiğinde, THE Hook SHALL f-string veya % formatting kullanımını engeller
3. **REQ-1.3** WHEN parameterized query kontrol edildiğinde, THE Hook SHALL SQLAlchemy ORM veya prepared statement kullanımını zorunlu kılar
4. **REQ-1.4** WHEN user input SQL'e geçirildiğinde, THE Hook SHALL input validation eksikliğini tespit eder
5. **REQ-1.5** WHEN SQL injection riski tespit edildiğinde, THE Hook SHALL exit code 2 döner ve güvenli alternatif önerir
6. **REQ-1.6** WHEN ORM kullanıldığında, THE Hook SHALL raw() veya execute() kullanımını uyarı ile işaretler

---

### Requirement 2: Secret Detection Hook

**User Story:** As a DevOps engineer, I want kodda hardcoded secret'ların tespit edilmesini, so that credential leak önlensin.

#### Acceptance Criteria

1. **REQ-2.1** WHEN kod yazıldığında, THE PreToolUse Hook SHALL regex pattern ile API key, password, token tarar
2. **REQ-2.2** WHEN secret pattern tespit edildiğinde, THE Hook SHALL secret tipini kategorize eder (AWS key, JWT token, database password)
3. **REQ-2.3** WHEN environment variable kullanımı kontrol edildiğinde, THE Hook SHALL os.getenv() veya pydantic Settings kullanımını önerir
4. **REQ-2.4** WHEN .env dosyası commit edilmeye çalışıldığında, THE Hook SHALL commit'i engeller
5. **REQ-2.5** WHEN secret tespit edildiğinde, THE Hook SHALL exit code 2 döner ve "Use environment variables" mesajı verir
6. **REQ-2.6** WHEN false positive olduğunda, THE Hook SHALL # nosec comment ile bypass'a izin verir

---

### Requirement 3: XSS Prevention Hook

**User Story:** As a frontend developer, I want XSS açıklarının tespit edilmesini, so that kullanıcı güvenliği sağlansın.

#### Acceptance Criteria

1. **REQ-3.1** WHEN HTML render edildiğinde, THE Hook SHALL user input'un escape edilip edilmediğini kontrol eder
2. **REQ-3.2** WHEN innerHTML kullanıldığında, THE Hook SHALL XSS riski uyarısı verir
3. **REQ-3.3** WHEN template engine kullanıldığında, THE Hook SHALL auto-escaping aktif olduğunu doğrular
4. **REQ-3.4** WHEN dangerouslySetInnerHTML (React) tespit edildiğinde, THE Hook SHALL kritik uyarı verir
5. **REQ-3.5** WHEN sanitization library kontrol edildiğinde, THE Hook SHALL DOMPurify veya bleach kullanımını önerir
6. **REQ-3.6** WHEN XSS riski yüksek olduğunda, THE Hook SHALL exit code 2 döner

---

### Requirement 4: Dependency Vulnerability Scanning

**User Story:** As a security engineer, I want bağımlılıklardaki güvenlik açıklarının tespit edilmesini, so that vulnerable library kullanılmasın.

#### Acceptance Criteria

1. **REQ-4.1** WHEN requirements.txt değiştiğinde, THE PostToolUse Hook SHALL safety check komutunu çalıştırır
2. **REQ-4.2** WHEN vulnerability bulunduğunda, THE Hook SHALL CVE numarası, severity (critical, high, medium, low), ve affected version gösterir
3. **REQ-4.3** WHEN critical vulnerability tespit edildiğinde, THE Hook SHALL exit code 2 döner ve güncelleme önerir
4. **REQ-4.4** WHEN patch version mevcut olduğunda, THE Hook SHALL otomatik güncelleme önerir
5. **REQ-4.5** WHEN vulnerability database güncellendiğinde, THE Hook SHALL günlük olarak database'i yeniler
6. **REQ-4.6** WHEN false positive olduğunda, THE Hook SHALL .safety-policy.yml ile ignore pattern destekler

---

### Requirement 5: Bandit Security Linting

**User Story:** As a developer, I want Python kodundaki güvenlik açıklarının otomatik tespit edilmesini, so that secure code yazayım.

#### Acceptance Criteria

1. **REQ-5.1** WHEN Python dosyası yazıldığında, THE PostToolUse Hook SHALL bandit -r . komutunu çalıştırır
2. **REQ-5.2** WHEN güvenlik açığı bulunduğunda, THE Hook SHALL issue ID (B101, B201, vb.), severity, ve confidence gösterir
3. **REQ-5.3** WHEN high severity issue tespit edildiğinde, THE Hook SHALL exit code 2 döner
4. **REQ-5.4** WHEN insecure function kullanıldığında, THE Hook SHALL güvenli alternatif önerir (örn: pickle → json)
5. **REQ-5.5** WHEN hardcoded password tespit edildiğinde, THE Hook SHALL B105 issue verir
6. **REQ-5.6** WHEN baseline oluşturulduğunda, THE Hook SHALL bandit -f json -o baseline.json ile baseline kaydeder

---

### Requirement 6: CSRF Protection Validation

**User Story:** As a backend developer, I want CSRF korumasının aktif olduğunu bilmek, so that state-changing request'ler güvenli olsun.

#### Acceptance Criteria

1. **REQ-6.1** WHEN POST/PUT/DELETE endpoint yazıldığında, THE Hook SHALL CSRF token validation kontrol eder
2. **REQ-6.2** WHEN FastAPI endpoint'inde CSRF eksik olduğunda, THE Hook SHALL uyarı verir
3. **REQ-6.3** WHEN form submission yapıldığında, THE Hook SHALL CSRF token varlığını doğrular
4. **REQ-6.4** WHEN SameSite cookie attribute kontrol edildiğinde, THE Hook SHALL SameSite=Lax veya Strict olmasını bekler
5. **REQ-6.5** WHEN CORS configuration kontrol edildiğinde, THE Hook SHALL wildcard origin (*) kullanımını engeller
6. **REQ-6.6** WHEN API endpoint public olduğunda, THE Hook SHALL explicit @public decorator bekler

---

### Requirement 7: Authentication ve Authorization Check

**User Story:** As a security engineer, I want authentication/authorization eksikliklerinin tespit edilmesini, so that unauthorized access önlensin.

#### Acceptance Criteria

1. **REQ-7.1** WHEN API endpoint yazıldığında, THE Hook SHALL authentication decorator varlığını kontrol eder
2. **REQ-7.2** WHEN protected endpoint tespit edildiğinde, THE Hook SHALL @requires_auth veya Depends(get_current_user) bekler
3. **REQ-7.3** WHEN role-based access kontrol edildiğinde, THE Hook SHALL @requires_role decorator varlığını doğrular
4. **REQ-7.4** WHEN JWT token kullanıldığında, THE Hook SHALL token expiration ve signature validation kontrol eder
5. **REQ-7.5** WHEN password hashing kontrol edildiğinde, THE Hook SHALL bcrypt veya argon2 kullanımını bekler
6. **REQ-7.6** WHEN authentication eksik olduğunda, THE Hook SHALL exit code 2 döner ve decorator eklenmesini önerir

---

### Requirement 8: Security Headers Validation

**User Story:** As a DevOps engineer, I want HTTP security header'larının doğru yapılandırıldığını bilmek, so that browser-level güvenlik sağlansın.

#### Acceptance Criteria

1. **REQ-8.1** WHEN FastAPI middleware yapılandırıldığında, THE Hook SHALL security header'ları kontrol eder
2. **REQ-8.2** WHEN X-Content-Type-Options kontrol edildiğinde, THE Hook SHALL "nosniff" değerini bekler
3. **REQ-8.3** WHEN X-Frame-Options kontrol edildiğinde, THE Hook SHALL "DENY" veya "SAMEORIGIN" bekler
4. **REQ-8.4** WHEN Content-Security-Policy kontrol edildiğinde, THE Hook SHALL CSP header varlığını doğrular
5. **REQ-8.5** WHEN Strict-Transport-Security kontrol edildiğinde, THE Hook SHALL HSTS header'ı bekler
6. **REQ-8.6** WHEN security header eksik olduğunda, THE Hook SHALL middleware configuration örneği gösterir

---

## Bağımlılıklar

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **SQLAlchemy**: ORM (SQL injection prevention)
- **Pydantic**: Input validation
- **python-dotenv**: Environment variable management
- **cryptography**: Secure hashing
- **pre-commit**: Git hook yönetimi

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 1 hafta
**Beklenen Güvenlik Açığı Azalması:** %95

## Security Validation Flow

```
1. Developer Kod Yazıyor
   ↓
2. PreToolUse Hook Tetiklendi (Bash/SQL Command Öncesi)
   ↓
3. Security Checks (Paralel)
   ├─ SQL Injection Detection
   │  ├─ String Concatenation Check
   │  ├─ Parameterized Query Validation
   │  └─ Exit Code: 0 (Safe) / 2 (Unsafe)
   ├─ Secret Detection
   │  ├─ Regex Pattern Matching
   │  ├─ API Key / Password Scan
   │  └─ Exit Code: 0 (Clean) / 2 (Secret Found)
   ├─ XSS Prevention
   │  ├─ HTML Escape Check
   │  ├─ innerHTML Detection
   │  └─ Exit Code: 0 (Safe) / 2 (XSS Risk)
   └─ CSRF Protection
      ├─ Token Validation Check
      ├─ SameSite Cookie Check
      └─ Exit Code: 0 (Protected) / 2 (Vulnerable)
   ↓
4. PostToolUse Hook Tetiklendi (Kod Yazıldıktan Sonra)
   ↓
5. Additional Security Checks
   ├─ Bandit Security Linting
   │  ├─ bandit -r .
   │  ├─ High Severity Issues
   │  └─ Exit Code: 0 (Clean) / 2 (Issues Found)
   ├─ Dependency Vulnerability Scan
   │  ├─ safety check
   │  ├─ CVE Database Lookup
   │  └─ Exit Code: 0 (Safe) / 2 (Vulnerable)
   ├─ Authentication Check
   │  ├─ Decorator Validation
   │  ├─ JWT Token Check
   │  └─ Exit Code: 0 (Secured) / 2 (Unsecured)
   └─ Security Headers Validation
      ├─ Middleware Configuration
      ├─ HSTS, CSP, X-Frame-Options
      └─ Exit Code: 0 (Configured) / 2 (Missing)
   ↓
6. Result Aggregation
   ├─ All Checks Passed? → Exit 0 ✓
   └─ Any Check Failed? → Exit 2 ✗
   ↓
7. Feedback to Claude (if Exit 2)
   ├─ Security Issue Details
   ├─ Severity Level
   ├─ Affected Code Location
   └─ Remediation Suggestions
```

## Success Metrics

1. **SQL Injection Prevention:** %100
2. **Secret Exposure Prevention:** %100
3. **XSS Prevention:** >= %95
4. **Dependency Vulnerability Detection:** >= %98
5. **OWASP Top 10 Coverage:** %100

## Bandit Configuration (.bandit)

```yaml
exclude_dirs:
  - /tests/
  - /venv/
  - /.venv/

tests:
  - B201  # flask_debug_true
  - B301  # pickle
  - B302  # marshal
  - B303  # md5
  - B304  # insecure_cipher
  - B305  # insecure_cipher_mode
  - B306  # mktemp_q
  - B307  # eval
  - B308  # mark_safe
  - B309  # httpsconnection
  - B310  # urllib_urlopen
  - B311  # random
  - B312  # telnetlib
  - B313  # xml_bad_cElementTree
  - B314  # xml_bad_ElementTree
  - B315  # xml_bad_expatreader
  - B316  # xml_bad_expatbuilder
  - B317  # xml_bad_sax
  - B318  # xml_bad_minidom
  - B319  # xml_bad_pulldom
  - B320  # xml_bad_etree
  - B321  # ftplib
  - B323  # unverified_context
  - B324  # hashlib_new_insecure_functions
  - B325  # tempnam
  - B401  # import_telnetlib
  - B402  # import_ftplib
  - B403  # import_pickle
  - B404  # import_subprocess
  - B405  # import_xml_etree
  - B406  # import_xml_sax
  - B407  # import_xml_expat
  - B408  # import_xml_minidom
  - B409  # import_xml_pulldom
  - B410  # import_lxml
  - B411  # import_xmlrpclib
  - B412  # import_httpoxy
  - B413  # import_pycrypto
  - B501  # request_with_no_cert_validation
  - B502  # ssl_with_bad_version
  - B503  # ssl_with_bad_defaults
  - B504  # ssl_with_no_version
  - B505  # weak_cryptographic_key
  - B506  # yaml_load
  - B507  # ssh_no_host_key_verification
  - B601  # paramiko_calls
  - B602  # shell_injection
  - B603  # subprocess_without_shell_equals_true
  - B604  # any_other_function_with_shell_equals_true
  - B605  # start_process_with_a_shell
  - B606  # start_process_with_no_shell
  - B607  # start_process_with_partial_path
  - B608  # hardcoded_sql_expressions
  - B609  # linux_commands_wildcard_injection
  - B610  # django_extra_used
  - B611  # django_rawsql_used
  - B701  # jinja2_autoescape_false
  - B702  # use_of_mako_templates
  - B703  # django_mark_safe
```

