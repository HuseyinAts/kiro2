# BÖLÜM 8: Subagent Tanımlama Formatı

## 8.1 Dosya Yapısı

### Konum

Custom subagent tanımları `.claude/agents/` dizininde bulunur.

```
.claude/
└── agents/
    ├── security-reviewer.md
    ├── test-runner.md
    ├── content-validator.md
    ├── matematik-generator.md
    └── ...
```

### Dosya Adlandırma

| Özellik | Kural |
|---------|-------|
| Uzantı | `.md` (Markdown) |
| İsimlendirme | `kebab-case` (küçük harf, tire ile ayrılmış) |
| Uzunluk | Max 50 karakter |
| Karakter seti | `a-z`, `0-9`, `-` |

**Doğru örnekler:**
- `security-reviewer.md`
- `test-runner.md`
- `kiro2-content-validator.md`

**Yanlış örnekler:**
- `SecurityReviewer.md` ❌ (büyük harf)
- `security_reviewer.md` ❌ (alt çizgi)
- `security reviewer.md` ❌ (boşluk)

---

## 8.2 YAML Frontmatter

### Genel Yapı

Her subagent dosyası YAML frontmatter ile başlar:

```yaml
---
name: agent-name
description: "Agent description for Claude to understand when to use"
model: sonnet
tools:
  - Read
  - Write
  - Bash
allowedTools:
  - Read
  - Glob
disallowedTools:
  - Bash
permissionMode: default
maxTurns: 50
timeout: 300
skills:
  - skill-name
---

# Markdown content starts here
```

### Alan Referansı

| Alan | Zorunlu | Tip | Varsayılan | Açıklama |
|------|---------|-----|------------|----------|
| `name` | ✅ | string | - | Benzersiz tanımlayıcı |
| `description` | ✅ | string | - | Claude'un ne zaman kullanacağını belirler |
| `model` | ❌ | enum | `inherit` | Kullanılacak model |
| `tools` | ❌ | array | parent'tan miras | Araç listesi |
| `allowedTools` | ❌ | array | - | Whitelist (sadece bunlar) |
| `disallowedTools` | ❌ | array | - | Blacklist (bunlar hariç) |
| `permissionMode` | ❌ | enum | `default` | İzin modu |
| `maxTurns` | ❌ | integer | 100 | Max iterasyon |
| `timeout` | ❌ | integer | 600 | Saniye cinsinden süre |
| `skills` | ❌ | array | - | Yüklenecek skill dosyaları |

---

## 8.3 Alan Detayları

### `name`

**Zorunlu:** Evet

**Format:** `kebab-case`, 3-50 karakter

**Kurallar:**
- Benzersiz olmalı (aynı isimde iki agent olamaz)
- Küçük harf ve tire
- Sayı ile başlayamaz

```yaml
# Doğru
name: security-reviewer
name: test-runner-v2
name: kiro2-content-validator

# Yanlış
name: SecurityReviewer      # büyük harf
name: security_reviewer     # alt çizgi
name: 2nd-reviewer          # sayı ile başlıyor
```

### `description`

**Zorunlu:** Evet

**Amaç:** Claude'un bu agent'ı ne zaman kullanacağını belirler.

**Best practices:**
1. Ne yaptığını açıkça belirt
2. Ne zaman kullanılacağını belirt
3. `PROACTIVELY` veya `MUST BE USED` ekle (otomatik tetikleme için)

```yaml
# Temel
description: "Reviews code for security issues"

# İyi
description: "Reviews code for security vulnerabilities including SQL injection, XSS, and CSRF. Use for any auth or payment code."

# Mükemmel (proaktif)
description: "Reviews code for security vulnerabilities. Use PROACTIVELY for any authentication, authorization, payment, or sensitive data handling code."
```

### `model`

**Zorunlu:** Hayır

**Değerler:**
| Değer | Açıklama | Kullanım |
|-------|----------|----------|
| `opus` | Claude Opus 4.5 | Derin analiz, karmaşık görevler |
| `sonnet` | Claude Sonnet 4.5 | Genel amaçlı, dengeli |
| `haiku` | Claude Haiku 4.5 | Hızlı, basit görevler |
| `inherit` | Parent'ın modeli | Varsayılan |

```yaml
# Güvenlik için en iyi model
model: opus

# Hızlı test çalıştırma
model: haiku

# Parent ile aynı
model: inherit
```

### `tools`

**Zorunlu:** Hayır

**Davranış:** Belirtilmezse parent'tan miras alır.

**Mevcut araçlar:**
| Araç | Kategori | Açıklama |
|------|----------|----------|
| `Read` | Dosya | Dosya içeriği okuma |
| `Write` | Dosya | Dosya yazma/oluşturma |
| `Edit` | Dosya | Dosya düzenleme |
| `MultiEdit` | Dosya | Çoklu düzenleme |
| `Glob` | Dosya | Pattern ile dosya bulma |
| `Grep` | Dosya | Metin arama |
| `LS` | Dosya | Dizin listeleme |
| `Bash` | Sistem | Komut çalıştırma |
| `Task` | Agent | Subagent oluşturma |
| `TodoRead` | Görev | Görev listesi okuma |
| `TodoWrite` | Görev | Görev listesi yazma |
| `WebFetch` | Web | URL'den içerik çekme |
| `WebSearch` | Web | Web araması |
| `NotebookRead` | Notebook | Jupyter notebook okuma |
| `NotebookEdit` | Notebook | Jupyter notebook düzenleme |

```yaml
# Sadece okuma araçları
tools:
  - Read
  - Glob
  - Grep
  - LS

# Tam erişim
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
```

### `allowedTools` vs `disallowedTools`

**Fark:**
- `allowedTools`: Whitelist - SADECE bunlara izin ver
- `disallowedTools`: Blacklist - Bunlar HARİÇ hepsine izin ver

**Öncelik:** `allowedTools` > `disallowedTools`

```yaml
# Whitelist yaklaşımı (daha güvenli)
allowedTools:
  - Read
  - Grep
# Sonuç: Sadece Read ve Grep kullanabilir

# Blacklist yaklaşımı
disallowedTools:
  - Bash
  - Write
# Sonuç: Bash ve Write hariç hepsini kullanabilir

# İkisi birden kullanılamaz (allowedTools kazanır)
allowedTools:
  - Read
disallowedTools:
  - Bash
# Sonuç: Sadece Read (allowedTools geçerli)
```

### `permissionMode`

**Zorunlu:** Hayır

**Değerler:**
| Mod | Açıklama | Kullanım |
|-----|----------|----------|
| `default` | Normal izin akışı | Genel amaçlı |
| `acceptEdits` | Düzenlemeleri otomatik kabul | Güvenilen görevler |
| `bypassPermissions` | Tüm izinleri atla | Tam otomasyon (dikkat!) |
| `plan` | Sadece planlama, değişiklik yok | Analiz, review |

```yaml
# Güvenli analiz
permissionMode: plan

# Otonom düzenleme
permissionMode: acceptEdits

# Tam otomasyon (sadece güvenilen agent'lar için)
permissionMode: bypassPermissions
```

**⚠️ Uyarı:** `bypassPermissions` sadece çok güvenilen, iyi test edilmiş agent'lar için kullanılmalı.

### `maxTurns`

**Zorunlu:** Hayır

**Varsayılan:** 100

**Amaç:** Sonsuz döngü koruması

```yaml
# Kısa görev
maxTurns: 20

# Orta görev
maxTurns: 50

# Uzun görev
maxTurns: 100

# Çok uzun görev (dikkat!)
maxTurns: 200
```

**Önerilen değerler:**
| Görev tipi | maxTurns |
|------------|----------|
| Basit review | 10-20 |
| Code fix | 20-50 |
| Refactoring | 50-100 |
| Large migration | 100-200 |

### `timeout`

**Zorunlu:** Hayır

**Varsayılan:** 600 (10 dakika)

**Birim:** Saniye

```yaml
# Hızlı görev (2 dakika)
timeout: 120

# Orta görev (5 dakika)
timeout: 300

# Uzun görev (15 dakika)
timeout: 900

# Çok uzun görev (30 dakika)
timeout: 1800
```

### `skills`

**Zorunlu:** Hayır

**Amaç:** Önceden tanımlanmış skill dosyalarını yükle

**Konum:** `.claude/skills/` dizini

```yaml
skills:
  - python-best-practices
  - security-checklist
  - testing-patterns
```

**Skill dosyası örneği (`.claude/skills/security-checklist.md`):**
```markdown
# Security Review Checklist

## Authentication
- [ ] Password hashing (bcrypt, argon2)
- [ ] Session management
- [ ] CSRF protection

## Authorization
- [ ] Role-based access control
- [ ] Resource ownership checks

## Data Validation
- [ ] Input sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention
```

---

## 8.4 PROACTIVELY Pattern

### Otomatik Delegasyon

`description` alanına `PROACTIVELY` veya `MUST BE USED` eklendiğinde, Claude ilgili durumları tespit ettiğinde otomatik olarak bu agent'ı çağırır.

### Tetikleyici İfadeler

| İfade | Davranış |
|-------|----------|
| `Use PROACTIVELY` | Güçlü tetikleme |
| `MUST BE USED` | Zorunlu tetikleme |
| `ALWAYS use` | Her zaman tetikleme |
| `Use for any` | Koşullu tetikleme |

### Örnekler

**Güvenlik review'ı (her auth kodu için):**
```yaml
description: "Security reviewer. Use PROACTIVELY for any authentication, authorization, or payment code."
```

**Test yazımı (her yeni fonksiyon için):**
```yaml
description: "Test writer. MUST BE USED after implementing any new function."
```

**Dokümantasyon (her API değişikliği için):**
```yaml
description: "Documentation updater. ALWAYS use when API endpoints change."
```

### Tetikleme Senaryoları

**Agent tanımı:**
```yaml
name: security-reviewer
description: "Use PROACTIVELY for authentication code changes"
```

**Senaryo 1 - Otomatik tetikleme:**
```
User: "Fix the login bug in auth/login.py"

Claude: (auth dosyası algılandı, PROACTIVELY tetiklendi)
"I'll fix the bug and have the security-reviewer check the changes."
[Task security-reviewer: Review auth/login.py changes]
```

**Senaryo 2 - Manuel tetikleme gerekmez:**
```
User: "Review auth module for security"

Claude: (zaten security context'i, doğrudan agent kullanılır)
[Task security-reviewer: Full security audit of auth/]
```

---

## 8.5 Markdown Body

### Yapı

YAML frontmatter'dan sonra Markdown içerik gelir. Bu içerik agent'ın "beyni"dir.

```markdown
---
[YAML frontmatter]
---

# Agent Title

## Role
[Agent'ın rolü ve amacı]

## Responsibilities
[Yapması gerekenler]

## Rules
### Must Do
[Zorunlu kurallar]

### Must Not Do
[Yasaklar]

## Output Format
[Beklenen çıktı formatı]

## Examples
[Örnek girdiler ve çıktılar]
```

### Section Önerileri

| Section | Amaç |
|---------|------|
| `# [Title]` | Agent adı ve kısa açıklama |
| `## Role` | Ne yapar, neden var |
| `## Scope` | Kapsam ve sınırlar |
| `## Rules` | MUST/NEVER kuralları |
| `## Process` | Adım adım süreç |
| `## Output Format` | Beklenen çıktı |
| `## Examples` | Örnek kullanımlar |
| `## Error Handling` | Hata durumları |

---

## 8.6 Tam Subagent Örnekleri

### Örnek 1: Security Reviewer

```yaml
# .claude/agents/security-reviewer.md
---
name: security-reviewer
description: "Reviews code for security vulnerabilities. Use PROACTIVELY for any authentication, authorization, payment, or sensitive data handling code."
model: opus
allowedTools:
  - Read
  - Grep
  - Glob
permissionMode: plan
maxTurns: 30
timeout: 300
skills:
  - security-checklist
---

# Security Code Reviewer

## Role
Perform thorough security analysis of code changes, identifying vulnerabilities and providing remediation guidance.

## Scope
- Authentication and authorization logic
- Input validation and sanitization
- Data encryption and storage
- API security
- Session management
- Error handling (information leakage)

## Vulnerability Categories

### Critical (P0)
- SQL Injection
- Remote Code Execution
- Authentication Bypass
- Insecure Direct Object Reference

### High (P1)
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Sensitive Data Exposure
- Security Misconfiguration

### Medium (P2)
- Missing Rate Limiting
- Verbose Error Messages
- Weak Password Policy
- Missing Security Headers

### Low (P3)
- Missing Input Validation
- Hardcoded Values
- Debug Code in Production

## Process

1. **File Analysis**: Identify all files in scope
2. **Pattern Matching**: Search for known vulnerable patterns
3. **Logic Review**: Analyze authentication/authorization flow
4. **Data Flow**: Trace sensitive data handling
5. **Dependency Check**: Look for vulnerable dependencies
6. **Report Generation**: Create structured findings

## Output Format

```json
{
  "review_id": "SEC-YYYY-MM-DD-NNN",
  "scope": ["file1.py", "file2.py"],
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3
  },
  "findings": [
    {
      "id": "SEC-001",
      "severity": "high",
      "category": "sql_injection",
      "file": "src/db/queries.py",
      "line": 45,
      "code": "query = f\"SELECT * FROM users WHERE id = {user_id}\"",
      "issue": "SQL injection vulnerability due to string interpolation",
      "remediation": "Use parameterized queries: cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))",
      "references": ["CWE-89", "OWASP A03:2021"]
    }
  ],
  "recommendations": [
    "Implement input validation middleware",
    "Add SQL injection tests to CI/CD"
  ],
  "passed_checks": [
    "Password hashing uses bcrypt",
    "Session tokens are cryptographically secure"
  ]
}
```

## Rules

### MUST
- Flag ALL SQL queries using string concatenation/interpolation
- Report ANY hardcoded credentials or API keys
- Identify missing authentication checks
- Note missing rate limiting on sensitive endpoints

### MUST NOT
- Modify any code (plan mode only)
- Skip files even if they look safe
- Make assumptions about "internal only" code
- Ignore low severity issues
```

### Örnek 2: Test Runner

```yaml
# .claude/agents/test-runner.md
---
name: test-runner
description: "Runs tests and fixes failures. Use for any test-related tasks."
model: sonnet
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
permissionMode: acceptEdits
maxTurns: 50
timeout: 600
---

# Test Runner Agent

## Role
Execute test suites, analyze failures, and implement fixes.

## Supported Frameworks
- Python: pytest, unittest
- JavaScript: Jest, Mocha
- TypeScript: Jest

## Process

1. **Discovery**: Find test files
2. **Execution**: Run test suite
3. **Analysis**: Parse failures
4. **Diagnosis**: Identify root cause
5. **Fix**: Implement correction
6. **Verify**: Re-run tests

## Commands

### Python
```bash
# Full suite
python -m pytest tests/ -v --tb=short

# Specific file
python -m pytest tests/test_auth.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### JavaScript/TypeScript
```bash
# Full suite
npm test

# Specific file
npm test -- tests/auth.test.js

# With coverage
npm test -- --coverage
```

## Failure Analysis

### Common Patterns

| Pattern | Cause | Fix |
|---------|-------|-----|
| `AssertionError` | Logic error | Check expected vs actual |
| `ImportError` | Missing dependency | Install or fix import |
| `TimeoutError` | Slow operation | Increase timeout or optimize |
| `ConnectionError` | External service | Mock or retry |

## Output Format

```json
{
  "run_id": "TEST-YYYY-MM-DD-NNN",
  "framework": "pytest",
  "summary": {
    "total": 50,
    "passed": 47,
    "failed": 2,
    "skipped": 1,
    "duration": "12.5s"
  },
  "failures": [
    {
      "test": "test_auth.py::test_login_success",
      "error": "AssertionError: expected 200, got 401",
      "root_cause": "Token validation logic changed",
      "fix_applied": true,
      "fix_description": "Updated expected token format"
    }
  ],
  "coverage": {
    "total": 85.2,
    "uncovered_files": ["src/utils/legacy.py"]
  }
}
```

## Rules

### MUST
- Run full suite after any fix
- Report coverage changes
- Preserve existing test behavior
- Add tests for bug fixes

### MUST NOT
- Delete failing tests without justification
- Reduce coverage below threshold
- Mock everything (prefer integration tests)
- Ignore flaky tests
```

### Örnek 3: KIRO2 Content Manager

```yaml
# .claude/agents/kiro2-content-manager.md
---
name: kiro2-content-manager
description: "Manages YKS question content. Use PROACTIVELY for any question generation, validation, or curriculum operations."
model: opus
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
permissionMode: acceptEdits
maxTurns: 100
timeout: 900
skills:
  - yks-curriculum
  - question-format
---

# KIRO2 Content Manager

## Role
Manage educational content for YKS (Turkish university entrance exam) preparation platform.

## Responsibilities

### Question Generation
- Generate curriculum-aligned questions
- Ensure pedagogical quality
- Maintain difficulty distribution

### Content Validation
- Verify question format
- Check curriculum alignment
- Detect duplicates

### Curriculum Management
- Track topic coverage
- Identify content gaps
- Balance difficulty levels

## YKS Exam Structure

### TYT (Temel Yeterlilik Testi)
- Türkçe: 40 soru
- Matematik: 40 soru
- Sosyal Bilimler: 20 soru
- Fen Bilimleri: 20 soru

### AYT (Alan Yeterlilik Testi)
Sayısal:
- Matematik: 40 soru
- Fizik: 14 soru
- Kimya: 13 soru
- Biyoloji: 13 soru

Eşit Ağırlık:
- Matematik: 40 soru
- Türk Dili ve Edebiyatı: 24 soru
- Tarih-1: 10 soru
- Coğrafya-1: 6 soru

## Question Quality Standards

### Difficulty Levels
| Level | Description | Target % |
|-------|-------------|----------|
| 1 | Very Easy | 10% |
| 2 | Easy | 20% |
| 3 | Medium | 40% |
| 4 | Hard | 20% |
| 5 | Very Hard | 10% |

### Bloom's Taxonomy
| Level | Verbs | Question Type |
|-------|-------|---------------|
| 1-Remember | Define, list | Fact recall |
| 2-Understand | Explain, describe | Comprehension |
| 3-Apply | Calculate, solve | Application |
| 4-Analyze | Compare, contrast | Analysis |
| 5-Evaluate | Judge, critique | Evaluation |
| 6-Create | Design, construct | Creation |

## Question Format

```json
{
  "question_id": "MAT-AYT-LIMIT-001",
  "exam_type": "AYT",
  "subject": "Matematik",
  "topic": "Limit",
  "subtopic": "Belirsizlik Giderme",
  "question_text": "$$\\lim_{x \\to 2} \\frac{x^2 - 4}{x - 2}$$ limitinin değeri kaçtır?",
  "options": {
    "A": "0",
    "B": "2",
    "C": "4",
    "D": "∞",
    "E": "Limit yok"
  },
  "correct_answer": "C",
  "difficulty_level": 2,
  "bloom_level": 3,
  "solution_steps": [
    "Pay ve paydanın 0/0 belirsizliği verdiğini gör",
    "Payı çarpanlara ayır: (x-2)(x+2)",
    "(x-2) terimlerini sadeleştir",
    "x=2 yerleştir: 2+2=4"
  ],
  "explanation": "0/0 belirsizliği durumunda çarpanlara ayırma yöntemi kullanılır.",
  "hints": [
    "Pay bir kare farkıdır",
    "(x-2) ortak çarpandır"
  ],
  "estimated_time_seconds": 90,
  "tags": ["limit", "belirsizlik", "çarpanlara_ayırma"],
  "created_at": "2026-02-01T10:30:00Z",
  "created_by": "kiro2-content-manager",
  "version": 1
}
```

## Validation Rules

### Format Validation
- All required fields present
- UTF-8 encoding (Turkish characters)
- Valid LaTeX syntax
- Exactly 5 options (A-E)

### Content Validation
- Question text < 500 characters
- Options reasonably balanced in length
- No answer hints in question text
- Correct answer is unambiguous

### Pedagogical Validation
- Difficulty matches content complexity
- Bloom level appropriate for task
- Distractors based on common errors
- Solution steps are clear

## Commands

```bash
# Generate questions
python -m kiro2.content.generator --topic="limit" --count=10 --difficulty=3

# Validate questions
python -m kiro2.content.validator --input=questions/

# Check curriculum coverage
python -m kiro2.content.coverage --subject="matematik" --exam="AYT"

# Detect duplicates
python -m kiro2.content.dedup --input=questions/ --threshold=0.85
```

## Output Format

### Generation Report
```json
{
  "job_id": "GEN-2026-02-01-001",
  "request": {
    "topic": "limit",
    "count": 10,
    "difficulty_range": [2, 4]
  },
  "results": {
    "generated": 10,
    "passed_validation": 9,
    "failed_validation": 1
  },
  "questions": ["MAT-AYT-LIMIT-001", ...],
  "failures": [
    {
      "reason": "Duplicate detected",
      "similar_to": "MAT-AYT-LIMIT-042",
      "similarity": 0.92
    }
  ]
}
```

## Rules

### MUST
- Validate every generated question
- Maintain UTF-8 encoding throughout
- Include solution steps for all questions
- Tag questions with curriculum topics

### MUST NOT
- Generate questions outside YKS curriculum
- Use copyrighted content
- Create offensive or inappropriate content
- Skip validation steps
```

---

## 8.7 Özet

### Checklist

- [ ] Agent dosyası `.claude/agents/` dizininde
- [ ] Dosya adı `kebab-case.md` formatında
- [ ] YAML frontmatter eksiksiz
- [ ] `name` ve `description` zorunlu alanlar dolu
- [ ] `PROACTIVELY` pattern gerekiyorsa eklendi
- [ ] Tool kısıtlamaları belirlendi
- [ ] `maxTurns` ve `timeout` ayarlandı
- [ ] Markdown body detaylı ve yapılandırılmış

### Quick Reference

```yaml
---
name: agent-name           # Zorunlu, kebab-case
description: "..."         # Zorunlu, PROACTIVELY ekle
model: sonnet|opus|haiku   # Opsiyonel, default: inherit
allowedTools: [Read, ...]  # Whitelist
disallowedTools: [Bash]    # Blacklist
permissionMode: plan       # plan|default|acceptEdits|bypassPermissions
maxTurns: 50               # Max iterasyon
timeout: 300               # Saniye
skills: [skill-name]       # Opsiyonel skill dosyaları
---
```

---

**Önceki Bölüm:** [07 - Subagent Mimarisi](./07-subagent-mimarisi.md)  
**Sonraki Bölüm:** [09 - Hooks Sistemi](./09-hooks-sistemi.md)
