# Design Document - YKS Soru Kalite Doğrulama Sistemi

## Overview

YKS Soru Kalite Doğrulama Sistemi, Boris Cherny'nin #1 önerisi olan verification feedback loops prensibine göre tasarlanmış, otomatik soru kalite kontrol sistemidir. Sistem, üretilen her ÖSYM sorusunu 4 farklı validator ile kontrol eder ve 0-100 arası kalite skoru üretir.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Soru Üretim Sistemi                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  PostToolUse Hook Trigger                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Validation Orchestrator                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. ÖSYM Format Validator        (30% weight)        │  │
│  │  2. Müfredat Checker             (30% weight)        │  │
│  │  3. Zemberek Turkish Validator   (20% weight)        │  │
│  │  4. SymPy Math Validator         (20% weight)        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Quality Score Calculator                      │
│              (Weighted Average: 0-100)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                    Score >= 70?
                         │
            ┌────────────┴────────────┐
            │                         │
         YES│                         │NO
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │Soru Onaylandı│          │ Hata Raporu  │
    │   (Approve)  │          │  + Öneriler  │
    └──────────────┘          └──────────────┘
```

### Component Architecture

```python
# Core Components
app/
├── validators/
│   ├── __init__.py
│   ├── base_validator.py          # Abstract base class
│   ├── osym_format_validator.py   # ÖSYM format check
│   ├── mufredat_checker.py        # MEB curriculum check
│   ├── turkish_validator.py       # Zemberek integration
│   └── math_validator.py          # SymPy integration
├── scoring/
│   ├── __init__.py
│   ├── quality_scorer.py          # Weighted scoring
│   └── score_aggregator.py        # Score combination
├── hooks/
│   ├── __init__.py
│   └── post_tool_use_hook.py      # Hook trigger
├── reporting/
│   ├── __init__.py
│   ├── error_reporter.py          # Error reporting
│   └── suggestion_generator.py    # Fix suggestions
└── orchestrator/
    ├── __init__.py
    └── validation_orchestrator.py # Main coordinator
```

## Components and Interfaces

### 1. Base Validator (Abstract)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel

class ValidationResult(BaseModel):
    """Validation result model"""
    is_valid: bool
    score: float  # 0-100
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metadata: Dict[str, any]

class BaseValidator(ABC):
    """Abstract base validator"""
    
    def __init__(self, weight: float):
        self.weight = weight
    
    @abstractmethod
    async def validate(self, question: Dict) -> ValidationResult:
        """Validate question and return result"""
        pass
    
    @abstractmethod
    def get_validator_name(self) -> str:
        """Return validator name"""
        pass
```

### 2. ÖSYM Format Validator

```python
class OSYMFormatValidator(BaseValidator):
    """ÖSYM format validation"""
    
    REQUIRED_FIELDS = ["question_text", "options", "correct_answer", "difficulty"]
    VALID_OPTIONS = ["A", "B", "C", "D"]
    VALID_DIFFICULTIES = ["kolay", "orta", "zor"]
    
    async def validate(self, question: Dict) -> ValidationResult:
        errors = []
        warnings = []
        score = 100.0
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in question:
                errors.append(f"Eksik alan: {field}")
                score -= 25
        
        # Check options count
        if len(question.get("options", [])) != 4:
            errors.append("Seçenek sayısı 4 olmalı")
            score -= 20
        
        # Check option labels
        for opt in question.get("options", []):
            if opt.get("label") not in self.VALID_OPTIONS:
                errors.append(f"Geçersiz seçenek etiketi: {opt.get('label')}")
                score -= 10
        
        # Check correct answer
        if question.get("correct_answer") not in self.VALID_OPTIONS:
            errors.append("Doğru cevap A, B, C veya D olmalı")
            score -= 25
        
        # Check difficulty
        if question.get("difficulty") not in self.VALID_DIFFICULTIES:
            warnings.append("Zorluk seviyesi belirsiz")
            score -= 5
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_suggestions(errors),
            metadata={"validator": "ÖSYM Format"}
        )
```

### 3. Müfredat Checker

```python
class MufredatChecker(BaseValidator):
    """MEB curriculum compliance checker"""
    
    def __init__(self, weight: float, meb_api_client):
        super().__init__(weight)
        self.meb_api = meb_api_client
    
    async def validate(self, question: Dict) -> ValidationResult:
        # Extract topic and grade level
        topic = question.get("topic")
        grade = question.get("grade_level")
        
        # Fetch relevant kazanımlar from MEB API
        kazanimlar = await self.meb_api.get_kazanimlar(topic, grade)
        
        # Calculate semantic similarity
        question_embedding = await self._get_embedding(question["question_text"])
        
        best_match_score = 0
        matched_kazanim = None
        
        for kazanim in kazanimlar:
            kazanim_embedding = await self._get_embedding(kazanim["description"])
            similarity = self._cosine_similarity(question_embedding, kazanim_embedding)
            
            if similarity > best_match_score:
                best_match_score = similarity
                matched_kazanim = kazanim
        
        # Score based on similarity
        score = best_match_score * 100
        
        errors = []
        warnings = []
        
        if score < 80:
            warnings.append(f"Müfredat uyumu düşük: %{score:.1f}")
        
        if score < 50:
            errors.append("Soru müfredata uygun değil")
        
        return ValidationResult(
            is_valid=score >= 50,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=[f"İlgili kazanım: {matched_kazanim['code']}"],
            metadata={
                "validator": "Müfredat",
                "matched_kazanim": matched_kazanim,
                "similarity_score": best_match_score
            }
        )
```

### 4. Turkish Validator (Zemberek)

```python
from zemberek import TurkishMorphology

class TurkishValidator(BaseValidator):
    """Turkish language quality validator using Zemberek"""
    
    def __init__(self, weight: float):
        super().__init__(weight)
        self.morphology = TurkishMorphology.create_with_defaults()
    
    async def validate(self, question: Dict) -> ValidationResult:
        text = question["question_text"]
        errors = []
        warnings = []
        score = 100.0
        
        # Spell check
        words = text.split()
        misspelled = []
        
        for word in words:
            analysis = self.morphology.analyze(word)
            if not analysis.is_correct():
                misspelled.append(word)
                score -= 5
        
        if misspelled:
            errors.append(f"Yazım hataları: {', '.join(misspelled)}")
        
        # Sentence complexity check
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        avg_words_per_sentence = len(words) / max(1, sentence_count)
        
        if avg_words_per_sentence > 25:
            warnings.append("Cümleler çok uzun ve karmaşık")
            score -= 10
        
        # Turkish character check
        turkish_chars = set('çğıöşüÇĞİÖŞÜ')
        if not any(c in turkish_chars for c in text):
            warnings.append("Türkçe karakter kullanımı eksik olabilir")
            score -= 5
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_corrections(misspelled),
            metadata={"validator": "Turkish Language"}
        )
```

### 5. Math Validator (SymPy)

```python
from sympy import sympify, solve, simplify
from sympy.parsing.sympy_parser import parse_expr

class MathValidator(BaseValidator):
    """Mathematical correctness validator using SymPy"""
    
    async def validate(self, question: Dict) -> ValidationResult:
        # Only validate if question type is math
        if question.get("subject") not in ["matematik", "fizik", "kimya"]:
            return ValidationResult(
                is_valid=True,
                score=100.0,
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={"validator": "Math", "skipped": True}
            )
        
        errors = []
        warnings = []
        score = 100.0
        
        try:
            # Extract mathematical expressions
            expressions = self._extract_math_expressions(question["question_text"])
            
            # Validate each expression
            for expr_str in expressions:
                try:
                    expr = parse_expr(expr_str)
                    simplified = simplify(expr)
                    
                    # Check if expression is valid
                    if expr is None:
                        errors.append(f"Geçersiz matematiksel ifade: {expr_str}")
                        score -= 20
                        
                except Exception as e:
                    errors.append(f"İfade parse edilemedi: {expr_str}")
                    score -= 15
            
            # Validate correct answer
            correct_answer = question.get("correct_answer_value")
            if correct_answer:
                # Verify answer is mathematically correct
                is_correct = self._verify_answer(expressions, correct_answer)
                if not is_correct:
                    errors.append("Doğru cevap matematiksel olarak yanlış")
                    score -= 50
            
            # Check distractors
            for option in question.get("options", []):
                if option["label"] != question["correct_answer"]:
                    # Verify distractor is incorrect
                    if self._verify_answer(expressions, option.get("value")):
                        warnings.append(f"Çeldirici {option['label']} doğru olabilir")
                        score -= 10
        
        except Exception as e:
            errors.append(f"Matematiksel doğrulama hatası: {str(e)}")
            score = 0
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            score=max(0, score),
            errors=errors,
            warnings=warnings,
            suggestions=self._generate_math_suggestions(errors),
            metadata={"validator": "Math"}
        )
```

### 6. Validation Orchestrator

```python
class ValidationOrchestrator:
    """Coordinates all validators and calculates final score"""
    
    def __init__(self):
        self.validators = [
            OSYMFormatValidator(weight=0.30),
            MufredatChecker(weight=0.30, meb_api_client=MEBAPIClient()),
            TurkishValidator(weight=0.20),
            MathValidator(weight=0.20)
        ]
    
    async def validate_question(self, question: Dict) -> Dict:
        """Run all validators and calculate final score"""
        
        results = []
        
        # Run all validators in parallel
        tasks = [validator.validate(question) for validator in self.validators]
        validation_results = await asyncio.gather(*tasks)
        
        # Calculate weighted score
        total_score = 0
        total_weight = 0
        
        for validator, result in zip(self.validators, validation_results):
            if not result.metadata.get("skipped", False):
                total_score += result.score * validator.weight
                total_weight += validator.weight
        
        final_score = total_score / total_weight if total_weight > 0 else 0
        
        # Aggregate errors and warnings
        all_errors = []
        all_warnings = []
        all_suggestions = []
        
        for result in validation_results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_suggestions.extend(result.suggestions)
        
        # Determine if question passes
        is_approved = final_score >= 70 and len(all_errors) == 0
        
        return {
            "question_id": question.get("id"),
            "final_score": round(final_score, 2),
            "is_approved": is_approved,
            "validation_results": [r.dict() for r in validation_results],
            "errors": all_errors,
            "warnings": all_warnings,
            "suggestions": all_suggestions,
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class QuestionOption(BaseModel):
    label: str = Field(..., pattern="^[A-D]$")
    text: str
    value: Optional[float] = None

class Question(BaseModel):
    id: Optional[str] = None
    question_text: str
    options: List[QuestionOption] = Field(..., min_items=4, max_items=4)
    correct_answer: str = Field(..., pattern="^[A-D]$")
    difficulty: str = Field(..., pattern="^(kolay|orta|zor)$")
    subject: str
    topic: str
    grade_level: int = Field(..., ge=9, le=12)
    kazanim_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ValidationReport(BaseModel):
    question_id: str
    final_score: float = Field(..., ge=0, le=100)
    is_approved: bool
    validation_results: List[Dict]
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    timestamp: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Score Bounds
*For any* question validation, the final quality score must be between 0 and 100 inclusive.
**Validates: Requirements 6.5**

### Property 2: Weighted Average Correctness
*For any* set of validator scores, the final score must equal the weighted average of individual validator scores.
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 3: Approval Threshold
*For any* question with final score >= 70 and zero errors, the question must be approved.
**Validates: Requirements 6.6**

### Property 4: Format Validation Completeness
*For any* question, if ÖSYM format validator passes, then all required fields must be present and valid.
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

### Property 5: Error Reporting Completeness
*For any* validation failure, at least one error message must be present in the report.
**Validates: Requirements 7.1, 7.2**

### Property 6: Performance Bound
*For any* single question validation, the total execution time must be less than 5 seconds.
**Validates: Requirements 8.1**

## Error Handling

- **ValidationError**: Raised when validation logic fails
- **TimeoutError**: Raised when validation exceeds 5 seconds
- **ExternalAPIError**: Raised when MEB API is unavailable
- **MathParseError**: Raised when mathematical expression cannot be parsed

## Testing Strategy

### Unit Tests
- Test each validator independently with mock data
- Test score calculation with various weight combinations
- Test error message generation

### Property Tests (Hypothesis)
- **Property 1 Test**: Generate random validator scores, verify final score in [0, 100]
- **Property 2 Test**: Generate random weights and scores, verify weighted average
- **Property 3 Test**: Generate questions with score >= 70, verify approval
- **Property 6 Test**: Measure validation time for 100 random questions

### Integration Tests
- Test full validation pipeline with real questions
- Test PostToolUse hook trigger
- Test database persistence of validation results

**Test Configuration**: Minimum 100 iterations per property test
