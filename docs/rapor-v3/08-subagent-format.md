# BÖLÜM 8: Subagent Tanımlama Formatı

## 8.1 Dosya Yapısı

### Konum

Custom subagent'lar `.claude/agents/` dizininde tanımlanır.

```
.claude/
└── agents/
    ├── code-reviewer.md
    ├── security-auditor.md
    ├── test-runner.md
    └── matematik-subagent.md
```

### Dosya İsimlendirme

**Convention:** `[görev]-[tip].md`

| Pattern | Örnek |
|---------|-------|
| `[konu]-subagent.md` | `matematik-subagent.md` |
| `[görev]-[tip].md` | `code-reviewer.md` |
| `[domain]-[eylem].md` | `security-auditor.md` |

**Kurallar:**
- Küçük harf
- Tire ile ayırma (snake_case değil)
- `.md` uzantısı zorunlu
- Açıklayıcı isimler

---

## 8.2 Dosya Formatı

### Genel Yapı

```markdown
---
# YAML Frontmatter (metadata)
name: subagent-name
description: "Description text"
model: sonnet
# ... diğer alanlar
---

# Markdown Body (instructions)
## Görev Açıklaması
...

## Kurallar
...

## Output Formatı
...
```

### İki Bölüm

1. **YAML Frontmatter:** Metadata ve konfigürasyon
2. **Markdown Body:** Detaylı talimatlar ve kurallar

---

## 8.3 YAML Frontmatter Alanları

### Zorunlu Alanlar

#### `name`

**Tip:** String
**Açıklama:** Subagent'ın benzersiz tanımlayıcısı

```yaml
name: security-reviewer
```

**Kurallar:**
- Küçük harf
- Tire ile ayırma
- Unique olmalı
- Max 50 karakter

#### `description`

**Tip:** String
**Açıklama:** Subagent'ın ne zaman kullanılacağını açıklar

```yaml
description: "Reviews code for security vulnerabilities. Use PROACTIVELY for any auth, payment, or data handling code."
```

**Önemli:** Bu alan Claude'un subagent'ı otomatik seçmesini etkiler!

---

### Model Seçimi

#### `model`

**Tip:** Enum
**Değerler:** `opus`, `sonnet`, `haiku`, `inherit`
**Default:** `inherit` (parent'tan al)

```yaml
model: opus  # Derin analiz için
model: sonnet  # Dengeli
model: haiku  # Hızlı, basit görevler
model: inherit  # Parent ile aynı
```

**Seçim rehberi:**

| Model | Kullanım | Maliyet | Hız |
|-------|----------|---------|-----|
| `opus` | Kompleks reasoning, güvenlik, planlama | Yüksek | Yavaş |
| `sonnet` | Genel geliştirme, review | Orta | Orta |
| `haiku` | Basit validasyon, format check | Düşük | Hızlı |
| `inherit` | Parent context koruması | Parent'a bağlı | Parent'a bağlı |

---

### Araç Konfigürasyonu

#### `tools`

**Tip:** Array of strings
**Açıklama:** Subagent'ın kullanabileceği araçlar

```yaml
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
```

**Mevcut araçlar:**

| Araç | Açıklama | Risk |
|------|----------|------|
| `Read` | Dosya okuma | Düşük |
| `Write` | Dosya yazma | Orta |
| `Edit` | Dosya düzenleme | Orta |
| `MultiEdit` | Çoklu düzenleme | Orta |
| `Bash` | Komut çalıştırma | Yüksek |
| `Glob` | Pattern matching | Düşük |
| `Grep` | Metin arama | Düşük |
| `LS` | Dizin listeleme | Düşük |
| `Task` | Subagent çağırma | Düşük |
| `WebSearch` | Web araması | Düşük |
| `WebFetch` | URL içerik çekme | Düşük |
| `NotebookRead` | Jupyter okuma | Düşük |
| `NotebookEdit` | Jupyter düzenleme | Orta |

#### `allowedTools`

**Tip:** Array of strings
**Açıklama:** Whitelist - SADECE bu araçlara izin ver

```yaml
allowedTools:
  - Read
  - Glob
  - Grep
```

**Not:** `tools` yerine kullanılır, birlikte kullanılmaz.

#### `disallowedTools`

**Tip:** Array of strings
**Açıklama:** Blacklist - Bu araçları YASAKLA

```yaml
disallowedTools:
  - Bash
  - Write
  - Edit
```

**Not:** `tools` ile birlikte kullanılabilir.

**Öncelik sırası:**
```
allowedTools > disallowedTools > tools > default (parent inheritance)
```

---

### Permission Mode

#### `permissionMode`

**Tip:** Enum
**Değerler:** `default`, `acceptEdits`, `bypassPermissions`, `plan`
**Default:** `default`

```yaml
permissionMode: acceptEdits
```

| Mode | Davranış | Kullanım |
|------|----------|----------|
| `default` | Her işlem için onay sor | Güvenli, yavaş |
| `acceptEdits` | Düzenlemeleri otomatik kabul | Trusted subagent |
| `bypassPermissions` | Tüm izinleri atla | ⚠️ Dikkatli kullan! |
| `plan` | Sadece okuma, değişiklik yok | Analiz/review |

**Güvenlik notu:**
```
plan < default < acceptEdits < bypassPermissions
(en güvenli → en riskli)
```

---

### Limitler

#### `maxTurns`

**Tip:** Integer
**Default:** 50
**Açıklama:** Maksimum iterasyon sayısı

```yaml
maxTurns: 100  # Uzun görevler için
maxTurns: 20   # Kısa görevler için
```

**Önerilen değerler:**

| Görev tipi | maxTurns |
|------------|----------|
| Quick validation | 10-20 |
| Code review | 30-50 |
| Soru üretimi | 50-100 |
| Kompleks refactoring | 100-200 |

#### `timeout`

**Tip:** Integer (saniye)
**Default:** 300 (5 dakika)
**Açıklama:** Toplam zaman limiti

```yaml
timeout: 600  # 10 dakika
timeout: 120  # 2 dakika (hızlı görevler)
```

**Önerilen değerler:**

| Görev tipi | Timeout |
|------------|---------|
| Quick check | 60-120 |
| Standard task | 300-600 |
| Long task | 900-1800 |

---

### Skills

#### `skills`

**Tip:** Array of strings
**Açıklama:** Otomatik yüklenecek skill dosyaları

```yaml
skills:
  - security-checklist
  - code-style-guide
```

**Skill dosyaları konumu:** `.claude/skills/[skill-name].md`

**Örnek skill dosyası:**
```markdown
# .claude/skills/security-checklist.md

## Security Review Checklist

### Input Validation
- [ ] All user input is validated
- [ ] SQL injection prevention
- [ ] XSS prevention

### Authentication
- [ ] Password hashing (bcrypt)
- [ ] Session management
- [ ] Rate limiting

### Data Protection
- [ ] Sensitive data encryption
- [ ] Secure transmission (HTTPS)
- [ ] PII handling
```

---

## 8.4 PROACTIVELY Pattern

### Tanım

`description` alanında "PROACTIVELY" veya "MUST BE USED" ifadeleri kullanıldığında, Claude bu subagent'ı kullanıcı açık istek olmadan bile otomatik devreye sokar.

### Kullanım

```yaml
description: "Reviews code for security vulnerabilities. Use PROACTIVELY for any auth, payment, or data handling code."
```

```yaml
description: "Validates question format and content. MUST BE USED after any question generation."
```

### Davranış

| Description | Claude Davranışı |
|-------------|------------------|
| Normal | Kullanıcı isterse kullanır |
| "Use PROACTIVELY for..." | İlgili dosya görünce otomatik kullanır |
| "MUST BE USED when..." | Belirtilen durumda zorunlu kullanır |

### Örnekler

**Security reviewer:**
```yaml
description: "Security code review. Use PROACTIVELY for files in: auth/, payment/, crypto/, api/v*/secure/"
```

Claude davranışı:
- `src/auth/login.py` düzenlenince → Otomatik security review
- `src/utils/helpers.py` düzenlenince → Review yapılmaz

**Test validator:**
```yaml
description: "Validates test coverage. MUST BE USED after any test file modification."
```

Claude davranışı:
- `tests/test_auth.py` düzenlenince → Zorunlu coverage check

---

## 8.5 Markdown Body Yazımı

### Yapı Önerisi

```markdown
# [Subagent Adı]

## Görev
[Tek paragraf görev tanımı]

## Kurallar
[Bullet list of rules]

## Kontrol Listesi
[Checkbox list]

## Output Formatı
[Beklenen çıktı formatı]

## Örnekler
[Input/output örnekleri]
```

### Etkili Talimat Yazımı

**Kötü:**
```markdown
Check the code for problems.
```

**İyi:**
```markdown
## Görev
Review Python code for security vulnerabilities with focus on:
1. Input validation
2. Authentication logic
3. Data exposure

## Kontrol Listesi
- [ ] No SQL injection vulnerabilities
- [ ] No hardcoded credentials
- [ ] Proper input sanitization
- [ ] Rate limiting on sensitive endpoints

## Output Formatı
Return JSON:
{
  "status": "PASS" | "FAIL",
  "issues": [
    {
      "severity": "HIGH" | "MEDIUM" | "LOW",
      "file": "path/to/file.py",
      "line": 42,
      "description": "Issue description",
      "recommendation": "How to fix"
    }
  ],
  "summary": "Brief overall assessment"
}
```

---

## 8.6 KIRO2 Subagent Örnekleri

### matematik-subagent.md

```yaml
---
name: matematik-subagent
description: "YKS matematik soruları üretir ve doğrular. Use PROACTIVELY for TYT/AYT matematik içeriği."
model: opus
tools:
  - Read
  - Write
  - Bash
permissionMode: acceptEdits
maxTurns: 100
timeout: 600
skills:
  - yks-mufredat
  - soru-formati
---

# Matematik Soru Üretici

## Görev
TYT ve AYT müfredatına uygun matematik soruları üret. Her soru pedagojik açıdan kaliteli, doğru ve Türkçe dil kurallarına uygun olmalı.

## Kapsam

### TYT Konuları
- Temel Kavramlar, Sayılar, Çarpanlar-Katlar
- Üslü-Köklü Sayılar, Eşitsizlikler
- Polinomlar, Problemler
- Mantık, Kümeler, Fonksiyonlar (Temel)
- Permütasyon-Kombinasyon, Olasılık
- İstatistik, Geometri (Temel)

### AYT Konuları
- Fonksiyonlar (İleri), Trigonometri
- Logaritma, Diziler
- Limit, Türev, İntegral
- Analitik Geometri, Uzay Geometri

## Kurallar

### Format Kuralları
- YOU MUST include: question_id, question_text, options (A-E), correct_answer
- YOU MUST include: difficulty_level (1-5), topic_tags, subtopic, explanation
- ALWAYS use UTF-8 encoding for Turkish characters (ğ, ü, ş, ı, ö, ç)
- ALWAYS use LaTeX for math: inline $...$ or display $$...$$

### Pedagojik Kurallar
- Difficulty must match the topic complexity
- Distractors must be plausible (common mistakes)
- Explanation must include step-by-step solution
- No ambiguous or trick questions

### Kalite Kuralları
- NEVER produce duplicate questions
- NEVER embed answer in question text
- ALWAYS balance option lengths
- CHECK grammar and spelling

## Output Formatı

```json
{
  "question_id": "MAT_TYT_001",
  "question_text": "$\\sqrt{48} + \\sqrt{27}$ işleminin sonucu kaçtır?",
  "options": {
    "A": "$5\\sqrt{3}$",
    "B": "$6\\sqrt{3}$",
    "C": "$7\\sqrt{3}$",
    "D": "$8\\sqrt{3}$",
    "E": "$9\\sqrt{3}$"
  },
  "correct_answer": "C",
  "difficulty_level": 2,
  "topic_tags": ["köklü_sayılar", "sadeleştirme"],
  "subtopic": "uslu_koklu_sayilar",
  "exam_type": "TYT",
  "explanation": "Adım 1: $\\sqrt{48} = \\sqrt{16 \\cdot 3} = 4\\sqrt{3}$\nAdım 2: $\\sqrt{27} = \\sqrt{9 \\cdot 3} = 3\\sqrt{3}$\nAdım 3: $4\\sqrt{3} + 3\\sqrt{3} = 7\\sqrt{3}$",
  "estimated_time_seconds": 60,
  "hints": ["Köklü sayıları sadeleştirerek başlayın"]
}
```

## Doğrulama

Her soru üretiminden sonra otomatik olarak:
1. JSON format kontrolü
2. Zorunlu alan kontrolü
3. LaTeX syntax kontrolü
4. Türkçe karakter encoding kontrolü
```

### content-validator.md

```yaml
---
name: content-validator
description: "Üretilen içeriği format ve pedagojik açıdan doğrular. MUST BE USED after any question generation."
model: sonnet
allowedTools:
  - Read
  - Grep
  - Glob
permissionMode: plan
maxTurns: 30
timeout: 180
---

# İçerik Doğrulayıcı

## Görev
Üretilen soruları format, içerik ve pedagojik açıdan doğrula. Validation pipeline'ının 2-4. adımlarını çalıştır.

## Kontrol Listesi

### 1. Format Kontrolü
- [ ] JSON schema'ya uygun
- [ ] Zorunlu alanlar mevcut
- [ ] UTF-8 encoding doğru
- [ ] LaTeX syntax geçerli

### 2. İçerik Kontrolü
- [ ] Soru metni anlaşılır
- [ ] 5 seçenek (A-E) mevcut
- [ ] Doğru cevap seçeneklerde var
- [ ] Seçenek uzunlukları dengeli

### 3. Pedagojik Kontrol
- [ ] Zorluk seviyesi tutarlı
- [ ] Müfredata uygun
- [ ] Çeldirici kalitesi yeterli
- [ ] Açıklama yeterli

### 4. Duplicate Kontrolü
- [ ] Exact match yok
- [ ] Semantic similarity < 0.85

## Output Formatı

```json
{
  "status": "PASS" | "FAIL" | "WARNING",
  "question_id": "MAT_TYT_001",
  "checks": {
    "format": {"status": "PASS", "details": null},
    "content": {"status": "PASS", "details": null},
    "pedagogy": {"status": "WARNING", "details": "Difficulty may be higher than marked"},
    "duplicate": {"status": "PASS", "details": "No similar questions found"}
  },
  "issues": [
    {
      "severity": "WARNING",
      "check": "pedagogy",
      "message": "Zorluk seviyesi 2 olarak işaretlenmiş ama soru seviye 3 zorluğunda olabilir",
      "suggestion": "difficulty_level: 3 olarak güncellemeyi düşünün"
    }
  ],
  "summary": "1 warning, soru kabul edilebilir"
}
```

## Karar Mantığı

- **PASS:** Tüm kontroller başarılı
- **WARNING:** Minor issues, kabul edilebilir
- **FAIL:** Major issues, düzeltme gerekli

Herhangi bir FAIL → Soru reddedilir ve üreticiye geri gönderilir
```

### security-reviewer.md

```yaml
---
name: security-reviewer
description: "Kod güvenlik incelemesi yapar. Use PROACTIVELY for files in: auth/, api/, payment/, models/user*, *password*, *token*, *secret*"
model: opus
allowedTools:
  - Read
  - Grep
  - Glob
disallowedTools:
  - Write
  - Edit
  - Bash
permissionMode: plan
maxTurns: 50
timeout: 300
skills:
  - security-checklist
  - owasp-top-10
---

# Güvenlik İnceleyici

## Görev
Kod değişikliklerini güvenlik açısından incele. OWASP Top 10 ve genel güvenlik best practices'e göre değerlendir.

## Odak Alanları

### Authentication & Authorization
- Password hashing (bcrypt, argon2)
- Session management
- JWT handling
- Role-based access control

### Input Validation
- SQL injection
- XSS (Cross-Site Scripting)
- Command injection
- Path traversal

### Data Protection
- Sensitive data exposure
- Encryption at rest and in transit
- PII handling
- API key management

### Security Configuration
- Debug mode in production
- Verbose error messages
- Default credentials
- Missing security headers

## Severity Levels

| Level | Criteria | Action |
|-------|----------|--------|
| CRITICAL | Immediate exploitation possible | Block deployment |
| HIGH | Significant risk, exploitable | Fix before merge |
| MEDIUM | Potential risk, requires conditions | Fix in next sprint |
| LOW | Minor issue, defense in depth | Track for future |
| INFO | Informational, best practice | Optional |

## Output Formatı

```json
{
  "status": "PASS" | "FAIL",
  "overall_risk": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NONE",
  "files_reviewed": ["src/auth/login.py", "src/api/users.py"],
  "findings": [
    {
      "id": "SEC-001",
      "severity": "HIGH",
      "category": "Authentication",
      "title": "Weak password hashing",
      "file": "src/auth/login.py",
      "line": 45,
      "code_snippet": "hashlib.md5(password.encode())",
      "description": "MD5 is cryptographically broken and unsuitable for password hashing",
      "recommendation": "Use bcrypt with cost factor >= 12",
      "references": ["CWE-328", "OWASP A02:2021"]
    }
  ],
  "summary": "1 HIGH severity issue found. Fix required before merge.",
  "recommendations": [
    "Replace MD5 with bcrypt for password hashing",
    "Add rate limiting to login endpoint"
  ]
}
```

## Karar Kuralları

- ANY CRITICAL → FAIL, deployment blocked
- ANY HIGH → FAIL, review required
- MEDIUM only → WARNING, fix recommended
- LOW/INFO only → PASS with notes
```

---

## 8.7 Özet

### Checklist

- [ ] `.claude/agents/` dizini oluşturuldu
- [ ] Subagent dosyaları YAML frontmatter + Markdown body formatında
- [ ] PROACTIVELY pattern ilgili subagent'larda kullanıldı
- [ ] Model seçimi görev tipine uygun
- [ ] Permission mode güvenlik gereksinimlerine uygun
- [ ] maxTurns ve timeout değerleri ayarlandı
- [ ] Output formatı net tanımlandı

### YAML Alanları Quick Reference

| Alan | Zorunlu | Default | Açıklama |
|------|---------|---------|----------|
| `name` | ✅ | - | Benzersiz tanımlayıcı |
| `description` | ✅ | - | Ne zaman kullanılacağı |
| `model` | ❌ | inherit | opus/sonnet/haiku/inherit |
| `tools` | ❌ | parent | Araç listesi |
| `allowedTools` | ❌ | - | Whitelist |
| `disallowedTools` | ❌ | - | Blacklist |
| `permissionMode` | ❌ | default | default/acceptEdits/bypassPermissions/plan |
| `maxTurns` | ❌ | 50 | Max iterasyon |
| `timeout` | ❌ | 300 | Saniye |
| `skills` | ❌ | - | Skill dosyaları |

---

**Önceki Bölüm:** [07 - Subagent Mimarisi](./07-subagent-mimarisi.md)  
**Sonraki Bölüm:** [09 - Hooks Sistemi](./09-hooks-sistemi.md)
