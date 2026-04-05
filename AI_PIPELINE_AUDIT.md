# KIRO2 AI/OCR Pipeline Audit Report

**Generated:** 2026-04-05
**Section:** AI PIPELINE (OCR + Dataset Processing)
**Severity:** P0-P2 Issues Identified

---

## 1. PIPELINE OVERVIEW

### 1.1 Production Statistics (v3.5+)

| Metric | Value |
|--------|-------|
| Total Questions | **77,336** |
| Books Processed | 405 |
| Match Rate | ~85% book, ~15% AI solving |
| Validation Pass Rate | 100% |
| Critical Errors | 0 |

### 1.2 Version History

| Version | Questions | Changes |
|---------|-----------|---------|
| v1.0 | 36,967 | Initial |
| v2.4 | 86,249 | YOLO + OCR merge |
| v3.0 | 86,188 | answer_not_in_options fix |
| v3.1 | 80,208 | db_v7 + bos source removed |
| v3.2 | 77,537 | AI + PI_from_db_v7 removed |
| v3.3 | 76,554 | rematch + LOW conf removed |
| v3.4 | 76,527 | 27 crop'suz zayif removed |
| **v3.5+** | **77,336** | **Current production** |

---

## 2. DIRECTORY STRUCTURE AUDIT

```
d-dataset/
├── config.yaml                    # ✅ Main configuration
├── requirements.txt               # ✅ Python dependencies
├── CLAUDE.md                      # ✅ Project metadata
│
├── scripts/                       # ⚠️ NOT git-tracked (manual backup needed)
│   ├── pipeline.py               # ✅ Main YOLO + Multi-Provider OCR
│   ├── script_common.py          # ✅ 1,824 lines shared utilities
│   ├── ai_solve_pipeline.py      # ✅ AI self-solving
│   ├── cevap_crop_ocr.py          # ✅ Answer key extraction
│   ├── match_questions_v5.py      # ✅ Q&A matching with ultra-quality
│   ├── ab_validate_ocr.py         # ✅ A/B testing for OCR
│   ├── validate_3tier.py          # ✅ 3-tier validation
│   ├── ensemble_voting.py         # ✅ Ensemble voting
│   ├── phase4_page_inline_answers.py  # ✅ Inline answer extraction
│   ├── match_from_db.py          # ✅ DB-based matching
│   ├── vision_solve_gemini.py     # ✅ Vision-based solving
│   ├── local_ocr/                 # ✅ Local OCR models
│   │   ├── paddle_models/         # ✅ PaddleOCR models
│   │   └── setup_environment.bat
│   └── scripts_legacy/           # ⚠️ Legacy scripts
│
├── output/                        # ✅ Processing outputs
│   ├── detections/               # ✅ YOLO detection JSON
│   ├── crops/                     # ✅ Cropped question regions
│   ├── ocr_v3/                    # ✅ OCR results
│   ├── ocr_crops/                 # ✅ Crop OCR results
│   ├── matched_v4/               # ✅ Matched Q&A pairs
│   ├── matched_v5_combined/      # ✅ Combined matched
│   ├── recovered_v1/             # ✅ Recovered questions
│   ├── answer_keys_v7/           # ⚠️ Legacy (v7)
│   ├── answer_keys_v8/           # ✅ Current answer keys
│   └── final/                     # ✅ Final processed data
│
├── processed/                     # ⚠️ NOT git-tracked (manual backup needed)
│   ├── preprocessed_screenshots/ # ✅ Preprocessed books
│   ├── eslesmis_sorucevap*.jsonl # ✅ Matched datasets (v3.5+ current)
│   ├── quality_improvement/      # ✅ Quality outputs
│   └── vision_solve_crop/        # ✅ Vision solving results
│
├── answer_keys_extracted/        # ✅ Extracted answer key images
├── backups/                       # ✅ Backup versions
├── ocr_results/                   # ✅ OCR processing results
└── scripts_legacy/               # ⚠️ Legacy/archived scripts
```

---

## 3. PIPELINE STAGES AUDIT

### Stage 1: Book Screenshot Processing

| Aspect | Finding |
|--------|---------|
| Source | `C:\Users\husey\kiro2\veriseti\zkitap\screenshots\` |
| Books | 400+ YKS preparation books (TYT/AYT/YDT) |
| Format | PNG screenshots per page |
| Status | ✅ ACTIVE |

**Status:** ✅ HEALTHY

---

### Stage 2: YOLO Object Detection

| Aspect | Finding |
|--------|---------|
| Model | YOLO26 (`yolo26_best.pt`) |
| Classes | soru(0), konu(1), cevaplar(2), test_no(3), sayfa(4), cozum(5), kitap(6) |
| Confidence | 0.25 (configurable) |
| IOU Threshold | 0.45 |
| Device | cuda (GPU) |
| Output | JSON detections per page |

**Configuration (config.yaml):**
```yaml
yolo:
  confidence: 0.25
  iou_threshold: 0.45
  device: "cuda"
  classes: {0: soru, 1: konu, 2: cevaplar, 3: test_no, ...}
```

**Status:** ✅ HEALTHY

---

### Stage 3: Region Cropping

| Aspect | Finding |
|--------|---------|
| Extraction | Question regions, answer options, topics, test numbers |
| Padding | Configurable (default 10px) |
| Output | Individual PNG crop images |

**Status:** ✅ HEALTHY

---

### Stage 4: OCR Processing

**⚠️ MULTI-PROVIDER COMPLEXITY**

| Provider | Use Case | Status |
|----------|----------|--------|
| **Gemini Flash/Pro** | Primary OCR | ✅ ACTIVE |
| **GPT-4o-mini** | Secondary OCR | ✅ ACTIVE |
| **Qwen2.5-VL-2B** | Local via Ollama | ✅ ACTIVE |
| **PaddleOCR** | Fallback | ✅ ACTIVE |

**Environment Variables Required:**
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `DASHSCOPE_API_KEY` (for Qwen)

**Output Format:** JSONL with question text, options, metadata

**Status:** ✅ ROBUST (multi-provider fallback)

---

### Stage 5: Answer Key Extraction

**Three-Phase Strategy:**

| Phase | Method | Status |
|-------|--------|--------|
| 1 | Scan OCR results for answer patterns | ✅ |
| 2 | Process book-end pages (last 10%) | ✅ |
| 3 | Smart crop filtering and OCR | ✅ |

**Output:** SQLite database (`answers_v8.db`)

**Database Schema:**
```sql
-- answers_page_inline table
(book_name, page_number, question_number, answer, confidence, source)

-- answers table
(book_name, test_number, question_number, answer, confidence, source)

-- test_groups table
(book_name, group_id, chapter_index, first_page, last_page)
```

**Status:** ✅ COMPLETE

---

### Stage 6: Question-Answer Matching

| Strategy | Confidence | Status |
|----------|------------|--------|
| Page-based matching | 95% | ✅ |
| YOLO test_no direct | 90% | ✅ |
| Smart test estimation | 65-85% | ✅ |

**Matching Process:**
1. Page-based: Direct page alignment
2. YOLO detection: test_no field matching
3. Smart estimation: Fallback algorithm

**Status:** ✅ HIGH ACCURACY

---

### Stage 7: AI Self-Solving (Unmatched Questions)

**For questions without answer keys:**

| Aspect | Finding |
|--------|---------|
| Provider | Gemini Flash |
| Method | 3x Chain-of-Thought attempts |
| Voting | Majority voting (3/3=high, 2/3=medium) |
| Pro Verification | Optional for 2/3 cases |

**Output:** JSONL with AI-generated answers + confidence

**Status:** ✅ ACTIVE

---

### Stage 8: Quality Validation

**LLM-Free Validation (`script_common.py`):**

| Check | Implementation |
|-------|---------------|
| Question number extraction | 8 regex patterns |
| Option extraction | 5 patterns (A-E) |
| Hallucination detection | Identical options, letter-only, repeated text |
| Minimum quality | Text >= 30 chars, 3+ options |

**A/B Validation Criteria (`ab_validate_ocr.py`):**
- `cannot_solve` >= 20% relative reduction
- `invalid_option/no_answer` >= 15% relative reduction
- Answer-key match >= +2 percentage points
- Average latency increase <= 25%

**3-Tier Validation:**
- **Tier A:** Page-based direct match (highest)
- **Tier B:** YOLO test_no match (high)
- **Tier C:** Smart test estimation (medium)
- **Tier D:** AI self-solving with consensus

**Status:** ✅ COMPREHENSIVE

---

## 4. KEY SCRIPTS AUDIT

### 4.1 Main Pipeline Script
**File:** `d-dataset/scripts/pipeline.py`

| Aspect | Finding |
|--------|---------|
| Function | Main orchestrator - YOLO + OCR |
| Providers | Gemini, OpenAI, Ollama (Qwen), PaddleOCR |
| Features | Checkpointing, error recovery, GPU memory management |

**Status:** ✅ PRODUCTION READY

### 4.2 Shared Utilities
**File:** `d-dataset/scripts/script_common.py`

| Aspect | Finding |
|--------|---------|
| Lines | 1,824 |
| Functions | Turkish normalization, image preprocessing, quality metrics |

**Key Functions:**
```python
def normalize_turkish_text(text: str) -> str
def preprocess_image(image_path: str) -> np.ndarray
def calculate_quality_score(ocr_result: dict) -> float
def detect_hallucination(text: str) -> bool
def extract_question_number(text: str) -> Optional[int]
```

**Status:** ✅ WELL STRUCTURED

### 4.3 AI Solve Pipeline
**File:** `d-dataset/scripts/ai_solve_pipeline.py`

| Aspect | Finding |
|--------|---------|
| Purpose | Self-solving MCQs using Gemini Flash |
| Method | 3x CoT attempts + majority voting |
| Output | JSONL with answers + confidence |

**Status:** ✅ ACTIVE

### 4.4 Answer Key Extraction
**File:** `d-dataset/scripts/cevap_crop_ocr.py`

| Aspect | Finding |
|--------|---------|
| Model | Qwen3-VL via Ollama |
| Purpose | Answer key extraction from crops |

**Status:** ✅ ACTIVE

### 4.5 Matching Script
**File:** `d-dataset/scripts/match_questions_v5.py`

| Aspect | Finding |
|--------|---------|
| Purpose | Q&A matching with ultra-quality filtering |
| Confidence | Tier-based (A/B/C/D) |

**Status:** ✅ ACTIVE

---

## 5. DATA QUALITY AUDIT

### 5.1 Quality Metrics

| Metric | Threshold | Status |
|--------|-----------|--------|
| Text length | >= 30 chars | ✅ |
| Options count | 3-5 options | ✅ |
| Confidence | >= 70% | ✅ |
| Quality score | >= 50 | ✅ |

### 5.2 Filtered Categories (v3.5+ Cleanup)

| Category | Count | Reason |
|----------|-------|--------|
| db_v7 | REMOVED | Unreliable source |
| rematch | REMOVED | Match failure |
| LOW confidence | REMOVED | <70% confidence |
| Crop'suz | 27 removed | Missing image |

### 5.3 Current Quality Distribution

| Source | Count | Percentage |
|--------|-------|------------|
| Book answers | ~55,867 | 72.2% |
| AI crossval/bayes | ~12,691 | 16.4% |
| AI crop solve | 809 + 919 tier5 | 2.2% |

**Status:** ✅ HIGH QUALITY

---

## 6. DEPENDENCY AUDIT

### 6.1 External API Services

| Service | Configuration | Purpose |
|---------|---------------|---------|
| Gemini API | `GEMINI_API_KEY` | Primary OCR |
| OpenAI API | `OPENAI_API_KEY` | Secondary OCR |
| DashScope | `dashscope-intl.aliyuncs.com` | Qwen3.5-VL cloud |
| Ollama | `localhost:11434` | Local Qwen3-VL |

### 6.2 Local Models

| Model | Location | Purpose |
|-------|----------|---------|
| YOLO26 | `models/yolo26_best.pt` | Question detection |
| PaddleOCR | `scripts/local_ocr/paddle_models/` | Fallback OCR |
| Turkish BERT | `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr` | Embeddings |

### 6.3 GPU Configuration

| Aspect | Value |
|--------|-------|
| Compute | CUDA (RTX 3080 Laptop, 16GB VRAM) |
| Memory Fraction | 85% |
| Cache Clearing | Every 50 images |

**Status:** ✅ CONFIGURED

---

## 7. DATABASE CONNECTIONS AUDIT

### 7.1 PostgreSQL
**Connection:** `localhost:5434/kiro2`

| Purpose | Status |
|---------|--------|
| Question bank storage | ✅ ACTIVE |
| Import script | `import_to_kiro2.py` |

### 7.2 SQLite (Answer Keys)
**Databases:** `answers_v7.db`, `answers_v8.db`

| Version | Status |
|---------|--------|
| v7 | Legacy (deprecated) |
| **v8** | **Current production** |

**Note:** v8 removed `answers` table (39% accuracy was unusable)

### 7.3 ChromaDB
**Location:** `C:\Users\husey\kiro2\backend\vector_db`

| Purpose | Status |
|---------|--------|
| Semantic search embeddings | ✅ ACTIVE |

**Status:** ✅ HEALTHY

---

## 8. CONFIGURATION AUDIT

### 8.1 config.yaml Structure

```yaml
paths:
  source_dir: "C:/Users/husey/kiro2/veriseti/zkitap/screenshots"
  yolo_model: "C:/Users/husey/kiro2/models/yolo26_best.pt"
  output_dir: "C:/Users/husey/kiro2/d-dataset/output"

yolo:
  confidence: 0.25
  iou_threshold: 0.45
  device: "cuda"

ocr:
  provider: "dashscope"
  mode: "qwen3.5-plus"

processing:
  batch_size: 50
  checkpoint_interval: 100
  skip_first_pages: 10
  quality_routing:
    contrast: 20.0
    sharpness: 450.0
```

**Status:** ✅ WELL STRUCTURED

---

## 9. IMAGE QUALITY ASSESSMENT

### 9.1 Quality Routing

| Mode | Trigger | Action |
|------|---------|--------|
| Normal | contrast >= 20, sharpness >= 450 | Standard OCR |
| Fallback | contrast < 20 OR sharpness < 450 | Enhanced preprocessing |
| Severe | Both metrics very low | Manual review |

### 9.2 Root Cause Classification

| Cause | Indicator | Action |
|-------|-----------|--------|
| `pdf_low_dpi` | Resolution < 300px | Flag for reprocessing |
| `dark_scan` | Low contrast | Contrast enhancement |
| `blurry_scan` | Low sharpness | Sharpen filter |
| `poor_source` | Both low | Manual review |

**Status:** ✅ COMPREHENSIVE

---

## 10. PIPELINE LIMITATIONS AND RISKS

### 10.1 Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|-------------|
| 85% match rate | 15% must be AI-solved | Human review for critical |
| Turkish compound words | Tokenization issues | Zemberek enhancement planned |
| Chi-square 9.49 unrealistic | YKS books non-uniform | Empirical validation used |
| OCR provider rate limits | Processing delays | Multi-provider fallback |

### 10.2 ⚠️ Critical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Scripts not git-tracked | Backup risk | Manual backup required |
| Large processed files | Storage | Git LFS needed |
| API key exposure | Security | Env var management |
| GPU memory limits | Processing瓶颈 | Batch size tuning |

---

## 11. BACKUP AND RECOVERY AUDIT

### 11.1 Backup Strategy

| Data Type | Backup Location | Status |
|-----------|---------------|--------|
| Processed JSONL | `d-dataset/backups/` | ✅ |
| Answer DBs | `d-dataset/output/answer_keys_v*/` | ✅ |
| Scripts | Manual (not git-tracked) | ⚠️ |

### 11.2 Versioned Backups

| File | Questions | Date |
|------|-----------|------|
| `eslesmis_sorucevap_v3.4_backup_20260304.jsonl` | 76,527 | 2026-03-04 |
| `eslesmis_sorucevap_v3.3_backup_20260304.jsonl` | 76,554 | 2026-03-04 |
| `eslesmis_sorucevap_v3.2_backup_20260304.jsonl` | 77,537 | 2026-03-04 |
| `eslesmis_sorucevap_v3.1_backup_20260304.jsonl` | 80,208 | 2026-03-04 |
| `eslesmis_sorucevap_v2.4_backup_20260304.jsonl` | 86,249 | 2026-03-04 |

**Status:** ✅ GOOD BACKUP PRACTICE

---

## 12. ORCHESTRATOR INTEGRATION AUDIT

### 12.1 Backend Agent Systems

| System | Location | Purpose |
|--------|----------|---------|
| `DomainBlackboard` | `backend/agents/coordination/blackboard.py` | Redis-based communication |
| `LearningPathAgent` | `backend/agents/learning_path_agent.py` | ZPD-aware recommendations |

### 12.2 Claude Code Plugins

| Plugin | Purpose |
|--------|---------|
| `kiro2-yks` | IRT/ZPD/FSRS calculation tools |
| `kiro2-taxonomy` | SOLO, Marzano, Webb DOK classifiers |
| `kiro2-lsp` | Language server protocol |

### 12.3 Orchestrator Graph Status

**File:** `orchestrator/core/graph.py`

| Node | Status | Notes |
|------|--------|-------|
| `_plan_node` | ⚠️ TODO | LLM integration incomplete |
| `_implement_node` | ⚠️ TODO | Real implementation missing |
| `_review_node` | ⚠️ TODO | Stub implementation |

**Note:** Orchestrator has TODO markers - actual LLM integration incomplete

**Status:** ⚠️ NEEDS COMPLETION

---

## 13. FINDINGS SUMMARY

### 13.1 Critical Issues (P0)

| # | Issue | Location | Recommendation |
|---|-------|----------|----------------|
| 1 | Pipeline scripts not git-tracked | `d-dataset/scripts/` | Manual backup required |
| 2 | Orchestrator LLM integration incomplete | `orchestrator/core/graph.py` | Complete TODO markers |

### 13.2 High Priority Issues (P1)

| # | Issue | Location | Recommendation |
|---|-------|----------|----------------|
| 3 | 15% questions rely on AI solving | Pipeline | Increase book matching |
| 4 | Large processed files need Git LFS | `d-dataset/processed/` | Configure Git LFS |
| 5 | Multi-provider complexity | `pipeline.py` | Document fallback logic |

### 13.3 Medium Priority Issues (P2)

| # | Issue | Location | Recommendation |
|---|-------|----------|----------------|
| 6 | Turkish compound word handling | `script_common.py` | Zemberek enhancement |
| 7 | OCR provider rate limits | External APIs | Implement retry logic |
| 8 | GPU memory management | `pipeline.py` | Optimize batch sizes |

---

## 14. RECOMMENDATIONS

### Immediate Actions (This Week)

1. **Verify backup status** - Confirm all scripts backed up
2. **Check API key configuration** - Ensure env vars set
3. **Test recovery procedure** - Validate backup restore

### Short-term Actions (This Month)

1. **Configure Git LFS** - For large processed files
2. **Complete orchestrator LLM integration** - Replace TODO markers
3. **Increase match rate** - Improve book-based matching

### Long-term Actions (This Quarter)

1. **Zemberek enhancement** - Improve Turkish tokenization
2. **Quality monitoring** - Real-time quality dashboards
3. **Automated reprocessing** - Retry failed questions

---

## 15. VARSATIMLAR (Assumptions)

The following assumptions were made during this audit:

| # | Assumption | Basis |
|---|------------|-------|
| 1 | YOLO26 model file exists at specified path | Referenced in config.yaml |
| 2 | GPU has 16GB VRAM available | Specified in pipeline config |
| 3 | All API keys are set in environment | Required by multi-provider OCR |
| 4 | 405 books processed successfully | Production statistics |
| 5 | Scripts manual backup is adequate | Standard practice |

**Note:** These assumptions should be verified in production environment.

---

**Report Generated:** 2026-04-05
**Next:** See `INFRA_TEST_AUDIT.md` for infrastructure and test findings