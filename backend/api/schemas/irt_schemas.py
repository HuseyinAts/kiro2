"""
IRT (Item Response Theory) Pydantic Schemas
Standardized validation for IRT parameters across the platform

IRT Parameter Ranges (KIRO2 Standards):
- difficulty (b): [-4.0, 4.0] (item difficulty)
- discrimination (a): [0.2, 4.0] (item discrimination)
- guessing (c): [0.0, 0.35] (pseudo-guessing parameter)
- upper_asymptote (d): [0.9, 1.0] (upper asymptote for 4PL)

ZPD Optimal Range:
- Success probability: 15% - 85%
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class IRTModelType(str, Enum):
    """IRT model types"""
    RASCH = "1PL"  # Rasch Model (only difficulty)
    TWO_PL = "2PL"  # 2-Parameter Logistic
    THREE_PL = "3PL"  # 3-Parameter Logistic (most common)
    FOUR_PL = "4PL"  # 4-Parameter Logistic


class DifficultyLevel(str, Enum):
    """Human-readable difficulty levels"""
    VERY_EASY = "very_easy"  # b < -2.0
    EASY = "easy"  # -2.0 <= b < -0.5
    MEDIUM = "medium"  # -0.5 <= b < 0.5
    HARD = "hard"  # 0.5 <= b < 2.0
    VERY_HARD = "very_hard"  # b >= 2.0


# =============================================================================
# Core IRT Parameter Schema
# =============================================================================


class IRTParametersBase(BaseModel):
    """
    Base IRT parameters with strict validation.

    This is the standard schema for IRT parameters across KIRO2.
    All API endpoints dealing with IRT should use this schema.

    Attributes:
        difficulty: Item difficulty parameter (b) [-4.0, 4.0]
        discrimination: Item discrimination parameter (a) [0.2, 4.0]
        guessing: Pseudo-guessing parameter (c) [0.0, 0.35]
    """

    difficulty: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Item difficulty parameter (b). Range: [-4.0, 4.0]. "
                    "Higher values indicate harder items."
    )

    discrimination: float = Field(
        default=1.0,
        ge=0.2,
        le=4.0,
        description="Item discrimination parameter (a). Range: [0.2, 4.0]. "
                    "Higher values indicate better discrimination between abilities."
    )

    guessing: float = Field(
        default=0.0,
        ge=0.0,
        le=0.35,
        description="Pseudo-guessing parameter (c). Range: [0.0, 0.35]. "
                    "For 4-choice items, expected ~0.25."
    )

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: float) -> float:
        """Validate difficulty is within psychometric bounds"""
        if v < -4.0 or v > 4.0:
            raise ValueError(
                f"Difficulty must be between -4.0 and 4.0, got {v}. "
                "Values outside this range indicate potential calibration issues."
            )
        return round(v, 4)  # 4 decimal precision

    @field_validator('discrimination')
    @classmethod
    def validate_discrimination(cls, v: float) -> float:
        """Validate discrimination is within acceptable bounds"""
        if v < 0.2:
            raise ValueError(
                f"Discrimination must be >= 0.2, got {v}. "
                "Values below 0.2 indicate poor item quality."
            )
        if v > 4.0:
            raise ValueError(
                f"Discrimination must be <= 4.0, got {v}. "
                "Values above 4.0 are rare and may indicate estimation issues."
            )
        return round(v, 4)

    @field_validator('guessing')
    @classmethod
    def validate_guessing(cls, v: float) -> float:
        """Validate guessing parameter"""
        if v < 0.0 or v > 0.35:
            raise ValueError(
                f"Guessing must be between 0.0 and 0.35, got {v}. "
                "Values above 0.35 indicate item is too easily guessed."
            )
        return round(v, 4)


class IRTParameters(IRTParametersBase):
    """
    Full IRT parameters including model type and calibration info.

    Extends IRTParametersBase with:
    - Model type specification
    - Upper asymptote for 4PL
    - Calibration metadata
    """

    model_type: IRTModelType = Field(
        default=IRTModelType.THREE_PL,
        description="IRT model type"
    )

    upper_asymptote: float = Field(
        default=1.0,
        ge=0.9,
        le=1.0,
        description="Upper asymptote parameter (d) for 4PL. Range: [0.9, 1.0]"
    )

    # Calibration metadata
    calibration_sample_size: int | None = Field(
        default=None,
        ge=0,
        description="Number of responses used for calibration"
    )

    calibration_date: datetime | None = Field(
        default=None,
        description="Date of last calibration"
    )

    standard_error: float | None = Field(
        default=None,
        ge=0.0,
        description="Standard error of the difficulty estimate"
    )

    fit_statistics: dict[str, float] | None = Field(
        default=None,
        description="Model fit statistics (infit, outfit, etc.)"
    )

    @model_validator(mode='after')
    def validate_model_parameters(self) -> 'IRTParameters':
        """Validate parameters based on model type"""
        if self.model_type == IRTModelType.RASCH:
            # Rasch model: discrimination = 1.0, guessing = 0.0
            if self.discrimination != 1.0:
                raise ValueError(
                    "Rasch model (1PL) requires discrimination = 1.0"
                )
            if self.guessing != 0.0:
                raise ValueError(
                    "Rasch model (1PL) requires guessing = 0.0"
                )

        elif self.model_type == IRTModelType.TWO_PL:
            # 2PL: guessing = 0.0
            if self.guessing != 0.0:
                raise ValueError(
                    "2PL model requires guessing = 0.0"
                )

        return self


# =============================================================================
# Question IRT Schema
# =============================================================================


class QuestionIRTData(BaseModel):
    """
    IRT data for a single question.

    Used in API responses when returning question with IRT info.
    """

    question_id: str = Field(..., description="Unique question identifier")
    irt_params: IRTParameters = Field(..., description="IRT parameters")

    # Derived values
    difficulty_level: DifficultyLevel | None = Field(
        default=None,
        description="Human-readable difficulty level"
    )

    zpd_optimal: bool = Field(
        default=False,
        description="Whether item is in ZPD optimal range (15-85% success probability)"
    )

    information_at_zero: float | None = Field(
        default=None,
        ge=0.0,
        description="Item information at theta=0 (average ability)"
    )

    @model_validator(mode='after')
    def compute_derived_values(self) -> 'QuestionIRTData':
        """Compute derived values from IRT parameters"""
        b = self.irt_params.difficulty

        # Set difficulty level
        if b < -2.0:
            self.difficulty_level = DifficultyLevel.VERY_EASY
        elif b < -0.5:
            self.difficulty_level = DifficultyLevel.EASY
        elif b < 0.5:
            self.difficulty_level = DifficultyLevel.MEDIUM
        elif b < 2.0:
            self.difficulty_level = DifficultyLevel.HARD
        else:
            self.difficulty_level = DifficultyLevel.VERY_HARD

        # Check ZPD optimal (success probability 15-85% at theta=0)
        # P(0) = c + (1-c)/(1 + exp(-a*(0-b)))
        import math
        a = self.irt_params.discrimination
        c = self.irt_params.guessing

        exp_val = math.exp(-a * (0 - b))
        p_at_zero = c + (1 - c) / (1 + exp_val)

        self.zpd_optimal = 0.15 <= p_at_zero <= 0.85

        # Item information at theta=0
        # I(0) = a^2 * P'(0)^2 / (P(0) * (1 - P(0)))
        p_prime = a * (1 - c) * exp_val / (1 + exp_val) ** 2
        if 0 < p_at_zero < 1:
            self.information_at_zero = round(
                (p_prime ** 2) / (p_at_zero * (1 - p_at_zero)), 4
            )

        return self


# =============================================================================
# Request/Response Schemas
# =============================================================================


class IRTParametersUpdateRequest(BaseModel):
    """Request to update IRT parameters for a question"""

    question_id: str = Field(..., description="Question ID to update")
    difficulty: float | None = Field(
        default=None,
        ge=-4.0,
        le=4.0,
        description="New difficulty parameter"
    )
    discrimination: float | None = Field(
        default=None,
        ge=0.2,
        le=4.0,
        description="New discrimination parameter"
    )
    guessing: float | None = Field(
        default=None,
        ge=0.0,
        le=0.35,
        description="New guessing parameter"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "q-12345",
                "difficulty": 0.5,
                "discrimination": 1.2,
                "guessing": 0.25
            }
        }
    }


class IRTBatchUpdateRequest(BaseModel):
    """Request to update IRT parameters for multiple questions"""

    updates: list[IRTParametersUpdateRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of IRT parameter updates (max 100)"
    )


class IRTCalibrationRequest(BaseModel):
    """Request to recalibrate IRT parameters from response data"""

    question_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Questions to recalibrate"
    )

    model_type: IRTModelType = Field(
        default=IRTModelType.THREE_PL,
        description="IRT model to use for calibration"
    )

    min_responses: int = Field(
        default=200,
        ge=50,
        description="Minimum responses required for calibration"
    )

    force_recalibration: bool = Field(
        default=False,
        description="Force recalibration even if recent calibration exists"
    )


class IRTAnalysisResponse(BaseModel):
    """Response with IRT analysis results"""

    question_id: str
    irt_params: IRTParameters
    difficulty_level: DifficultyLevel
    zpd_optimal: bool
    information_at_zero: float

    # Quality indicators
    is_well_calibrated: bool = Field(
        description="Whether calibration meets quality standards"
    )
    quality_warnings: list[str] = Field(
        default_factory=list,
        description="Quality warnings for this item"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "question_id": "q-12345",
                "irt_params": {
                    "difficulty": 0.5,
                    "discrimination": 1.2,
                    "guessing": 0.25,
                    "model_type": "3PL",
                    "upper_asymptote": 1.0,
                    "calibration_sample_size": 500
                },
                "difficulty_level": "medium",
                "zpd_optimal": True,
                "information_at_zero": 0.45,
                "is_well_calibrated": True,
                "quality_warnings": []
            }
        }
    }


# =============================================================================
# ZPD (Zone of Proximal Development) Schema
# =============================================================================


class ZPDOptimalRange(BaseModel):
    """ZPD optimal range for student ability"""

    student_ability: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Student ability level (theta)"
    )

    min_difficulty: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Minimum difficulty for ZPD"
    )

    max_difficulty: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Maximum difficulty for ZPD"
    )

    optimal_difficulty: float = Field(
        ...,
        ge=-4.0,
        le=4.0,
        description="Optimal difficulty (50% success probability)"
    )

    @model_validator(mode='after')
    def validate_range(self) -> 'ZPDOptimalRange':
        """Validate min < optimal < max"""
        if not (self.min_difficulty <= self.optimal_difficulty <= self.max_difficulty):
            raise ValueError(
                "ZPD range must satisfy: min_difficulty <= optimal_difficulty <= max_difficulty"
            )
        return self


class ZPDRecommendation(BaseModel):
    """ZPD-based question recommendation"""

    student_id: str
    student_ability: float = Field(ge=-4.0, le=4.0)
    zpd_range: ZPDOptimalRange

    recommended_questions: list[str] = Field(
        default_factory=list,
        description="Question IDs in ZPD optimal range"
    )

    recommendation_count: int = Field(
        default=0,
        ge=0,
        description="Number of recommended questions"
    )
