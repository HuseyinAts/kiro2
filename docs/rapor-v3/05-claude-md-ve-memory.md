# BÖLÜM 5: CLAUDE.md ve Memory Sistemi

## 5.1 CLAUDE.md Nedir?

CLAUDE.md, Claude Code'un "kurumsal hafızası"dır. Her oturum başında otomatik olarak okunur ve Claude'un davranışını, proje kurallarını ve tercihlerini şekillendirir.

### Boris Cherny'nin Açıklaması

**İngilizce:**
> "CLAUDE.md is the single most important file for getting consistent results from Claude Code. It's like onboarding documentation for an AI teammate that joins fresh every session."

**Türkçe:**
> "CLAUDE.md, Claude Code'dan tutarlı sonuçlar almanın en önemli dosyasıdır. Her oturumda taze katılan bir AI takım arkadaşı için onboarding dokümantasyonu gibidir."

### Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| Otomatik yükleme | Her session başında okunur |
| Markdown format | Başlıklar, listeler, kod blokları |
| Hiyerarşik | Global → Proje → Local katmanlar |
| Git-friendly | Versiyon kontrolü yapılabilir |
| Paylaşılabilir | Takım genelinde kullanılabilir |

---

## 5.2 Dosya Hiyerarşisi (Kesin Öncelik Sırası)

Claude Code birden fazla CLAUDE.md dosyasını okuyabilir. Çakışma durumunda **yüksek öncelikli dosya kazanır**.

### Seviye 1: User Global (En Düşük Öncelik)

**Konum:** `~/.claude/CLAUDE.md`

**Windows:** `C:\Users\<username>\.claude\CLAUDE.md`
**macOS/Linux:** `~/.claude/CLAUDE.md`

**Kapsam:** Tüm projeler, tüm oturumlar

**İçerik önerileri:**
- Kişisel tercihler (dil, format)
- Global kısayollar
- Evrensel kurallar
- Varsayılan araçlar

**Örnek:**
```markdown
# Global Claude Preferences

## Language
- Respond in Turkish when asked in Turkish
- Use English for code comments

## Style
- Prefer concise explanations
- Use bullet points for lists
- Include code examples when relevant

## Tools
- ALWAYS run `ruff format` after Python edits
- NEVER commit directly to main branch
```

### Seviye 2: Project Root (Orta Öncelik)

**Konum:** `./CLAUDE.md` veya `./.claude/CLAUDE.md`

Her iki konum da geçerli. Tercih:
- `./CLAUDE.md`: Görünür, kolay erişim
- `./.claude/CLAUDE.md`: Gizli, temiz root

**Kapsam:** Bu proje, tüm geliştiriciler

**İçerik önerileri:**
- Proje mimarisi
- Kod standartları
- Build/test komutları
- Önemli dosya yolları
- Takım kuralları

### Seviye 3: Local Memory (Kişisel)

**Konum:** `./CLAUDE.local.md`

**Önemli:** Bu dosya `.gitignore`'a eklenmeli!

**Kapsam:** Bu proje, sadece bu geliştirici

**İçerik önerileri:**
- Kişisel notlar
- Deneysel kurallar
- WIP (work in progress) durumlar
- Debugging ipuçları

**Örnek:**
```markdown
# Local Notes (DO NOT COMMIT)

## Current Focus
Working on rate limiter bug. Check src/auth/rate_limiter.py line 45.

## Experiments
- Trying new caching strategy
- Test with CACHE_TTL=300

## Personal Shortcuts
- Use `./scripts/quick-test.sh` for fast iteration
```

### Seviye 4: Rules Directory (Koşullu Kurallar)

**Konum:** `./.claude/rules/*.md`

Glob pattern ile eşleşen tüm `.md` dosyaları yüklenir.

**Kapsam:** Koşullu, dosya türüne veya duruma özel

**Dosya örnekleri:**
- `python-rules.md`: Python dosyaları için
- `security-rules.md`: Güvenlik ile ilgili
- `testing-rules.md`: Test yazarken
- `api-rules.md`: API endpoint'leri için

**Örnek (`python-rules.md`):**
```markdown
# Python Code Rules

## Type Hints
- ALWAYS use type hints for function parameters
- ALWAYS use type hints for return values
- Use `from __future__ import annotations` for forward references

## Docstrings
- Use Google style docstrings
- Include Args, Returns, Raises sections
- Add examples for complex functions

## Imports
- Use absolute imports
- Group: stdlib, third-party, local
- Sort with isort
```

### Seviye 5: Enterprise Policy (En Yüksek Öncelik)

**Konum:** Organizasyon tarafından merkezi yönetim

**Kapsam:** Tüm organizasyon, override edilemez

**Yönetim:** Anthropic Admin Console veya MDM

**İçerik örnekleri:**
- Güvenlik politikaları
- Compliance kuralları
- Yasaklı operasyonlar
- Zorunlu review süreçleri

---

## 5.3 Öncelik Çakışması Çözümü

### Kural: Yüksek Öncelik Kazanır

```
Enterprise Policy  >  Rules Directory  >  Local  >  Project  >  User Global
```

### Örnek Senaryo

**User Global (~/.claude/CLAUDE.md):**
```markdown
Use 2-space indentation for all code.
```

**Project (./CLAUDE.md):**
```markdown
Use 4-space indentation for Python.
```

**Rules (./.claude/rules/python-rules.md):**
```markdown
Use tabs for indentation in Python.
```

**Sonuç:** Python dosyalarında tabs kullanılır (rules kazanır).

### Additive vs Override

| Direktif Tipi | Davranış |
|---------------|----------|
| Pozitif (DO) | Additive - hepsi geçerli |
| Negatif (NEVER) | Override - en yüksek öncelik |
| Conditional (WHEN) | Context'e göre |

**Örnek:**
```markdown
# User Global
ALWAYS write tests.

# Project
ALWAYS write integration tests.

# Sonuç: Her ikisi de geçerli - hem unit hem integration test yaz
```

```markdown
# User Global
NEVER use print() for logging.

# Project
You may use print() for debugging.

# Sonuç: NEVER kazanır - print() yasak
```

---

## 5.4 Etkili CLAUDE.md Yazımı

### Yapı Şablonu

```markdown
# [Proje Adı] - Claude Code Rules

## Quick Reference
- Build: `[command]`
- Test: `[command]`
- Lint: `[command]`
- Format: `[command]`

## Architecture Overview
[2-3 cümle proje açıklaması]

## Directory Structure
```
src/
├── module1/    # [açıklama]
├── module2/    # [açıklama]
└── utils/      # [açıklama]
```

## Code Standards
### [Dil] Rules
- [Kural 1]
- [Kural 2]

## IMPORTANT Rules
- YOU MUST: [zorunluluk]
- NEVER: [yasak]

## Known Issues
- [Issue 1]: [workaround]

## Contacts
- [Modül]: @[kişi]
```

### Vurgulama Teknikleri

**En güçlüden en zayıfa:**

| Teknik | Kullanım | Örnek |
|--------|----------|-------|
| `NEVER` | Kesin yasak | `NEVER delete production data` |
| `ALWAYS` | Kesin zorunluluk | `ALWAYS run tests before commit` |
| `YOU MUST` | Güçlü zorunluluk | `YOU MUST use type hints` |
| `IMPORTANT:` | Dikkat çekici | `IMPORTANT: Database on port 5434` |
| `WARNING:` | Uyarı | `WARNING: This API is deprecated` |
| `NOTE:` | Bilgi | `NOTE: Uses Redis for caching` |

### Anti-Patterns

**❌ Çok uzun açıklamalar:**
```markdown
# KÖTÜ
When you are writing Python code, you should always make sure to include 
type hints for all function parameters and return values because this 
helps with code maintainability and allows tools like mypy to catch 
potential type errors before runtime...
```

**✅ Kısa ve öz:**
```markdown
# İYİ
## Python Type Hints
ALWAYS use type hints for:
- Function parameters
- Return values
- Class attributes
```

**❌ Belirsiz kurallar:**
```markdown
# KÖTÜ
Write good code.
Use best practices.
```

**✅ Somut kurallar:**
```markdown
# İYİ
- Line length: max 100 characters
- Function length: max 50 lines
- Cyclomatic complexity: max 10
```

---

## 5.5 KIRO2 İçin CLAUDE.md

### Ana Proje CLAUDE.md

**Dosya:** `C:\Users\husey\kiro2\CLAUDE.md`

```markdown
# KIRO2 YKS Hazırlık Platformu - Claude Code Rules

## Quick Reference
```bash
# Build & Run
cd backend && python -m uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Test
python -m pytest tests/ -v --cov=src
npm test

# Lint & Format
ruff check . --fix && ruff format .
mypy --strict src/

# Database
# PostgreSQL: localhost:5434
# Redis: localhost:6379
```

## Project Overview
KIRO2 is a Turkish university entrance exam (YKS) preparation platform with AI-powered question generation and adaptive learning. The orchestrator module manages multi-agent workflows for content creation and quality assurance.

## Architecture
```
kiro2/
├── orchestrator/           # AI orchestration system
│   ├── core/              # Core modules (state, memory, routing)
│   ├── agents/            # Agent definitions
│   ├── validators/        # Content validation
│   └── workflows/         # LangGraph workflows
├── backend/               # FastAPI backend
├── frontend/              # React frontend
├── d-dataset/             # Question bank and datasets
└── tests/                 # Test suites
```

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy
- **Frontend:** React 18, TypeScript, TailwindCSS
- **Database:** PostgreSQL 15 (port 5434), Redis 7
- **AI:** LangGraph, LangChain, Anthropic API
- **Infrastructure:** Docker, GitHub Actions

## IMPORTANT Rules

### Database
- NEVER connect directly to production database
- ALWAYS use connection pooling
- PostgreSQL port is 5434 (NOT default 5432)

### API Keys
- NEVER hardcode API keys in source code
- ALWAYS use environment variables
- Store secrets in `.env` (gitignored)

### Content Generation
- YOU MUST validate all generated questions
- YOU MUST include difficulty_level (1-5)
- YOU MUST include topic_tags (list)
- ALWAYS use UTF-8 encoding for Turkish characters

### Code Quality
- ALWAYS run `ruff check` before commit
- ALWAYS run `mypy --strict` for type checking
- Test coverage must be > 80%

## Module Owners
- Orchestrator: @huseyin
- Backend API: @huseyin
- Frontend: @huseyin
- Content Pipeline: @huseyin

## Known Issues
1. **Rate Limiter:** Currently hardcoded to 5 req/min, should be 10
   - File: `src/auth/rate_limiter.py:45`
   - Status: In progress

2. **Memory Leak:** Long-running sessions accumulate memory
   - Workaround: Restart orchestrator every 24h
   - Status: Investigating

## Development Workflow
1. Create feature branch: `git checkout -b feature/[name]`
2. Implement with tests
3. Run full test suite: `python -m pytest`
4. Create PR with description
5. Merge after review

## Commit Message Format
```
[type]: [short description]

[detailed description if needed]

Types: feat, fix, docs, style, refactor, test, chore
```

## Environment Variables
```env
# Required
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:pass@localhost:5434/kiro2
REDIS_URL=redis://localhost:6379

# Optional
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=kiro2
```
```

### Rules Directory

**Dosya:** `.claude/rules/python-rules.md`

```markdown
# Python Development Rules

## Type Hints (MANDATORY)
```python
# CORRECT
def calculate_score(answers: list[str], key: dict[str, str]) -> float:
    ...

# WRONG - no type hints
def calculate_score(answers, key):
    ...
```

## Docstrings (Google Style)
```python
def generate_question(
    topic: str,
    difficulty: int,
    *,
    include_hints: bool = False
) -> Question:
    """Generate a YKS question for the given topic.
    
    Args:
        topic: The subject topic (e.g., "limit", "türev")
        difficulty: Difficulty level from 1 (easy) to 5 (hard)
        include_hints: Whether to include solution hints
    
    Returns:
        A Question object with all required fields
    
    Raises:
        ValueError: If difficulty is not in range 1-5
        TopicNotFoundError: If topic is not in curriculum
    
    Example:
        >>> q = generate_question("limit", 3)
        >>> q.difficulty_level
        3
    """
```

## Error Handling
```python
# CORRECT - specific exceptions
try:
    result = api_call()
except HTTPError as e:
    logger.error(f"API call failed: {e}")
    raise
except TimeoutError:
    logger.warning("Request timed out, retrying...")
    return retry_with_backoff()

# WRONG - bare except
try:
    result = api_call()
except:
    pass
```

## Async Patterns
```python
# CORRECT - proper async
async def fetch_questions(topic: str) -> list[Question]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/questions/{topic}") as response:
            return await response.json()

# WRONG - blocking in async
async def fetch_questions(topic: str) -> list[Question]:
    response = requests.get(f"/api/questions/{topic}")  # BLOCKING!
    return response.json()
```

## Testing
- Test file naming: `test_[module].py`
- Test function naming: `test_[function]_[scenario]`
- Use fixtures for common setup
- Mock external dependencies

```python
# Example
@pytest.fixture
def mock_api():
    with patch("module.api_client") as mock:
        mock.get.return_value = {"status": "ok"}
        yield mock

def test_fetch_questions_success(mock_api):
    result = fetch_questions("limit")
    assert len(result) > 0
    mock_api.get.assert_called_once()
```
```

**Dosya:** `.claude/rules/security-rules.md`

```markdown
# Security Rules

## Secrets Management
- NEVER commit secrets to git
- NEVER log secrets (even partially)
- NEVER include secrets in error messages
- ALWAYS use environment variables
- ALWAYS rotate keys periodically

## Input Validation
- ALWAYS validate user input
- NEVER trust client-side validation alone
- Use parameterized queries (no string concatenation)
- Sanitize all output to prevent XSS

## Authentication
- ALWAYS use bcrypt for password hashing (cost factor 12+)
- ALWAYS use secure session tokens (256-bit random)
- NEVER store passwords in plaintext
- Implement rate limiting on auth endpoints

## Dangerous Operations (Require Extra Review)
- Database migrations
- User deletion
- Permission changes
- API key generation
- File system operations

## Audit Logging
Log these events:
- Login attempts (success and failure)
- Permission changes
- Data exports
- Admin actions
```

---

## 5.6 `#` Tuşu ve Anlık Notlar

### Kullanım

Claude Code CLI'da `#` tuşuna basarak anlık not ekleme moduna girilebilir.

**Davranış:**
1. `#` tuşuna bas
2. Not yaz
3. Enter'a bas
4. Not `CLAUDE.local.md`'ye eklenir

### Örnek Akış

```
> # Bu fonksiyon deprecated, refactor lazım
Note added to CLAUDE.local.md

> # Rate limiter threshold 10 olmalı
Note added to CLAUDE.local.md
```

**CLAUDE.local.md içeriği:**
```markdown
# Session Notes

- Bu fonksiyon deprecated, refactor lazım (2026-02-01 10:30)
- Rate limiter threshold 10 olmalı (2026-02-01 10:32)
```

### Best Practices

**Not eklerken:**
- Kısa ve öz tut
- Context ekle (dosya adı, satır numarası)
- Aciliyet belirt (TODO, FIXME, HACK)

**Periyodik temizlik:**
- Haftalık `CLAUDE.local.md` review
- Çözülen notları kaldır
- Önemli notları `CLAUDE.md`'ye taşı

---

## 5.7 Memory Persistence ve Session Continuity

### Session İçi Memory

Claude her session başında:
1. `~/.claude/CLAUDE.md` okur (varsa)
2. `./CLAUDE.md` okur (varsa)
3. `./CLAUDE.local.md` okur (varsa)
4. `./.claude/rules/*.md` okur (varsa)

### Session Arası Persistence

**Ne kalıcı:**
- CLAUDE.md dosyaları
- Git commit'leri
- Dışa aktarılan session'lar

**Ne geçici:**
- Konuşma geçmişi (/clear ile silinir)
- Tool çıktıları
- Ara hesaplamalar

### Document & Clear Pattern

Uzun görevlerde context yönetimi için:

**Adım 1:** Progress kaydet
```
"Write current progress to docs/progress.md including:
- Completed steps
- Current state
- Next steps
- Open questions"
```

**Adım 2:** Context temizle
```
/clear
```

**Adım 3:** Devam et
```
"Read docs/progress.md and continue from where we left off"
```

### KIRO2 Progress Template

**Dosya:** `docs/progress.md`

```markdown
# Development Progress

## Last Updated
2026-02-01 14:30 UTC

## Current Sprint
Sprint 5: Verification Pipeline

## Completed
- [x] SyntaxValidator implemented
- [x] SchemaValidator implemented
- [x] ContentValidator implemented

## In Progress
- [ ] PedagogicalValidator (70% complete)
  - Curriculum mapping done
  - Difficulty estimation TODO

## Next Steps
1. Complete PedagogicalValidator
2. Implement DuplicateDetector
3. Write integration tests

## Open Questions
- Should we use cosine similarity or euclidean distance for duplicates?
- What's the optimal similarity threshold?

## Blockers
- None currently

## Notes
- Using sentence-transformers for embeddings
- PostgreSQL vector extension might be needed for production
```

---

## 5.8 Özet

### Checklist

- [ ] `~/.claude/CLAUDE.md` oluşturuldu (global preferences)
- [ ] `./CLAUDE.md` oluşturuldu (proje kuralları)
- [ ] `./CLAUDE.local.md` oluşturuldu ve `.gitignore`'a eklendi
- [ ] `./.claude/rules/` dizini yapılandırıldı
- [ ] Vurgulama teknikleri (NEVER, ALWAYS, etc.) kullanıldı
- [ ] Quick reference section eklendi
- [ ] Architecture overview yazıldı

### Dosya Konumları Özet

| Dosya | Konum | Git | Öncelik |
|-------|-------|-----|---------|
| User Global | `~/.claude/CLAUDE.md` | ❌ | 1 (en düşük) |
| Project | `./CLAUDE.md` | ✅ | 2 |
| Local | `./CLAUDE.local.md` | ❌ | 3 |
| Rules | `./.claude/rules/*.md` | ✅ | 4 |
| Enterprise | Merkezi | N/A | 5 (en yüksek) |

### Metrikler

| Metrik | Önerilen |
|--------|----------|
| CLAUDE.md boyutu | < 5KB (token verimli) |
| Kural sayısı | 20-50 kural |
| Update sıklığı | Her sprint sonunda |
| Team sync | Haftalık review |

---

**Önceki Bölüm:** [04 - Paralel Oturum Yönetimi](./04-paralel-oturum-yonetimi.md)  
**Sonraki Bölüm:** [06 - Context Yönetimi](./06-context-yonetimi.md)
