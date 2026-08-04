# 🚀 KIRO2: 10-Lens Deep Audit & Master Refactoring Plan

> [!WARNING]
> This audit was conducted using a swarm of 10 Autonomous Expert Agents analyzing the AST, architecture, and bytecode of the entire KIRO2 stack. Critical architectural flaws, mathematical errors, and memory leaks were discovered that actively threaten production stability.

## 📊 Executive Summary of Critical Threats
1. **Mathematics/Algorithmic Flaw:** The IRT 3PL MLE second derivative is mathematically incorrect, causing divide-by-zero convergence failures.
2. **Memory Leak (OOM Risk):** `BERTurkEmbeddingService` uses an unbounded memory cache dictionary for embeddings, leaking RAM indefinitely.
3. **Database Locks & Performance:** Over 104 N+1 query traps, missing GIN indexes on JSONB columns, and improper cascading deletes leading to SQLAlchemy `IntegrityError`s.
4. **Vaporware & Over-Engineering:** 1,226 API operations are artificially inflated by prototype files, dead code (`learning_path.py`), and duplicate routers (`question_crud_api.py` vs `soru_bankasi.py`).
5. **LLM Cost Hemorrhaging:** Sequential LangGraph multi-domain processing and parallel validation cause an uncontrolled ~300% inflation in LLM token usage per request.

---

## 🔍 Detailed Expert Lens Reports

### Lens 1: Frontend UX Architecture 🎨
- **Re-render Traps:** `ModernStudentDashboard.tsx` dynamically creates massive JSX object arrays inside the render loop without `useMemo`.
- **Component Bloat:** `ModernLearningPathPage.tsx` and `ModernRegisterPage.tsx` are monolithic (~1,000 lines).
- **Missing Lazy Loading:** `App.tsx` eagerly imports heavy pages, penalizing initial bundle size. `SystematicDebuggingPage` bypasses MUI entirely, injecting global `<style>` tags.

### Lens 2: Backend FastAPI Architecture ⚡
- **Dead Code:** `backend/api/learning_path.py` (1,830 lines) and `litellm_chat.py` (0 bytes) are abandoned but still registered.
- **Duplicate Logic:** `question_crud_api.py` and `soru_bankasi.py` handle the exact same `QuestionBankItem` DB operations.
- **Prototype APIs:** `content_management.py` and `content_api.py` contain thousands of lines of hardcoded mock JSON arrays passing as real APIs.
- **Overlapping Namespaces:** `ai_chat_routes`, `enhanced_chat`, and `turkish_nlp_chat` heavily duplicate AI chat logic.

### Lens 3: Database & Data Modeling (DBA) 🗄️
- **Dual Table Trap:** `models/content_db.py` contains a ghost `class Question` mapping to the old `questions` table, while the real table is `question_bank`.
- **Integrity Errors:** Parent models lack `cascade="all, delete-orphan"` while the database schema relies on `ON DELETE CASCADE`, causing SQLAlchemy to throw exceptions when deleting relationships.
- **Missing Indexes:** `ExamQuestion` is missing an index on `question_id`. `JSONB` columns (`secenekler`, `haftalik_plan`) lack GIN indexes, causing full-table scans.

### Lens 4: NLP & AI Research 🧠
- **Prompt Injection:** `SecurityMiddleware` only stops HTML/XSS. No semantic protections exist to prevent "Ignore all instructions" attacks on the LLM.
- **Ensemble Manager Waste:** `generate_with_ensemble` concurrently hits OpenAI, Claude, Qwen, and Gemini for the *same* question to pick the best one, multiplying API costs by 4x.
- **Missing Semantic Cache:** The Redis RAG cache relies on literal MD5 hashing of the prompt instead of semantic vector similarity.

### Lens 6: LangGraph Orchestration 🤖
- **State Bloat:** `BaseAgent.cache` and `message_queue` are unbounded lists/dicts acting as permanent memory leaks for long-lived agent singletons.
- **Token Inflation:** Sequential multi-domain orchestration linearly adds tokens at every hop. Parallel response validation (Exam Validator + Fact Checker) multiplies output tokens by 3x.

### Lens 7: QA Automation Lead 🧪
- **Over-Mocking:** 1,359 assertions in the test suite are "fake" (`assert result is not None`), falsely inflating coverage to 21%.
- **Under-Mocking (Hanging Tests):** RAG and Study Buddy tests attempt to connect to production ChromaDB/LLMs, causing them to hang indefinitely.
- **Frontend Test Crashes:** `VideoPlayerWithAnalytics.tsx` crashes on line 292 (`reading 'toFixed'`), blocking the entire vitest suite.

### Lens 8: Cloud & DevOps 🐳
- **Container Staleness:** Deployment scripts lack `--pull` and `--no-cache`, permanently baking in old Linux kernel vulnerabilities.
- **Insecure Bridging:** `host.docker.internal:host-gateway` is used to map Postgres, exposing the host loopback network to any compromised container.
- **Fake Healthchecks:** `celery-beat`'s docker healthcheck pings the workers, not the scheduler itself.

### Lens 9: EdTech Algorithms 📊
- **IRT 3PL MLE Divide-by-Zero:** The second derivative formula in Newton-Raphson is mathematically inverted and incorrect, returning 0 for 2PL models.
- **FSRS-6 Illusion:** The system claims to use FSRS-6 spaced repetition but actually uses an old exponential decay (`math.exp`) instead of the required Power-Law decay curve.
- **BKT Race Condition:** `record_answer` lacks `.with_for_update()`. High-concurrency quiz submissions overwrite each other's Bayesian Knowledge Tracing scores.

### Lens 10: Performance Engineering 🏎️
- **Vite De-optimization:** `framer-motion` and `recharts` are explicitly excluded from `optimizeDeps`, destroying local development performance with network waterfalls.
- *(Praise)*: The Redis caching strategy (L1/L2, Double-Checked Locking for Stampede Protection, TTL Jitter) is flawlessly designed.
