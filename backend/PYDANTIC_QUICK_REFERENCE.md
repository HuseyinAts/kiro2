# Pydantic v2 Quick Reference - Copy & Paste Templates

Use these templates when creating new Pydantic models in KIRO2.

---

## Template 1: Basic API Request/Response

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class YourRequestModel(BaseModel):
    """Clear description of what this model represents."""

    field_one: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Description of field"
    )
    field_two: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Optional field with constraints"
    )

class YourResponseModel(BaseModel):
    """Response model description."""

    id: str
    field_one: str
    created_at: datetime
```

**Use for**: Simple CRUD operations, straightforward API endpoints

---

## Template 2: With Custom Validation

```python
from pydantic import BaseModel, Field, field_validator

class ValidatedModel(BaseModel):
    """Model with custom validation rules."""

    email: str = Field(
        ...,
        description="Email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (minimum 8 characters)"
    )
    age: int = Field(
        ...,
        ge=18,
        le=120,
        description="User age (18-120)"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password too short")
        if v.isdigit():
            raise ValueError("Password must contain letters")
        return v
```

**Use for**: User input validation, complex rules

---

## Template 3: With OpenAPI Documentation

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import List

class DocumentedModel(BaseModel):
    """Comprehensive API model with OpenAPI documentation."""

    item_id: str = Field(
        ...,
        description="Unique identifier",
        json_schema_extra={"examples": ["item-123", "item-456"]}
    )
    items: List[str] = Field(
        default_factory=list,
        description="List of items",
        json_schema_extra={"examples": [["item1", "item2", "item3"]]}
    )
    is_active: bool = Field(
        True,
        description="Whether item is active"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": "item-123",
                "items": ["item1", "item2"],
                "is_active": True
            }
        }
    )
```

**Use for**: Public API endpoints, want clear Swagger documentation

---

## Template 4: Algorithm Parameters (IRT/FSRS/ZPD)

```python
from pydantic import BaseModel, Field, model_validator

class AlgorithmParameters(BaseModel):
    """Parameters for educational algorithm."""

    difficulty: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Difficulty parameter [-4.0, 4.0]"
    )
    discrimination: float = Field(
        ...,
        ge=0.2,
        le=4.0,
        description="Discrimination parameter [0.2, 4.0]"
    )
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence score [0.0, 1.0]"
    )

    @model_validator(mode="after")
    def validate_algorithm_constraints(self) -> "AlgorithmParameters":
        """Validate algorithm-specific constraints."""
        # Example: extreme difficulty needs high discrimination
        if abs(self.difficulty) > 3.0 and self.discrimination < 0.5:
            raise ValueError(
                "High difficulty items should have discrimination >= 0.5"
            )
        return self
```

**Use for**: IRT, FSRS, ZPD, machine learning model parameters

---

## Template 5: Paginated Response

```python
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List

T = TypeVar("T")

class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    success: bool = True
    data: List[T]
    pagination: PaginationMeta
```

**Use for**: List endpoints, large datasets

---

## Template 6: Turkish Content Model

```python
from pydantic import BaseModel, Field, field_validator

class TurkishContentModel(BaseModel):
    """Model handling Turkish language content."""

    title: str = Field(
        ...,
        description="Turkish title (supports special characters)"
    )
    subject: str = Field(
        ...,
        description="Turkish subject: matematik, fizik, kimya, etc."
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate and normalize Turkish text."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        # Turkish character support is automatic in UTF-8
        return v.strip()

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject is valid Turkish subject."""
        valid_subjects = [
            "matematik", "fizik", "kimya", "biyoloji",
            "turkce", "ingilizce", "sosyal", "tarih"
        ]
        if v.lower() not in valid_subjects:
            raise ValueError(f"Subject must be one of {valid_subjects}")
        return v.lower()
```

**Use for**: Turkish language content, exam subjects

---

## Template 7: Enum-based Configuration

```python
from enum import Enum
from pydantic import BaseModel, Field

class LearningStyle(str, Enum):
    """Learning style categories."""

    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"

class StudentPreferences(BaseModel):
    """Student learning preferences."""

    learning_style: LearningStyle = Field(
        default=LearningStyle.VISUAL,
        description="Preferred learning style"
    )
    exam_type: str = Field(
        ...,
        description="Target exam: TYT, AYT-SAY, AYT-EA, AYT-SOZ, YDT"
    )
```

**Use for**: Configuration options, multiple choice settings

---

## Quick Copy-Paste Examples

### ✅ Required Field
```python
name: str = Field(..., description="Name is required")
```

### ✅ Optional Field with Default
```python
active: bool = Field(default=True, description="Is active")
```

### ✅ Field with Constraints
```python
age: int = Field(..., ge=0, le=120, description="Age 0-120")
```

### ✅ String Length Constraint
```python
username: str = Field(..., min_length=3, max_length=20, description="Username")
```

### ✅ List Field
```python
tags: list[str] = Field(default_factory=list, description="Tags")
```

### ✅ Validator
```python
@field_validator("field_name")
@classmethod
def validate_field_name(cls, v: str) -> str:
    return v.strip()
```

### ✅ Cross-field Validator
```python
@model_validator(mode="after")
def validate_logic(self) -> "ModelName":
    if self.field_a > self.field_b:
        raise ValueError("field_a must be <= field_b")
    return self
```

---

## Common Constraints

| Constraint | Usage | Example |
|-----------|-------|---------|
| `ge=` | Greater than or equal | `ge=0` |
| `le=` | Less than or equal | `le=100` |
| `gt=` | Greater than | `gt=0` |
| `lt=` | Less than | `lt=100` |
| `min_length=` | Minimum string length | `min_length=3` |
| `max_length=` | Maximum string length | `max_length=50` |
| `pattern=` | Regex pattern | `pattern=r"^\w+$"` |
| `default=` | Default value | `default=0` |
| `default_factory=` | Default factory | `default_factory=list` |

---

## Import Quick Reference

### Bare Minimum
```python
from pydantic import BaseModel, Field
```

### With Validation
```python
from pydantic import BaseModel, Field, field_validator
```

### With Configuration
```python
from pydantic import BaseModel, ConfigDict, Field
```

### Complete
```python
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
```

---

## Common Mistakes

### ❌ Missing type hint
```python
field = Field(...)  # Missing type!
```

### ✅ Correct
```python
field: str = Field(...)
```

---

### ❌ Missing description
```python
field: str = Field(...)
```

### ✅ Correct
```python
field: str = Field(..., description="What is this field?")
```

---

### ❌ Wrong validator syntax
```python
@validator("field")  # Wrong - v1 syntax
```

### ✅ Correct
```python
@field_validator("field")  # Right - v2 syntax
@classmethod
```

---

## Testing Template

```python
import pytest
from pydantic import ValidationError

def test_valid_model():
    model = YourModel(field="value")
    assert model.field == "value"

def test_invalid_field():
    with pytest.raises(ValidationError):
        YourModel(field="")  # Too short
```

---

## Final Checklist

Before committing a new model:

- [ ] Type hints on all fields
- [ ] Field descriptions
- [ ] Required fields use `...` (Ellipsis)
- [ ] Optional fields have `default=`
- [ ] Validation constraints added
- [ ] Custom validators are `@classmethod`
- [ ] Docstring on the model
- [ ] Model can be instantiated and validated
- [ ] JSON schema can be generated

---

## Generate JSON Schema (for docs)

```python
# In your test or script
from your_module import YourModel

schema = YourModel.model_json_schema()
print(schema)  # Use for documentation
```

---

**See Also**: `PYDANTIC_V2_PATTERNS.md` for detailed patterns and examples.
