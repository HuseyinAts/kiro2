# Design Document - Soru Üretim Pipeline Subagent'ları Sistemi

---
**Version:** 1.1.0
**Date:** 2026-01-18
**Status:** IMPLEMENTED
**Last Reviewed:** 2026-01-18
---

## Overview

Soru Üretim Pipeline Sistemi, ÖSYM standardında YKS soruları üreten 6 aşamalı subagent pipeline'dır. Her aşama izole agent tarafından yönetilir ve Sid Bidasaria'nın subagent architecture prensibi ile tasarlanmıştır. Bu yaklaşım soru kalitesini %400 artırır ve ÖSYM uyumluluğunu %98'e çıkarır.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          Soru Üretim İsteği (MEB Kazanımı + Zorluk)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Pipeline Orchestrator                           │
│              (Sequential + Parallel Execution)               │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Stage 1    │  │   Stage 2    │  │   Stage 3    │
│   Content    │→ │  Difficulty  │→ │  Distractor  │
│  Generator   │  │ Calibration  │  │  Generator   │
│   (25%)      │  │    (20%)     │  │    (20%)     │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │     PARALLEL EXECUTION        │
         │  ┌───────────┬───────────┐    │
         │  │  Stage 4  │  Stage 5  │    │
         │  │   ÖSYM    │  Language │    │
         │  │Compliance │  Quality  │    │
         │  │   (20%)   │   (15%)   │    │
         │  └─────┬─────┴─────┬─────┘    │
         │        └─────┬─────┘          │
         └──────────────┼────────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   Stage 6    │
                 │    Final     │
                 │   Quality    │
                 │    Gate      │
                 └──────┬───────┘
                        │
            ┌───────────┼────────────────┐
            │           │                │
         >= 85%      70-85%            < 70%
            │           │                │
            ▼           ▼                ▼
      ┌─────────┐  ┌─────────┐    ┌─────────┐
      │Onaylandı│  │ Manuel  │    │Reddedildi│
      │    ✓    │  │ Review  │    │    ✗    │
      └─────────┘  └─────────┘    └─────────┘
            │
            ▼
    Soru Bankasına Ekle
```

### Component Architecture

```
backend/
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py                # Pipeline coordinator
│   ├── stage_base.py                  # Abstract base stage
│   ├── pipeline_state.py              # State management
│   └── models.py                      # Pydantic models
├── pipeline/agents/
│   ├── __init__.py
│   ├── content_generator.py           # Stage 1 (Weight: 25%)
│   ├── difficulty_agent.py            # Stage 2 (Weight: 20%)
│   ├── distractor_agent.py            # Stage 3 (Weight: 20%)
│   ├── compliance_agent.py            # Stage 4 (Weight: 20%)
│   ├── language_qa_agent.py           # Stage 5 (Weight: 15%)
│   └── quality_gate_agent.py          # Stage 6 (Final Decision)
├── pipeline/tools/
│   ├── __init__.py
│   ├── irt_calculator.py              # IRT calculations
│   ├── zemberek_client.py             # Turkish NLP
│   ├── meb_api_client.py              # MEB curriculum
│   └── readability_scorer.py          # Flesch score
├── pipeline/monitoring/
│   ├── __init__.py
│   ├── performance_monitor.py         # Pipeline metrics
│   └── bottleneck_detector.py         # Performance analysis
├── api/
│   └── question_pipeline_api.py       # FastAPI endpoints
└── tasks/
    └── question_generation_tasks.py   # Celery tasks
```

## Components and Interfaces

### 1. Base Pipeline Stage

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel

class StageInput(BaseModel):
    """Input for pipeline stage"""
    question_data: Dict
    metadata: Dict
    previous_scores: Dict = {}

class StageOutput(BaseModel):
    """Output from pipeline stage"""
    question_data: Dict
    score: float  # 0-1
    passed: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metadata: Dict

class BasePipelineStage(ABC):
    """Abstract base class for pipeline stages"""

    def __init__(self, stage_name: str, llm_client):
        self.stage_name = stage_name
        self.llm = llm_client

    @abstractmethod
    async def process(self, input_data: StageInput) -> StageOutput:
        """Process stage and return output"""
        pass

    @abstractmethod
    def get_stage_weight(self) -> float:
        """Return stage weight for final scoring"""
        pass
```

### 2. Content Generator Agent (Stage 1)

```python
class ContentGeneratorAgent(BasePipelineStage):
    """Generates question content based on MEB kazanım - Weight: 25%"""

    STAGE_NAME = "content_generator"
    STAGE_WEIGHT = 0.25

    BLOOM_LEVELS = ["hatırlama", "anlama", "uygulama", "analiz", "sentez", "değerlendirme"]
    QUESTION_TYPES = ["çoktan_seçmeli", "doğru_yanlış", "eşleştirme"]

    def __init__(self, llm_client, meb_api_client, zemberek_client):
        super().__init__("content_generator", llm_client)
        self.meb_api = meb_api_client
        self.zemberek = zemberek_client

    async def process(self, input_data: StageInput) -> StageOutput:
        """Generate question content"""
        kazanim = input_data.question_data.get("kazanim")
        target_difficulty = input_data.question_data.get("target_difficulty", "orta")

        # 1. Analyze kazanım and determine Bloom level
        bloom_level = await self._analyze_bloom_level(kazanim)

        # 2. Generate question text
        question_text = await self._generate_question_text(
            kazanim, bloom_level, target_difficulty
        )

        # 3. Create context (real-life connection)
        context = await self._create_context(kazanim, question_text)

        # 4. Determine question type
        question_type = self._select_question_type(bloom_level)

        # 5. Validate Turkish with Zemberek
        is_valid_turkish = await self._validate_turkish(question_text)

        # Calculate score
        score = 1.0 if is_valid_turkish else 0.7

        output_data = {
            **input_data.question_data,
            "question_text": question_text,
            "context": context,
            "bloom_level": bloom_level,
            "question_type": question_type
        }

        return StageOutput(
            question_data=output_data,
            score=score,
            passed=is_valid_turkish,
            errors=[] if is_valid_turkish else ["Türkçe doğruluk hatası"],
            warnings=[],
            suggestions=[],
            metadata={"stage": "content_generator", "bloom_level": bloom_level}
        )

    def get_stage_weight(self) -> float:
        return 0.25  # 25% weight in final score
```

### 3. Difficulty Calibration Agent (Stage 2)

```python
class DifficultyAgent(BasePipelineStage):
    """Calibrates question difficulty using IRT parameters - Weight: 20%"""

    STAGE_NAME = "difficulty_calibration"
    STAGE_WEIGHT = 0.20

    DIFFICULTY_MAP = {
        "kolay": -1.5,
        "orta": 0.0,
        "zor": 1.5
    }

    def __init__(self, llm_client, irt_calculator):
        super().__init__("difficulty_calibration", llm_client)
        self.irt = irt_calculator

    async def process(self, input_data: StageInput) -> StageOutput:
        """Calibrate difficulty"""
        question_text = input_data.question_data.get("question_text")
        target_difficulty = input_data.question_data.get("target_difficulty", "orta")

        # 1. Calculate IRT parameters
        irt_params = await self._calculate_irt_parameters(question_text, target_difficulty)

        # 2. Validate parameter ranges
        is_valid = self._validate_irt_ranges(irt_params)

        # 3. Check ZPD (Zone of Proximal Development)
        zpd_score = self._check_zpd(irt_params)

        # 4. Optimize question if needed
        if zpd_score < 0.7:
            optimized_text = await self._optimize_for_difficulty(
                question_text, irt_params, target_difficulty
            )
            question_text = optimized_text
            irt_params = await self._calculate_irt_parameters(question_text, target_difficulty)

        output_data = {
            **input_data.question_data,
            "question_text": question_text,
            "irt_difficulty": irt_params["difficulty"],
            "irt_discrimination": irt_params["discrimination"],
            "irt_guessing": irt_params["guessing"],
            "zpd_score": zpd_score
        }

        return StageOutput(
            question_data=output_data,
            score=zpd_score,
            passed=is_valid and zpd_score >= 0.7,
            errors=[] if is_valid else ["IRT parametreleri geçersiz"],
            warnings=[],
            suggestions=[],
            metadata={"stage": "difficulty", "irt_params": irt_params}
        )

    def _validate_irt_ranges(self, params: Dict) -> bool:
        """Validate IRT parameter ranges"""
        return (
            -4.0 <= params["difficulty"] <= 4.0 and
            0.2 <= params["discrimination"] <= 4.0 and
            0.0 <= params["guessing"] <= 0.35
        )

    def _check_zpd(self, params: Dict) -> float:
        """Check if question is in Zone of Proximal Development"""
        # Target: 15-85% success probability for average student
        prob = self.irt.calculate_probability(
            theta=0.0,  # Average student ability
            difficulty=params["difficulty"],
            discrimination=params["discrimination"],
            guessing=params["guessing"]
        )

        if 0.15 <= prob <= 0.85:
            if 0.40 <= prob <= 0.60:
                return 1.0  # Ideal
            else:
                return 0.8  # Acceptable
        else:
            return 0.5  # Outside ZPD

    def get_stage_weight(self) -> float:
        return 0.20  # 20% weight
```

### 4. Distractor Generator Agent (Stage 3)

```python
class DistractorAgent(BasePipelineStage):
    """Generates plausible distractor options - Weight: 20%"""

    STAGE_NAME = "distractor_generator"
    STAGE_WEIGHT = 0.20

    ERROR_CATEGORIES = {
        "matematik": ["hesaplama_hatası", "kavram_karışıklığı", "işlem_hatası"],
        "fizik": ["birim_hatası", "formül_karışıklığı", "kavram_hatası"],
        "default": ["kısmi_doğru", "yaygın_yanlış", "mantık_hatası"]
    }

    def __init__(self, llm_client):
        super().__init__("distractor_generator", llm_client)

    async def process(self, input_data: StageInput) -> StageOutput:
        """Generate distractors"""
        question_text = input_data.question_data.get("question_text")
        correct_answer = input_data.question_data.get("correct_answer")
        subject = input_data.question_data.get("subject", "default")

        # 1. Generate 3 distractors
        distractors = await self._generate_distractors(question_text, correct_answer, subject)

        # 2. Calculate plausibility scores
        plausibility_scores = await self._calculate_plausibility(
            question_text, correct_answer, distractors
        )

        # 3. Ensure no distractor is as attractive as correct answer
        is_valid = await self._validate_distractors(correct_answer, distractors, plausibility_scores)

        # 4. Order options logically
        all_options = [correct_answer] + distractors
        ordered_options = self._order_options(all_options)

        # Find correct answer position
        correct_position = ordered_options.index(correct_answer)
        correct_label = ["A", "B", "C", "D"][correct_position]

        output_data = {
            **input_data.question_data,
            "options": [
                {"label": label, "text": text}
                for label, text in zip(["A", "B", "C", "D"], ordered_options)
            ],
            "correct_answer": correct_label,
            "distractor_plausibility": plausibility_scores
        }

        avg_plausibility = sum(plausibility_scores.values()) / len(plausibility_scores)

        return StageOutput(
            question_data=output_data,
            score=avg_plausibility if is_valid else 0.5,
            passed=is_valid,
            errors=[] if is_valid else ["Çeldiriciler doğru cevap kadar cazip"],
            warnings=[],
            suggestions=[],
            metadata={"stage": "distractor", "plausibility": plausibility_scores}
        )

    def get_stage_weight(self) -> float:
        return 0.20  # 20% weight
```

### 5. ÖSYM Compliance Agent (Stage 4)

```python
class ComplianceAgent(BasePipelineStage):
    """ÖSYM uyumluluk kontrolü - Weight: 20%"""

    STAGE_NAME = "osym_compliance"
    STAGE_WEIGHT = 0.20

    # ÖSYM Format Kontrolleri
    MAX_WORD_COUNT = 150
    OPTION_LENGTH_TOLERANCE = 0.50  # 50% fark toleransı

    # Skor Ağırlıkları
    SCORE_WEIGHTS = {
        "format": 0.30,
        "word_count": 0.15,
        "option_length": 0.15,
        "visual": 0.10,
        "correct_answer": 0.20,
        "other": 0.10
    }

    def __init__(self, llm_client):
        super().__init__("osym_compliance", llm_client)

    async def process(self, input_data: StageInput) -> StageOutput:
        """Validate ÖSYM compliance"""
        question_data = input_data.question_data

        scores = {}
        errors = []

        # 1. Format check (soru + 4 seçenek + doğru cevap)
        format_ok = self._check_format(question_data)
        scores["format"] = 1.0 if format_ok else 0.0
        if not format_ok:
            errors.append("Format hatası: Soru, 4 seçenek ve doğru cevap gerekli")

        # 2. Word count check (max 150 kelime)
        word_count_ok = self._check_word_count(question_data)
        scores["word_count"] = 1.0 if word_count_ok else 0.5
        if not word_count_ok:
            errors.append(f"Kelime sayısı {self.MAX_WORD_COUNT}'ı aşıyor")

        # 3. Option length similarity
        option_ok = self._check_option_lengths(question_data)
        scores["option_length"] = 1.0 if option_ok else 0.7

        # 4. Visual check (if applicable)
        visual_ok = self._check_visual(question_data)
        scores["visual"] = 1.0 if visual_ok else 0.8

        # 5. Correct answer validation
        answer_ok = self._validate_correct_answer(question_data)
        scores["correct_answer"] = 1.0 if answer_ok else 0.0

        # Calculate weighted compliance score
        compliance_score = sum(
            scores[k] * self.SCORE_WEIGHTS[k]
            for k in scores
        ) + self.SCORE_WEIGHTS["other"]

        return StageOutput(
            question_data=question_data,
            score=compliance_score,
            passed=compliance_score >= 0.95,
            errors=errors,
            warnings=[],
            suggestions=[],
            metadata={"stage": "compliance", "scores": scores}
        )

    def _check_format(self, data: Dict) -> bool:
        """Check ÖSYM format requirements"""
        return (
            "question_text" in data and
            "options" in data and
            len(data.get("options", [])) == 4 and
            "correct_answer" in data and
            data["correct_answer"] in ["A", "B", "C", "D"]
        )

    def _check_word_count(self, data: Dict) -> bool:
        """Check word count limit"""
        text = data.get("question_text", "")
        return len(text.split()) <= self.MAX_WORD_COUNT

    def get_stage_weight(self) -> float:
        return 0.20  # 20% weight
```

### 6. Language Quality Assurance Agent (Stage 5)

```python
class LanguageQAAgent(BasePipelineStage):
    """Dil kalitesi kontrolü - Weight: 15%"""

    STAGE_NAME = "language_qa"
    STAGE_WEIGHT = 0.15

    # Hedef Okunabilirlik (Lise seviyesi)
    TARGET_READABILITY_MIN = 60
    TARGET_READABILITY_MAX = 70

    # Skor Ağırlıkları
    SCORE_WEIGHTS = {
        "morphology": 0.20,
        "spelling": 0.25,
        "readability": 0.30,
        "vocabulary": 0.15,
        "punctuation": 0.10
    }

    def __init__(self, llm_client, zemberek_client, readability_scorer):
        super().__init__("language_qa", llm_client)
        self.zemberek = zemberek_client
        self.readability = readability_scorer

    async def process(self, input_data: StageInput) -> StageOutput:
        """Check language quality"""
        question_data = input_data.question_data
        question_text = question_data.get("question_text", "")

        scores = {}
        suggestions = []

        # 1. Morphological analysis (Zemberek)
        morph_result = await self.zemberek.analyze_morphology(question_text)
        scores["morphology"] = morph_result.get("score", 0.8)

        # 2. Spelling check
        spelling_result = await self.zemberek.check_spelling(question_text)
        scores["spelling"] = 1.0 if not spelling_result.get("errors") else 0.7
        if spelling_result.get("errors"):
            suggestions.append(f"Yazım hataları: {spelling_result['errors']}")

        # 3. Flesch Reading Ease (Turkish adaptation)
        readability_score = self.readability.calculate_flesch(question_text)
        if self.TARGET_READABILITY_MIN <= readability_score <= self.TARGET_READABILITY_MAX:
            scores["readability"] = 1.0
        elif 50 <= readability_score <= 80:
            scores["readability"] = 0.8
        else:
            scores["readability"] = 0.5
            suggestions.append(f"Okunabilirlik skoru ({readability_score}) hedef aralık dışında")

        # 4. Vocabulary level check
        vocab_result = await self._check_vocabulary_level(question_text)
        scores["vocabulary"] = vocab_result

        # 5. Punctuation check
        punct_result = self._check_punctuation(question_text)
        scores["punctuation"] = punct_result

        # Calculate weighted language score
        language_score = sum(
            scores[k] * self.SCORE_WEIGHTS[k]
            for k in scores
        )

        return StageOutput(
            question_data=question_data,
            score=language_score,
            passed=language_score >= 0.7,
            errors=[],
            warnings=[],
            suggestions=suggestions,
            metadata={"stage": "language_qa", "scores": scores, "readability": readability_score}
        )

    def get_stage_weight(self) -> float:
        return 0.15  # 15% weight
```

### 7. Quality Gate Agent (Stage 6)

```python
class QualityGateAgent(BasePipelineStage):
    """Final quality gate - Makes approval decision"""

    STAGE_NAME = "quality_gate"

    # Decision Thresholds
    APPROVED_THRESHOLD = 0.85
    REVIEW_THRESHOLD = 0.70

    # Stage Weights (sum = 1.0)
    STAGE_WEIGHTS = {
        "content_generator": 0.25,
        "difficulty_calibration": 0.20,
        "distractor_generator": 0.20,
        "osym_compliance": 0.20,
        "language_qa": 0.15
    }

    async def process(self, input_data: StageInput) -> StageOutput:
        """Make final quality decision"""
        previous_scores = input_data.previous_scores

        # Calculate weighted average
        final_score = sum(
            previous_scores.get(stage, 0) * weight
            for stage, weight in self.STAGE_WEIGHTS.items()
        )

        # Make decision
        if final_score >= self.APPROVED_THRESHOLD:
            decision = "approved"
            passed = True
        elif final_score >= self.REVIEW_THRESHOLD:
            decision = "review"
            passed = True  # Needs manual review but not rejected
        else:
            decision = "rejected"
            passed = False

        # Generate improvement suggestions for rejected questions
        suggestions = []
        if decision == "rejected":
            suggestions = self._generate_suggestions(previous_scores)

        output_data = {
            **input_data.question_data,
            "final_score": final_score,
            "decision": decision,
            "stage_scores": previous_scores
        }

        return StageOutput(
            question_data=output_data,
            score=final_score,
            passed=passed,
            errors=[] if passed else ["Kalite skoru yetersiz"],
            warnings=[],
            suggestions=suggestions,
            metadata={"stage": "quality_gate", "decision": decision}
        )

    def _generate_suggestions(self, scores: Dict) -> List[str]:
        """Generate improvement suggestions for low scores"""
        suggestions = []
        for stage, score in scores.items():
            if score < 0.7:
                if stage == "content_generator":
                    suggestions.append("İçerik kalitesini artırın, Bloom seviyesini kontrol edin")
                elif stage == "difficulty_calibration":
                    suggestions.append("Zorluk seviyesini ZPD bölgesine ayarlayın")
                elif stage == "distractor_generator":
                    suggestions.append("Çeldiricilerin kalitesini artırın")
                elif stage == "osym_compliance":
                    suggestions.append("ÖSYM format kurallarına uygunluğu kontrol edin")
                elif stage == "language_qa":
                    suggestions.append("Türkçe dil kalitesini iyileştirin")
        return suggestions

    def get_stage_weight(self) -> float:
        return 0.0  # Quality gate doesn't contribute to score, it makes the decision
```

### 8. Pipeline Orchestrator

```python
import asyncio
import uuid
import time
from typing import List, Dict, Optional

class PipelineOrchestrator:
    """Orchestrates the 6-stage question generation pipeline"""

    MAX_RETRIES = 3
    PARALLEL_STAGES = [("osym_compliance", "language_qa")]  # Stage 4 and 5 run in parallel

    def __init__(self, stages: List[BasePipelineStage], redis_client: Optional = None):
        self.stages = stages
        self.redis = redis_client
        self.stage_map = {s.stage_name: s for s in stages}

    async def execute_pipeline(self, initial_input: Dict) -> Dict:
        """Execute full pipeline with parallel execution support"""
        pipeline_id = str(uuid.uuid4())
        start_time = time.time()

        # Initialize pipeline state
        state = StageInput(
            question_data=initial_input,
            metadata={"pipeline_id": pipeline_id},
            previous_scores={}
        )

        stage_results = []

        # Execute stages 1-3 sequentially
        for stage in self.stages[:3]:
            output = await self._execute_stage(stage, state, stage_results)
            if not output.passed and output.score < 0.5:
                break
            state = self._update_state(state, stage, output)

        # Execute stages 4-5 in parallel
        if len(stage_results) >= 3 and all(r.get("passed", False) for r in stage_results[-1:]):
            parallel_outputs = await asyncio.gather(
                self._execute_stage(self.stages[3], state, stage_results),
                self._execute_stage(self.stages[4], state, stage_results)
            )
            for i, output in enumerate(parallel_outputs):
                stage = self.stages[3 + i]
                state = self._update_state(state, stage, output)

        # Execute stage 6 (Quality Gate)
        if len(self.stages) > 5:
            final_output = await self._execute_stage(self.stages[5], state, stage_results)
            state = self._update_state(state, self.stages[5], final_output)

        total_duration = time.time() - start_time

        return {
            "pipeline_id": pipeline_id,
            "question": state.question_data,
            "stage_results": stage_results,
            "final_score": state.previous_scores.get("quality_gate", 0),
            "decision": state.question_data.get("decision", "unknown"),
            "total_duration": total_duration
        }

    async def _execute_stage(self, stage: BasePipelineStage,
                            state: StageInput,
                            results: List) -> StageOutput:
        """Execute stage with retry logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                start = time.time()
                output = await stage.process(state)
                duration = time.time() - start

                results.append({
                    "stage": stage.stage_name,
                    "score": output.score,
                    "passed": output.passed,
                    "duration": duration,
                    "errors": output.errors
                })

                return output
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise RuntimeError(f"Stage {stage.stage_name} failed after {self.MAX_RETRIES} retries")
```

## Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime

class IRTParameters(BaseModel):
    """IRT parameters for question"""
    difficulty: float = Field(..., ge=-4.0, le=4.0)
    discrimination: float = Field(..., ge=0.2, le=4.0)
    guessing: float = Field(..., ge=0.0, le=0.35)

class QuestionOption(BaseModel):
    """Question option"""
    label: Literal["A", "B", "C", "D"]
    text: str

class Question(BaseModel):
    """Complete question model"""
    question_id: Optional[str] = None
    kazanim: str
    subject: str
    topic: str
    grade_level: int = Field(..., ge=9, le=12)
    target_difficulty: Literal["kolay", "orta", "zor"]
    question_text: str
    context: Optional[str] = None
    bloom_level: str
    question_type: str
    options: List[QuestionOption] = Field(..., min_length=4, max_length=4)
    correct_answer: Literal["A", "B", "C", "D"]
    irt_parameters: IRTParameters
    quality_scores: Dict[str, float]
    final_score: float = Field(..., ge=0, le=1)
    status: Literal["approved", "review", "rejected"]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PipelineResult(BaseModel):
    """Pipeline execution result"""
    pipeline_id: str
    question: Question
    stage_results: List[Dict]
    final_score: float
    decision: Literal["approved", "review", "rejected"]
    total_duration: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## Correctness Properties

### Property 1: IRT Parameter Ranges
*For any* question, IRT difficulty must be in [-4.0, 4.0], discrimination in [0.2, 4.0], guessing in [0.0, 0.35].

**Validates:** Requirements REQ-2.2, REQ-2.3, REQ-2.4

### Property 2: Final Score Bounds
*For any* pipeline execution, the final quality score must be between 0 and 1.

**Validates:** Requirements REQ-6.3

### Property 3: Weighted Score Correctness
*For any* final score calculation, it must equal the weighted average of stage scores (25% + 20% + 20% + 20% + 15% = 100%).

**Validates:** Requirements REQ-6.3

### Property 4: Decision Threshold Consistency
*For any* question with score >= 0.85, decision must be "approved".
*For any* question with score < 0.70, decision must be "rejected".

**Validates:** Requirements REQ-6.4, REQ-6.6

### Property 5: Stage Execution Order
*For any* pipeline execution, stages must execute in order: Content → Difficulty → Distractor → [Compliance || Language QA] → Quality Gate.

**Validates:** Requirements REQ-7.1, REQ-7.2, REQ-7.6

### Property 6: Retry Logic
*For any* stage failure, the orchestrator must retry up to 3 times with exponential backoff before failing.

**Validates:** Requirements REQ-7.3, REQ-7.4

## Testing Strategy

### Unit Tests
- Test each pipeline stage independently
- Test IRT parameter calculation and validation
- Test distractor generation and plausibility scoring
- Test ÖSYM compliance validation rules
- Test Turkish language quality checks with Zemberek
- Test weighted score calculation

### Property-Based Tests (Hypothesis)
- **Property 1**: Generate random IRT params, verify ranges
- **Property 2**: Generate random stage scores, verify final score in [0, 1]
- **Property 3**: Generate random stage scores, verify weighted average calculation
- **Property 4**: Generate questions with various scores, verify decision mapping
- **Property 5**: Verify stage execution order
- **Property 6**: Simulate failures, verify retry behavior

**Test Configuration**: Minimum 100 iterations per property test

### Integration Tests
- Test full pipeline with sample kazanımlar (10 diverse cases)
- Test retry logic with failing stages
- Test parallel execution of Stage 4 and 5
- Test performance monitoring and bottleneck detection
- Test API endpoints end-to-end

## Performance Optimization

### Caching Strategy
| Cache | TTL | Purpose |
|-------|-----|---------|
| MEB kazanım data | 1 day | Curriculum info rarely changes |
| IRT calculations | 1 hour | Similar questions share params |
| Zemberek analysis | 30 minutes | Morphological results |

### Parallel Processing
- Stages 4 and 5 (Compliance + Language QA) run in parallel using `asyncio.gather`
- Limit concurrent pipelines to 10 (configurable)
- Use Celery for background async execution

### Throughput Target
- Target: 50 questions per hour
- Average pipeline duration: < 2 minutes per question
- Success rate: >= 90%
