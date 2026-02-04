"""
Task 104: University Information API Routes

REST API for campus info, living costs, dormitories, and scholarships
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.university_info_service import UniversityInfoService
from models.university_info import CampusType, AccommodationType, ScholarshipType


router = APIRouter(prefix="/api/university-info", tags=["University Information"])


# ============================================================
# Request/Response Models
# ============================================================


# Campus Models
class CampusCreateRequest(BaseModel):
    """Request model for creating campus info"""

    university_id: UUID
    campus_name: str
    city: str
    campus_type: CampusType = CampusType.MAIN_CAMPUS
    district: Optional[str] = None
    total_area_sqm: Optional[int] = None
    student_clubs: Optional[List[Dict[str, Any]]] = None
    total_student_clubs: Optional[int] = None
    health_center: bool = False
    career_center: bool = False
    wifi_available: bool = True
    shuttle_service: bool = False


class CampusResponse(BaseModel):
    """Response model for campus info"""

    id: UUID
    campus_name: str
    campus_type: Optional[str]
    city: str
    total_area_sqm: Optional[int]
    total_student_clubs: Optional[int]
    health_center: bool
    career_center: bool
    wifi_available: bool

    class Config:
        from_attributes = True


# Living Cost Models
class LivingCostCreateRequest(BaseModel):
    """Request model for creating living cost data"""

    city: str
    year: int = 2024
    rent_studio_avg: Optional[int] = None
    food_budget_avg: Optional[int] = None
    public_transport_monthly: Optional[int] = None
    total_avg_budget: Optional[int] = None
    cost_of_living_index: Optional[float] = None


class LivingCostResponse(BaseModel):
    """Response model for living cost data"""

    id: UUID
    city: str
    year: int
    rent_studio_avg: Optional[int]
    food_budget_avg: Optional[int]
    public_transport_monthly: Optional[int]
    total_avg_budget: Optional[int]
    cost_of_living_index: Optional[float]

    class Config:
        from_attributes = True


# Dormitory Models
class DormitoryCreateRequest(BaseModel):
    """Request model for creating dormitory info"""

    university_id: Optional[UUID] = None
    name: str
    accommodation_type: AccommodationType
    city: str
    district: Optional[str] = None
    total_capacity: Optional[int] = None
    price_avg: Optional[int] = None
    meals_included: bool = False
    wifi_included: bool = True
    distance_to_campus_km: Optional[float] = None


class DormitoryResponse(BaseModel):
    """Response model for dormitory info"""

    id: UUID
    name: str
    accommodation_type: str
    city: str
    total_capacity: Optional[int]
    price_avg: Optional[int]
    meals_included: bool
    wifi_included: bool
    distance_to_campus_km: Optional[float]

    class Config:
        from_attributes = True


# Scholarship Models
class ScholarshipCreateRequest(BaseModel):
    """Request model for creating scholarship program"""

    university_id: Optional[UUID] = None
    name: str
    scholarship_type: ScholarshipType
    coverage_percentage: Optional[float] = None
    amount_avg: Optional[int] = None
    covers_tuition: bool = True
    covers_accommodation: bool = False
    min_exam_score: Optional[float] = None
    active: bool = True


class ScholarshipResponse(BaseModel):
    """Response model for scholarship program"""

    id: UUID
    name: str
    scholarship_type: str
    coverage_percentage: Optional[float]
    amount_avg: Optional[int]
    covers_tuition: bool
    covers_accommodation: bool
    min_exam_score: Optional[float]
    active: bool

    class Config:
        from_attributes = True


# ============================================================
# Task 104.1: Campus Information Endpoints
# ============================================================


@router.get("/campus/{university_id}", response_model=List[CampusResponse])
async def get_campus_info(university_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get all campus information for a university

    Returns list of campuses with facilities and services
    """
    service = UniversityInfoService(db)
    campuses = await service.get_campus_info(university_id)

    return [
        CampusResponse(
            id=c.id,
            campus_name=c.campus_name,
            campus_type=c.campus_type.value if c.campus_type else None,
            city=c.city,
            total_area_sqm=c.total_area_sqm,
            total_student_clubs=c.total_student_clubs,
            health_center=c.health_center,
            career_center=c.career_center,
            wifi_available=c.wifi_available,
        )
        for c in campuses
    ]


@router.post("/campus", response_model=CampusResponse)
async def create_campus_info(
    request: CampusCreateRequest, db: AsyncSession = Depends(get_db)
):
    """Create new campus information"""
    service = UniversityInfoService(db)

    campus = await service.create_campus_info(
        university_id=request.university_id,
        campus_name=request.campus_name,
        city=request.city,
        campus_type=request.campus_type,
        district=request.district,
        total_area_sqm=request.total_area_sqm,
        student_clubs=request.student_clubs,
        total_student_clubs=request.total_student_clubs,
        health_center=request.health_center,
        career_center=request.career_center,
        wifi_available=request.wifi_available,
        shuttle_service=request.shuttle_service,
    )

    return CampusResponse(
        id=campus.id,
        campus_name=campus.campus_name,
        campus_type=campus.campus_type.value if campus.campus_type else None,
        city=campus.city,
        total_area_sqm=campus.total_area_sqm,
        total_student_clubs=campus.total_student_clubs,
        health_center=campus.health_center,
        career_center=campus.career_center,
        wifi_available=campus.wifi_available,
    )


@router.get("/campus/{university_id}/facilities", response_model=Dict[str, Any])
async def get_campus_facilities(
    university_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Get aggregate facilities for all campuses

    Returns combined facilities, clubs, and services across all campuses
    """
    service = UniversityInfoService(db)
    facilities = await service.get_campus_facilities(university_id)

    return facilities


# ============================================================
# Task 104.2: City Living Costs Endpoints
# ============================================================


@router.get("/living-cost/{city}", response_model=Optional[LivingCostResponse])
async def get_city_living_cost(
    city: str,
    year: int = Query(2024, description="Year for cost data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get living cost data for a city

    Returns accommodation, food, transport, and total budget estimates
    """
    service = UniversityInfoService(db)
    cost = await service.get_city_living_cost(city, year)

    if not cost:
        raise HTTPException(
            status_code=404, detail="Living cost data not found for this city"
        )

    return LivingCostResponse(
        id=cost.id,
        city=cost.city,
        year=cost.year,
        rent_studio_avg=cost.rent_studio_avg,
        food_budget_avg=cost.food_budget_avg,
        public_transport_monthly=cost.public_transport_monthly,
        total_avg_budget=cost.total_avg_budget,
        cost_of_living_index=cost.cost_of_living_index,
    )


@router.post("/living-cost", response_model=LivingCostResponse)
async def create_living_cost(
    request: LivingCostCreateRequest, db: AsyncSession = Depends(get_db)
):
    """Create new city living cost data"""
    service = UniversityInfoService(db)

    cost = await service.create_city_living_cost(
        city=request.city,
        year=request.year,
        rent_studio_avg=request.rent_studio_avg,
        food_budget_avg=request.food_budget_avg,
        public_transport_monthly=request.public_transport_monthly,
        total_avg_budget=request.total_avg_budget,
        cost_of_living_index=request.cost_of_living_index,
    )

    return LivingCostResponse(
        id=cost.id,
        city=cost.city,
        year=cost.year,
        rent_studio_avg=cost.rent_studio_avg,
        food_budget_avg=cost.food_budget_avg,
        public_transport_monthly=cost.public_transport_monthly,
        total_avg_budget=cost.total_avg_budget,
        cost_of_living_index=cost.cost_of_living_index,
    )


@router.get("/living-cost/compare/cities", response_model=List[Dict[str, Any]])
async def compare_city_costs(
    cities: str = Query(..., description="Comma-separated city names"),
    year: int = Query(2024, description="Year for cost data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare living costs across multiple cities

    Pass cities as comma-separated string: "Istanbul,Ankara,Izmir"
    """
    service = UniversityInfoService(db)
    city_list = [c.strip() for c in cities.split(",")]

    comparison = await service.compare_city_costs(city_list, year)

    return comparison


@router.get("/living-cost/{city}/student-budget", response_model=Dict[str, Any])
async def get_student_budget_estimate(
    city: str,
    accommodation_type: str = Query(
        "dormitory", description="Type: dormitory, studio, shared"
    ),
    year: int = Query(2024, description="Year for budget data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get estimated student budget for a city

    Returns monthly and annual cost breakdown
    """
    service = UniversityInfoService(db)
    budget = await service.get_student_budget_estimate(city, accommodation_type, year)

    if not budget:
        raise HTTPException(
            status_code=404, detail="Budget data not available for this city"
        )

    return budget


# ============================================================
# Task 104.3: Dormitory Information Endpoints
# ============================================================


@router.get("/dormitories", response_model=List[DormitoryResponse])
async def get_dormitories(
    university_id: Optional[UUID] = Query(None, description="Filter by university"),
    city: Optional[str] = Query(None, description="Filter by city"),
    accommodation_type: Optional[AccommodationType] = Query(
        None, description="Filter by type"
    ),
    max_price: Optional[int] = Query(None, description="Maximum monthly price"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dormitory information with filters

    Returns list of dormitories sorted by price
    """
    service = UniversityInfoService(db)
    dormitories = await service.get_dormitories(
        university_id=university_id,
        city=city,
        accommodation_type=accommodation_type,
        max_price=max_price,
    )

    return [
        DormitoryResponse(
            id=d.id,
            name=d.name,
            accommodation_type=d.accommodation_type.value
            if d.accommodation_type
            else "unknown",
            city=d.city,
            total_capacity=d.total_capacity,
            price_avg=d.price_avg,
            meals_included=d.meals_included,
            wifi_included=d.wifi_included,
            distance_to_campus_km=d.distance_to_campus_km,
        )
        for d in dormitories
    ]


@router.get("/dormitories/{dormitory_id}", response_model=DormitoryResponse)
async def get_dormitory_by_id(dormitory_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get specific dormitory information"""
    service = UniversityInfoService(db)
    dormitory = await service.get_dormitory_by_id(dormitory_id)

    if not dormitory:
        raise HTTPException(status_code=404, detail="Dormitory not found")

    return DormitoryResponse(
        id=dormitory.id,
        name=dormitory.name,
        accommodation_type=dormitory.accommodation_type.value
        if dormitory.accommodation_type
        else "unknown",
        city=dormitory.city,
        total_capacity=dormitory.total_capacity,
        price_avg=dormitory.price_avg,
        meals_included=dormitory.meals_included,
        wifi_included=dormitory.wifi_included,
        distance_to_campus_km=dormitory.distance_to_campus_km,
    )


@router.post("/dormitories", response_model=DormitoryResponse)
async def create_dormitory_info(
    request: DormitoryCreateRequest, db: AsyncSession = Depends(get_db)
):
    """Create new dormitory information"""
    service = UniversityInfoService(db)

    dormitory = await service.create_dormitory_info(
        name=request.name,
        accommodation_type=request.accommodation_type,
        city=request.city,
        university_id=request.university_id,
        district=request.district,
        total_capacity=request.total_capacity,
        price_avg=request.price_avg,
        meals_included=request.meals_included,
        wifi_included=request.wifi_included,
        distance_to_campus_km=request.distance_to_campus_km,
    )

    return DormitoryResponse(
        id=dormitory.id,
        name=dormitory.name,
        accommodation_type=dormitory.accommodation_type.value,
        city=dormitory.city,
        total_capacity=dormitory.total_capacity,
        price_avg=dormitory.price_avg,
        meals_included=dormitory.meals_included,
        wifi_included=dormitory.wifi_included,
        distance_to_campus_km=dormitory.distance_to_campus_km,
    )


@router.get("/dormitories/statistics/summary", response_model=Dict[str, Any])
async def get_dormitory_statistics(
    university_id: Optional[UUID] = Query(None, description="Filter by university"),
    city: Optional[str] = Query(None, description="Filter by city"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregate dormitory statistics

    Returns total capacity, average price, and type distribution
    """
    service = UniversityInfoService(db)
    stats = await service.get_dormitory_statistics(
        university_id=university_id, city=city
    )

    return stats


# ============================================================
# Task 104.4: Scholarship Programs Endpoints
# ============================================================


@router.get("/scholarships", response_model=List[ScholarshipResponse])
async def get_scholarships(
    university_id: Optional[UUID] = Query(None, description="Filter by university"),
    scholarship_type: Optional[ScholarshipType] = Query(
        None, description="Filter by type"
    ),
    min_coverage: Optional[float] = Query(
        None, description="Minimum coverage percentage"
    ),
    active_only: bool = Query(True, description="Show only active scholarships"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get scholarship programs with filters

    Returns list of scholarships sorted by coverage percentage
    """
    service = UniversityInfoService(db)
    scholarships = await service.get_scholarships(
        university_id=university_id,
        scholarship_type=scholarship_type,
        min_coverage=min_coverage,
        active_only=active_only,
    )

    return [
        ScholarshipResponse(
            id=s.id,
            name=s.name,
            scholarship_type=s.scholarship_type.value
            if s.scholarship_type
            else "unknown",
            coverage_percentage=s.coverage_percentage,
            amount_avg=s.amount_avg,
            covers_tuition=s.covers_tuition,
            covers_accommodation=s.covers_accommodation,
            min_exam_score=s.min_exam_score,
            active=s.active,
        )
        for s in scholarships
    ]


@router.get("/scholarships/{scholarship_id}", response_model=ScholarshipResponse)
async def get_scholarship_by_id(
    scholarship_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Get specific scholarship information"""
    service = UniversityInfoService(db)
    scholarship = await service.get_scholarship_by_id(scholarship_id)

    if not scholarship:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    return ScholarshipResponse(
        id=scholarship.id,
        name=scholarship.name,
        scholarship_type=scholarship.scholarship_type.value
        if scholarship.scholarship_type
        else "unknown",
        coverage_percentage=scholarship.coverage_percentage,
        amount_avg=scholarship.amount_avg,
        covers_tuition=scholarship.covers_tuition,
        covers_accommodation=scholarship.covers_accommodation,
        min_exam_score=scholarship.min_exam_score,
        active=scholarship.active,
    )


@router.post("/scholarships", response_model=ScholarshipResponse)
async def create_scholarship_program(
    request: ScholarshipCreateRequest, db: AsyncSession = Depends(get_db)
):
    """Create new scholarship program"""
    service = UniversityInfoService(db)

    scholarship = await service.create_scholarship_program(
        name=request.name,
        scholarship_type=request.scholarship_type,
        university_id=request.university_id,
        coverage_percentage=request.coverage_percentage,
        amount_avg=request.amount_avg,
        covers_tuition=request.covers_tuition,
        covers_accommodation=request.covers_accommodation,
        min_exam_score=request.min_exam_score,
        active=request.active,
    )

    return ScholarshipResponse(
        id=scholarship.id,
        name=scholarship.name,
        scholarship_type=scholarship.scholarship_type.value,
        coverage_percentage=scholarship.coverage_percentage,
        amount_avg=scholarship.amount_avg,
        covers_tuition=scholarship.covers_tuition,
        covers_accommodation=scholarship.covers_accommodation,
        min_exam_score=scholarship.min_exam_score,
        active=scholarship.active,
    )


@router.get(
    "/scholarships/eligible/{university_id}", response_model=List[ScholarshipResponse]
)
async def get_eligible_scholarships(
    university_id: UUID,
    exam_score: float = Query(..., description="Student's exam score"),
    high_school_gpa: Optional[float] = Query(None, description="High school GPA"),
    family_income: Optional[int] = Query(None, description="Family income (TRY)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get scholarships the student is eligible for

    Returns scholarships matching student's qualifications
    """
    service = UniversityInfoService(db)
    scholarships = await service.get_eligible_scholarships(
        university_id=university_id,
        exam_score=exam_score,
        high_school_gpa=high_school_gpa,
        family_income=family_income,
    )

    return [
        ScholarshipResponse(
            id=s.id,
            name=s.name,
            scholarship_type=s.scholarship_type.value
            if s.scholarship_type
            else "unknown",
            coverage_percentage=s.coverage_percentage,
            amount_avg=s.amount_avg,
            covers_tuition=s.covers_tuition,
            covers_accommodation=s.covers_accommodation,
            min_exam_score=s.min_exam_score,
            active=s.active,
        )
        for s in scholarships
    ]


@router.get("/scholarships/statistics/{university_id}", response_model=Dict[str, Any])
async def get_scholarship_statistics(
    university_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Get aggregate scholarship statistics

    Returns total scholarships, coverage stats, and type distribution
    """
    service = UniversityInfoService(db)
    stats = await service.get_scholarship_statistics(university_id)

    return stats


# ============================================================
# Comprehensive University Information Endpoint
# ============================================================


@router.get("/comprehensive/{university_id}", response_model=Dict[str, Any])
async def get_comprehensive_university_info(
    university_id: UUID,
    year: int = Query(2024, description="Year for data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all university information in one call

    Returns campuses, living costs, dormitories, scholarships, and statistics
    """
    service = UniversityInfoService(db)
    info = await service.get_comprehensive_university_info(university_id, year)

    return info


# ============================================================
# University Statistics Endpoints
# ============================================================


@router.get("/statistics/{university_id}", response_model=Dict[str, Any])
async def get_university_statistics(
    university_id: UUID,
    year: int = Query(2024, description="Year for statistics"),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate statistics for a university"""
    service = UniversityInfoService(db)
    stats = await service.get_university_statistics(university_id, year)

    if not stats:
        raise HTTPException(status_code=404, detail="Statistics not found")

    return {
        "id": stats.id,
        "university_id": stats.university_id,
        "year": stats.year,
        "total_campuses": stats.total_campuses,
        "total_student_clubs": stats.total_student_clubs,
        "avg_monthly_cost": stats.avg_monthly_cost,
        "total_dormitory_capacity": stats.total_dormitory_capacity,
        "total_scholarships": stats.total_scholarships,
        "affordability_score": stats.affordability_score,
    }


@router.post("/statistics/{university_id}/generate", response_model=Dict[str, Any])
async def generate_university_statistics(
    university_id: UUID,
    year: int = Query(2024, description="Year for statistics"),
    db: AsyncSession = Depends(get_db),
):
    """Generate or update aggregate statistics for a university"""
    service = UniversityInfoService(db)
    stats = await service.generate_university_statistics(university_id, year)

    return {
        "id": stats.id,
        "university_id": stats.university_id,
        "year": stats.year,
        "total_campuses": stats.total_campuses,
        "total_student_clubs": stats.total_student_clubs,
        "avg_monthly_cost": stats.avg_monthly_cost,
        "total_dormitory_capacity": stats.total_dormitory_capacity,
        "total_scholarships": stats.total_scholarships,
        "affordability_score": stats.affordability_score,
        "last_updated": stats.last_updated,
    }
