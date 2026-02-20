# KIRO2 Project Instructions

## 🎯 Project Overview

KIRO2 is a Turkish EdTech platform for YKS/TYT/AYT university entrance exam preparation.

**Mission:** Deliver personalized, AI-powered exam preparation using Turkish NLP and adaptive learning.

**Project Root:** `C:\Users\husey\kiro2`

## 📊 Current Status (February 2026)

### Database & Content ✅
- ✅ **PostgreSQL 15** (port 5434) - Production ready
  - **PgBouncer:** Not yet configured (planned for 100K+ concurrent users)
- ✅ **Redis 7** (port 6379) - Session & cache layer
- ✅ **31,801 YKS questions in production** (v2.2, Target: 45K by March 2026)
  - 📊 **Pipeline:** 75,745 OCR → 36,713 matched (v2.1) → 31,801 clean (v2.2)
  - v2.2: 28,248 clean + 653 rescued + 2,900 flagged = 31,801
  - 4,912 silindi: hallucination (2,035), letter-only (1,330), generic (884), duplicate (635), twin (480)
  - 3,546 soru re-OCR ile kurtarılabilir (tahmini 1,521-2,511)
- ✅ **308 source books** processed from 426 total, **118 remaining**
- ✅ **eslesmis_sorucevap.jsonl** format in production (v2.2)
- ✅ **Quality pipeline**: validate_sample.py v2 (13 checks) + pipeline_v2_2.py (4-tier)

### 🎯 Next Priorities
1. ~~Low-confidence question refinement pipeline~~ ✅ **DONE** (+19,248 questions improved)
2. ~~Manual validation + v2.2 cleanup~~ ✅ **DONE** (4,912 silindi, 653 kurtarıldı, 31,801 production)
3. **P0: OCR pipeline fix** — hallucination prevention + letter-only fix (118 yeni kitap için)
4. **P0: 118 yeni kitap işleme** — 10,599-11,312 yeni soru hedefi
5. **P1: Re-OCR recovery** — 1,521-2,511 soru kurtarma (silinen 3,546'dan)
6. **Performance optimization**: API <2s, vector search <100ms

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
  - **v2.2: 31,801 questions (CURRENT PRODUCTION)**
    - 4,912 deleted (hallucination 2,035, letter-only 1,330, generic 884, duplicate 635, twin 480)
    - 653 rescued (twin option removal)
    - 2,900 flagged (warnings only)
    - 28,248 clean
  - **Pipeline**: `pipeline_v2_2.py` (4-tier) + `validate_sample.py` v2 (13 checks)
  - **Reports**: `v2.2_quality_report.md`, `book_analysis_report.md`

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
- v2.2: 31,801 questions (4,912 deep quality filtered, 653 rescued) ← CURRENT

### Quality Improvement Pipeline (d-dataset/scripts/)
```bash
# REQ-1: Zero-DB cross-validation (ignore unreliable DB answers)
python cross_validate_answers.py --zero-db --analyze --simulate

# REQ-2: Confidence calibration (Platt scaling + per-subject)
python confidence_calibration.py --output d-dataset/processed/calibration/

# REQ-3: Image quality audit + enhancement
python image_quality_audit.py --math-geo-only

# Orchestrator (runs all 3 in sequence)
python quality_improvement_pipeline.py --pilot --dry-run
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
| Vector Search | <100ms | ~300ms | 🟡 HNSW migration ready (004) |
| DB Queries | <50ms | ~150ms | 🟡 GIN+composite indexes ready (004) |
| Frontend Load | <2s | ~3s | 🟡 Needs optimization |
| **Total Clean Questions** | **45K by March** | **31,801** | 🟡 v2.2 (71%), +118 books needed |
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
- [ ] Target: **45,000+ total clean questions** (currently 31,801)
  - [ ] P0: OCR pipeline fix (hallucination + letter-only)
  - [ ] P0: Process 118 remaining books (+10,599-11,312)
  - [ ] P1: Re-OCR recovery (+1,521-2,511)
- [x] ~~Achieve **90%+ high-confidence match rate**~~ Done: 99.5%
- [x] ~~Manual QA + v2.2 quality pipeline~~ Done: 31,801 clean (100% pass)
- [ ] Performance optimization: deploy indexes, benchmark <2s API
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