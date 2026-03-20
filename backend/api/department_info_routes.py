"""
Task 103: Department Information API Routes

REST API for curriculum, career opportunities, salary expectations, and sector analysis
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.department_info_service import DepartmentInfoService
from models.department_info import ExperienceLevel, IndustryType


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
    core_courses: List[Dict[str, Any]]
    elective_courses: Optional[List[Dict[str, Any]]] = None
    specialization_tracks: Optional[List[str]] = None
    learning_outcomes: Optional[List[str]] = None
    skills_gained: Optional[List[str]] = None
    internship_required: bool = False
    thesis_required: bool = False
    capstone_project: bool = False
    ects_credits: Optional[int] = None
    exchange_programs_available: bool = False


class CurriculumResponse(BaseModel):
    """Response model for curriculum"""

    id: UUID
    department_id: UUID
    total_credits: int
    duration_years: int
    duration_semesters: int
    core_courses: List[Dict[str, Any]]
    elective_courses: Optional[List[Dict[str, Any]]]
    specialization_tracks: Optional[List[str]]
    learning_outcomes: Optional[List[str]]
    skills_gained: Optional[List[str]]
    internship_required: bool
    thesis_required: bool
    capstone_project: bool
    ects_credits: Optional[int]
    exchange_programs_available: bool

    model_config = ConfigDict(from_attributes=True)


class CareerOpportunityCreateRequest(BaseModel):
    """Request model for creating career opportunity"""

    department_id: UUID
    job_title: str
    job_description: Optional[str] = None
    industry_type: Optional[IndustryType] = None
    employment_rate: Optional[float] = None
    average_hiring_time_days: Optional[int] = None
    demand_level: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_certifications: Optional[List[str]] = None
    career_growth_potential: Optional[str] = None
    work_life_balance_rating: Optional[float] = None
    job_satisfaction_rating: Optional[float] = None
    top_employers: Optional[List[str]] = None


class CareerOpportunityResponse(BaseModel):
    """Response model for career opportunity"""

    id: UUID
    department_id: UUID
    job_title: str
    job_description: Optional[str]
    industry_type: Optional[IndustryType]
    employment_rate: Optional[float]
    average_hiring_time_days: Optional[int]
    demand_level: Optional[str]
    required_skills: Optional[List[str]]
    preferred_certifications: Optional[List[str]]
    career_growth_potential: Optional[str]
    work_life_balance_rating: Optional[float]
    job_satisfaction_rating: Optional[float]
    top_employers: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)


class SalaryExpectationCreateRequest(BaseModel):
    """Request model for creating salary expectation"""

    department_id: UUID
    experience_level: ExperienceLevel
    min_salary: int
    max_salary: int
    average_salary: int
    median_salary: Optional[int] = None
    region: Optional[str] = None
    city: Optional[str] = None
    industry_type: Optional[IndustryType] = None
    currency: str = "TRY"
    year: int = 2024
    sample_size: Optional[int] = None
    average_bonus_percentage: Optional[float] = None
    stock_options_common: bool = False
    remote_work_percentage: Optional[float] = None
    career_opportunity_id: Optional[UUID] = None


class SalaryExpectationResponse(BaseModel):
    """Response model for salary expectation"""

    id: UUID
    department_id: UUID
    experience_level: ExperienceLevel
    min_salary: int
    max_salary: int
    average_salary: int
    median_salary: Optional[int]
    region: Optional[str]
    city: Optional[str]
    industry_type: Optional[IndustryType]
    currency: str
    year: int
    sample_size: Optional[int]
    average_bonus_percentage: Optional[float]
    stock_options_common: bool
    remote_work_percentage: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class SectorAnalysisCreateRequest(BaseModel):
    """Request model for creating sector analysis"""

    industry_type: IndustryType
    sector_name: str
    market_size_billion_tl: Optional[float] = None
    total_employment: Optional[int] = None
    annual_growth_rate: Optional[float] = None
    job_growth_rate: Optional[float] = None
    growth_trend: Optional[str] = None
    total_job_openings: Optional[int] = None
    in_demand_skills: Optional[List[str]] = None
    emerging_technologies: Optional[List[str]] = None
    future_demand_prediction: Optional[str] = None
    automation_risk: Optional[str] = None
    sustainability_rating: Optional[float] = None
    innovation_index: Optional[float] = None
    year: int = 2024
    related_department_ids: Optional[List[UUID]] = None


class SectorAnalysisResponse(BaseModel):
    """Response model for sector analysis"""

    id: UUID
    industry_type: IndustryType
    sector_name: str
    market_size_billion_tl: Optional[float]
    total_employment: Optional[int]
    annual_growth_rate: Optional[float]
    job_growth_rate: Optional[float]
    growth_trend: Optional[str]
    total_job_openings: Optional[int]
    in_demand_skills: Optional[List[str]]
    emerging_technologies: Optional[List[str]]
    future_demand_prediction: Optional[str]
    automation_risk: Optional[str]
    sustainability_rating: Optional[float]
    innovation_index: Optional[float]
    year: int

    model_config = ConfigDict(from_attributes=True)


class EmploymentStatisticsResponse(BaseModel):
    """Response for employment statistics"""

    total_career_paths: int
    average_employment_rate: float
    average_hiring_time_days: int
    high_demand_careers: int
    top_industries: List[Dict[str, Any]]
    career_growth_high: int


class SalaryProgressionResponse(BaseModel):
    """Response for salary progression"""

    progression: Dict[str, Dict[str, Any]]


class RegionalSalaryComparisonResponse(BaseModel):
    """Response for regional salary comparison"""

    comparisons: List[Dict[str, Any]]


class JobMarketTrendsResponse(BaseModel):
    """Response for job market trends"""

    overall_growth: str
    annual_growth_rate: float
    total_job_openings: int
    sectors_analyzed: int
    top_skills: List[str]
    employment_rate: float
    sectors: List[Dict[str, Any]]


class ComprehensiveDepartmentInfoResponse(BaseModel):
    """Response for comprehensive department information"""

    curriculum: Dict[str, Any]
    career_opportunities: List[Dict[str, Any]]
    salary_progression: Dict[str, Any]
    regional_salaries: List[Dict[str, Any]]
    sectors: List[Dict[str, Any]]
    job_market_trends: Dict[str, Any]
    statistics: Dict[str, Any]


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
    request: CurriculumCreateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Create curriculum information for a department

    Requires department admin permissions (not implemented in this endpoint)
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


@router.get("/curriculum/{department_id}/specializations", response_model=List[str])
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


@router.get("/careers/{department_id}", response_model=List[CareerOpportunityResponse])
async def get_career_opportunities(
    department_id: UUID,
    industry_type: Optional[IndustryType] = Query(
        None, description="Filter by industry"
    ),
    demand_level: Optional[str] = Query(
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
    request: CareerOpportunityCreateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Create a career opportunity entry for a department

    Requires admin permissions (not implemented in this endpoint)
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


@router.get("/salaries/{department_id}", response_model=List[SalaryExpectationResponse])
async def get_salary_expectations(
    department_id: UUID,
    experience_level: Optional[ExperienceLevel] = Query(
        None, description="Filter by experience level"
    ),
    city: Optional[str] = Query(None, description="Filter by city"),
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
    city: Optional[str] = Query(None, description="Filter by city"),
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
    "/sectors/department/{department_id}", response_model=List[SectorAnalysisResponse]
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


@router.get("/statistics/{department_id}", response_model=Dict[str, Any])
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


@router.post("/statistics/{department_id}/generate", response_model=Dict[str, Any])
async def generate_department_statistics(
    department_id: UUID,
    year: int = Query(2024, description="Year for statistics"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or update aggregate statistics for a department

    Recomputes statistics from current career, salary, and sector data
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
