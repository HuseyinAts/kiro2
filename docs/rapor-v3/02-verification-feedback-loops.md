# BÖLÜM 2: Verification Feedback Loops

## 2.1 Tanım ve Kritik Önem

### Boris Cherny'nin Tanımı

Boris Cherny, Claude Code'un yaratıcısı ve Anthropic'te Staff Engineer. Ocak 2026'da Twitter'da paylaştığı thread 7.4 milyon görüntüleme aldı ve Claude Code kullanımının en kapsamlı rehberi olarak kabul ediliyor.

**Orijinal İngilizce alıntı:**
> "Probably the single most important way to get great results from Claude Code - give Claude the ability to verify its work. Having Claude in this feedback loop improves the quality of the final result by 2-3x."

**Türkçe çeviri:**
> "Claude Code'dan harika sonuçlar almanın muhtemelen en önemli yolu - Claude'a çalışmasını doğrulama imkanı vermek. Claude'un bu geri bildirim döngüsüne sahip olması, nihai sonucun kalitesini 2-3 kat artırıyor."

### Neden %200-300 Artış?

Verification olmadan Claude'un davranışı:
1. Kod yazar
2. "Muhtemelen çalışır" varsayımıyla durur
3. Hata varsa kullanıcı geri bildirim verir
4. Düzeltir, tekrar varsayımla durur

Verification ile Claude'un davranışı:
1. Kod yazar
2. Test/lint/typecheck çalıştırır
3. Hatayı görür, kendisi düzeltir
4. Tekrar doğrular
5. Tüm testler geçene kadar iterasyon yapar
6. "Kesinlikle çalışır" durumunda kullanıcıya sunar

**Fark:** İnsan müdahalesi gerektiren döngü sayısı 5-10'dan 1-2'ye düşüyor.

---

## 2.2 Altı Doğrulama Seviyesi

Boris Cherny altı farklı doğrulama yöntemi tanımladı. Bunlar karmaşıklık ve kullanım alanına göre sıralanıyor:

### Seviye 1: Bash Komutu Çalıştırma

**Açıklama:** En basit doğrulama. Claude bir dosya oluşturduğunda veya değiştirdiğinde, sonucu doğrulamak için bash komutu çalıştırır.

**Kullanım senaryoları:**
- Dosya oluşturuldu mu? `ls -la filename`
- Script çalışıyor mu? `python script.py`
- Syntax hatası var mı? `python -m py_compile script.py`
- JSON geçerli mi? `python -c "import json; json.load(open('file.json'))"`

**KIRO2 Uygulaması:**
```bash
# Soru dosyası oluşturulduktan sonra
python -c "
import json
with open('questions/mat_001.json', 'r', encoding='utf-8') as f:
    q = json.load(f)
    assert 'question_text' in q
    assert 'options' in q
    assert len(q['options']) == 5
    assert 'correct_answer' in q
    print('✓ Soru formatı geçerli')
"
```

**Avantajlar:**
- Hızlı (milisaniye)
- Ek araç gerektirmez
- Her ortamda çalışır

**Dezavantajlar:**
- Sadece temel doğrulama
- Mantıksal hataları yakalamaz

---

### Seviye 2: Test Suite Çalıştırma

**Açıklama:** Otomatik test süitleri verification'ın omurgası. pytest, jest, mocha gibi framework'ler Claude'a anında geri bildirim veriyor.

**Desteklenen framework'ler:**
| Dil | Framework | Komut |
|-----|-----------|-------|
| Python | pytest | `python -m pytest` |
| Python | unittest | `python -m unittest discover` |
| JavaScript | Jest | `npm test` |
| JavaScript | Mocha | `npx mocha` |
| TypeScript | Jest | `npx jest` |
| Go | testing | `go test ./...` |
| Rust | cargo test | `cargo test` |

**KIRO2 Uygulaması:**
```python
# tests/test_question_validator.py

import pytest
from question_generator import QuestionGenerator

class TestQuestionGeneration:
    def test_question_has_required_fields(self):
        """Her soru zorunlu alanları içermeli"""
        gen = QuestionGenerator()
        question = gen.generate(topic="limit", difficulty=3)
        
        required_fields = [
            'question_text', 'options', 'correct_answer',
            'difficulty_level', 'topic_tags', 'explanation'
        ]
        
        for field in required_fields:
            assert field in question, f"Eksik alan: {field}"
    
    def test_options_count(self):
        """Her soru 5 seçenek içermeli (A, B, C, D, E)"""
        gen = QuestionGenerator()
        question = gen.generate(topic="türev", difficulty=4)
        
        assert len(question['options']) == 5
        assert all(opt in question['options'] for opt in ['A', 'B', 'C', 'D', 'E'])
    
    def test_correct_answer_in_options(self):
        """Doğru cevap seçenekler arasında olmalı"""
        gen = QuestionGenerator()
        question = gen.generate(topic="integral", difficulty=5)
        
        assert question['correct_answer'] in ['A', 'B', 'C', 'D', 'E']
    
    def test_difficulty_range(self):
        """Zorluk seviyesi 1-5 arasında olmalı"""
        gen = QuestionGenerator()
        question = gen.generate(topic="geometri", difficulty=3)
        
        assert 1 <= question['difficulty_level'] <= 5
    
    def test_turkish_encoding(self):
        """Türkçe karakterler UTF-8 ile doğru kodlanmalı"""
        gen = QuestionGenerator()
        question = gen.generate(topic="türkçe_dilbilgisi", difficulty=2)
        
        turkish_chars = "ğüşıöçĞÜŞİÖÇ"
        text = question['question_text']
        
        # Encoding hatası varsa exception fırlatır
        text.encode('utf-8').decode('utf-8')
```

**Claude'un test çıktısını yorumlaması:**
```
FAILED tests/test_question_validator.py::TestQuestionGeneration::test_options_count
AssertionError: assert 4 == 5

Claude'un yorumu: "Soru üretici sadece 4 seçenek üretiyor. 
E seçeneğini de eklemem gerekiyor."
```

---

### Seviye 3: Linter ve Type Checker

**Açıklama:** Statik analiz araçları runtime'dan önce hataları yakalıyor.

**Python araçları:**

| Araç | Amaç | Komut |
|------|------|-------|
| Ruff | Linting + Formatting | `ruff check . && ruff format .` |
| mypy | Type checking | `mypy --strict .` |
| pylint | Detaylı linting | `pylint src/` |
| black | Formatting | `black .` |
| isort | Import sorting | `isort .` |

**JavaScript/TypeScript araçları:**

| Araç | Amaç | Komut |
|------|------|-------|
| ESLint | Linting | `npx eslint .` |
| Prettier | Formatting | `npx prettier --write .` |
| TypeScript | Type checking | `npx tsc --noEmit` |

**KIRO2 İçin Önerilen Kombinasyon:**
```bash
# Tek komutla tüm kontroller
ruff check . --fix && \
ruff format . && \
mypy --strict src/ && \
python -m pytest tests/ -v
```

**Ruff Konfigürasyonu (`pyproject.toml`):**
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = ["E501"]  # line too long (ruff format handles this)

[tool.ruff.lint.isort]
known-first-party = ["kiro2", "orchestrator"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

---

### Seviye 4: Chrome Extension ile Tarayıcı Testi

**Açıklama:** Boris Cherny'nin kendi kullandığı yöntem. Claude Code'un Chrome extension'ı tarayıcıyı kontrol edebiliyor.

**Boris'in açıklaması:**
> "Claude, claude.ai/code'a yaptığım her değişikliği Chrome extension kullanarak test ediyor. Tarayıcı açıyor, arayüzü test ediyor ve kod çalışıp kullanıcı deneyimi iyi hissettirene kadar iterasyonlara devam ediyor."

**Teknik detaylar:**
- Claude Code Chrome Extension gerekli
- Extension Claude'a tarayıcı kontrolü veriyor
- Screenshot alma, element tıklama, form doldurma
- Visual regression testing

**Kullanım senaryoları:**
- Frontend değişikliklerinin görsel doğrulaması
- Form submission testleri
- Navigation flow testleri
- Responsive design kontrolü

**KIRO2 Uygulaması:**
```javascript
// Chrome extension ile öğrenci arayüzü testi
const testStudentDashboard = async () => {
    // Dashboard'a git
    await page.goto('http://localhost:3000/student/dashboard');
    
    // Soru kartının görünür olduğunu doğrula
    const questionCard = await page.$('.question-card');
    assert(questionCard !== null, 'Soru kartı görünmeli');
    
    // Seçenek butonlarını kontrol et
    const options = await page.$$('.option-button');
    assert(options.length === 5, '5 seçenek butonu olmalı');
    
    // Screenshot al ve karşılaştır
    await page.screenshot({ path: 'test-results/dashboard.png' });
};
```

---

### Seviye 5: Puppeteer/Playwright Otomasyonu

**Açıklama:** Daha karmaşık UI testleri için headless browser otomasyonu.

**Puppeteer vs Playwright:**

| Özellik | Puppeteer | Playwright |
|---------|-----------|------------|
| Tarayıcı desteği | Chrome, Firefox | Chrome, Firefox, Safari, Edge |
| Dil | JavaScript/TypeScript | JS/TS, Python, C#, Java |
| Auto-wait | Manuel | Otomatik |
| Network interception | Var | Daha gelişmiş |
| Paralel çalışma | Manuel | Built-in |

**KIRO2 için Playwright Python örneği:**
```python
# tests/e2e/test_question_flow.py

from playwright.sync_api import sync_playwright, expect

def test_complete_question_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Login
        page.goto("http://localhost:3000/login")
        page.fill("#email", "test@kiro2.com")
        page.fill("#password", "testpass123")
        page.click("button[type='submit']")
        
        # 2. Dashboard'a yönlendirme bekle
        expect(page).to_have_url("http://localhost:3000/dashboard")
        
        # 3. Soru çözmeye başla
        page.click("text=Deneme Sınavı Başlat")
        
        # 4. Soru yüklenene kadar bekle
        expect(page.locator(".question-text")).to_be_visible()
        
        # 5. Bir seçenek seç
        page.click("button:has-text('A')")
        
        # 6. Sonraki soruya geç
        page.click("button:has-text('Sonraki')")
        
        # 7. İkinci soru yüklendiğini doğrula
        expect(page.locator(".question-number")).to_have_text("Soru 2/40")
        
        browser.close()
```

---

### Seviye 6: Background Agent ile Doğrulama

**Açıklama:** En gelişmiş yöntem. Ana Claude görevi tamamladığında, ayrı bir background agent bağımsız doğrulama yapıyor.

**Boris'in önerisi:**
> "Claude'a tamamlandığında arka plan ajanıyla doğrulama yapması söyle"

**Çalışma prensibi:**
1. Ana Claude (Primary) kodu yazar
2. Primary tamamlandığını bildirir
3. Background Agent (Verifier) devreye girer
4. Verifier farklı bir perspektiften kodu inceler
5. Sorun bulursa Primary'ye geri bildirim
6. Primary düzeltir, döngü tekrarlar

**KIRO2 Subagent yapısı:**
```yaml
# .claude/agents/question-verifier.md
---
name: question-verifier
description: "Üretilen soruları bağımsız olarak doğrular. MUST BE USED after question generation."
model: sonnet
tools:
  - Read
  - Grep
  - Bash
permissionMode: plan
maxTurns: 20
---

# Soru Doğrulayıcı Agent

## Görev
Matematik-subagent tarafından üretilen soruları bağımsız olarak doğrula.

## Kontrol Listesi

### 1. Format Kontrolü
- [ ] JSON schema'ya uygun mu?
- [ ] Tüm zorunlu alanlar var mı?
- [ ] UTF-8 encoding doğru mu?

### 2. İçerik Kontrolü
- [ ] Soru metni anlaşılır mı?
- [ ] Matematiksel notation doğru mu?
- [ ] Şıklar mantıklı mı?

### 3. Pedagojik Kontrol
- [ ] Zorluk seviyesi doğru mu?
- [ ] Müfredata uygun mu?
- [ ] Çeldirici kalitesi yeterli mi?

### 4. Duplicate Kontrolü
- [ ] Soru bankasında benzer soru var mı?
- [ ] Aynı sorunun farklı formatı mı?

## Çıktı Formatı
```json
{
  "status": "PASS" | "FAIL",
  "checks": {
    "format": true,
    "content": true,
    "pedagogy": false,
    "duplicate": true
  },
  "issues": [
    {
      "check": "pedagogy",
      "message": "Zorluk seviyesi 3 olarak işaretlenmiş ama soru seviye 5 zorluğunda",
      "suggestion": "difficulty_level: 5 olarak güncelle"
    }
  ]
}
```
```

---

## 2.3 Ralph-Wiggum Plugin

### Plugin Nedir?

Ralph-Wiggum, Claude Code için geliştirilmiş bir loop detection ve auto-continuation plugin'i. Adını The Simpsons karakterinden alıyor.

**GitHub:** `ralph-wiggum-claude-plugin` (community maintained)

### Çözdüğü Problemler

1. **No-progress detection:** Claude aynı hatayı tekrar tekrar yapıyorsa tespit eder
2. **Infinite loop prevention:** Belirlenen turn limitine ulaşılınca uyarı verir
3. **Auto-continuation:** Uzun görevlerde otomatik devam etme
4. **Completion promise:** Binary success criteria tanımlama

### Kurulum

```bash
# npm ile kurulum
npm install -g ralph-wiggum-claude-plugin

# Veya manuel
git clone https://github.com/community/ralph-wiggum-claude-plugin
cd ralph-wiggum-claude-plugin
npm install && npm link
```

### Konfigürasyon

`.claude/plugins/ralph-wiggum.json`:
```json
{
  "enabled": true,
  "maxTurns": 50,
  "noProgressThreshold": 3,
  "completionPromise": {
    "enabled": true,
    "criteria": [
      "All tests pass",
      "No lint errors",
      "Type check successful"
    ]
  },
  "autoRetry": {
    "enabled": true,
    "maxRetries": 3,
    "backoffMs": 1000
  },
  "alerts": {
    "onNoProgress": "notify",
    "onMaxTurns": "stop",
    "onCompletion": "celebrate"
  }
}
```

### Kullanım Senaryoları

**Senaryo 1 - Kompleks Refactoring (30+ dakika):**
```
Claude: "Tüm repository'yi Python 3.11+ type hints ile güncelleyeceğim."

Ralph-Wiggum izliyor:
- Turn 15: İlerleme var, devam
- Turn 25: İlerleme var, devam
- Turn 35: Aynı dosyada takılı, uyarı
- Turn 36: Farklı strateji önerisi
- Turn 45: Tamamlandı
```

**Senaryo 2 - Test Suite Geçirme:**
```
Claude: "Tüm testleri geçireceğim."

Completion Promise:
- pytest exit code == 0 ✓
- Coverage > 80% ✓
- No skipped tests ✓

Ralph-Wiggum: "Completion criteria karşılandı. 🎉"
```

---

## 2.4 KIRO2 Verification Pipeline

### Pipeline Mimarisi

```
┌─────────────────────────────────────────────────────────────────┐
│                    SORU ÜRETİM PIPELINE'I                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ Generate │───▶│ Validate │───▶│ Verify   │───▶│ Store    │   │
│  │ Question │    │ Schema   │    │ Content  │    │ to DB    │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│       │               │               │               │          │
│       ▼               ▼               ▼               ▼          │
│  matematik-      PreToolUse     PostToolUse     PostgreSQL      │
│  subagent        Hook           Hook            (port 5434)     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    DOĞRULAMA KATMANLARI                   │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 1. Syntax Validation      - JSON/YAML format             │   │
│  │ 2. Schema Validation      - Zorunlu alanlar              │   │
│  │ 3. Content Validation     - Türkçe NLP                   │   │
│  │ 4. Pedagogical Validation - Müfredat uyumu               │   │
│  │ 5. Duplicate Detection    - Semantic similarity          │   │
│  │ 6. Human Sampling         - %5 rastgele inceleme         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Adım 1: Syntax Validation

**Amaç:** Üretilen sorunun JSON/YAML formatının geçerli olduğunu doğrula.

```python
# orchestrator/validators/syntax_validator.py

import json
from typing import Dict, Any, Tuple

class SyntaxValidator:
    """Soru dosyasının syntax'ını doğrular."""
    
    def validate(self, content: str) -> Tuple[bool, str]:
        """
        Args:
            content: Soru içeriği (JSON string)
        
        Returns:
            (is_valid, error_message)
        """
        try:
            data = json.loads(content)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"JSON parse hatası: {e.msg} (satır {e.lineno}, kolon {e.colno})"
    
    def validate_file(self, filepath: str) -> Tuple[bool, str]:
        """Dosyadan doğrulama."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.validate(content)
        except FileNotFoundError:
            return False, f"Dosya bulunamadı: {filepath}"
        except UnicodeDecodeError:
            return False, f"Encoding hatası: Dosya UTF-8 değil"
```

### Adım 2: Schema Validation

**Amaç:** Zorunlu alanların varlığını ve tiplerini doğrula.

```python
# orchestrator/validators/schema_validator.py

from typing import Dict, Any, Tuple, List
from dataclasses import dataclass

@dataclass
class SchemaField:
    name: str
    type: type
    required: bool = True
    allowed_values: List[Any] = None

class SchemaValidator:
    """Soru schema'sını doğrular."""
    
    QUESTION_SCHEMA = [
        SchemaField("question_id", str, required=True),
        SchemaField("question_text", str, required=True),
        SchemaField("options", dict, required=True),
        SchemaField("correct_answer", str, required=True, 
                   allowed_values=["A", "B", "C", "D", "E"]),
        SchemaField("difficulty_level", int, required=True,
                   allowed_values=[1, 2, 3, 4, 5]),
        SchemaField("topic_tags", list, required=True),
        SchemaField("subtopic", str, required=True),
        SchemaField("explanation", str, required=True),
        SchemaField("solution_steps", list, required=False),
        SchemaField("hints", list, required=False),
        SchemaField("estimated_time_seconds", int, required=False),
        SchemaField("source", str, required=False),
    ]
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Args:
            data: Soru verisi (dict)
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        for field in self.QUESTION_SCHEMA:
            # Required field kontrolü
            if field.required and field.name not in data:
                errors.append(f"Zorunlu alan eksik: {field.name}")
                continue
            
            if field.name not in data:
                continue
            
            value = data[field.name]
            
            # Tip kontrolü
            if not isinstance(value, field.type):
                errors.append(
                    f"Tip hatası: {field.name} {field.type.__name__} olmalı, "
                    f"{type(value).__name__} verildi"
                )
                continue
            
            # Allowed values kontrolü
            if field.allowed_values and value not in field.allowed_values:
                errors.append(
                    f"Geçersiz değer: {field.name}={value}, "
                    f"izin verilenler: {field.allowed_values}"
                )
        
        # Options kontrolü (özel)
        if "options" in data:
            options = data["options"]
            required_options = ["A", "B", "C", "D", "E"]
            for opt in required_options:
                if opt not in options:
                    errors.append(f"Eksik seçenek: {opt}")
        
        return len(errors) == 0, errors
```

### Adım 3: Content Validation

**Amaç:** Türkçe dil kuralları ve içerik kalitesini doğrula.

```python
# orchestrator/validators/content_validator.py

import re
from typing import Dict, Any, Tuple, List

class ContentValidator:
    """İçerik kalitesini doğrular."""
    
    # Türkçe karakterler
    TURKISH_CHARS = "ğüşıöçĞÜŞİÖÇ"
    
    # Minimum uzunluklar
    MIN_QUESTION_LENGTH = 20
    MIN_OPTION_LENGTH = 1
    MIN_EXPLANATION_LENGTH = 50
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        # Soru metni kontrolü
        question_text = data.get("question_text", "")
        if len(question_text) < self.MIN_QUESTION_LENGTH:
            errors.append(
                f"Soru metni çok kısa: {len(question_text)} karakter "
                f"(minimum {self.MIN_QUESTION_LENGTH})"
            )
        
        # Türkçe karakter encoding kontrolü
        try:
            question_text.encode('utf-8').decode('utf-8')
        except UnicodeError:
            errors.append("Soru metninde encoding hatası")
        
        # Seçenekler kontrolü
        options = data.get("options", {})
        for key, value in options.items():
            if len(str(value)) < self.MIN_OPTION_LENGTH:
                errors.append(f"Seçenek {key} boş veya çok kısa")
        
        # Seçenek dengeliliği (uzunluk benzerliği)
        option_lengths = [len(str(v)) for v in options.values()]
        if option_lengths:
            avg_length = sum(option_lengths) / len(option_lengths)
            for i, (key, length) in enumerate(zip(options.keys(), option_lengths)):
                if length < avg_length * 0.3 or length > avg_length * 3:
                    errors.append(
                        f"Seçenek {key} diğerlerinden çok farklı uzunlukta "
                        f"({length} vs ortalama {avg_length:.0f})"
                    )
        
        # Açıklama kontrolü
        explanation = data.get("explanation", "")
        if len(explanation) < self.MIN_EXPLANATION_LENGTH:
            errors.append(
                f"Açıklama çok kısa: {len(explanation)} karakter "
                f"(minimum {self.MIN_EXPLANATION_LENGTH})"
            )
        
        # Matematiksel notation kontrolü
        math_patterns = [
            (r'\$\$.*?\$\$', 'LaTeX display math'),
            (r'\$.*?\$', 'LaTeX inline math'),
            (r'\\frac\{.*?\}\{.*?\}', 'LaTeX fraction'),
            (r'\\sqrt\{.*?\}', 'LaTeX square root'),
        ]
        
        has_math = any(
            re.search(pattern, question_text) 
            for pattern, _ in math_patterns
        )
        
        # Matematik sorusu ise math notation olmalı
        topic_tags = data.get("topic_tags", [])
        math_topics = ["limit", "türev", "integral", "fonksiyon", "denklem"]
        is_math_question = any(
            tag.lower() in math_topics 
            for tag in topic_tags
        )
        
        if is_math_question and not has_math:
            errors.append(
                "Matematik sorusu matematiksel notation içermiyor. "
                "LaTeX formatı kullanın: $...$ veya $$...$$"
            )
        
        return len(errors) == 0, errors
```

### Adım 4: Pedagogical Validation

**Amaç:** Eğitimsel kalite ve müfredat uyumunu doğrula.

```python
# orchestrator/validators/pedagogical_validator.py

from typing import Dict, Any, Tuple, List
from enum import Enum

class ExamType(Enum):
    TYT = "TYT"
    AYT = "AYT"

class PedagogicalValidator:
    """Pedagojik kaliteyi doğrular."""
    
    # YKS Müfredat Haritası
    CURRICULUM = {
        ExamType.TYT: {
            "matematik": [
                "temel_kavramlar", "sayilar", "carpanlar_katlar",
                "uslu_koklu_sayilar", "esitsizlikler", "mutlak_deger",
                "polinomlar", "problemler", "mantik", "kumeler",
                "fonksiyonlar_temel", "permutasyon_kombinasyon",
                "olasilik", "istatistik_temel", "geometri_temel"
            ],
            "turkce": [
                "sozcukte_anlam", "cumle_anlam", "paragraf",
                "anlatim_bozukluklari", "noktalama", "yazim_kurallari"
            ]
        },
        ExamType.AYT: {
            "matematik": [
                "fonksiyonlar_ileri", "trigonometri", "logaritma",
                "diziler", "limit", "turev", "integral",
                "analitik_geometri", "uzay_geometri"
            ],
            "fizik": [
                "kuvvet_hareket", "enerji", "elektrik", "manyetizma",
                "optik", "dalgalar", "atom_fizigi"
            ]
        }
    }
    
    # Zorluk seviyesi - Konu eşleştirmesi
    DIFFICULTY_TOPICS = {
        1: ["temel_kavramlar", "sayilar"],  # Çok kolay
        2: ["carpanlar_katlar", "esitsizlikler"],  # Kolay
        3: ["polinomlar", "fonksiyonlar_temel", "olasilik"],  # Orta
        4: ["trigonometri", "limit", "turev"],  # Zor
        5: ["integral", "analitik_geometri", "uzay_geometri"]  # Çok zor
    }
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        warnings = []
        
        topic_tags = data.get("topic_tags", [])
        difficulty = data.get("difficulty_level", 3)
        subtopic = data.get("subtopic", "")
        
        # 1. Müfredat uyumu kontrolü
        is_in_curriculum = False
        for exam_type in ExamType:
            for subject, topics in self.CURRICULUM.get(exam_type, {}).items():
                if subtopic.lower() in [t.lower() for t in topics]:
                    is_in_curriculum = True
                    break
        
        if not is_in_curriculum:
            errors.append(
                f"Konu müfredatta bulunamadı: {subtopic}. "
                f"YKS müfredatına uygun bir konu seçin."
            )
        
        # 2. Zorluk-konu tutarlılığı
        expected_difficulty_range = self._get_expected_difficulty(subtopic)
        if expected_difficulty_range:
            min_d, max_d = expected_difficulty_range
            if difficulty < min_d or difficulty > max_d:
                errors.append(
                    f"Zorluk seviyesi tutarsız: {subtopic} için "
                    f"beklenen {min_d}-{max_d}, verilen {difficulty}"
                )
        
        # 3. Çeldirici kalitesi kontrolü
        options = data.get("options", {})
        correct = data.get("correct_answer", "")
        
        if self._check_obvious_distractors(options, correct):
            errors.append(
                "Çeldirici kalitesi düşük: Yanlış seçenekler çok bariz. "
                "Daha makul çeldiriciler ekleyin."
            )
        
        # 4. Bloom taksonomisi kontrolü
        question_text = data.get("question_text", "")
        bloom_level = self._estimate_bloom_level(question_text)
        
        if difficulty >= 4 and bloom_level < 3:
            warnings.append(
                f"Yüksek zorluk ama düşük Bloom seviyesi: "
                f"Zorluk {difficulty}, Bloom tahmini {bloom_level}. "
                f"Analiz/sentez gerektiren soru düşünün."
            )
        
        return len(errors) == 0, errors
    
    def _get_expected_difficulty(self, subtopic: str) -> Tuple[int, int]:
        """Konu için beklenen zorluk aralığını döndür."""
        subtopic_lower = subtopic.lower()
        
        for difficulty, topics in self.DIFFICULTY_TOPICS.items():
            if subtopic_lower in [t.lower() for t in topics]:
                # ±1 tolerans
                return max(1, difficulty - 1), min(5, difficulty + 1)
        
        return None  # Bilinmeyen konu
    
    def _check_obvious_distractors(
        self, 
        options: Dict[str, str], 
        correct: str
    ) -> bool:
        """Çeldiricilerin çok bariz olup olmadığını kontrol et."""
        correct_option = options.get(correct, "")
        
        for key, value in options.items():
            if key == correct:
                continue
            
            # Çok kısa seçenek
            if len(str(value)) < len(str(correct_option)) * 0.2:
                return True
            
            # "Hiçbiri" benzeri seçenekler
            obvious_patterns = [
                "hiçbiri", "hepsi", "yok", "belirlenemez",
                "none", "all", "cannot"
            ]
            if any(p in str(value).lower() for p in obvious_patterns):
                if key != correct:  # Eğer doğru cevap değilse
                    return True
        
        return False
    
    def _estimate_bloom_level(self, question_text: str) -> int:
        """Bloom taksonomisi seviyesini tahmin et (1-6)."""
        question_lower = question_text.lower()
        
        # Seviye 6: Yaratma
        if any(w in question_lower for w in ["tasarla", "oluştur", "yarat"]):
            return 6
        
        # Seviye 5: Değerlendirme
        if any(w in question_lower for w in ["değerlendir", "karşılaştır", "eleştir"]):
            return 5
        
        # Seviye 4: Analiz
        if any(w in question_lower for w in ["analiz", "neden", "ilişki", "fark"]):
            return 4
        
        # Seviye 3: Uygulama
        if any(w in question_lower for w in ["hesapla", "çöz", "uygula", "bul"]):
            return 3
        
        # Seviye 2: Anlama
        if any(w in question_lower for w in ["açıkla", "özetle", "yorumla"]):
            return 2
        
        # Seviye 1: Hatırlama
        return 1
```

### Adım 5: Duplicate Detection

**Amaç:** Soru bankasında benzer soruların olup olmadığını kontrol et.

```python
# orchestrator/validators/duplicate_detector.py

from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

class DuplicateDetector:
    """Semantic similarity ile duplicate tespiti."""
    
    def __init__(
        self, 
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        similarity_threshold: float = 0.85
    ):
        self.model = SentenceTransformer(model_name)
        self.threshold = similarity_threshold
        self.question_embeddings: Dict[str, np.ndarray] = {}
    
    def load_question_bank(self, questions: List[Dict[str, Any]]):
        """Mevcut soru bankasını yükle ve embedding'leri hesapla."""
        for q in questions:
            q_id = q.get("question_id", "")
            q_text = q.get("question_text", "")
            
            if q_id and q_text:
                embedding = self.model.encode(q_text)
                self.question_embeddings[q_id] = embedding
    
    def check_duplicate(
        self, 
        new_question: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], float]:
        """
        Yeni sorunun duplicate olup olmadığını kontrol et.
        
        Returns:
            (is_duplicate, similar_question_id, similarity_score)
        """
        new_text = new_question.get("question_text", "")
        if not new_text:
            return False, None, 0.0
        
        new_embedding = self.model.encode(new_text)
        
        max_similarity = 0.0
        most_similar_id = None
        
        for q_id, embedding in self.question_embeddings.items():
            similarity = self._cosine_similarity(new_embedding, embedding)
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_id = q_id
        
        is_duplicate = max_similarity >= self.threshold
        
        return is_duplicate, most_similar_id, max_similarity
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """İki vektör arasındaki cosine similarity."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validator interface'i için wrapper."""
        is_dup, similar_id, score = self.check_duplicate(data)
        
        if is_dup:
            return False, [
                f"Duplicate tespit edildi: {similar_id} ile %{score*100:.1f} benzerlik. "
                f"Threshold: %{self.threshold*100:.0f}"
            ]
        
        return True, []
```

### Adım 6: Human Sampling

**Amaç:** Otomatik doğrulamayı geçen soruların %5'ini insan incelemesine al.

```python
# orchestrator/validators/human_sampling.py

import random
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum

class ReviewStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

class HumanSampling:
    """İnsan incelemesi için örnekleme."""
    
    def __init__(self, sample_rate: float = 0.05):
        """
        Args:
            sample_rate: İncelemeye alınacak soru oranı (0.05 = %5)
        """
        self.sample_rate = sample_rate
        self.review_queue: List[Dict[str, Any]] = []
    
    def should_sample(self) -> bool:
        """Bu soru incelemeye alınmalı mı?"""
        return random.random() < self.sample_rate
    
    def add_to_review_queue(self, question: Dict[str, Any]) -> str:
        """Soruyu inceleme kuyruğuna ekle."""
        review_item = {
            "question": question,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": ReviewStatus.PENDING.value,
            "reviewer": None,
            "review_notes": None,
            "reviewed_at": None
        }
        
        self.review_queue.append(review_item)
        return question.get("question_id", "unknown")
    
    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """Bekleyen incelemeleri getir."""
        return [
            item for item in self.review_queue 
            if item["status"] == ReviewStatus.PENDING.value
        ]
    
    def submit_review(
        self, 
        question_id: str, 
        status: ReviewStatus,
        reviewer: str,
        notes: str = ""
    ):
        """İnceleme sonucunu kaydet."""
        for item in self.review_queue:
            if item["question"].get("question_id") == question_id:
                item["status"] = status.value
                item["reviewer"] = reviewer
                item["review_notes"] = notes
                item["reviewed_at"] = datetime.utcnow().isoformat()
                break
    
    def get_review_stats(self) -> Dict[str, Any]:
        """İnceleme istatistiklerini getir."""
        total = len(self.review_queue)
        
        stats = {
            "total": total,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "needs_revision": 0,
            "approval_rate": 0.0
        }
        
        for item in self.review_queue:
            status = item["status"]
            if status in stats:
                stats[status] += 1
        
        reviewed = stats["approved"] + stats["rejected"] + stats["needs_revision"]
        if reviewed > 0:
            stats["approval_rate"] = stats["approved"] / reviewed
        
        return stats
```

---

## 2.5 PostToolUse Hook Konfigürasyonu

### Hook Dosyası

```bash
#!/bin/bash
# .claude/hooks/verify-question.sh
# PostToolUse hook for question verification

set -e

# Environment variables from Claude Code
FILE_PATH="$CC_FILE_PATH"
TOOL_NAME="$CC_TOOL_NAME"

# Sadece Write tool için çalış
if [[ "$TOOL_NAME" != "Write" ]]; then
    exit 0
fi

# Sadece soru dosyaları için çalış
if [[ ! "$FILE_PATH" =~ .*questions.*\.json$ ]]; then
    exit 0
fi

echo "🔍 Soru doğrulama başlıyor: $FILE_PATH"

# Python validation script çalıştır
python3 -c "
import sys
import json

sys.path.insert(0, '.')
from orchestrator.validators.syntax_validator import SyntaxValidator
from orchestrator.validators.schema_validator import SchemaValidator
from orchestrator.validators.content_validator import ContentValidator
from orchestrator.validators.pedagogical_validator import PedagogicalValidator

filepath = '$FILE_PATH'

# Dosyayı oku
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Syntax
syntax_val = SyntaxValidator()
is_valid, error = syntax_val.validate(content)
if not is_valid:
    print(f'❌ Syntax hatası: {error}', file=sys.stderr)
    sys.exit(2)
print('✓ Syntax OK')

# JSON parse
data = json.loads(content)

# 2. Schema
schema_val = SchemaValidator()
is_valid, errors = schema_val.validate(data)
if not is_valid:
    for e in errors:
        print(f'❌ Schema hatası: {e}', file=sys.stderr)
    sys.exit(2)
print('✓ Schema OK')

# 3. Content
content_val = ContentValidator()
is_valid, errors = content_val.validate(data)
if not is_valid:
    for e in errors:
        print(f'❌ İçerik hatası: {e}', file=sys.stderr)
    sys.exit(2)
print('✓ İçerik OK')

# 4. Pedagogy
pedagogy_val = PedagogicalValidator()
is_valid, errors = pedagogy_val.validate(data)
if not is_valid:
    for e in errors:
        print(f'❌ Pedagojik hata: {e}', file=sys.stderr)
    sys.exit(2)
print('✓ Pedagoji OK')

print('✅ Tüm doğrulamalar geçti!')
"

# Python script başarılı olduysa
if [ $? -eq 0 ]; then
    echo "✅ Soru doğrulandı: $FILE_PATH"
    exit 0
else
    echo "❌ Soru doğrulanamadı" >&2
    exit 2
fi
```

### Settings.json Konfigürasyonu

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": ".claude/hooks/verify-question.sh",
        "timeout": 30000
      },
      {
        "matcher": "Write|Edit",
        "command": "ruff format $CC_FILE_PATH && ruff check $CC_FILE_PATH --fix",
        "timeout": 10000
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": ".claude/hooks/validate-bash.sh",
        "timeout": 5000
      }
    ]
  }
}
```

---

## 2.6 Özet: Verification Best Practices

### Checklist

- [ ] Her soru üretiminde 5 validation adımı çalışıyor
- [ ] PostToolUse hook konfigüre edildi
- [ ] Validation hataları Claude'a exit 2 ile geri bildiriliyor
- [ ] Human sampling %5 oranında aktif
- [ ] Duplicate detection semantic similarity ile çalışıyor
- [ ] Test coverage %80+ hedeflendi
- [ ] Ralph-Wiggum plugin kuruldu (opsiyonel)

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Syntax validation pass rate | %100 |
| Schema validation pass rate | %100 |
| Content validation pass rate | %95+ |
| Pedagogical validation pass rate | %90+ |
| Duplicate detection accuracy | %95+ |
| Human review approval rate | %90+ |

---

**Önceki Bölüm:** [01 - Giriş ve Özet](./01-giris-ve-ozet.md)  
**Sonraki Bölüm:** [03 - Plan Mode](./03-plan-mode.md)
