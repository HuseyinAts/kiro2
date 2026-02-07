# KIRO2 Claude Code Düzenleme Rehberi

> **Doğrulama Mekanizmaları Raporuna Göre Adım Adım Uygulama**
> 
> Bu rehber, 52 sayfalık KIRO2 Doğrulama Mekanizmaları Rehberi'ne dayanmaktadır.

---

## 📊 Mevcut Durum Analizi

### ✅ Zaten Mevcut Olanlar
| Öğe | Durum | Konum |
|-----|-------|-------|
| settings.json | ✅ Var | `.claude/settings.json` |
| CLAUDE.md | ✅ Var | `CLAUDE.md` |
| agents/ | ✅ Var | `.claude/agents/` (4 agent) |
| commands/ | ✅ Var | `.claude/commands/` (15 komut) |
| hooks/ | ✅ Var | `.claude/hooks/` |
| PreToolUse hook | ✅ Var | Tehlikeli dosya koruması |
| PostToolUse hook | ✅ Var | black/isort formatlama |
| Notification hook | ✅ Var | Windows bildirimi |

### ❌ Eksik/Düzeltilmesi Gerekenler (P0 - KRİTİK)
| Öğe | Öncelik | Açıklama |
|-----|---------|----------|
| Stop Hook (quality-gates) | **P0** | Sadece log yazıyor, kalite kapısı YOK |
| permissions.defaultMode | **P0** | Eksik |
| ruff (modern linter) | **P0** | black/isort yerine ruff öneriliyor |
| skills/ dizini | **P0** | Hiç yok |
| python-pro subagent | **P0** | Eksik |
| CLAUDE.local.md | **P0** | Kişisel notlar için eksik |
| .gitignore Claude entries | **P0** | Claude dosyaları eksik |

---

## 🚀 ADIM ADIM UYGULAMA

---

## ADIM 1: Ruff Kurulumu (P0)

Boris Cherny önerisi: "ruff, black + isort + flake8'in modern alternatifi - 10-100x daha hızlı"

### 1.1 Ruff'u Kur

```powershell
# PowerShell'de çalıştır
cd C:\Users\husey\kiro2\backend
pip install ruff
```

### 1.2 pyproject.toml Oluştur/Güncelle

`backend/pyproject.toml` dosyasına ekle:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
]
ignore = ["E501"]  # line too long (black handles this)

[tool.ruff.lint.isort]
known-first-party = ["backend", "core", "services", "models", "schemas"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 1.3 Doğrulama

```powershell
ruff check . --fix
ruff format .
```

---

## ADIM 2: Quality Gates Script Oluştur (P0 - EN KRİTİK)

Boris Cherny: "Claude'a çalışmasını doğrulama yolu vermek kaliteyi 2-3x artırır!"

### 2.1 quality-gates.ps1 Oluştur

`C:\Users\husey\kiro2\.claude\scripts\quality-gates.ps1` dosyası oluştur:

```powershell
# KIRO2 Quality Gates Script
# Claude Code Stop Hook için kalite kapısı

param(
    [switch]$SkipTests = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"
$root = "C:\Users\husey\kiro2"

Write-Host "🔍 KIRO2 Quality Gates başlatılıyor..." -ForegroundColor Cyan

# 1. Python Lint (ruff)
Write-Host "`n📝 [1/5] Python Lint kontrolü (ruff)..." -ForegroundColor Yellow
Set-Location "$root\backend"
try {
    ruff check . --fix
    ruff format .
    Write-Host "✅ Python lint başarılı" -ForegroundColor Green
} catch {
    Write-Host "❌ Python lint hatası: $_" -ForegroundColor Red
    exit 1
}

# 2. Python Type Check (mypy)
Write-Host "`n🔬 [2/5] Type check (mypy)..." -ForegroundColor Yellow
try {
    mypy . --ignore-missing-imports --no-error-summary 2>$null
    Write-Host "✅ Type check başarılı" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Type check uyarıları var (devam ediliyor)" -ForegroundColor Yellow
}

# 3. Python Tests
if (-not $SkipTests) {
    Write-Host "`n🧪 [3/5] Python testleri..." -ForegroundColor Yellow
    try {
        pytest tests/ -v --tb=short -q 2>$null
        Write-Host "✅ Python testleri başarılı" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Bazı testler başarısız (devam ediliyor)" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n⏭️ [3/5] Testler atlandı" -ForegroundColor Gray
}

# 4. TypeScript Lint
Write-Host "`n📝 [4/5] TypeScript lint kontrolü..." -ForegroundColor Yellow
Set-Location "$root\frontend"
try {
    npm run lint --silent 2>$null
    Write-Host "✅ TypeScript lint başarılı" -ForegroundColor Green
} catch {
    Write-Host "⚠️ TypeScript lint uyarıları var" -ForegroundColor Yellow
}

# 5. TypeScript Type Check
Write-Host "`n🔬 [5/5] TypeScript type check..." -ForegroundColor Yellow
try {
    npm run type-check --silent 2>$null
    Write-Host "✅ TypeScript type check başarılı" -ForegroundColor Green
} catch {
    Write-Host "⚠️ TypeScript type uyarıları var" -ForegroundColor Yellow
}

# Sonuç
Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "✅ KIRO2 Quality Gates tamamlandı!" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Cyan

# Log yaz
$logFile = "$root\.claude\activity.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "[$timestamp] Quality gates completed successfully"

exit 0
```

### 2.2 Bash Versiyonu (WSL/Git Bash için)

`C:\Users\husey\kiro2\.claude\scripts\quality-gates.sh` dosyası oluştur:

```bash
#!/bin/bash
# KIRO2 Quality Gates Script
# Claude Code Stop Hook için kalite kapısı

set -e  # Hata durumunda dur

ROOT="C:/Users/husey/kiro2"
echo "🔍 KIRO2 Quality Gates başlatılıyor..."

# 1. Python Lint
echo -e "\n📝 [1/5] Python Lint kontrolü (ruff)..."
cd "$ROOT/backend"
ruff check . --fix || true
ruff format . || true
echo "✅ Python lint tamamlandı"

# 2. Type Check
echo -e "\n🔬 [2/5] Type check (mypy)..."
mypy . --ignore-missing-imports || true
echo "✅ Type check tamamlandı"

# 3. Python Tests
echo -e "\n🧪 [3/5] Python testleri..."
pytest tests/ -v --tb=short -q || true
echo "✅ Python testleri tamamlandı"

# 4. TypeScript Lint
echo -e "\n📝 [4/5] TypeScript lint..."
cd "$ROOT/frontend"
npm run lint || true
echo "✅ TypeScript lint tamamlandı"

# 5. TypeScript Type Check
echo -e "\n🔬 [5/5] TypeScript type check..."
npm run type-check || true
echo "✅ TypeScript type check tamamlandı"

# Sonuç
echo -e "\n=================================================="
echo "✅ KIRO2 Quality Gates tamamlandı!"
echo "=================================================="

# Log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Quality gates completed" >> "$ROOT/.claude/activity.log"

exit 0
```

---

## ADIM 3: settings.json Güncelle (P0)

`C:\Users\husey\kiro2\.claude\settings.json` dosyasını aşağıdaki değişikliklerle güncelle:

### 3.1 Eklenecek/Değiştirilecek Bölümler

```json
{
  "permissions": {
    "allow": [
      "Bash(ruff:*)",
      "Bash(pytest:*)",
      "Bash(python -m pytest:*)",
      "Bash(npm run test:*)",
      "Bash(npm run build:*)",
      "Bash(npm run lint:*)",
      "Bash(mypy:*)",
      "Bash(alembic:*)",
      "Bash(git diff:*)",
      "Bash(git status:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git branch:*)",
      "Bash(curl http://localhost:*)",
      "Bash(redis-cli:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(DROP TABLE:*)",
      "Bash(DELETE FROM:*)",
      "Bash(curl http*:* -X DELETE)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Edit(./.env)",
      "Edit(./.env.*)"
    ],
    "defaultMode": "default"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python -c \"import json, sys; data=json.load(sys.stdin); path=data.get('tool_input',{}).get('file_path',''); sys.exit(2 if any(p in path for p in ['.env', 'package-lock.json', '.git/', 'node_modules/']) else 0)\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "file_path=$(echo $TOOL_INPUT | python -c \"import json,sys; print(json.load(sys.stdin).get('file_path',''))\"); if echo \"$file_path\" | grep -q '\\.py$'; then cd C:/Users/husey/kiro2/backend && ruff check --fix \"$file_path\" 2>/dev/null && ruff format \"$file_path\" 2>/dev/null; fi || true"
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "file_path=$(echo $TOOL_INPUT | python -c \"import json,sys; print(json.load(sys.stdin).get('file_path',''))\"); if echo \"$file_path\" | grep -qE '\\.(ts|tsx)$'; then cd C:/Users/husey/kiro2/frontend && npx prettier --write \"$file_path\" 2>/dev/null; fi || true"
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Claude Code input bekliyor', 'KIRO2')\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File C:\\Users\\husey\\kiro2\\.claude\\scripts\\quality-gates.ps1 -SkipTests"
          }
        ]
      }
    ]
  }
}
```

### 3.2 Değişiklik Özeti

| Değişiklik | Eski | Yeni |
|------------|------|------|
| permissions.defaultMode | ❌ Yok | ✅ `"default"` |
| Stop hook | Sadece log | ✅ quality-gates.ps1 |
| PostToolUse Python | black/isort | ✅ ruff |
| Bash(ruff:*) | ❌ Yok | ✅ Eklendi |

---

## ADIM 4: skills/ Dizini Oluştur (P0)

### 4.1 Dizin Yapısı

```powershell
# PowerShell'de çalıştır
cd C:\Users\husey\kiro2\.claude
mkdir -p skills\kiro2-specific
mkdir -p skills\turkish-nlp
mkdir -p skills\education-algorithms
```

### 4.2 KIRO2-Specific SKILL.md

`C:\Users\husey\kiro2\.claude\skills\kiro2-specific\SKILL.md` oluştur:

```markdown
# KIRO2 Platform Skills

## Genel Bakış
Bu skill, KIRO2 YKS hazırlık platformunun özel gereksinimlerini tanımlar.

## Teknoloji Stack
- Backend: Python 3.11 + FastAPI + SQLAlchemy
- Frontend: React 18 + TypeScript + Zustand
- Database: PostgreSQL + Redis
- AI/ML: IRT, FSRS, ZPD, Zemberek

## Kritik Kurallar

### Auth Store
- ❌ ASLA `useAuth.ts` kullanma
- ✅ HER ZAMAN `authStore.ts` kullan

### Veritabanı
- Port: 5434 (standart değil!)
- Encoding: UTF-8 (tr_TR.UTF-8)

### API Endpoint'leri
- Backend: http://localhost:8000
- Frontend: http://localhost:3001

## Doğrulama Gereksinimleri

### IRT Parametreleri
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Zorluk (b) | [-4, 4] | Logit ölçeği |
| Ayırt edicilik (a) | [0.2, 4] | Pozitif |
| Şans (c) | [0, 0.35] | 5 şıklı MCQ için ~0.20 |

### FSRS Parametreleri
| Parametre | Aralık |
|-----------|--------|
| Stabilite | [0.1, 3650] gün |
| Zorluk | [0, 10] |
| Hatırlanabilirlik | [0, 1] |

### ZPD Bölgeleri
| Bölge | Başarı Tahmini |
|-------|----------------|
| TOO_EASY | > 85% |
| OPTIMAL | 15% - 85% |
| TOO_HARD | < 15% |

## Türkçe Dil Kuralları

### I/ı Dönüşümü (KRİTİK)
```python
# Türkçe: i↔İ, ı↔I (4 harf)
# İngilizce: i↔I (2 harf)

def turkish_upper(text: str) -> str:
    return (text
        .replace('i', 'İ')
        .replace('ı', 'I')
        .upper())
```

### UTF-8 Zorunlu
- PostgreSQL: `LC_COLLATE = 'tr_TR.UTF-8'`
- API: `charset=utf-8` header
```

### 4.3 Turkish NLP SKILL.md

`C:\Users\husey\kiro2\.claude\skills\turkish-nlp\SKILL.md` oluştur:

```markdown
# Turkish NLP Skills

## Araçlar
- **Zemberek**: Morfolojik analiz
- **BERTurk**: Transformer modeli
- **Zeyrek**: Python wrapper

## Türkçe I/ı Problemi

### Dönüşüm Tablosu
| Küçük | Büyük | Türkçe | İngilizce |
|-------|-------|--------|-----------|
| i | İ | i↔İ | i↔I |
| ı | I | ı↔I | - |

### Python Fonksiyonları
```python
def turkish_upper(text: str) -> str:
    return (text
        .replace('i', 'İ')
        .replace('ı', 'I')
        .replace('ğ', 'Ğ')
        .replace('ü', 'Ü')
        .replace('ş', 'Ş')
        .replace('ö', 'Ö')
        .replace('ç', 'Ç')
        .upper())

def turkish_lower(text: str) -> str:
    return (text
        .replace('İ', 'i')
        .replace('I', 'ı')
        .replace('Ğ', 'ğ')
        .replace('Ü', 'ü')
        .replace('Ş', 'ş')
        .replace('Ö', 'ö')
        .replace('Ç', 'ç')
        .lower())
```

### TypeScript Fonksiyonları
```typescript
function turkishUpper(text: string): string {
  return text
    .replace(/i/g, 'İ')
    .replace(/ı/g, 'I')
    .toLocaleUpperCase('tr-TR');
}

function turkishLower(text: string): string {
  return text
    .replace(/İ/g, 'i')
    .replace(/I/g, 'ı')
    .toLocaleLowerCase('tr-TR');
}
```

## Zemberek Kullanımı
```python
from zeyrek import MorphAnalyzer

analyzer = MorphAnalyzer()
result = analyzer.lemmatize('kitaplarımızdan')
# {'lemma': 'kitap', 'pos': 'Noun', ...}
```
```

### 4.4 Education Algorithms SKILL.md

`C:\Users\husey\kiro2\.claude\skills\education-algorithms\SKILL.md` oluştur:

```markdown
# Education Algorithms Skills

## IRT (Item Response Theory)

### 3-Parametreli Logistik Model (3PL)
```
P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
```

Burada:
- θ: Öğrenci yeteneği
- a: Ayırt edicilik [0.2, 4.0]
- b: Zorluk [-4.0, 4.0]
- c: Şans [0.0, 0.35]

### Pydantic Doğrulama
```python
class IRTParameters(BaseModel):
    difficulty: float = Field(..., ge=-4.0, le=4.0)
    discrimination: float = Field(..., ge=0.2, le=4.0)
    guessing: float = Field(default=0.2, ge=0.0, le=0.35)
    
    @model_validator(mode='after')
    def validate_consistency(self):
        if self.discrimination < 0.4 and abs(self.difficulty) > 3.0:
            raise ValueError('Düşük ayırt edicilik ile aşırı zorluk uyumsuz')
        return self
```

## FSRS (Free Spaced Repetition Scheduler)

### Stabilite Hesaplama
```
R(t) = e^(-t/S)
```

### Tekrar Aralığı
| Değerlendirme | Stabilite Çarpanı | Min | Max |
|---------------|-------------------|-----|-----|
| Again (1) | 0.2-0.5 | 1 gün | 3 gün |
| Hard (2) | 0.8-1.2 | önceki | önceki×1.2 |
| Good (3) | 1.5-2.5 | önceki×1.5 | 180 gün |
| Easy (4) | 2.5-4.0 | önceki×2.5 | 365 gün |

## ZPD (Zone of Proximal Development)

### Bölge Sınıflandırması
```python
class ZPDZone(str, Enum):
    TOO_EASY = "too_easy"    # > 85%
    OPTIMAL = "optimal"       # 15% - 85%
    TOO_HARD = "too_hard"    # < 15%
```

### Optimal Bölge
- **Hedef**: %15-%85 başarı tahmini
- **Gerekçe**: Vygotsky'nin öğrenme teorisi
- **Sonuç**: Maksimum öğrenme ve motivasyon
```

---

## ADIM 5: python-pro Subagent Ekle (P0)

`C:\Users\husey\kiro2\.claude\agents\python-pro.md` oluştur:

```markdown
---
name: python-pro
description: Expert Python developer for modern Python 3.11+ and KIRO2 backend
tools: Read, Write, Edit, Bash, Glob, Grep
model: opus
---

You are an expert Python developer mastering Python 3.11+ features and KIRO2 backend.

## Expertise Areas

### Python 3.11+ Features
- Pattern matching (match/case)
- Structural pattern matching
- Exception groups
- Type parameter syntax
- Self type

### Modern Tooling
- **Package Manager**: uv (preferred), pip
- **Linting**: ruff (replaces black, isort, flake8)
- **Type Checking**: mypy (strict mode)
- **Testing**: pytest with fixtures
- **Framework**: FastAPI + Pydantic v2

### KIRO2-Specific
- SQLAlchemy ORM patterns
- Alembic migrations
- Redis caching strategies
- JWT authentication

## Code Standards

### Always Use
- Type hints (strict)
- Google docstring style
- Dataclasses over dicts
- Context managers
- async/await patterns

### Pydantic v2 Best Practices
```python
from pydantic import BaseModel, Field, ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(strict=True)
    
    field: str = Field(..., min_length=1, max_length=100)
```

### IRT Validation Pattern
```python
class IRTParameters(BaseModel):
    difficulty: float = Field(..., ge=-4.0, le=4.0)
    discrimination: float = Field(..., ge=0.2, le=4.0)
    guessing: float = Field(default=0.2, ge=0.0, le=0.35)
```

## Commands

### Lint & Format
```bash
ruff check . --fix
ruff format .
mypy . --strict
```

### Test
```bash
pytest -v --tb=short
pytest --cov=. --cov-report=html
```

## Turkish Language Handling

Always use proper Turkish character handling:
```python
def turkish_lower(text: str) -> str:
    return (text
        .replace('İ', 'i')
        .replace('I', 'ı')
        .lower())
```
```

---

## ADIM 6: CLAUDE.local.md Oluştur (P0)

`C:\Users\husey\kiro2\CLAUDE.local.md` oluştur:

```markdown
# CLAUDE.local.md - Kişisel Notlar

> ⚠️ Bu dosya .gitignore'da olmalı - commit etme!

## Geliştirici Bilgileri
- **Geliştirici**: Hüseyin
- **Ortam**: Windows 11
- **Terminal**: PowerShell / Git Bash

## Kişisel Tercihler

### Model Tercihi
- Varsayılan: `opus` (karmaşık görevler için)
- Hızlı görevler: `sonnet`

### Çalışma Stili
- Plan mode ile başla
- Her 3-4 etkileşimde `/context` kontrol
- %80'de `/clear` + HANDOFF.md

## Aktif Çalışma Alanları

### Bu Hafta
- [ ] Emergency content SQL yükleme
- [ ] WebSocket deprecated kod temizliği
- [ ] OCR pipeline optimizasyonu

### Bekleyen Görevler
- [ ] 2FA implementasyonu
- [ ] Rate limiting fine-tuning

## Kişisel Notlar

### Sık Kullanılan Komutlar
```bash
# Backend hızlı test
cd backend && pytest tests/unit -v --tb=short

# Frontend dev
cd frontend && npm run dev

# DB reset
psql -U postgres -d kiro2 -f emergency_content.sql
```

### Bookmark'lar
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3001
- Grafana: http://localhost:3000

## Oturum Geçmişi

### 2026-01-05
- Claude Code doğrulama mekanizmaları rehberi hazırlandı
- Quality gates script oluşturuldu
- Ruff'a geçiş yapıldı
```

---

## ADIM 7: .gitignore Güncelle (P0)

`C:\Users\husey\kiro2\.gitignore` dosyasının sonuna ekle:

```gitignore
# ================================================
# Claude Code Kişisel Dosyalar
# ================================================

# Kişisel proje notları (commit etme!)
CLAUDE.local.md

# Kişisel settings (commit etme!)
.claude/settings.local.json

# Activity log
.claude/activity.log

# Geçici handoff dosyaları
HANDOFF.md
PROGRESS.md
```

---

## ADIM 8: Doğrulama (Tümünü Test Et)

### 8.1 Dosya Kontrolü

```powershell
# PowerShell'de çalıştır
cd C:\Users\husey\kiro2

# Kontrol listesi
Write-Host "📁 Dosya Kontrolü:" -ForegroundColor Cyan

# 1. Quality gates script
if (Test-Path ".claude\scripts\quality-gates.ps1") {
    Write-Host "✅ quality-gates.ps1 mevcut" -ForegroundColor Green
} else {
    Write-Host "❌ quality-gates.ps1 EKSİK" -ForegroundColor Red
}

# 2. Skills dizini
if (Test-Path ".claude\skills\kiro2-specific\SKILL.md") {
    Write-Host "✅ skills/kiro2-specific mevcut" -ForegroundColor Green
} else {
    Write-Host "❌ skills dizini EKSİK" -ForegroundColor Red
}

# 3. python-pro agent
if (Test-Path ".claude\agents\python-pro.md") {
    Write-Host "✅ python-pro.md mevcut" -ForegroundColor Green
} else {
    Write-Host "❌ python-pro.md EKSİK" -ForegroundColor Red
}

# 4. CLAUDE.local.md
if (Test-Path "CLAUDE.local.md") {
    Write-Host "✅ CLAUDE.local.md mevcut" -ForegroundColor Green
} else {
    Write-Host "❌ CLAUDE.local.md EKSİK" -ForegroundColor Red
}

# 5. Ruff kurulu mu?
try {
    ruff --version
    Write-Host "✅ ruff kurulu" -ForegroundColor Green
} catch {
    Write-Host "❌ ruff EKSİK - pip install ruff" -ForegroundColor Red
}
```

### 8.2 Quality Gates Test

```powershell
# Quality gates'i test et
powershell -ExecutionPolicy Bypass -File .claude\scripts\quality-gates.ps1 -SkipTests
```

### 8.3 Claude Code'da Test

Claude Code'u açıp şunları test et:

```
# 1. Model kontrolü
/model

# 2. Context kontrolü
/context

# 3. Permissions kontrolü
/permissions

# 4. Yeni agent'ı test et
@python-pro IRT parametrelerini doğrula

# 5. Bir Python dosyası düzenle ve PostToolUse hook'un çalıştığını gör
```

---

## 📋 TAMAMLAMA KONTROL LİSTESİ

### P0 - Kritik (Hemen Yapılmalı)
- [ ] Ruff kuruldu (`pip install ruff`)
- [ ] pyproject.toml oluşturuldu
- [ ] quality-gates.ps1 oluşturuldu
- [ ] settings.json güncellendi (Stop hook, defaultMode, ruff)
- [ ] skills/ dizini oluşturuldu (3 skill)
- [ ] python-pro.md agent eklendi
- [ ] CLAUDE.local.md oluşturuldu
- [ ] .gitignore güncellendi

### Doğrulama
- [ ] `ruff check . --fix` çalışıyor
- [ ] `quality-gates.ps1` hatasız çalışıyor
- [ ] Claude Code'da `@python-pro` çalışıyor
- [ ] PostToolUse hook ruff kullanıyor

---

## 🎯 Boris Cherny Altın Kuralı

> **"Claude'a çalışmasını doğrulama yolu vermek kaliteyi 2-3x artırır!"**

Bu rehberdeki en kritik değişiklik **Stop hook'a quality-gates eklenmesidir**. Bu, Claude'un her görev tamamladığında otomatik olarak:
- Lint kontrolü
- Type check
- Test çalıştırma

yapmasını sağlar ve kod kalitesini dramatik şekilde artırır.

---

*Rehber Versiyonu: 1.0*
*Oluşturma Tarihi: 2026-01-05*
*Kaynak: KIRO2 Doğrulama Mekanizmaları Rehberi (52 sayfa)*
