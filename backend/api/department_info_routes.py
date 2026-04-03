"""
Task 103: Department Information API Routes

REST API for curriculum, career opportunities, salary expectations, and sector analysis
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import AuthenticatedUser, get_current_admin_user
from models.department_info import ExperienceLevel, IndustryType
from services.department_info_service import DepartmentInfoService

router = APIRouter(prefix="/api/v1/department-info", tags=["Department Information"])


# ============================================================
# Request/Response Models
# ============================================================


class CurriculumCreateRequest(BaseModel):
    """Request model for creating curriculum"""

    department_id: UUID
    total_credits: int
    duration_years: int
    duration_semesters: int
    core_courses: list[dict[str, Any]]
    elective_courses: list[dict[str, Any]] | None = None
    specialization_tracks: list[str] | None = None
    learning_outcomes: list[str] | None = None
    skills_gained: list[str] | None = None
    internship_required: bool = False
    thesis_required: bool = False
    capstone_project: bool = False
    ects_credits: int | None = None
    exchange_programs_available: bool = False


class CurriculumResponse(BaseModel):
    """Response model for curriculum"""

    id: UUID
    department_id: UUID
    total_credits: int
    duration_years: int
    duration_semesters: int
    core_courses: list[dict[str, Any]]
    elective_courses: list[dict[str, Any]] | None
    specialization_tracks: list[str] | None
    learning_outcomes: list[str] | None
    skills_gained: list[str] | None
    internship_required: bool
    thesis_required: bool
    capstone_project: bool
    ects_credits: int | None
    exchange_programs_available: bool

    model_config = ConfigDict(from_attributes=True)


class CareerOpportunityCreateRequest(BaseModel):
    """Request model for creating career opportunity"""

    department_id: UUID
    job_title: str
    job_description: str | None = None
    industry_type: IndustryType | None = None
    employment_rate: float | None = None
    average_hiring_time_days: int | None = None
    demand_level: str | None = None
    required_skills: list[str] | None = None
    preferred_certifications: list[str] | None = None
    career_growth_potential: str | None = None
    work_life_balance_rating: float | None = None
    job_satisfaction_rating: float | None = None
    top_employers: list[str] | None = None


class CareerOpportunityResponse(BaseModel):
    """Response model for career opportunity"""

    id: UUID
    department_id: UUID
    job_title: str
    job_description: str | None
    industry_type: IndustryType | None
    employment_rate: float | None
    average_hiring_time_days: int | None
    demand_level: str | None
    required_skills: list[str] | None
    preferred_certifications: list[str] | None
    career_growth_potential: str | None
    work_life_balance_rating: float | None
    job_satisfaction_rating: float | None
    top_employers: list[str] | None

    model_config = ConfigDict(from_attributes=True)


class SalaryExpectationCreateRequest(BaseModel):
    """Request model for creating salary expectation"""

    department_id: UUID
    experience_level: ExperienceLevel
    min_salary: int
    max_salary: int
    average_salary: int
    median_salary: int | None = None
    region: str | None = None
    city: str | None = None
    industry_type: IndustryType | None = None
    currency: str = "TRY"
    year: int = 2024
    sample_size: int | None = None
    average_bonus_percentage: float | None = None
    stock_options_common: bool = False
    remote_work_percentage: float | None = None
    career_opportunity_id: UUID | None = None


class SalaryExpectationResponse(BaseModel):
    """Response model for salary expectation"""

    id: UUID
    department_id: UUID
    experience_level: ExperienceLevel
    min_salary: int
    max_salary: int
    average_salary: int
    median_salary: int | None
    region: str | None
    city: str | None
    industry_type: IndustryType | None
    currency: str
    year: int
    sample_size: int | None
    average_bonus_percentage: float | None
    stock_options_common: bool
    remote_work_percentage: float | None

    model_config = ConfigDict(from_attributes=True)


class SectorAnalysisCreateRequest(BaseModel):
    """Request model for creating sector analysis"""

    industry_type: IndustryType
    sector_name: str
    market_size_billion_tl: float | None = None
    total_employment: int | None = None
    annual_growth_rate: float | None = None
    job_growth_rate: float | None = None
    growth_trend: str | None = None
    total_job_openings: int | None = None
    in_demand_skills: list[str] | None = None
    emerging_technologies: list[str] | None = None
    future_demand_prediction: str | None = None
    automation_risk: str | None = None
    sustainability_rating: float | None = None
    innovation_index: float | None = None
    year: int = 2024
    related_department_ids: list[UUID] | None = None


class SectorAnalysisResponse(BaseModel):
    """Response model for sector analysis"""

    id: UUID
    industry_type: IndustryType
    sector_name: str
    market_size_billion_tl: float | None
    total_employment: int | None
    annual_growth_rate: float | None
    job_growth_rate: float | None
    growth_trend: str | None
    total_job_openings: int | None
    in_demand_skills: list[str] | None
    emerging_technologies: list[str] | None
    future_demand_prediction: str | None
    automation_risk: str | None
    sustainability_rating: float | None
    innovation_index: float | None
    year: int

    model_config = ConfigDict(from_attributes=True)


class EmploymentStatisticsResponse(BaseModel):
    """Response for employment statistics"""

    total_career_paths: int
    average_employment_rate: float
    average_hiring_time_days: int
    high_demand_careers: int
    top_industries: list[dict[str, Any]]
    career_growth_high: int


class SalaryProgressionResponse(BaseModel):
    """Response for salary progression"""

    progression: dict[str, dict[str, Any]]


class RegionalSalaryComparisonResponse(BaseModel):
    """Response for regional salary comparison"""

    comparisons: list[dict[str, Any]]


class JobMarketTrendsResponse(BaseModel):
    """Response for job market trends"""

    overall_growth: str
    annual_growth_rate: float
    total_job_openings: int
    sectors_analyzed: int
    top_skills: list[str]
    employment_rate: float
    sectors: list[dict[str, Any]]


class ComprehensiveDepartmentInfoResponse(BaseModel):
    """Response for comprehensive department information"""

    curriculum: dict[str, Any]
    career_opportunities: list[dict[str, Any]]
    salary_progression: dict[str, Any]
    regional_salaries: list[dict[str, Any]]
    sectors: list[dict[str, Any]]
    job_market_trends: dict[str, Any]
    statistics: dict[str, Any]


# ============================================================
# Task 103.1: Curriculum Information Endpoints
# ============================================================


@router.get("/curriculum/{department_id}", response_model=Optional[CurriculumResponse])
async def get_department_curriculum(
    department_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Get curriculum information for a department

    Returns detailed curriculum including courses, specializations, and requirements
    """
    service = DepartmentInfoService(db)
    curriculum = await service.get_department_curriculum(department_id)

    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    return curriculum


@router.post("/curriculum", response_model=CurriculumResponse)
async def create_curriculum(
    request: CurriculumCreateRequest,
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create curriculum information for a department (Admin only)
    """
    service = DepartmentInfoService(db)

    curriculum = await service.create_curriculum(
        department_id=request.department_id,
        total_credits=request.total_credits,
        duration_years=request.duration_years,
        duration_semesters=request.duration_semesters,
        core_courses=request.core_courses,
        elective_courses=request.elective_courses,
        specialization_tracks=request.specialization_tracks,
        learning_outcomes=request.learning_outcomes,
        skills_gained=request.skills_gained,
        internship_required=request.internship_required,
        thesis_required=request.thesis_required,
        capstone_project=request.capstone_project,
        ects_credits=request.ects_credits,
        exchange_programs_available=request.exchange_programs_available,
    )

    return curriculum


@router.get("/curriculum/{department_id}/specializations", response_model=list[str])
async def get_specialization_options(
    department_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Get specialization tracks available for a department

    Returns list of specialization options students can choose
    """
    service = DepartmentInfoService(db)
    specializations = await service.get_specialization_options(department_id)

    return specializations


# ============================================================
# Task 103.2: Career Opportunities Endpoints
# ============================================================


@router.get("/careers/{department_id}", response_model=list[CareerOpportunityResponse])
async def get_career_opportunities(
    department_id: UUID,
    industry_type: IndustryType | None = Query(None, description="Filter by industry"),
    demand_level: str | None = Query(
        None, description="Filter by demand level (high, medium, low)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get career opportunities for a department

    Optionally filter by industry type and demand level
    """
    service = DepartmentInfoService(db)

    careers = await service.get_career_opportunities(
        department_id=department_id,
        industry_type=industry_type,
        demand_level=demand_level,
    )

    return careers


@router.post("/careers", response_model=CareerOpportunityResponse)
async def create_career_opportunity(
    request: CareerOpportunityCreateRequest,
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a career opportunity entry for a department (Admin only)
    """
    service = DepartmentInfoService(db)

    opportunity = await service.create_career_opportunity(
        department_id=request.department_id,
        job_title=request.job_title,
        job_description=request.job_description,
        industry_type=request.industry_type,
        employment_rate=request.employment_rate,
        average_hiring_time_days=request.average_hiring_time_days,
        demand_level=request.demand_level,
        required_skills=request.required_skills,
        preferred_certifications=request.preferred_certifications,
        career_growth_potential=request.career_growth_potential,
        work_life_balance_rating=request.work_life_balance_rating,
        job_satisfaction_rating=request.job_satisfaction_rating,
        top_employers=request.top_employers,
    )

    return opportunity


@router.get(
    "/careers/{department_id}/statistics", response_model=EmploymentStatisticsResponse
)
async def get_employment_statistics(
    department_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Get employment statistics for a department

    Returns aggregate employment data including rates, hiring times, and top industries
    """
    service = DepartmentInfoService(db)
    stats = await service.get_employment_statistics(department_id)

    return stats


# ============================================================
# Task 103.3: Salary Expectations Endpoints
# ============================================================


@router.get("/salaries/{department_id}", response_model=list[SalaryExpectationResponse])
async def get_salary_expectations(
    department_id: UUID,
    experience_level: ExperienceLevel | None = Query(
        None, description="Filter by experience level"
    ),
    city: str | None = Query(None, description="Filter by city"),
    year: int = Query(2024, description="Year for salary data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get salary expectations for a department

    Optionally filter by experience level and city
    """
    service = DepartmentInfoService(db)

    salaries = await service.get_salary_expectations(
        department_id=department_id,
        experience_level=experience_level,
        city=city,
        year=year,
    )

    return salaries


@router.get(
    "/salaries/{department_id}/progression", response_model=SalaryProgressionResponse
)
async def get_salary_progression(
    department_id: UUID,
    city: str | None = Query(None, description="Filter by city"),
    year: int = Query(2024, description="Year for salary data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get salary progression by experience level

    Returns salary ranges for each experience level (entry, junior, mid, senior, expert)
    """
    service = DepartmentInfoService(db)

    progression = await service.get_salary_progression(
        department_id=department_id, city=city, year=year
    )

    return {"progression": progression}


@router.get(
    "/salaries/{department_id}/regional",
    response_model=RegionalSalaryComparisonResponse,
)
async def get_regional_salary_comparison(
    department_id: UUID,
    experience_level: ExperienceLevel = Query(
        ExperienceLevel.ENTRY, description="Experience level to compare"
    ),
    year: int = Query(2024, description="Year for salary data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare salaries across different regions

    Returns salary data for each city, sorted by average salary
    """
    service = DepartmentInfoService(db)

    comparison = await service.get_regional_salary_comparison(
        department_id=department_id, experience_level=experience_level, year=year
    )

    return {"comparisons": comparison}


# ============================================================
# Task 103.4: Sector Analysis Endpoints
# ============================================================


@router.get("/sectors/{industry_type}", response_model=Optional[SectorAnalysisResponse])
async def get_sector_analysis(
    industry_type: IndustryType,
    year: int = Query(2024, description="Year for sector data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get sector analysis for an industry

    Returns market size, employment, growth rates, and future predictions
    """
    service = DepartmentInfoService(db)

    sector = await service.get_sector_analysis(industry_type=industry_type, year=year)

    if not sector:
        raise HTTPException(status_code=404, detail="Sector analysis not found")

    return sector


@router.get(
    "/sectors/department/{department_id}", response_model=list[SectorAnalysisResponse]
)
async def get_related_sectors(
    department_id: UUID,
    year: int = Query(2024, description="Year for sector data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get sector analyses related to a department

    Returns all sectors where this department's graduates typically work
    """
    service = DepartmentInfoService(db)

    sectors = await service.get_related_sectors(department_id=department_id, year=year)

    return sectors


@router.get(
    "/sectors/department/{department_id}/trends", response_model=JobMarketTrendsResponse
)
async def get_job_market_trends(
    department_id: UUID,
    year: int = Query(2024, description="Year for trend data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive job market trends for a department

    Combines sector analyses and employment data to provide overall market outlook
    """
    service = DepartmentInfoService(db)

    trends = await service.get_job_market_trends(department_id=department_id, year=year)

    return trends


# ============================================================
# Department Statistics Endpoints
# ============================================================


@router.get("/statistics/{department_id}", response_model=dict[str, Any])
async def get_department_statistics(
    department_id: UUID,
    year: int = Query(2024, description="Year for statistics"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregate statistics for a department

    Returns pre-computed statistics combining employment, salary, and sector data
    """
    service = DepartmentInfoService(db)

    stats = await service.get_department_statistics(
        department_id=department_id, year=year
    )

    if not stats:
        raise HTTPException(status_code=404, detail="Statistics not found")

    return {
        "id": stats.id,
        "department_id": stats.department_id,
        "year": stats.year,
        "overall_employment_rate": stats.overall_employment_rate,
        "average_hiring_time_days": stats.average_hiring_time_days,
        "entry_level_avg_salary": stats.entry_level_avg_salary,
        "entry_level_min_salary": stats.entry_level_min_salary,
        "entry_level_max_salary": stats.entry_level_max_salary,
        "mid_career_avg_salary": stats.mid_career_avg_salary,
        "senior_avg_salary": stats.senior_avg_salary,
        "salary_growth_rate": stats.salary_growth_rate,
        "top_industries": stats.top_industries,
    }


@router.post("/statistics/{department_id}/generate", response_model=dict[str, Any])
async def generate_department_statistics(
    department_id: UUID,
    year: int = Query(2024, description="Year for statistics"),
    _admin: AuthenticatedUser = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or update aggregate statistics for a department (Admin only)
    """
    service = DepartmentInfoService(db)

    stats = await service.generate_department_statistics(
        department_id=department_id, year=year
    )

    return {
        "id": stats.id,
        "department_id": stats.department_id,
        "year": stats.year,
        "overall_employment_rate": stats.overall_employment_rate,
        "average_hiring_time_days": stats.average_hiring_time_days,
        "entry_level_avg_salary": stats.entry_level_avg_salary,
        "salary_growth_rate": stats.salary_growth_rate,
        "top_industries": stats.top_industries,
        "last_updated": stats.last_updated,
    }


# ============================================================
# Comprehensive Department Info Endpoint
# ============================================================


@router.get(
    "/comprehensive/{department_id}", response_model=ComprehensiveDepartmentInfoResponse
)
async def get_comprehensive_department_info(
    department_id: UUID,
    year: int = Query(2024, description="Year for data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all department information in one call

    Returns curriculum, careers, salaries, sectors, job trends, and statistics
    This is the most efficient endpoint for getting complete department information
    """
    service = DepartmentInfoService(db)

    info = await service.get_comprehensive_department_info(
        department_id=department_id, year=year
    )

    return info
