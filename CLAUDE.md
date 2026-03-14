# KIRO2 Project Instructions

## Session Management

- **Session resume**: Önceki session'dan devam ederken, codebase'i sıfırdan explore ETME. Bildiğin context'i hemen belirt ve sonraki adımları öner. Gereksiz keşif yapmadan önce SOR.
- **State persistence**: Session sonunda `.claude/sessions/latest.md`'ye state yaz (yapılanlar, bekleyenler, engelleyiciler, dokunulan dosyalar, sonraki adımlar). 50 satırı geçmesin.
- **Plan time-boxing**: Plan modunda 2-3 dk keşiften sonra kullanıcıya check-in yap. Açık onay almadan 3 turdan fazla plan taslağı yapma.
- **Context validation**: Session resume sonrasi, hook'tan gelen state'i CLAUDE.md/MEMORY.md ile karsilastir. Tutarsizlik varsa (branch, soru sayisi, son commit) kullaniciya bildir.

## Communication Rules

1. **Direct Answer First**: Kullanıcı evet/hayır veya kısa cevap gerektiren soru sorduğunda ÖNCE 1 cümle ile cevapla, SONRA analiz/keşif yap. Dosya keşfi cevaptan ÖNCE yapılmaz.
2. **Plan Iteration Limit**: Plan oluştururken maksimum 2 iterasyon. 2. iterasyonda hâlâ netleşmediyse kullanıcıya sun ve yön sor. Onaysız auto-pivot yapma.
3. **Windows Environment**: Bu bir Windows 11 + NTFS ortamı. Linux/Mac komutları önerme. NTFS dosya tarama yavaştır — batch işlemlerde bunu hesaba kat. `python3` yok, `python` kullan.
4. **Direct questions**: Direkt soru sorulduğunda (hangi model?, X yapıldı mı?) ÖNCE direkt cevap ver, SONRA gerekirse doğrula/keşfet. Asla dosya keşfiyle başlama.

## Git Operations

- **Push fail (>2GB pack)**: 1) `git-lfs` ile büyük dosyaları track et, 2) `.gitignore` güncelle, 3) BFG Repo-Cleaner ile history temizle. Push'u tekrar tekrar deneme.
- **Pre-commit**: 50MB+ dosya commit'e girmeye çalışırsa engelle.
- **Pre-push file check**: Push öncesi `find . -size +100M -not -path './.git/*'` ile büyük dosyaları kontrol et. >100MB varsa git-lfs veya .gitignore öner.
- **LFS tracked patterns**: `*.jsonl` (>50MB), `*.bin`, `*.pt`, `*.db` (>50MB)

## 🎯 Project Overview

KIRO2 is a Turkish EdTech platform for YKS/TYT/AYT university entrance exam preparation.

**Mission:** Deliver personalized, AI-powered exam preparation using Turkish NLP and adaptive learning.

**Project Root:** `C:\Users\husey\kiro2`

## 📊 Current Status (March 2026)

### Database & Content ✅
- ✅ **PostgreSQL 15** (port 5434) - Production ready
  - **PgBouncer:** Not yet configured (planned for 100K+ concurrent users)
- ✅ **Redis 7** (port 6379) - Session & cache layer
- ✅ **77,336 YKS questions in production** (v3.5+, Target: 45K by March 2026 - EXCEEDED 172%)
  - 📊 **Pipeline:** 75,745 OCR → 86,249 matched (v2.4) → 77,336 clean (v3.5+)
  - v3.5+: db_v7=0, rematch=0, LOW confidence=0, 100% validation PASS
  - Answer DB: **answers_v8.db** (answers table removed — 39% accuracy was unusable)
  - 9,695 unreliable questions removed from v2.4 (db_v7, rematch, empty source, LOW conf)
- ✅ **405 source books** in production, ~~118 remaining~~ **DONE** (98 processed, 19 unviable)
  - 19 unviable: 3 corrupt screenshots, 8 no questions detected, 4 too few (<7), 3 non-question content, 1 false detection
- ✅ **eslesmis_sorucevap.jsonl** format in production (v3.5+)
- ✅ **Quality pipeline**: validate_sample.py v2 (13 checks) + cross_validate_answers.py (Bayesian)

### 🎯 Next Priorities
1. ~~Low-confidence question refinement pipeline~~ ✅ **DONE** (+19,248 questions improved)
2. ~~Manual validation + v2.2 cleanup~~ ✅ **DONE** (4,912 silindi, 653 kurtarıldı, 31,801 production)
3. ~~OCR pipeline fix~~ ✅ **DONE** (hallucination prevention + letter-only fix applied)
4. ~~118 yeni kitap işleme~~ ✅ **DONE** (98/117 processed, 19 unviable — corrupt/empty/non-question)
5. **P1: Re-OCR recovery** — 1,521-2,511 soru kurtarma (silinen 3,546'dan)
6. **P0: Performance optimization**: API <2s, vector search <100ms ✅ (21ms avg)
7. **P0: Git push** — HTTPS HTTP 500 (5.5GB), SSH gerekli

### Orchestrator Architecture ✅
- ✅ **orchestrator/** v2.5.0 (LangGraph 1.0.5) - **ACTIVE**
  - 24 modules (graph.py, routing.py, policy_engine.py, etc.)
  - 45 policies
  - 20 active agents
- ❌ **kiro2-orchestrator/** - **DEPRECATED** (safe to delete, legacy code)
- ✅ **YKS Module**: `.claude/plugins/installed/kiro2-yks/`

### d-dataset Pipeline Status
- ✅ **Phase 1-3 COMPLETED**
  - OCR processing: 75,745 questions extracted
  - Answer key extraction: 88,711 answers identified
  - Matching pipeline: 36,967 successful pairs (48.8% match rate)
- ✅ **Phase 4 COMPLETED**: Quality enhancement
  - v2.0: 99.5% high-confidence (36,767/36,967) - up from 47.4%
  - v2.1: 36,713 questions (254 unusable removed)
  - v2.2: 31,801 questions (4,912 deep quality filtered, 653 rescued)
  - v2.3: 33,342 questions (AI solved merged)
  - v2.4: 86,249 questions (v3 crop OCR pipeline merge)
  - v3.3: 76,554 questions (db_v7/rematch/LOW conf cleanup)
  - **v3.5+: 77,336 questions (CURRENT PRODUCTION)**
    - v3.5: +809 new book crop solve, v3.5+: +919 tier5 crop solve
    - 405 books, 0 db_v7, 0 rematch, 0 LOW conf
    - validate_sample.py: 100.0% PASS
  - **Pipeline**: `cross_validate_answers.py` (Bayesian) + `validate_sample.py` v2 (13 checks)

**Release Workflow (v2.2 Pipeline → Production):**
```bash
# Step 1: Run v2.2 pipeline (13 quality checks, 4-tier assignment)
python d-dataset/processed/pipeline_v2_2.py --input d-dataset/eslesmis_sorucevap.jsonl

# Step 2: Cross-validate output (must be 100% PASS)
python scripts/validate_sample.py d-dataset/processed/eslesmis_sorucevap_v2.2.jsonl --all

# Step 3: Backup current production
cp d-dataset/eslesmis_sorucevap.jsonl d-dataset/backups/eslesmis_sorucevap_vX.X_backup.jsonl

# Step 4: Promote to production
cp d-dataset/processed/eslesmis_sorucevap_v2.2.jsonl d-dataset/eslesmis_sorucevap.jsonl

# ⚠️ NEVER skip cross-validation step before production update
```

**Version History:**
- v1.0: 22,440 questions (initial)
- v2.0: 36,967 questions (Phase 4 confidence improvement)
- v2.1: 36,713 questions (254 unusable removed)
- v2.2: 31,801 questions (4,912 deep quality filtered, 653 rescued)
- v2.3: 33,342 questions (AI solved merged)
- v2.4: 86,249 questions (v3 crop OCR pipeline merge)
- v3.0-v3.1: 80,208 questions (DB v8 redesign, empty source cleanup)
- v3.3: 76,554 questions (db_v7/rematch/LOW conf cleanup)
- v3.5+: 77,336 questions (+809 new book + 919 tier5 crop solve) ← CURRENT

### Quality Pipeline (d-dataset/scripts/)
```bash
# Cross-validation (Bayesian posterior scoring)
python cross_validate_answers.py --analyze --simulate

# Validate production (must be 100% PASS)
cd C:\Users\husey\kiro2
python scripts/validate_sample.py d-dataset/eslesmis_sorucevap.jsonl --all

# DB v8 creation (from v7 page_inline + extraction data)
python create_answers_v8.py --validate
```

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | FastAPI (Python 3.11+), Uvicorn | Latest |
| Frontend | React 18 + TypeScript (Vite) | 18.x |
| Database | PostgreSQL 15 | 15.x |
| Cache | Redis 7 | 7.x |
| AI/NLP | Qwen3-8B (fine-tuned for Turkish) | Custom |
| Search | pgvector for semantic search | Latest |
| Auth | JWT + OAuth2 | - |
| Real-time | SSE (Server-Sent Events) | Default |

## 📁 Project Structure

```
kiro2/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (41 endpoints)
│   │   ├── core/          # Config, security, deps
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── nlp/           # Turkish NLP modules
│   ├── tests/
│   └── alembic/           # DB migrations
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Route pages
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API clients
│   │   └── store/         # State management
│   └── tests/
├── orchestrator/          # ✅ ACTIVE - v2.5.0 (LangGraph)
├── kiro2-orchestrator/    # ❌ DEPRECATED - safe to delete
├── d-dataset/             # C:\Users\husey\kiro2\d-dataset
│   ├── ocr_output/        # 75,745 extracted questions (READ-ONLY)
│   ├── answer_keys/       # 88,711 answer entries (READ-ONLY)
│   ├── eslesmis_sorucevap.jsonl  # Final matched pairs (READ-ONLY)
│   └── processed/         # ✅ WRITABLE - pipeline outputs
├── docker/
└── docs/
```

## 🔒 File Access Rules

### ✅ ALLOWED TO MODIFY (Writable)
- `backend/app/**/*.py` - Application code
- `frontend/src/**/*` - Frontend code
- `orchestrator/**/*.py` - Orchestrator code
- `d-dataset/processed/**` - Pipeline outputs
- `backend/tests/**/*.py` - Test files
- `frontend/tests/**/*` - Frontend tests
- `docs/**/*.md` - Documentation

### ❌ NEVER MODIFY (Read-only)
- `d-dataset/ocr_output/**` - Raw OCR data
- `d-dataset/answer_keys/**` - Answer key data
- `d-dataset/eslesmis_sorucevap.jsonl` - Production matched data
- `backend/alembic/versions/*.py` - Migration history
- `backend/app/core/config.py` - Core configuration (sensitive)
  - **⚠️ EVEN IF USER REQUESTS:** Config changes must go through `.env` or override mechanism, NEVER modify `core/config.py` directly
- `.env*` - Environment files (secrets)
- `node_modules/**` - Dependencies
- `venv/**` - Virtual environment
- `.git/**` - Git internals
- `kiro2-orchestrator/**` - Deprecated code

### ⚠️ NOT GIT-TRACKED (Persist on Disk Only)
- `d-dataset/scripts/**` - Pipeline scripts (manual backup needed)
- `d-dataset/processed/**` - Pipeline outputs (manual backup needed)
- These files are in `.gitignore` — changes survive across sessions but NOT across machines

**CRITICAL: Secrets & Environment**
- ❌ NEVER commit `.env*` files
- ❌ NEVER log secrets or API keys
- ❌ NEVER output secrets in responses
- ❌ Config changes: Use `.env` or environment variables, NOT `core/config.py`

## ⚠️ CRITICAL WARNINGS

### 1. Ripgrep Root Search Prevention
**NEVER run ripgrep on project root - causes 30min timeout!**

```bash
# ❌ WRONG: Searches entire 15GB+ project (timeout)
rg "pattern" C:\Users\husey\kiro2

# ✅ CORRECT: Target specific subdirectories
rg "pattern" C:\Users\husey\kiro2\backend\app
rg "pattern" C:\Users\husey\kiro2\orchestrator

# For multiple directories
rg "pattern" C:\Users\husey\kiro2\backend C:\Users\husey\kiro2\frontend
```

### 2. Directory Navigation
- Always use **orchestrator/** (active v2.5.0)
- Avoid **kiro2-orchestrator/** (deprecated legacy)

### 3. Turkish Text Encoding
**All Turkish text MUST be UTF-8 + NFC normalized (non-negotiable)**

### 4. Quality Gates (CI/CD)
All code changes must pass before commit:
```bash
# Backend quality gates (run from backend/ directory)
cd backend
ruff check . --fix                           # Linting
ruff format .                                # Formatting
mypy app/ --strict                           # Type checking (strict mode)
pytest -v --cov=app --cov-report=term-missing  # Tests + coverage with missing lines

# Frontend quality gates
cd frontend
npm run lint:fix          # ESLint with auto-fix
npm run format            # Prettier
npm run typecheck         # TypeScript
npm test -- --coverage    # Tests + coverage

# ❌ FAIL = DO NOT COMMIT
```

### 5. Basit Cozum Prensibi (KISS/YAGNI)
**Her zaman en basit calisan cozumu sec.**

- Yeni abstraction SADECE 3+ yerde tekrar ediliyorsa olustur
- Yeni dosya SADECE mevcut dosya 500+ satir veya sorumluluk farkliysa olustur
- Yeni hook/skill SADECE mevcut olanlar yetersiz kaliyorsa olustur
- Over-engineering sinyalleri: "ileride lazim olur", "esneklik icin", "genel amacli"

## 🔀 Agent Routing Rules

### Use Claude Code (this agent) for:

```yaml
ALWAYS_CLAUDE:
  - Turkish NLP tasks (sentiment, question generation, embeddings)
  - Qwen3-8B integration and fine-tuning
  - Complex multi-file refactoring
  - Security audits and vulnerability scanning
  - Database schema design and migrations
  - Performance optimization and profiling
  - Architectural decisions
  - Deep debugging requiring context preservation
  - d-dataset pipeline improvements
  - Orchestrator development
  - Turkish text normalization (NFC + casefold)
```

### Delegate to Codex CLI for:

```yaml
PREFER_CODEX:
  - New React component creation (simple, single-file)
  - FastAPI endpoint boilerplate (CRUD only)
  - Unit test generation (straightforward cases)
  - Documentation generation (OpenAPI, README)
  - Docker/CI-CD configuration (standard patterns)
  - Simple bug fixes (single-line, obvious)
  - CSS/Tailwind styling (non-complex)
```

### Routing Decision Logic

```
IF task contains [türkçe|turkish|nlp|qwen|sentiment] → Claude
IF task contains [security|auth|vulnerability|audit] → Claude
IF task contains [refactor|restructure|architecture] → Claude
IF task contains [d-dataset|ocr|matching|pipeline] → Claude
IF task contains [react|component|ui|frontend|css] AND simple → Codex
IF task contains [test|jest|pytest] AND straightforward → Codex
IF task contains [create|generate|add|new] AND clearly simple → Codex
IF task contains [debug|fix|optimize] AND complex → Claude
ELSE → Claude (default; repo is complex). Use Codex only for clearly simple tasks.
```

## 📋 Code Standards

### General
- All Turkish text MUST use **UTF-8 + NFC normalization**
- API response time target: <2s (realistic for complex queries)
- Test coverage minimum: 80%
- Follow existing patterns in codebase
- Use type hints everywhere (Python) / TypeScript (Frontend)

### Python/Backend
```python
# Use type hints everywhere
def create_question(content: str, topic_id: int) -> Question:
    ...

# Async by default for I/O operations
async def fetch_student_progress(student_id: int) -> Progress:
    ...

# Pydantic for validation
class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=2000)
    topic_id: int = Field(..., gt=0)
```

### React/Frontend
```typescript
// Functional components with TypeScript
interface QuestionCardProps {
  question: Question;
  onAnswer: (answer: string) => void;
}

const QuestionCard: React.FC<QuestionCardProps> = ({ question, onAnswer }) => {
  // Use hooks for state
  const [selected, setSelected] = useState<string | null>(null);
  ...
};
```

### Database
```sql
-- Always add indexes for foreign keys
CREATE INDEX idx_questions_topic_id ON questions(topic_id);

-- Use JSONB for flexible data
ALTER TABLE questions ADD COLUMN metadata JSONB DEFAULT '{}';
```

## 🇹🇷 Turkish NLP Guidelines

### ⚠️ CRITICAL: Turkish Text Normalization

**ALWAYS use NFC Unicode normalization + Turkish lowercase mapping**

```python
import unicodedata

def normalize_tr(text: str) -> str:
    """
    Normalize Turkish text for matching/comparison.
    
    CRITICAL RULES:
    1. NFC normalization FIRST (prevents İ decomposition)
    2. Turkish mapping: İ→i, I→ı (NOT İ→I!)
    3. Standard lowercase LAST
    
    ❌ WRONG: text.replace('İ', 'I')  # Breaks Turkish!
    ✅ CORRECT: See below
    """
    if not text:
        return text
    
    # Step 1: Unicode NFC normalization (prevents decomposition issues)
    text = unicodedata.normalize("NFC", text)
    
    # Step 2: Turkish-specific lowercase mapping
    text = text.replace("İ", "i").replace("I", "ı")
    
    # Step 3: Standard lowercase
    return text.lower()

def tr_casefold(text: str) -> str:
    """Case-insensitive comparison key for Turkish.
    
    Use this for:
    - Search queries
    - String comparison
    - Deduplication
    """
    return normalize_tr(text)

# Example usage
book_name = "ACİL Matematik İSTANBUL"
normalized = normalize_tr(book_name)  # "acil matematik istanbul"
```

### Zemberek Integration
```python
# Use zemberek for morphological analysis
from zemberek import TurkishMorphology

morphology = TurkishMorphology.create_with_defaults()

def analyze_turkish_word(word: str) -> list:
    """Morphological analysis for Turkish words."""
    return morphology.analyze(normalize_tr(word))
```

### Question Generation
```python
# Template for YKS-style questions
QUESTION_TEMPLATE = """
Aşağıdaki {konu} ile ilgili soruyu cevaplayınız:

{soru_metni}

A) {secenek_a}
B) {secenek_b}
C) {secenek_c}
D) {secenek_d}
E) {secenek_e}
"""
```

### Embeddings
- Use Qwen3-8B for Turkish text embeddings
- Vector dimension: 4096
- Similarity: cosine
- Store in pgvector

## 🔒 Security Requirements

### Authentication
- JWT tokens with 24h expiry
- Refresh tokens with 7d expiry
- Rate limiting: 100 req/min per user
  - **SSE endpoints exempt** from rate limiting (long-lived connections)
  - Alternative: Separate rate limit profile for SSE (1 connection per user)

### API Security
- Input validation on all endpoints
- SQL injection prevention (use ORM)
- XSS prevention (escape HTML)
- CORS configuration for frontend only

### Data Privacy
- Student data encrypted at rest
- PII anonymization in logs
- KVKK compliance (Turkish GDPR)

## 📈 Quality Metrics

### Current Status (as of 7 Feb 2026)
- Backend test results: **10,082 passed, 0 failures, 4,065 skipped**
  - Backend line coverage (api+core+services+models+algorithms): **~18%** (109K lines, massive codebase)
  - Run: `cd backend && pytest --cov=api --cov=core --cov=services --cov=models --cov=algorithms --cov-report=term`
- Orchestrator test results: **71 passed, 0 failures**
  - Run: `cd orchestrator && pytest tests/ -v`
- Frontend test files: **86 test files** (vitest, run takes 10+ minutes)
  - Run: `cd frontend && npx vitest run --coverage`

### Success Criteria
- ✅ All linting passes (ruff, mypy for Python)
- ✅ No type errors
- 🎯 API response time <2s (complex queries)
- 🎯 Test coverage >80% across all modules
- 🎯 High-confidence match rate >90%

### Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| API Response Time | <2s | ~2-3s | 🟡 Middleware ready, needs benchmarking |
| Vector Search | <100ms | **21ms** | 🟢 pgvector HNSW deployed |
| DB Queries | <50ms | ~150ms | 🟡 GIN+composite indexes ready (004) |
| Frontend Load | <2s | ~3s | 🟡 Needs optimization |
| **Total Clean Questions** | **45K by March** | **77,336** | 🟢 v3.5+ (172%), TARGET EXCEEDED |
| **Quality Rate (v2.2)** | **>95%** | **100%** | 🟢 0 critical in output |

## 🚀 Common Tasks

### Adding a New API Endpoint
```bash
# 1. Create schema in backend/app/schemas/
# 2. Add route in backend/app/api/
# 3. Implement service in backend/app/services/
# 4. Add tests in backend/tests/
# 5. Update OpenAPI docs
```

### Database Migration
```bash
# Generate migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Tests
```bash
# Backend with coverage
cd backend && pytest -v --cov=app --cov-report=html

# Frontend with coverage
cd frontend && npm test -- --coverage

# Orchestrator tests
cd orchestrator && pytest -v
```

### Measure Test Coverage
```bash
# Backend
cd C:\Users\husey\kiro2\backend
pytest --cov=app --cov-report=term-missing --cov-report=html

# View HTML report
# Open: backend/htmlcov/index.html

# Frontend
cd C:\Users\husey\kiro2\frontend
npm test -- --coverage

# View HTML report
# Open: frontend/coverage/lcov-report/index.html
```

## 🖥️ Windows Shell Notes

- Use `python` not `python3` (python3 doesn't exist on this Windows env)
- Path separators: `str(Path(...))` returns backslashes on Windows; use `.replace("\\", "/")` when needed for string operations
- Bash env vars: `VAR=value python script.py` works in Git Bash but not cmd/PowerShell

## 🔧 Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5434/kiro2  # Port 5434!
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key
QWEN_MODEL_PATH=/models/qwen3-8b-turkish

# Frontend (.env) - Vite standard
VITE_API_URL=http://localhost:8000
```

## 🌐 Real-time Communication

**Default:** Server-Sent Events (SSE)
- Unidirectional: Server → Client
- Use cases: Progress updates, notifications, leaderboard updates
- Endpoint pattern: `/api/v1/stream/*`

**Legacy:** WebSockets (deprecated, migration in progress)
- Bidirectional: Server ↔ Client
- Only for chat features (will migrate to SSE + polling)

## 📝 Commit Convention

```
feat: Add new feature
fix: Bug fix
refactor: Code refactoring
docs: Documentation
test: Tests
chore: Maintenance
perf: Performance improvement
style: Code style (formatting, etc.)
```

## ⚠️ Known Issues

### Current Challenges
1. **API Response Time**: Currently ~2-3s for complex queries
   - **Root cause**: Vector search on 36K+ questions
   - **Solution**: Query caching added to soru_bankasi_service + GIN indexes in migration 004
   - **Status**: Infrastructure ready, needs deployment + benchmarking

2. **Vector Search Performance**: pgvector queries ~300ms
   - **Root cause**: Large embedding dataset without HNSW indexing
   - **Solution**: HNSW index in migration 004 (m=16, ef_construction=200)
   - **Status**: Migration ready, needs `alembic upgrade head`

3. **Turkish Tokenization Edge Cases**
   - **Issue**: Some compound words not handled correctly
   - **Solution**: Enhance Zemberek integration, add custom rules

4. ~~**Low Confidence Matches (52.6%)**~~ **RESOLVED**
   - ~~Root cause: OCR errors, answer key format variations~~
   - **Result**: Phase 4 pipeline improved to 99.5% high-confidence (Feb 2026)

### Technical Debt
- [x] ~~Migrate from kiro2-orchestrator/ to orchestrator/~~ (deleted Feb 2026)
- [ ] Implement comprehensive test coverage (>80%) - currently ~18% backend
- [ ] Add performance monitoring dashboards
- [ ] Document all API endpoints in OpenAPI spec
- [ ] Migrate remaining WebSocket features to SSE

### GitHub Secrets (Required for CI/CD)

Configure in: Repository Settings → Secrets and variables → Actions

| Secret | Required | Purpose |
|--------|----------|---------|
| `GITHUB_TOKEN` | Auto | Built-in, auto-available for all workflows |
| `ANTHROPIC_API_KEY` | Yes | Claude AI code review (claude-ci.yml, claude-review.yml) |
| `SLACK_WEBHOOK_URL` | Optional | Health check alerts (health-checks.yml) |
| `SLACK_WEBHOOK` | Optional | Deployment notifications (deploy.yml) |
| `KUBE_CONFIG` | Staging | Kubernetes staging deployment (deploy.yml) |
| `PROD_KUBE_CONFIG` | Production | Kubernetes production deployment (deploy.yml) |
| `STAGING_TEST_PASSWORD` | Staging | Staging smoke test user password (deploy.yml) |
| `SNYK_TOKEN` | Optional | Security vulnerability scanning (security.yml) |

## 📞 Contact & Resources

- **Project Lead:** Hüseyin
- **Tech Stack:** FastAPI + React (Vite) + PostgreSQL (port 5434) + Redis + Qwen3-8B
- **Documentation:**
  - Main docs: `/docs`
  - API docs: http://localhost:8000/docs (when running)
  - Project guides: See uploaded documents

## 🎯 Q1 2026 Roadmap

### February
- [x] Complete Phase 1-3 of d-dataset pipeline (36,967 matches)
- [x] Measure and document test coverage (backend ~18%, 10,082 tests passing)
- [x] Implement Phase 4: Low-confidence improvement pipeline (99.5% high-confidence)
- [x] Clean up deprecated kiro2-orchestrator/ directory (deleted)
- [x] Performance optimization: indexes, caching, middleware (migration 004 ready)
- [x] GitHub Secrets documentation

### March
- [x] ~~Target: **45,000+ total clean questions**~~ Done: **77,336** (172% of target)
  - [x] ~~OCR pipeline fix (hallucination + letter-only)~~ Done
  - [x] ~~Process 118 remaining books~~ Done: 98/117 processed, 19 unviable
  - [ ] P1: Re-OCR recovery (+1,521-2,511 potential)
- [x] ~~Achieve **90%+ high-confidence match rate**~~ Done: 99.5%
- [x] ~~Manual QA + v2.2 quality pipeline~~ Done: 31,801 clean (100% pass)
- [x] ~~Vector search <100ms~~ Done: **21ms avg** (pgvector HNSW)
- [ ] Performance optimization: API <2s benchmark
- [ ] Git push fix (SSH setup for 5.5GB repo)
- [ ] Launch MVP for beta testing

## 📚 Lessons Learned (Agent Knowledge Base)

### Dogrulanmis Dersler (Verified, February 2026)

| # | Ders | Kategori | Uygulama |
|---|------|----------|----------|
| 1 | **Hibrit Yaklasim** | DRY/Refactoring | Merkezi fonksiyon + lokal fixture kombinasyonu en guvenli |
| 2 | **Adim Adim Ilerleme** | Process | 1 degisiklik -> 1 test -> basarili? devam : geri al |
| 3 | **Scope Analizi** | Test | Buyuk degisiklik oncesi bagimlilik ve context'i anla |
| 4 | **Geri Alma Stratejisi** | Safety | Her adimda recovery noktasi olustur |
| 5 | **Test Sonrasi Dogrulama** | Verification | Her kod degisikliginden sonra `pytest -x` ZORUNLU |

### Anti-Pattern'ler (Yapma!)

| Pattern | Neden Yanlis | Dogru Yaklasim |
|---------|--------------|----------------|
| Fixture'i tamamen kaldirmak | Context kaybi, test fail | Hibrit: import + lokal fixture |
| Buyuk degisiklik tek seferde | Geri almasi zor | Kucuk adimlar, her biri test edilebilir |
| Test calismadan commit | Hatalar prod'a gider | Her degisiklik sonrasi pytest |
| Scope anlamadan refactor | Beklenmeyen hatalar | Once analiz, sonra degisiklik |

### Agent'lara Entegre Edildi

- `.claude/rules/testing.md` - Ogrenilen dersler bolumu
- `.claude/rules/verification.md` - Adim adim ilerleme kurali
- `.claude/agents/verification-agent.md` - Dogrulanmis dersler tablosu
- `.claude/agents/kfc/spec-impl.md` - Anti-pattern'ler ve dersler

### Kaynak

Bu dersler JWT DRY Refactoring (Subat 2026) deneyiminden cikarilmistir:
- 9 dosyada kod tekrari tespit edildi
- Ilk yaklasim (tamamen merkezi) 32 test fail'e neden oldu
- Hibrit yaklasim ile 55 test pass elde edildi
- Boris Cherny verification feedback loop uygulandi

---

**Last Updated:** February 7, 2026
**Document Version:** 3.2
**Critical Fixes Applied:** Turkish normalization, Vite env, routing default, metric clarity, Lessons Learned section, Phase 4 results, performance indexes, GitHub Secrets, cleanup