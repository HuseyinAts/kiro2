"""
Shared API Schemas for Learning Path
Ensures frontend-backend type compatibility

BUG FIX #2: API Contract Mismatch
- Pydantic v2 schemas with validation
- OpenAPI auto-generation compatible
- Type-safe contracts
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from core.turkish_nlp_utils import normalize_tr


class LearningPathCreateRequest(BaseModel):
    """
    Learning path creation request schema

     BUG FIX #2: Flat structure (not nested student_profile)
     Field names match frontend expectations
     Comprehensive validation

    This schema is auto-exported to OpenAPI and used by frontend TypeScript types.

    Example:
        ```json
        {
            "student_id": "STU_20250102123456",
            "subject": "matematik",
            "duration_weeks": 4,
            "difficulty_level": "intermediate"
        }
        ```
    """

    student_id: str = Field(
        ...,
        description="Student ID (required)",
        min_length=1,
        max_length=100,
        json_schema_extra={"examples": ["STU_20250102123456", "student_123"]},
    )
    subject: str = Field(
        ...,
        description="Subject to learn (e.g., matematik, fizik, kimya)",
        min_length=1,
        max_length=100,
        json_schema_extra={"examples": ["matematik", "fizik", "kimya", "biyoloji"]},
    )
    target_date: str | None = Field(
        None,
        description="Target completion date (ISO format YYYY-MM-DD)",
        json_schema_extra={"examples": ["2025-06-01", "2025-12-31"]},
    )
    difficulty_level: str | None = Field(
        "intermediate",
        description="Difficulty level: beginner, intermediate, or advanced",
        json_schema_extra={"examples": ["beginner", "intermediate", "advanced"]},
    )
    duration_weeks: int | None = Field(
        4,
        description="Duration in weeks (1-52)",
        ge=1,
        le=52,
        json_schema_extra={"examples": [4, 8, 12]},
    )

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty(cls, v: str | None) -> str | None:
        """Validate difficulty level"""
        if v is None:
            return "intermediate"
        allowed = ["beginner", "intermediate", "advanced"]
        if v not in allowed:
            raise ValueError(f"difficulty_level must be one of {allowed}, got '{v}'")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Normalize subject name using Turkish-safe lowercasing."""
        return normalize_tr(v.strip())

    model_config = {
        "json_schema_extra": {
            "example": {
                "student_id": "STU_20250102123456",
                "subject": "matematik",
                "duration_weeks": 4,
                "difficulty_level": "intermediate",
                "target_date": "2025-06-01",
            }
        }
    }


class StudentProfileData(BaseModel):
    """
    Student profile for resource search

     BUG FIX #3: Structured student profile data
     Optional fields for flexible queries
    """

    student_id: str | None = Field(
        None,
        description="Student ID",
        json_schema_extra={"examples": ["STU_20250102123456"]},
    )
    learning_style: str | None = Field(
        None,
        description="Learning style preference",
        json_schema_extra={
            "examples": ["visual", "auditory", "kinesthetic", "reading"]
        },
    )
    grade: int | None = Field(
        None,
        description="Grade level (1-12)",
        ge=1,
        le=12,
        json_schema_extra={"examples": [9, 10, 11, 12]},
    )
    goals: list[str] | None = Field(
        None,
        description="Learning goals",
        json_schema_extra={"examples": [["matematik örenme", "YKS haz1rl1k"]]},
    )
    current_level: dict[str, Any] | None = Field(
        None,
        description="Current knowledge levels per subject",
        json_schema_extra={"examples": [{"matematik": 50, "fizik": 60}]},
    )
    preferences: dict[str, Any] | None = Field(
        None,
        description="Learning preferences",
        json_schema_extra={"examples": [{"grade": 12, "exam_type": "YKS"}]},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "student_id": "STU_123",
                "learning_style": "visual",
                "grade": 12,
                "goals": ["matematik örenme"],
                "preferences": {"exam_type": "YKS"},
            }
        }
    }


class ResourceSearchRequest(BaseModel):
    """
    Resource search request schema

     BUG FIX #3: Proper type structure for resource search
     Structured student_profile field
    """

    subject: str = Field(
        ...,
        description="Subject to search (required)",
        min_length=1,
        json_schema_extra={"examples": ["matematik", "fizik"]},
    )
    topic: str | None = Field(
        None,
        description="Specific topic within subject",
        json_schema_extra={"examples": ["türev", "integral", "limit"]},
    )
    difficulty: str | None = Field(
        "orta",
        description="Difficulty level (kolay, orta, zor)",
        json_schema_extra={"examples": ["kolay", "orta", "zor"]},
    )
    max_results: int | None = Field(
        10,
        description="Maximum number of results (1-50)",
        ge=1,
        le=50,
        json_schema_extra={"examples": [10, 20, 30]},
    )
    student_profile: StudentProfileData | None = Field(
        None, description="Student profile for personalized recommendations"
    )

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str | None) -> str:
        """Validate and normalize difficulty using Turkish-safe lowercasing."""
        if v is None:
            return "orta"
        v = normalize_tr(v.strip())
        allowed = ["kolay", "orta", "zor"]
        if v not in allowed:
            # Try to map English to Turkish
            mapping = {"easy": "kolay", "medium": "orta", "hard": "zor"}
            v = mapping.get(v, "orta")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "subject": "matematik",
                "topic": "türev",
                "difficulty": "orta",
                "max_results": 10,
                "student_profile": {"learning_style": "visual", "grade": 12},
            }
        }
    }


# Additional schemas for other endpoints


class QuizSubmission(BaseModel):
    """Quiz submission schema"""

    quiz_id: str = Field(..., description="Quiz ID")
    answers: list[str] = Field(..., description="Student answers")
    time_taken: int = Field(..., description="Time taken in seconds", ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "quiz_id": "QZ1",
                "answers": ["A", "B", "C", "D"],
                "time_taken": 300,
            }
        }
    }


class ProgressUpdateRequest(BaseModel):
    """Progress update request schema"""

    node_id: str = Field(..., description="Learning path node ID")
    progress_percentage: int = Field(
        ..., description="Progress percentage", ge=0, le=100
    )
    time_spent: int = Field(..., description="Time spent in minutes", ge=0)
    completed: bool = Field(False, description="Whether node is completed")

    model_config = {
        "json_schema_extra": {
            "example": {
                "node_id": "TOP1",
                "progress_percentage": 75,
                "time_spent": 45,
                "completed": False,
            }
        }
    }
