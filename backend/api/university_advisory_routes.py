"""
Task 101: University Advisory API Routes

REST API endpoints for university search, base scores, and recommendations
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_user
from models.university import ProgramType, ScoreType, UniversityType
from services.university_advisory_service import UniversityAdvisoryService

router = APIRouter(prefix="/api/v1/university-advisory", tags=["university-advisory"])


# ============================================================
# Request/Response Models
# ============================================================


class UniversityResponse(BaseModel):
    id: str
    name: str
    short_name: str | None
    university_type: str
    city: str
    district: str | None
    website: str | None
    established_year: int | None
    world_ranking: int | None
    turkey_ranking: int | None


class DepartmentResponse(BaseModel):
    id: str
    name: str
    degree_type: str
    education_language: str
    education_duration: int
    career_opportunities: list[str]
    average_salary: int | None
    employment_rate: float | None


class ProgramResponse(BaseModel):
    id: str
    program_name: str
    university_name: str
    department_name: str
    city: str
    year: int
    score_type: str
    base_score: float | None
    top_score: float | None
    median_score: float | None
    total_quota: int | None
    filled_quota: int | None
    acceptance_rate: float | None
    scholarship: bool
    tuition_fee: int | None


class RecommendationResponse(BaseModel):
    program: ProgramResponse
    match_score: float
    score_diff: float
    placement_probability: float


class UserPreferencesRequest(BaseModel):
    preferred_cities: list[str] | None = []
    preferred_university_types: list[str] | None = []
    preferred_score_types: list[str] | None = []
    yks_score: float | None = None
    score_type: str | None = None
    career_interests: list[str] | None = []
    target_departments: list[str] | None = []
    max_tuition_fee: int | None = None
    needs_scholarship: bool = False


# ============================================================
# Task 101.1: University Endpoints
# ============================================================


@router.get("/universities", response_model=list[UniversityResponse])
async def search_universities(
    query: str | None = Query(None, description="Search in university name"),
    city: str | None = Query(None, description="Filter by city"),
    university_type: str | None = Query(
        None, description="Filter by type (devlet/vakif)"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Search universities

    Returns list of universities with filters
    """
    service = UniversityAdvisoryService(db)

    uni_type = UniversityType(university_type) if university_type else None

    universities = await service.search_universities(
        query=query, city=city, university_type=uni_type, limit=limit, offset=offset
    )

    return [
        UniversityResponse(
            id=str(u.id),
            name=u.name,
            short_name=u.short_name,
            university_type=u.university_type.value,
            city=u.city,
            district=u.district,
            website=u.website,
            established_year=u.established_year,
            world_ranking=u.world_ranking,
            turkey_ranking=u.turkey_ranking,
        )
        for u in universities
    ]


@router.get("/universities/{university_id}", response_model=UniversityResponse)
async def get_university(university_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get university details by ID"""
    service = UniversityAdvisoryService(db)
    university = await service.get_university(university_id)

    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    return UniversityResponse(
        id=str(university.id),
        name=university.name,
        short_name=university.short_name,
        university_type=university.university_type.value,
        city=university.city,
        district=university.district,
        website=university.website,
        established_year=university.established_year,
        world_ranking=university.world_ranking,
        turkey_ranking=university.turkey_ranking,
    )


@router.get("/cities", response_model=list[str])
async def get_cities(db: AsyncSession = Depends(get_db)):
    """Get all cities with universities"""
    service = UniversityAdvisoryService(db)
    return await service.get_all_cities()


# ============================================================
# Task 101.2: Department Endpoints
# ============================================================


@router.get("/departments", response_model=list[DepartmentResponse])
async def search_departments(
    query: str | None = Query(None, description="Search in department name"),
    degree_type: str | None = Query(None, description="Filter by degree type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Search departments

    Returns list of departments with career information
    """
    service = UniversityAdvisoryService(db)

    departments = await service.search_departments(
        query=query, degree_type=degree_type, limit=limit, offset=offset
    )

    return [
        DepartmentResponse(
            id=str(d.id),
            name=d.name,
            degree_type=d.degree_type,
            education_language=d.education_language,
            education_duration=d.education_duration,
            career_opportunities=d.career_opportunities,
            average_salary=d.average_salary,
            employment_rate=d.employment_rate,
        )
        for d in departments
    ]


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get department details by ID"""
    service = UniversityAdvisoryService(db)
    department = await service.get_department(department_id)

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    return DepartmentResponse(
        id=str(department.id),
        name=department.name,
        degree_type=department.degree_type,
        education_language=department.education_language,
        education_duration=department.education_duration,
        career_opportunities=department.career_opportunities,
        average_salary=department.average_salary,
        employment_rate=department.employment_rate,
    )


# ============================================================
# Task 101.3 & 101.4: Program Search (Base Scores + Quotas)
# ============================================================


@router.get("/programs", response_model=list[ProgramResponse])
async def search_programs(
    year: int = Query(2024, description="Academic year"),
    score_type: str | None = Query(None, description="Score type (SAY/EA/SOZ/DIL)"),
    min_score: float | None = Query(None, description="Minimum base score"),
    max_score: float | None = Query(None, description="Maximum base score"),
    city: str | None = Query(None, description="University city"),
    university_type: str | None = Query(
        None, description="University type (devlet/vakif)"
    ),
    department_name: str | None = Query(None, description="Department name filter"),
    program_type: str | None = Query(None, description="Program type"),
    has_scholarship: bool | None = Query(None, description="Has scholarship"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("base_score", description="Sort field"),
    order_desc: bool = Query(True, description="Sort descending"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search university programs with base scores and quotas

    Comprehensive search with multiple filters
    """
    service = UniversityAdvisoryService(db)

    # Convert enums
    score_type_enum = ScoreType(score_type) if score_type else None
    uni_type_enum = UniversityType(university_type) if university_type else None
    prog_type_enum = ProgramType(program_type) if program_type else None

    programs = await service.search_programs(
        year=year,
        score_type=score_type_enum,
        min_score=min_score,
        max_score=max_score,
        city=city,
        university_type=uni_type_enum,
        department_name=department_name,
        program_type=prog_type_enum,
        has_scholarship=has_scholarship,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_desc=order_desc,
    )

    return [
        ProgramResponse(
            id=str(p.id),
            program_name=p.program_name,
            university_name=p.university.name if p.university else "N/A",
            department_name=p.department.name if p.department else "N/A",
            city=p.university.city if p.university else "N/A",
            year=p.year,
            score_type=p.score_type.value,
            base_score=p.base_score,
            top_score=p.top_score,
            median_score=p.median_score,
            total_quota=p.total_quota,
            filled_quota=p.filled_quota,
            acceptance_rate=p.acceptance_rate,
            scholarship=p.scholarship,
            tuition_fee=p.tuition_fee,
        )
        for p in programs
    ]


@router.get("/programs/{program_id}", response_model=ProgramResponse)
async def get_program(program_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get program details by ID"""
    service = UniversityAdvisoryService(db)
    program = await service.get_program(program_id)

    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    return ProgramResponse(
        id=str(program.id),
        program_name=program.program_name,
        university_name=program.university.name if program.university else "N/A",
        department_name=program.department.name if program.department else "N/A",
        city=program.university.city if program.university else "N/A",
        year=program.year,
        score_type=program.score_type.value,
        base_score=program.base_score,
        top_score=program.top_score,
        median_score=program.median_score,
        total_quota=program.total_quota,
        filled_quota=program.filled_quota,
        acceptance_rate=program.acceptance_rate,
        scholarship=program.scholarship,
        tuition_fee=program.tuition_fee,
    )


# ============================================================
# Statistics and Analytics
# ============================================================


@router.get("/statistics/base-scores")
async def get_base_score_statistics(
    year: int = Query(2024),
    score_type: str = Query(..., description="Score type (SAY/EA/SOZ/DIL)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get base score statistics

    Returns min, max, avg, count for a year and score type
    """
    service = UniversityAdvisoryService(db)
    score_type_enum = ScoreType(score_type)

    return await service.get_base_score_statistics(year, score_type_enum)


@router.get("/statistics/quotas")
async def get_quota_statistics(
    year: int = Query(2024),
    score_type: str | None = Query(None, description="Score type (SAY/EA/SOZ/DIL)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get quota statistics

    Returns total quotas, filled quotas, acceptance rates
    """
    service = UniversityAdvisoryService(db)
    score_type_enum = ScoreType(score_type) if score_type else None

    return await service.get_quota_statistics(year, score_type_enum)


@router.get("/programs/{program_id}/history")
async def get_program_history(
    program_id: UUID,
    years: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical base scores for a program

    Returns historical data for trend analysis
    """
    service = UniversityAdvisoryService(db)
    history = await service.get_historical_scores(program_id, years)

    return [
        {
            "year": h.year,
            "base_score": h.base_score,
            "top_score": h.top_score,
            "median_score": h.median_score,
            "total_quota": h.total_quota,
            "filled_quota": h.filled_quota,
        }
        for h in history
    ]


@router.get("/programs/{program_id}/prediction")
async def predict_base_score(
    program_id: UUID,
    target_year: int = Query(..., description="Year to predict"),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict base score for target year

    Uses linear regression on historical data
    """
    service = UniversityAdvisoryService(db)
    predicted_score = await service.predict_base_score(program_id, target_year)

    if predicted_score is None:
        raise HTTPException(
            status_code=400, detail="Insufficient historical data for prediction"
        )

    return {
        "program_id": str(program_id),
        "target_year": target_year,
        "predicted_base_score": predicted_score,
    }


@router.get("/competitive-programs")
async def get_competitive_programs(
    year: int = Query(2024),
    score_type: str = Query(..., description="Score type (SAY/EA/SOZ/DIL)"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most competitive programs

    Returns programs with highest competition ratios
    """
    service = UniversityAdvisoryService(db)
    score_type_enum = ScoreType(score_type)

    programs = await service.get_competitive_programs(year, score_type_enum, limit)

    return [
        {
            "program_name": p.program_name,
            "university_name": p.university.name if p.university else "N/A",
            "base_score": p.base_score,
            "competition_ratio": p.competition_ratio,
            "total_quota": p.total_quota,
        }
        for p in programs
    ]


# ============================================================
# Personalized Recommendations
# ============================================================


@router.get("/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(
    student_score: float = Query(..., description="Student's YKS score"),
    score_type: str = Query(..., description="Score type (SAY/EA/SOZ/DIL)"),
    year: int = Query(2024),
    limit: int = Query(50, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get personalized program recommendations

    Returns programs matched to student score and preferences
    """
    user_id = UUID(current_user.user_id)
    service = UniversityAdvisoryService(db)
    score_type_enum = ScoreType(score_type)

    recommendations = await service.get_personalized_recommendations(
        user_id=user_id,
        student_score=student_score,
        score_type=score_type_enum,
        year=year,
        limit=limit,
    )

    return [
        RecommendationResponse(
            program=ProgramResponse(
                id=str(r["program"].id),
                program_name=r["program"].program_name,
                university_name=r["program"].university.name
                if r["program"].university
                else "N/A",
                department_name=r["program"].department.name
                if r["program"].department
                else "N/A",
                city=r["program"].university.city if r["program"].university else "N/A",
                year=r["program"].year,
                score_type=r["program"].score_type.value,
                base_score=r["program"].base_score,
                top_score=r["program"].top_score,
                median_score=r["program"].median_score,
                total_quota=r["program"].total_quota,
                filled_quota=r["program"].filled_quota,
                acceptance_rate=r["program"].acceptance_rate,
                scholarship=r["program"].scholarship,
                tuition_fee=r["program"].tuition_fee,
            ),
            match_score=r["match_score"],
            score_diff=r["score_diff"],
            placement_probability=r["placement_probability"],
        )
        for r in recommendations
    ]


# ============================================================
# User Preferences
# ============================================================


@router.post("/preferences")
async def save_preferences(
    preferences: UserPreferencesRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or update user preferences"""
    user_id = UUID(current_user.user_id)
    service = UniversityAdvisoryService(db)

    saved_pref = await service.save_user_preferences(
        user_id=user_id, **preferences.dict(exclude_unset=True)
    )

    return {
        "id": str(saved_pref.id),
        "user_id": str(saved_pref.user_id),
        "preferred_cities": saved_pref.preferred_cities,
        "preferred_university_types": saved_pref.preferred_university_types,
        "yks_score": saved_pref.yks_score,
        "score_type": saved_pref.score_type,
    }


@router.get("/preferences")
async def get_preferences(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user preferences"""
    user_id = UUID(current_user.user_id)
    service = UniversityAdvisoryService(db)
    preferences = await service.get_user_preferences(user_id)

    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")

    return {
        "id": str(preferences.id),
        "user_id": str(preferences.user_id),
        "preferred_cities": preferences.preferred_cities,
        "preferred_university_types": preferences.preferred_university_types,
        "yks_score": preferences.yks_score,
        "score_type": preferences.score_type,
        "career_interests": preferences.career_interests,
        "max_tuition_fee": preferences.max_tuition_fee,
        "needs_scholarship": preferences.needs_scholarship,
    }
