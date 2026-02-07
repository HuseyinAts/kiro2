# Requirements Document - Python Code Quality Hooks Sistemi

## Introduction

Bu spec, Daisy Stanton'ın hooks system expertise'ine göre tasarlanmış Python kod kalitesi kontrol hook'larını tanımlar. PreToolUse ve PostToolUse hook'ları ile ruff, mypy, pytest otomatik çalıştırılır. Boris Cherny'nin verification feedback loops prensibi ile entegre edilerek kod kalitesi %200-300 artırılır ve bug oranı %95 azaltılır.

## Glossary

- **PreToolUse Hook**: Kod yazma öncesi çalışan hook
- **PostToolUse Hook**: Kod yazma sonrası çalışan hook
- **Ruff**: Python linter ve formatter
- **Mypy**: Static type checker
- **Pytest**: Test framework
- **Exit Code 2**: Engelleyici hata (Claude'a geri beslenir)
- **Auto-fix**: Otomatik kod düzeltme
- **Type Hints**: Python tip belirteçleri

## Requirements

### Requirement 1: Ruff Linting Hook

**User Story:** As a developer, I want kod yazdıktan sonra otomatik linting yapılmasını, so that kod standartlarına uygun yazayım.

#### Acceptance Criteria

1. **REQ-1.1** WHEN Python dosyası yazıldığında, THE PostToolUse Hook SHALL ruff check komutunu çalıştırır
2. **REQ-1.2** WHEN linting hatası bulunduğunda, THE Hook SHALL hata tipini kategorize eder (E: error, W: warning, F: fatal)
3. **REQ-1.3** WHEN auto-fix mümkün olduğunda, THE Hook SHALL ruff check --fix ile otomatik düzeltir
4. **REQ-1.4** WHEN hata düzeltilemediğinde, THE Hook SHALL detaylı hata mesajı ve satır numarası gösterir
5. **REQ-1.5** WHEN kritik hata (E, F) olduğunda, THE Hook SHALL exit code 2 döner (Claude'a geri beslenir)
6. **REQ-1.6** WHEN sadece warning olduğunda, THE Hook SHALL exit code 0 döner ama uyarı gösterir

---

### Requirement 2: Mypy Type Checking Hook

**User Story:** As a developer, I want type hint'lerin doğruluğunun kontrol edilmesini, so that runtime type error'ları önleyeyim.

#### Acceptance Criteria

1. **REQ-2.1** WHEN Python dosyası yazıldığında, THE PostToolUse Hook SHALL mypy --ignore-missing-imports komutunu çalıştırır
2. **REQ-2.2** WHEN type error bulunduğunda, THE Hook SHALL error message, satır numarası, ve expected/actual type gösterir
3. **REQ-2.3** WHEN fonksiyon type hint eksik olduğunda, THE Hook SHALL missing type hint uyarısı verir
4. **REQ-2.4** WHEN return type uyumsuz olduğunda, THE Hook SHALL incompatible return type hatası verir
5. **REQ-2.5** WHEN type error sayısı > 0 olduğunda, THE Hook SHALL exit code 2 döner
6. **REQ-2.6** WHEN strict mode aktif olduğunda, THE Hook SHALL --strict flag ile çalışır

---

### Requirement 3: Pytest Auto-Run Hook

**User Story:** As a developer, I want kod değiştirdikten sonra ilgili testlerin otomatik çalışmasını, so that regression bug'larını hemen tespit edeyim.

#### Acceptance Criteria

1. **REQ-3.1** WHEN Python dosyası değiştirildiğinde, THE PostToolUse Hook SHALL ilgili test dosyasını bulur
2. **REQ-3.2** WHEN test dosyası bulunduğunda, THE Hook SHALL pytest -x --tb=short komutunu çalıştırır
3. **REQ-3.3** WHEN test başarısız olduğunda, THE Hook SHALL ilk hatada durur ve traceback gösterir
4. **REQ-3.4** WHEN test bulunamadığında, THE Hook SHALL "Test yazılması gerekiyor" uyarısı verir
5. **REQ-3.5** WHEN test başarısız olduğunda, THE Hook SHALL exit code 2 döner
6. **REQ-3.6** WHEN tüm testler geçtiğinde, THE Hook SHALL yeşil onay mesajı gösterir

---

### Requirement 4: PreCommit Integration

**User Story:** As a developer, I want commit yapmadan önce tüm quality check'lerin çalışmasını, so that broken code commit etmeyeyim.

#### Acceptance Criteria

1. **REQ-4.1** WHEN git commit yapıldığında, THE PreCommit Hook SHALL .pre-commit-config.yaml'ı okur
2. **REQ-4.2** WHEN hook'lar çalıştığında, THE Hook SHALL ruff, mypy, pytest'i sırayla çalıştırır
3. **REQ-4.3** WHEN herhangi bir hook başarısız olduğunda, THE Hook SHALL commit'i engeller
4. **REQ-4.4** WHEN tüm hook'lar geçtiğinde, THE Hook SHALL commit'e izin verir
5. **REQ-4.5** WHEN hook bypass gerektiğinde, THE Hook SHALL --no-verify flag'ini destekler
6. **REQ-4.6** WHEN hook execution time loglandığında, THE Hook SHALL her hook'un süresini raporlar

---

### Requirement 5: Black Formatting Hook

**User Story:** As a developer, I want kodun otomatik formatlanmasını, so that formatting tartışmaları olmasın.

#### Acceptance Criteria

1. **REQ-5.1** WHEN Python dosyası kaydedildiğinde, THE PostToolUse Hook SHALL black formatter çalıştırır
2. **REQ-5.2** WHEN formatting yapıldığında, THE Hook SHALL line length 88 (Black default) kullanır
3. **REQ-5.3** WHEN dosya formatlandığında, THE Hook SHALL değişiklikleri otomatik kaydeder
4. **REQ-5.4** WHEN formatting conflict olduğunda, THE Hook SHALL ruff ile uyumlu çalışır
5. **REQ-5.5** WHEN check-only mode aktif olduğunda, THE Hook SHALL sadece kontrol eder, değiştirmez
6. **REQ-5.6** WHEN formatting başarılı olduğunda, THE Hook SHALL "Formatted X files" mesajı gösterir

---

### Requirement 6: Import Sorting Hook (isort)

**User Story:** As a developer, I want import'ların otomatik sıralanmasını, so that import düzeni tutarlı olsun.

#### Acceptance Criteria

1. **REQ-6.1** WHEN Python dosyası kaydedildiğinde, THE PostToolUse Hook SHALL isort çalıştırır
2. **REQ-6.2** WHEN import sıralama yapıldığında, THE Hook SHALL standard library → third-party → local sıralaması uygular
3. **REQ-6.3** WHEN Black ile uyumluluk sağlandığında, THE Hook SHALL --profile black kullanır
4. **REQ-6.4** WHEN import gruplaması yapıldığında, THE Hook SHALL boş satırlarla ayırır
5. **REQ-6.5** WHEN unused import tespit edildiğinde, THE Hook SHALL uyarı verir (ama silmez)
6. **REQ-6.6** WHEN import sıralaması değiştiğinde, THE Hook SHALL değişiklikleri otomatik kaydeder

---

### Requirement 7: Docstring Validation Hook

**User Story:** As a tech lead, I want tüm public fonksiyonların docstring'e sahip olmasını, so that kod dokümante edilsin.

#### Acceptance Criteria

1. **REQ-7.1** WHEN Python dosyası analiz edildiğinde, THE Hook SHALL tüm public fonksiyonları tarar
2. **REQ-7.2** WHEN docstring eksik olduğunda, THE Hook SHALL fonksiyon adı ve satır numarası ile uyarı verir
3. **REQ-7.3** WHEN docstring formatı kontrol edildiğinde, THE Hook SHALL Google style docstring bekler
4. **REQ-7.4** WHEN docstring parametreleri kontrol edildiğinde, THE Hook SHALL tüm parametrelerin dokümante edildiğini doğrular
5. **REQ-7.5** WHEN return type dokümante edilmediğinde, THE Hook SHALL uyarı verir
6. **REQ-7.6** WHEN docstring coverage hesaplandığında, THE Hook SHALL coverage yüzdesini raporlar

---

### Requirement 8: Performance ve Caching

**User Story:** As a developer, I want hook'ların hızlı çalışmasını, so that development akışım yavaşlamasın.

#### Acceptance Criteria

1. **REQ-8.1** WHEN hook çalıştığında, THE System SHALL sadece değişen dosyaları kontrol eder
2. **REQ-8.2** WHEN cache kullanıldığında, THE System SHALL .ruff_cache ve .mypy_cache dizinlerini kullanır
3. **REQ-8.3** WHEN paralel çalıştırma yapıldığında, THE System SHALL ruff, mypy, pytest'i paralel çalıştırır
4. **REQ-8.4** WHEN execution time ölçüldüğünde, THE System SHALL her hook'un süresini loglar
5. **REQ-8.5** WHEN timeout uygulandığında, THE System SHALL hook başına maksimum 30 saniye sınırı koyar
6. **REQ-8.6** WHEN hook yavaş olduğunda, THE System SHALL performance uyarısı verir

---

## Bağımlılıklar

- **Ruff**: Linting ve formatting
- **Mypy**: Type checking
- **Pytest**: Testing
- **Black**: Code formatting
- **isort**: Import sorting
- **pre-commit**: Git hook yönetimi
- **pydocstyle**: Docstring validation

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 1 hafta
**Beklenen Kalite Artışı:** %200-300

## Code Quality Hooks Flow

```
1. Developer Kod Yazıyor
   ↓
2. PostToolUse Hook Tetiklendi
   ↓
3. Paralel Quality Checks
   ├─ Ruff Linting
   │  ├─ ruff check --fix
   │  ├─ Auto-fix (if possible)
   │  └─ Exit Code: 0 (OK) / 2 (Error)
   ├─ Mypy Type Checking
   │  ├─ mypy --ignore-missing-imports
   │  ├─ Type Error Detection
   │  └─ Exit Code: 0 (OK) / 2 (Error)
   ├─ Black Formatting
   │  ├─ black .
   │  ├─ Auto-format
   │  └─ Exit Code: 0 (Always)
   ├─ isort Import Sorting
   │  ├─ isort --profile black
   │  ├─ Auto-sort
   │  └─ Exit Code: 0 (Always)
   └─ Pytest Auto-Run
      ├─ pytest -x --tb=short
      ├─ Test Execution
      └─ Exit Code: 0 (Pass) / 2 (Fail)
   ↓
4. Docstring Validation
   ├─ Public Function Scan
   ├─ Google Style Check
   └─ Coverage Report
   ↓
5. Result Aggregation
   ├─ All Checks Passed? → Exit 0 ✓
   └─ Any Check Failed? → Exit 2 ✗
   ↓
6. Feedback to Claude (if Exit 2)
   ├─ Error Details
   ├─ Line Numbers
   └─ Suggested Fixes
   ↓
7. PreCommit Hook (on git commit)
   ├─ Run All Quality Checks
   ├─ Block Commit if Failed
   └─ Allow Commit if Passed
```

## Success Metrics

1. **Linting Error Rate:** < %1
2. **Type Error Rate:** < %2
3. **Test Pass Rate:** >= %98
4. **Docstring Coverage:** >= %90
5. **Hook Execution Time:** < 10 saniye

## .pre-commit-config.yaml Example

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]
  
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile, black]
  
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [-x, --tb=short]
```

