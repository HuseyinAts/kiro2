# Pydantic v2 Patterns - KIRO2 Backend Standards

This document provides the standard patterns and best practices for writing Pydantic models in the KIRO2 backend.

## Quick Reference

### ✅ CORRECT: Basic Model with Validation

```python
from pydantic import BaseModel, Field, field_validator

class StudentProfile(BaseModel):
    """Student learning profile and preferences."""

    student_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique student identifier"
    )
    learning_style: str = Field(
        default="visual",
        description="Primary learning style: visual, auditory, kinesthetic, reading"
    )
    grade_level: int = Field(
        ...,
        ge=1,
        le=12,
        description="Student grade level (1-12)"
    )

    @field_validator("learning_style")
    @classmethod
    def validate_learning_style(cls, v: str) -> str:
        """Validate learning style is one of allowed values."""
        allowed = ["visual", "auditory", "kinesthetic", "reading"]
        if v not in allowed:
            raise ValueError(f"learning_style must be one of {allowed}")
        return v
```

### ✅ CORRECT: Model with Configuration

```python
from pydantic import BaseModel, ConfigDict, Field

class QuestionResponse(BaseModel):
    """API response for a question."""

    question_id: str
    text: str
    difficulty: float = Field(..., ge=-4.0, le=4.0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q-12345",
                "text": "Açı nedir?",
                "difficulty": 0.5
            }
        }
    )
```

### ✅ CORRECT: Model with Multi-field Validation

```python
from pydantic import BaseModel, field_validator, model_validator

class ExamSession(BaseModel):
    """Exam session configuration."""

    title: str = Field(..., min_length=1, max_length=200)
    duration_minutes: int = Field(..., ge=1, le=480)
    total_questions: int = Field(..., ge=1, le=100)
    passing_score: float = Field(..., ge=0.0, le=100.0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Title must not be all whitespace."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_passing_score_logic(self) -> "ExamSession":
        """Ensure passing score makes sense for exam."""
        if self.passing_score > 80:
            raise ValueError("Passing score should not exceed 80%")
        return self
```

## Detailed Patterns

### Pattern 1: Simple Request/Response Models

Use for API endpoints that require no special configuration.

```python
class CreateUserRequest(BaseModel):
    """Request to create a new user."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., description="User full name")

class CreateUserResponse(BaseModel):
    """Response after creating a user."""

    user_id: str
    email: str
    created_at: datetime
```

**Use When**:
- Simple API request/response contracts
- No special JSON schema needs
- Default validation is sufficient

---

### Pattern 2: Models with OpenAPI Examples

Use for models exposed in FastAPI endpoints (auto-generates OpenAPI docs).

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class LearningPathCreate(BaseModel):
    """Request to create a personalized learning path."""

    student_id: str = Field(
        ...,
        description="Student ID",
        json_schema_extra={"examples": ["STU_20250115", "student_123"]}
    )
    subject: str = Field(
        ...,
        description="Subject to study",
        json_schema_extra={"examples": ["matematik", "fizik", "kimya"]}
    )
    duration_weeks: Optional[int] = Field(
        4,
        ge=1,
        le=52,
        description="Duration in weeks",
        json_schema_extra={"examples": [4, 8, 12]}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "STU_20250115",
                "subject": "matematik",
                "duration_weeks": 8
            }
        }
    )
```

**Use When**:
- Defining API request/response models
- Want comprehensive OpenAPI documentation
- Need clear examples in Swagger UI

---

### Pattern 3: Models with Custom Validation

Use for complex business logic validation.

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import List

class IRTParameters(BaseModel):
    """IRT (Item Response Theory) parameters for a question."""

    question_id: str
    difficulty: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Difficulty parameter θ (theta)"
    )
    discrimination: float = Field(
        ...,
        ge=0.2,
        le=4.0,
        description="Discrimination parameter a (alpha)"
    )
    guessing: float = Field(
        default=0.2,
        ge=0.0,
        le=0.35,
        description="Guessing parameter c"
    )

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty_range(cls, v: float) -> float:
        """Ensure difficulty is within acceptable range."""
        if abs(v) > 4.0:
            raise ValueError("Difficulty must be between -4.0 and 4.0")
        return v

    @model_validator(mode="after")
    def validate_irt_consistency(self) -> "IRTParameters":
        """Validate IRT parameter consistency."""
        # Example: discrimination should correlate with difficulty
        if self.discrimination < 0.5 and abs(self.difficulty) > 2.0:
            raise ValueError(
                "Low discrimination (< 0.5) should not be used with "
                "high difficulty items (|d| > 2.0)"
            )
        return self
```

**Use When**:
- Validating algorithm parameters (IRT, FSRS, ZPD)
- Complex business rules requiring multiple field checks
- Need to ensure mathematical consistency

---

### Pattern 4: Generic Response Wrappers

Use for consistent API responses across all endpoints.

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, TypeVar, Optional, Any, Dict

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = Field(..., description="Operation succeeded")
    message: str = Field(default="", description="Response message")
    data: Optional[T] = Field(default=None, description="Response payload")
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed",
                "data": {"id": 1, "name": "Example"},
                "meta": {"timestamp": "2026-01-15T10:00:00Z"}
            }
        }
    )
```

**Use When**:
- Need consistent response format across all endpoints
- Want type-safe generic responses
- Implementing standardized error handling

---

### Pattern 5: Enum-based Models

Use for models with specific allowed values.

```python
from enum import Enum
from pydantic import BaseModel, Field

class ExamType(str, Enum):
    """Turkish standardized exam types."""

    TYT = "tyt"  # Temel Yeterlilik Testi
    AYT_SAY = "ayt_say"  # Alanında Yeterlilik Testi - Science
    AYT_EA = "ayt_ea"  # Alanında Yeterlilik Testi - Social Sciences
    AYT_SOZ = "ayt_soz"  # Alanında Yeterlilik Testi - Language
    YDT = "ydt"  # Yabancı Dil Testi

class ExamPreferences(BaseModel):
    """Student exam preferences."""

    exam_type: ExamType = Field(
        ...,
        description="Target exam type"
    )
    focus_subjects: list[str] = Field(
        default_factory=list,
        description="Subjects to focus on"
    )
```

**Use When**:
- Need to restrict fields to specific values
- Implementing enum-based configuration
- Want type-safe options without string errors

---

## Advanced Patterns

### Pattern 6: Conditional Validation

```python
from pydantic import BaseModel, model_validator

class LanguageExamConfig(BaseModel):
    """Language exam configuration."""

    exam_type: str  # "english", "arabic", "german", "french"
    duration_minutes: int
    include_speaking: bool = False
    speaking_duration_minutes: int = 0

    @model_validator(mode="after")
    def validate_speaking_config(self) -> "LanguageExamConfig":
        """Validate speaking configuration."""
        if self.include_speaking and self.speaking_duration_minutes <= 0:
            raise ValueError(
                "If speaking is included, speaking_duration_minutes must be > 0"
            )
        if not self.include_speaking and self.speaking_duration_minutes > 0:
            raise ValueError(
                "speaking_duration_minutes should be 0 if speaking is not included"
            )
        return self
```

### Pattern 7: Turkish Character Handling

```python
from pydantic import BaseModel, field_validator

class TurkishContent(BaseModel):
    """Content with Turkish character support."""

    title: str
    description: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Normalize Turkish characters."""
        # Ensure UTF-8 encoding
        if not isinstance(v, str):
            raise ValueError("Title must be a string")
        # Handle Turkish İ/i specifically
        v = v.replace("İ", "I").replace("ı", "i")
        return v
```

---

## Common Mistakes to Avoid

### ❌ WRONG: Using v1 Config class

```python
# WRONG - This is Pydantic v1 syntax
class OldModel(BaseModel):
    name: str

    class Config:
        orm_mode = True  # ❌ DEPRECATED
        json_encoders = {datetime: str}  # ❌ DEPRECATED
```

**Correct (v2)**:
```python
# CORRECT - Pydantic v2 syntax
from pydantic import ConfigDict

class NewModel(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)
```

---

### ❌ WRONG: Old validator syntax

```python
# WRONG - Pydantic v1 syntax
from pydantic import validator

class OldValidation(BaseModel):
    email: str

    @validator("email")  # ❌ WRONG
    def validate_email(cls, v):
        return v
```

**Correct (v2)**:
```python
# CORRECT - Pydantic v2 syntax
from pydantic import field_validator

class NewValidation(BaseModel):
    email: str

    @field_validator("email")  # ✅ CORRECT
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v
```

---

### ❌ WRONG: Missing type hints

```python
# WRONG - No type hints
class BadModel(BaseModel):
    user_id = Field(...)  # ❌ Missing type
    name = "John"  # ❌ Missing type
```

**Correct (v2)**:
```python
# CORRECT - Explicit types
class GoodModel(BaseModel):
    user_id: str = Field(...)  # ✅ Type specified
    name: str = Field(default="John")  # ✅ Type specified
```

---

## Testing Pydantic Models

```python
import pytest
from pydantic import ValidationError

def test_valid_model():
    """Test model with valid data."""
    model = StudentProfile(
        student_id="STU_001",
        learning_style="visual",
        grade_level=10
    )
    assert model.student_id == "STU_001"
    assert model.learning_style == "visual"

def test_invalid_learning_style():
    """Test validation error on invalid learning style."""
    with pytest.raises(ValidationError) as exc_info:
        StudentProfile(
            student_id="STU_001",
            learning_style="invalid_style",  # ❌ Not allowed
            grade_level=10
        )
    assert "learning_style" in str(exc_info.value)

def test_model_json_schema():
    """Test OpenAPI schema generation."""
    schema = StudentProfile.model_json_schema()
    assert "properties" in schema
    assert "student_id" in schema["properties"]
    assert "learning_style" in schema["properties"]
```

---

## Quick Checklist for New Models

When adding a new Pydantic model to KIRO2:

- [ ] Explicit type hints on all fields
- [ ] Field descriptions using `description=` parameter
- [ ] `...` (Ellipsis) for required fields
- [ ] `default=` or `default_factory=` for optional fields
- [ ] Validation constraints (`ge=`, `le=`, `min_length=`, `max_length=`)
- [ ] Custom `@field_validator` methods use `@classmethod`
- [ ] `@model_validator(mode="after")` for multi-field validation
- [ ] Docstring on the model class itself
- [ ] `model_config = ConfigDict(...)` if JSON schema customization needed
- [ ] Example JSON in `json_schema_extra` for API documentation

---

## Resources

- [Pydantic v2 Documentation](https://docs.pydantic.dev/2.0/)
- [Pydantic Migration Guide](https://docs.pydantic.dev/2.0/concepts/migration/)
- [FastAPI with Pydantic](https://fastapi.tiangolo.com/python-types/)
- KIRO2 Backend Standards: See `CLAUDE.md`

---

## Questions?

If you're unsure about a pattern, check:
1. Existing models in `/backend/api/schemas/`
2. This guide's pattern sections
3. Pydantic v2 official documentation
