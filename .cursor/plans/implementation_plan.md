# KIRO2 Multi-Agent Implementation Plan — Session 138

This document serves as the step-by-step execution roadmap to resolve the architectural, concurrency, performance, and Turkish NLP vulnerabilities identified in [AGENTS_STRATEGY.md](file:///C:/Users/husey/kiro2/AGENTS_STRATEGY.md).

---

## Phase 1: Zero-Tolerance Linguistic & Parsing Fixes (Claude 4.6 Thinking Domain)

### Step 1.1: Fix the Turkish Casing Bug in Normalization & Reranker
*   **Target Files:**
    *   [zemberek_service.py:L259](file:///C:/Users/husey/kiro2/backend/core/zemberek_service.py#L259)
    *   [enhanced_turkish_nlp.py:L334](file:///C:/Users/husey/kiro2/backend/ai_engine/enhanced_turkish_nlp.py#L334)
    *   [question_reranker.py:L80](file:///C:/Users/husey/kiro2/backend/services/question_reranker.py#L80)
*   **Problem:** Standard Python `.lower()` permanently converts dotted uppercase `İ` and dotless uppercase `I` incorrectly under non-Turkish locales, corrupting vocabulary matches.
*   **Action Plan:**
    *   Import and use `normalize_tr` from `core.turkish_nlp_utils` instead of raw `.lower()`.
    *   Example replacement:
        ```python
        # BEFORE
        normalized = text.lower()
        
        # AFTER
        from core.turkish_nlp_utils import normalize_tr
        normalized = normalize_tr(text)
        ```
*   **Verification:** Run `pytest tests/unit/test_turkish_normalization.py` or run a manual test script.

### Step 1.2: Fix the Vowel Harmony Bug in Infinitive Generator
*   **Target File:** [lemmatization.py:L252-L268](file:///C:/Users/husey/kiro2/backend/mcp_servers/zemberek_nlp/tools/lemmatization.py#L252-L268)
*   **Problem:** The front vowel mapping includes the back vowel `o` and omits the front vowel `ü`, creating corrupted infinitives (e.g., producing `koşmek` instead of `koşmak` and `sürmak` instead of `sürmek`).
*   **Action Plan:**
    *   Correct the vowel lists in `_get_infinitive`:
        ```python
        # BEFORE
        if last_vowel in "eioö":
            return lemma + "mek"
        
        # AFTER
        if last_vowel in "eiöü":  # Correct front vowels
            return lemma + "mek"
        ```
*   **Verification:** Execute Zemberek NLP unit tests: `pytest tests/ -k lemmatization`.

### Step 1.3: Fix Multiline Regex Matching in Heuristics
*   **Target File:** [assign_difficulty_heuristic.py:L114](file:///C:/Users/husey/kiro2/backend/scripts/assign_difficulty_heuristic.py#L114)
*   **Problem:** Regex checks on `COMPLEX_PATTERNS` fail to match multiline paragraphs because the `re.DOTALL` / `re.S` flag is omitted.
*   **Action Plan:**
    *   Append `re.DOTALL` to all regex compiling and search operations within difficulty checks:
        ```python
        # BEFORE
        match = re.search(pattern, text)
        
        # AFTER
        match = re.search(pattern, text, re.DOTALL)
        ```
*   **Verification:** Run `python scripts/assign_difficulty_heuristic.py --dry-run` and verify difficulty assignments.

### Step 1.4: Fix ChromaDB Fallback Vector Dimensions
*   **Target File:** [duplicate_detection_service.py:L139](file:///C:/Users/husey/kiro2/backend/services/duplicate_detection_service.py#L139)
*   **Problem:** The fallback hash-based vector generator outputs a 128-dimensional vector, which mismatches the 768-dimensional configuration of ChromaDB, causing immediate insertion crashes.
*   **Action Plan:**
    *   Change the fallback embedding padding to output a 768-dimensional vector.
        ```python
        # Ensure padding length matches the target embedding model dimension (768)
        padding_length = EmbeddingConfig.get_model_dimension()  # 768
        ```
*   **Verification:** Run deduplication unit tests: `pytest tests/ -k duplicate_detection`.

### Step 1.5: Fix Gemini OCR Paragraph Truncation
*   **Target File:** [gemini_ocr.py:L295](file:///C:/Users/husey/kiro2/backend/services/question_parser/gemini_ocr.py#L295)
*   **Problem:** Fragile start-of-line checks discard entire paragraphs starting with `"Soru"`, `"Konu"`, etc.
*   **Action Plan:**
    *   Refactor the text sanitizer to clean prefixes instead of stripping the entire line.
*   **Verification:** Run OCR parsing tests to verify question text preservation.

---

## Phase 2: Concurrency & Lifecycle Hotfixes (Gemini 3.1 Pro / 3.5 Flash Domain)

### Step 2.1: Fix Celery Event Loop Mismatch Crashes
*   **Target File:** [database.py:L324](file:///C:/Users/husey/kiro2/backend/core/database.py#L324) (DatabaseManager class)
*   **Problem:** Celery tasks run asynchronous operations in closed loops via `asyncio.run()`, while the global database manager retains an initialization flag, attempting to reuse closed engine pools.
*   **Action Plan:**
    *   Modify `DatabaseManager.initialize()` to check if the current event loop matches the initialized loop:
        ```python
        async def initialize(self) -> None:
            current_loop = asyncio.get_running_loop()
            if self._initialized and self._loop == current_loop:
                return
            # Initialize engine/sessionmaker bound to current_loop
            self._loop = current_loop
            self._initialized = True
        ```
*   **Verification:** Run celery task simulations and verify database query success across successive tasks.

### Step 2.2: Fix LLM Service Event Loop Blocking
*   **Target File:** [langchain_llm_service_enhanced.py:L167-L169](file:///C:/Users/husey/kiro2/backend/core/langchain_llm_service_enhanced.py#L167-L169)
*   **Problem:** `agenerate` runs a synchronous HTTP post request with a 30s timeout, blocking FastAPI's single-threaded event loop.
*   **Action Plan:**
    *   Offload the synchronous call to FastAPI's background thread pool:
        ```python
        from fastapi.concurrency import run_in_threadpool
        
        async def agenerate(self, prompt: str) -> str:
            return await run_in_threadpool(self.generate, prompt)
        ```
*   **Verification:** Run concurrency load testing using `ab` or `locust` to verify that other endpoints respond while LLM is generating.

### Step 2.3: Fix Cache Headers Middleware RAM Exhaustion (OOM)
*   **Target File:** [cache_headers.py:L388-L390](file:///C:/Users/husey/kiro2/backend/core/middleware/cache_headers.py#L388-L390)
*   **Problem:** Buffering large responses to generate ETags exhausts container memory under concurrent loads.
*   **Action Plan:**
    *   Cap buffering at 2MB. If the payload size exceeds this limit, bypass ETag generation and stream the response directly.
*   **Verification:** Perform load testing on large PDF exports and verify stable container RAM usage.

### Step 2.4: Close Redis connection pool in lifespan
*   **Target File:** [application.py:L178-L179](file:///C:/Users/husey/kiro2/backend/core/application.py#L178-L179)
*   **Problem:** Leaked Redis sockets occur on app reloading because the pool is not disposed of during shutdown.
*   **Action Plan:**
    *   Import and call `await cache_manager.close()` during the shutdown phase of FastAPI lifespan.
*   **Verification:** Verify active socket count remains stable during multiple reload sequences.

### Step 2.5: Modernize Pydantic v1 configs
*   **Target Files:**
    *   [dependencies.py:L89](file:///C:/Users/husey/kiro2/backend/core/dependencies.py#L89)
    *   [cat_schemas.py:L18](file:///C:/Users/husey/kiro2/backend/app/schemas/cat_schemas.py#L18)
    *   [student_feedback_api.py:L74](file:///C:/Users/husey/kiro2/backend/api/student_feedback_api.py#L74)
*   **Problem:** Nested `class Config` definitions trigger compatibility wrappers, slow down initialization, and throw deprecation warnings.
*   **Action Plan:**
    *   Refactor nested `class Config:` to `model_config = ConfigDict(...)` configuration model.
*   **Verification:** Run `pytest` and verify that all Pydantic compatibility warnings are resolved.

---

## Phase 3: Repository Decoupling & Test Coverage Expansion (Gemini 3.1 Pro Domain)

### Step 3.1: Decouple Routers from Direct Model Access
*   **Target Directory:** `backend/api/` (140+ files)
*   **Action Plan:**
    *   Audit database queries across routers.
    *   Route queries through `backend/repositories/` (e.g. `UserRepository`, `QuestionRepository`) instead of issuing raw session queries on database models directly.
*   **Verification:** Run `python scripts/audit_architecture.py` to verify layered compliance.

### Step 3.2: Write Unit and Integration Tests to Meet 80% Coverage Target
*   **Target Directory:** `backend/tests/`
*   **Action Plan:**
    *   Analyze test coverage report and identify untested methods.
    *   Add tests for edge cases, database queries, and async loop handling.
*   **Verification:** Run `pytest tests/ --cov=backend` and confirm coverage is above 80%.
