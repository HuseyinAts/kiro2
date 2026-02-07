# Requirements Document - Reward Hacking Prevention Hooks Sistemi

## Introduction

Bu spec, Daisy Stanton'ın reward hacking prevention expertise'ine göre tasarlanmış sahte başarı tespit hook'larını tanımlar. `assert True`, `echo Success`, `pass # placeholder` gibi reward hacking pattern'leri %100 tespit edilir ve engellenir. AI agent'ların gerçek çalışma yapmasını garanti eder.

## Glossary

- **Reward Hacking**: Gerçek çalışma yapmadan başarı gösterme
- **Fake Success Pattern**: Sahte başarı pattern'i
- **Placeholder Code**: Yer tutucu kod
- **Coverage Manipulation**: Test coverage manipülasyonu
- **Exit Code 2**: Engelleyici hata
- **Pattern Detection**: Pattern tespit sistemi

## Requirements

### Requirement 1: Assert True Detection

**User Story:** As a QA engineer, I want `assert True` gibi sahte test'lerin tespit edilmesini, so that gerçek test yazılsın.

#### Acceptance Criteria

1. **REQ-1.1** WHEN test dosyası yazıldığında, THE PostToolUse Hook SHALL `assert True` pattern'ini tarar
2. **REQ-1.2** WHEN `assert True` tespit edildiğinde, THE Hook SHALL exit code 2 döner
3. **REQ-1.3** WHEN `ASSERT_TRUE(true)` (C++ style) tespit edildiğinde, THE Hook SHALL aynı şekilde engeller
4. **REQ-1.4** WHEN `self.assertTrue(True)` tespit edildiğinde, THE Hook SHALL uyarı verir
5. **REQ-1.5** WHEN legitimate `assert True` kullanımı olduğunda, THE Hook SHALL context analizi yapar
6. **REQ-1.6** WHEN hata mesajı verildiğinde, THE Hook SHALL "Write meaningful assertion" önerir

---

### Requirement 2: Echo Success Detection

**User Story:** As a DevOps engineer, I want `echo Success` gibi sahte başarı mesajlarının tespit edilmesini, so that gerçek validation yapılsın.

#### Acceptance Criteria

1. **REQ-2.1** WHEN bash script yazıldığında, THE PreToolUse Hook SHALL `echo Success` pattern'ini tarar
2. **REQ-2.2** WHEN `echo "Success"` veya `print("Success")` tespit edildiğinde, THE Hook SHALL exit code 2 döner
3. **REQ-2.3** WHEN `return 0` ile birlikte `echo Success` olduğunda, THE Hook SHALL daha yüksek severity verir
4. **REQ-2.4** WHEN gerçek validation olmadan success mesajı olduğunda, THE Hook SHALL engeller
5. **REQ-2.5** WHEN legitimate success logging olduğunda, THE Hook SHALL context-based exception yapar
6. **REQ-2.6** WHEN alternatif önerildiğinde, THE Hook SHALL "Add actual validation before success message" der

---

### Requirement 3: Placeholder Code Detection

**User Story:** As a tech lead, I want `pass`, `TODO`, `FIXME` gibi placeholder'ların tespit edilmesini, so that incomplete code commit edilmesin.

#### Acceptance Criteria

1. **REQ-3.1** WHEN Python dosyası yazıldığında, THE PostToolUse Hook SHALL `pass # placeholder` pattern'ini tarar
2. **REQ-3.2** WHEN `# TODO:` veya `# FIXME:` tespit edildiğinde, THE Hook SHALL warning verir
3. **REQ-3.3** WHEN fonksiyon sadece `pass` içerdiğinde, THE Hook SHALL exit code 2 döner
4. **REQ-3.4** WHEN `raise NotImplementedError` tespit edildiğinde, THE Hook SHALL implementation ister
5. **REQ-3.5** WHEN `...` (Ellipsis) placeholder olarak kullanıldığında, THE Hook SHALL uyarı verir
6. **REQ-3.6** WHEN commit öncesi placeholder olduğunda, THE Hook SHALL commit'i engeller

---

### Requirement 4: Coverage Manipulation Detection

**User Story:** As a QA engineer, I want test coverage manipülasyonunun tespit edilmesini, so that gerçek coverage ölçülsün.

#### Acceptance Criteria

1. **REQ-4.1** WHEN test dosyası yazıldığında, THE Hook SHALL `# pragma: no cover` kullanımını tarar
2. **REQ-4.2** WHEN `# pragma: no cover` tespit edildiğinde, THE Hook SHALL gerekçe ister
3. **REQ-4.3** WHEN gerekçesiz `no cover` olduğunda, THE Hook SHALL exit code 2 döner
4. **REQ-4.4** WHEN `# type: ignore` aşırı kullanıldığında, THE Hook SHALL uyarı verir
5. **REQ-4.5** WHEN coverage threshold düşürüldüğünde, THE Hook SHALL approval ister
6. **REQ-4.6** WHEN legitimate exception olduğunda, THE Hook SHALL documented reason bekler

---

### Requirement 5: Mock Abuse Detection

**User Story:** As a developer, I want aşırı mock kullanımının tespit edilmesini, so that gerçek integration test yazılsın.

#### Acceptance Criteria

1. **REQ-5.1** WHEN test dosyası yazıldığında, THE Hook SHALL mock kullanım oranını hesaplar
2. **REQ-5.2** WHEN mock oranı > %80 olduğunda, THE Hook SHALL warning verir
3. **REQ-5.3** WHEN tüm external call'lar mock'landığında, THE Hook SHALL integration test önerir
4. **REQ-5.4** WHEN mock return value sabit olduğunda, THE Hook SHALL realistic data önerir
5. **REQ-5.5** WHEN mock verification eksik olduğunda, THE Hook SHALL assert_called_once() önerir
6. **REQ-5.6** WHEN mock abuse tespit edildiğinde, THE Hook SHALL test value'sini sorgular

---

### Requirement 6: Empty Exception Handler Detection

**User Story:** As a developer, I want boş exception handler'ların tespit edilmesini, so that error handling yapılsın.

#### Acceptance Criteria

1. **REQ-6.1** WHEN Python dosyası yazıldığında, THE Hook SHALL `except: pass` pattern'ini tarar
2. **REQ-6.2** WHEN boş except block tespit edildiğinde, THE Hook SHALL exit code 2 döner
3. **REQ-6.3** WHEN `except Exception:` ile boş block olduğunda, THE Hook SHALL logging önerir
4. **REQ-6.4** WHEN bare `except:` kullanıldığında, THE Hook SHALL specific exception önerir
5. **REQ-6.5** WHEN exception silently swallow edildiğinde, THE Hook SHALL re-raise önerir
6. **REQ-6.6** WHEN legitimate suppression olduğunda, THE Hook SHALL comment ile açıklama ister

---

### Requirement 7: Hardcoded Test Data Detection

**User Story:** As a QA engineer, I want hardcoded test data'nın tespit edilmesini, so that dynamic test data kullanılsın.

#### Acceptance Criteria

1. **REQ-7.1** WHEN test dosyası yazıldığında, THE Hook SHALL hardcoded value'ları tarar
2. **REQ-7.2** WHEN `user_id = 1` gibi magic number tespit edildiğinde, THE Hook SHALL fixture kullanımı önerir
3. **REQ-7.3** WHEN hardcoded email/password olduğunda, THE Hook SHALL factory pattern önerir
4. **REQ-7.4** WHEN test data çeşitliliği düşük olduğunda, THE Hook SHALL parametrize önerir
5. **REQ-7.5** WHEN edge case test eksik olduğunda, THE Hook SHALL boundary value testing önerir
6. **REQ-7.6** WHEN property-based testing uygun olduğunda, THE Hook SHALL Hypothesis önerir

---

### Requirement 8: CI/CD Bypass Detection

**User Story:** As a DevOps engineer, I want CI/CD bypass attempt'lerinin tespit edilmesini, so that quality gate'ler atlanamaz olsun.

#### Acceptance Criteria

1. **REQ-8.1** WHEN commit message'da `[skip ci]` tespit edildiğinde, THE Hook SHALL gerekçe ister
2. **REQ-8.2** WHEN gerekçesiz CI skip olduğunda, THE Hook SHALL commit'i engeller
3. **REQ-8.3** WHEN test skip decorator tespit edildiğinde, THE Hook SHALL `@pytest.mark.skip` gerekçesi ister
4. **REQ-8.4** WHEN quality gate disable edildiğinde, THE Hook SHALL approval workflow tetikler
5. **REQ-8.5** WHEN emergency bypass gerektiğinde, THE Hook SHALL incident ticket ister
6. **REQ-8.6** WHEN bypass audit log tutulduğunda, THE Hook SHALL who, when, why kaydeder

---

## Bağımlılıklar

- **AST (Abstract Syntax Tree)**: Python kod analizi
- **Regex**: Pattern matching
- **pytest**: Test framework
- **pre-commit**: Git hook yönetimi
- **Bandit**: Security linting
- **Ruff**: Code linting

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 1 hafta
**Beklenen Reward Hacking Önleme:** %100

## Reward Hacking Prevention Flow

```
1. Developer Kod/Test Yazıyor
   ↓
2. PostToolUse Hook Tetiklendi
   ↓
3. Pattern Detection (Paralel)
   ├─ Assert True Detection
   │  ├─ Regex: r'assert\s+True'
   │  ├─ AST Analysis
   │  └─ Exit Code: 0 (Clean) / 2 (Detected)
   ├─ Echo Success Detection
   │  ├─ Regex: r'echo\s+"?Success"?'
   │  ├─ Context Validation Check
   │  └─ Exit Code: 0 (Clean) / 2 (Detected)
   ├─ Placeholder Code Detection
   │  ├─ Regex: r'pass\s*#\s*placeholder'
   │  ├─ TODO/FIXME Scan
   │  └─ Exit Code: 0 (Clean) / 2 (Detected)
   ├─ Coverage Manipulation Detection
   │  ├─ Regex: r'#\s*pragma:\s*no\s*cover'
   │  ├─ Reason Documentation Check
   │  └─ Exit Code: 0 (Justified) / 2 (Unjustified)
   ├─ Mock Abuse Detection
   │  ├─ Mock Usage Ratio Calculation
   │  ├─ Integration Test Suggestion
   │  └─ Exit Code: 0 (Reasonable) / 1 (Warning)
   ├─ Empty Exception Handler Detection
   │  ├─ Regex: r'except.*:\s*pass'
   │  ├─ Logging/Re-raise Suggestion
   │  └─ Exit Code: 0 (Clean) / 2 (Detected)
   ├─ Hardcoded Test Data Detection
   │  ├─ Magic Number Detection
   │  ├─ Fixture/Factory Suggestion
   │  └─ Exit Code: 0 (Clean) / 1 (Warning)
   └─ CI/CD Bypass Detection
      ├─ Commit Message Scan
      ├─ Skip Decorator Check
      └─ Exit Code: 0 (Clean) / 2 (Detected)
   ↓
4. Result Aggregation
   ├─ No Reward Hacking? → Exit 0 ✓
   └─ Reward Hacking Detected? → Exit 2 ✗
   ↓
5. Feedback to Developer
   ├─ Pattern Type
   ├─ Location (File, Line)
   ├─ Severity Level
   └─ Remediation Suggestion
```

## Success Metrics

1. **Reward Hacking Detection Rate:** %100
2. **False Positive Rate:** < %5
3. **Developer Compliance:** >= %95
4. **Code Quality Improvement:** %200
5. **Real Test Coverage:** >= %80

## Banned Patterns List

```python
REWARD_HACKING_PATTERNS = {
    "assert_true": [
        r"assert\s+True\b",
        r"ASSERT_TRUE\(true\)",
        r"self\.assertTrue\(True\)",
    ],
    "echo_success": [
        r'echo\s+"?Success"?',
        r'print\("Success"\)',
        r'console\.log\("Success"\)',
    ],
    "placeholder": [
        r"pass\s*#\s*placeholder",
        r"#\s*TODO:",
        r"#\s*FIXME:",
        r"raise\s+NotImplementedError",
        r"^\s*\.\.\.\s*$",
    ],
    "coverage_manipulation": [
        r"#\s*pragma:\s*no\s*cover",
        r"#\s*type:\s*ignore",
    ],
    "empty_exception": [
        r"except.*:\s*pass",
        r"except\s+Exception:\s*pass",
    ],
}
```

