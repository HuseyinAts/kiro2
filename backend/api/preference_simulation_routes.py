"""
Task 102: Preference Simulation API Routes

REST API endpoints for score calculation, placement prediction, and simulation
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_user
from models.university import ScoreType
from services.preference_simulation_service import PreferenceSimulationService

router = APIRouter(
    prefix="/api/v1/preference-simulation", tags=["preference-simulation"]
)


# ============================================================
# Request/Response Models
# ============================================================


class TYTScores(BaseModel):
    turkish: float = Field(0.0, ge=0, le=40)
    math: float = Field(0.0, ge=0, le=40)
    science: float = Field(0.0, ge=0, le=20)
    social: float = Field(0.0, ge=0, le=20)


class AYTScoresSAY(BaseModel):
    math: float = Field(0.0, ge=0, le=40)
    physics: float = Field(0.0, ge=0, le=14)
    chemistry: float = Field(0.0, ge=0, le=13)
    biology: float = Field(0.0, ge=0, le=13)


class AYTScoresEA(BaseModel):
    math: float = Field(0.0, ge=0, le=40)
    literature: float = Field(0.0, ge=0, le=24)
    history: float = Field(0.0, ge=0, le=10)
    geography: float = Field(0.0, ge=0, le=6)


class AYTScoresSOZ(BaseModel):
    literature: float = Field(0.0, ge=0, le=24)
    history: float = Field(0.0, ge=0, le=10)
    geography: float = Field(0.0, ge=0, le=6)
    philosophy: float = Field(0.0, ge=0, le=12)


class AYTScoresDIL(BaseModel):
    foreign_language: float = Field(0.0, ge=0, le=80)


class ScoreCalculationRequest(BaseModel):
    score_type: str = Field(..., description="Score type (SAY/EA/SOZ/DIL)")
    tyt_scores: dict[str, float]
    ayt_scores: dict[str, float]
    diploma_grade: float | None = Field(None, ge=0, le=100)
    language_certificate: str | None = None
    special_talent: bool = False


class PlacementPredictionRequest(BaseModel):
    student_score: float = Field(..., ge=180, le=560)
    program_id: UUID
    year: int = Field(2024, ge=2020, le=2030)


class DepartmentRecommendationRequest(BaseModel):
    student_score: float = Field(..., ge=180, le=560)
    score_type: str
    interests: list[str] = []
    career_goals: list[str] = []
    preferred_cities: list[str] | None = None
    year: int = 2024
    limit: int = Field(30, ge=1, le=100)


class RankPredictionRequest(BaseModel):
    student_score: float = Field(..., ge=180, le=560)
    score_type: str
    year: int = 2024


class SimulatePreferencesRequest(BaseModel):
    student_score: float = Field(..., ge=180, le=560)
    score_type: str
    preference_list: list[UUID] = Field(..., min_items=1, max_items=50)
    year: int = 2024


# ============================================================
# Task 102.1: Score Calculation
# ============================================================


@router.post("/calculate-score")
async def calculate_score(
    request: ScoreCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Calculate YKS score with coefficients and bonus points

    Applies proper coefficients for TYT and AYT scores
    """
    service = PreferenceSimulationService(db)

    try:
        score_type_enum = ScoreType(request.score_type)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid score type. Use SAY, EA, SOZ, or DIL"
        )

    # Calculate base score
    result = service.calculate_yks_score(
        score_type=score_type_enum,
        tyt_scores=request.tyt_scores,
        ayt_scores=request.ayt_scores,
    )

    # Calculate bonus points
    bonus_points = service.apply_bonus_points(
        base_score=result["base_score"],
        diploma_grade=request.diploma_grade,
        language_certificate=request.language_certificate,
        special_talent=request.special_talent,
    )

    # Add bonus to result
    result["bonus_points"] = bonus_points
    result["total_score"] = round(result["base_score"] + bonus_points, 2)

    return result


@router.post("/calculate-bonus")
async def calculate_bonus(
    base_score: float = Query(..., ge=0, le=560),
    diploma_grade: float | None = Query(None, ge=0, le=100),
    language_certificate: str | None = Query(None),
    special_talent: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Calculate bonus points only

    Returns bonus points based on diploma grade, certificates, etc.
    """
    service = PreferenceSimulationService(db)

    bonus_points = service.apply_bonus_points(
        base_score=base_score,
        diploma_grade=diploma_grade,
        language_certificate=language_certificate,
        special_talent=special_talent,
    )

    return {
        "base_score": base_score,
        "bonus_points": bonus_points,
        "total_score": base_score + bonus_points,
        "bonus_breakdown": {
            "diploma": round(diploma_grade * 0.6, 2) if diploma_grade else 0.0,
            "language": 20.0
            if language_certificate in ["TOEFL", "IELTS", "Cambridge"]
            else 15.0
            if language_certificate == "YDS"
            else 0.0,
            "special_talent": 30.0 if special_talent else 0.0,
        },
    }


# ============================================================
# Task 102.2: Placement Prediction
# ============================================================


@router.post("/predict-placement")
async def predict_placement(
    request: PlacementPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Predict placement probability for a program

    Returns probability, risk level, and recommendation
    """
    service = PreferenceSimulationService(db)

    prediction = await service.predict_placement(
        student_score=request.student_score,
        program_id=request.program_id,
        year=request.year,
    )

    return prediction


@router.get("/placement-analysis/{program_id}")
async def get_placement_analysis(
    program_id: UUID,
    student_score: float = Query(..., ge=180, le=560),
    year: int = Query(2024),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get detailed placement analysis for a program

    Includes historical data and trend analysis
    """
    service = PreferenceSimulationService(db)

    prediction = await service.predict_placement(
        student_score=student_score, program_id=program_id, year=year
    )

    return prediction


# ============================================================
# Task 102.3: Department Recommendations
# ============================================================


@router.post("/recommend-departments")
async def recommend_departments(
    request: DepartmentRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get personalized department recommendations

    Based on interests, career goals, and score
    """
    service = PreferenceSimulationService(db)

    try:
        score_type_enum = ScoreType(request.score_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid score type")

    recommendations = await service.get_department_recommendations(
        student_score=request.student_score,
        score_type=score_type_enum,
        interests=request.interests,
        career_goals=request.career_goals,
        preferred_cities=request.preferred_cities,
        year=request.year,
        limit=request.limit,
    )

    return [
        {
            "program_id": str(r["program"].id),
            "program_name": r["program"].program_name,
            "university_name": r["program"].university.name
            if r["program"].university
            else "N/A",
            "city": r["program"].university.city if r["program"].university else "N/A",
            "base_score": r["program"].base_score,
            "match_score": round(r["match_score"], 2),
            "interest_alignment": round(r["interest_alignment"], 2),
            "career_alignment": round(r["career_alignment"], 2),
            "scholarship": r["program"].scholarship,
            "tuition_fee": r["program"].tuition_fee,
        }
        for r in recommendations
    ]


# ============================================================
# Task 102.4: Rank Prediction
# ============================================================


@router.post("/predict-rank")
async def predict_rank(
    request: RankPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Predict student's rank based on score

    Returns estimated rank, percentile, and peer comparison
    """
    service = PreferenceSimulationService(db)

    try:
        score_type_enum = ScoreType(request.score_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid score type")

    prediction = await service.predict_rank(
        student_score=request.student_score,
        score_type=score_type_enum,
        year=request.year,
    )

    return prediction


@router.get("/rank-analysis")
async def get_rank_analysis(
    student_score: float = Query(..., ge=180, le=560),
    score_type: str = Query(...),
    year: int = Query(2024),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed rank analysis

    Includes percentile, peer comparison, and interpretation
    """
    service = PreferenceSimulationService(db)

    try:
        score_type_enum = ScoreType(score_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid score type")

    prediction = await service.predict_rank(
        student_score=student_score, score_type=score_type_enum, year=year
    )

    return prediction


# ============================================================
# Batch Simulation
# ============================================================


@router.post("/simulate-preferences")
async def simulate_preferences(
    request: SimulatePreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Simulate placement for a list of preferences

    Returns prediction for each program in order
    """
    service = PreferenceSimulationService(db)

    try:
        score_type_enum = ScoreType(request.score_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid score type")

    results = await service.simulate_preferences(
        student_score=request.student_score,
        score_type=score_type_enum,
        preference_list=request.preference_list,
        year=request.year,
    )

    return results


@router.post("/batch-predictions")
async def batch_predictions(
    student_score: float = Query(..., ge=180, le=560),
    program_ids: list[UUID] = Query(..., min_items=1, max_items=100),
    year: int = Query(2024),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get placement predictions for multiple programs at once

    Useful for comparing multiple programs quickly
    """
    service = PreferenceSimulationService(db)

    predictions = []
    for program_id in program_ids:
        try:
            prediction = await service.predict_placement(
                student_score=student_score, program_id=program_id, year=year
            )
            predictions.append(prediction)
        except Exception:
            # Skip failed predictions
            continue

    return predictions


# ============================================================
# Helper Endpoints
# ============================================================


@router.get("/score-coefficients")
async def get_score_coefficients(
    score_type: str = Query(..., description="Score type (SAY/EA/SOZ/DIL)"),
):
    """
    Get score coefficients for a score type

    Returns TYT and AYT coefficients
    """
    try:
        score_type_enum = ScoreType(score_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid score type")

    service = PreferenceSimulationService(None)
    coefficients = service.COEFFICIENTS.get(score_type_enum)

    if not coefficients:
        raise HTTPException(status_code=404, detail="Coefficients not found")

    return {"score_type": score_type, "coefficients": coefficients}


@router.get("/risk-levels")
async def get_risk_levels():
    """
    Get risk level definitions

    Returns risk level ranges and descriptions
    """
    service = PreferenceSimulationService(None)

    return {
        "risk_levels": {
            level: {
                "range": f"{range_vals[0]}-{range_vals[1]}%",
                "description": service._get_risk_description(level),
            }
            for level, range_vals in service.RISK_LEVELS.items()
        }
    }
