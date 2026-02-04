"""
Task 104: University Information Service

Service layer for campus info, living costs, dormitories, and scholarships
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.university_info import (
    CampusInfo,
    CityLivingCost,
    DormitoryInfo,
    ScholarshipProgram,
    UniversityStatistics,
    CampusType,
    AccommodationType,
    ScholarshipType,
)


class UniversityInfoService:
    """Service for university information operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 104.1: Campus Information
    # ============================================================

    async def get_campus_info(self, university_id: UUID) -> List[CampusInfo]:
        """Get all campus information for a university"""
        query = select(CampusInfo).where(CampusInfo.university_id == university_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_campus_by_id(self, campus_id: UUID) -> Optional[CampusInfo]:
        """Get specific campus information"""
        query = select(CampusInfo).where(CampusInfo.id == campus_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_campus_info(
        self,
        university_id: UUID,
        campus_name: str,
        city: str,
        campus_type: CampusType = CampusType.MAIN_CAMPUS,
        **kwargs,
    ) -> CampusInfo:
        """Create new campus information"""
        campus = CampusInfo(
            university_id=university_id,
            campus_name=campus_name,
            city=city,
            campus_type=campus_type,
            **kwargs,
        )
        self.db.add(campus)
        await self.db.commit()
        await self.db.refresh(campus)
        return campus

    async def get_campus_facilities(self, university_id: UUID) -> Dict[str, Any]:
        """Get aggregate facilities information for all campuses"""
        campuses = await self.get_campus_info(university_id)

        all_facilities = {
            "libraries": [],
            "sports_facilities": [],
            "dining_facilities": [],
            "student_clubs": [],
            "cultural_centers": [],
            "total_clubs": 0,
            "has_health_center": False,
            "has_career_center": False,
            "has_counseling_center": False,
            "total_area_sqm": 0,
        }

        for campus in campuses:
            if campus.libraries:
                all_facilities["libraries"].extend(campus.libraries)
            if campus.sports_facilities:
                all_facilities["sports_facilities"].extend(campus.sports_facilities)
            if campus.dining_facilities:
                all_facilities["dining_facilities"].extend(campus.dining_facilities)
            if campus.student_clubs:
                all_facilities["student_clubs"].extend(campus.student_clubs)
            if campus.cultural_centers:
                all_facilities["cultural_centers"].extend(campus.cultural_centers)

            all_facilities["total_clubs"] += campus.total_student_clubs or 0
            all_facilities["total_area_sqm"] += campus.total_area_sqm or 0

            if campus.health_center:
                all_facilities["has_health_center"] = True
            if campus.career_center:
                all_facilities["has_career_center"] = True
            if campus.counseling_center:
                all_facilities["has_counseling_center"] = True

        # Remove duplicates
        all_facilities["sports_facilities"] = list(
            set(all_facilities["sports_facilities"])
        )
        all_facilities["cultural_centers"] = list(
            set(all_facilities["cultural_centers"])
        )

        return all_facilities

    # ============================================================
    # Task 104.2: City Living Costs
    # ============================================================

    async def get_city_living_cost(
        self, city: str, year: int = 2024
    ) -> Optional[CityLivingCost]:
        """Get living cost data for a city"""
        query = select(CityLivingCost).where(
            and_(CityLivingCost.city == city, CityLivingCost.year == year)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_cities_living_costs(
        self, year: int = 2024
    ) -> List[CityLivingCost]:
        """Get living costs for all cities"""
        query = (
            select(CityLivingCost)
            .where(CityLivingCost.year == year)
            .order_by(CityLivingCost.cost_of_living_index)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_city_living_cost(
        self, city: str, year: int = 2024, **kwargs
    ) -> CityLivingCost:
        """Create new city living cost entry"""
        living_cost = CityLivingCost(city=city, year=year, **kwargs)
        self.db.add(living_cost)
        await self.db.commit()
        await self.db.refresh(living_cost)
        return living_cost

    async def compare_city_costs(
        self, cities: List[str], year: int = 2024
    ) -> List[Dict[str, Any]]:
        """Compare living costs across multiple cities"""
        query = (
            select(CityLivingCost)
            .where(and_(CityLivingCost.city.in_(cities), CityLivingCost.year == year))
            .order_by(CityLivingCost.total_avg_budget)
        )

        result = await self.db.execute(query)
        city_costs = result.scalars().all()

        comparison = []
        for cost in city_costs:
            comparison.append(
                {
                    "city": cost.city,
                    "total_avg_budget": cost.total_avg_budget,
                    "avg_rent": cost.rent_studio_avg,
                    "food_budget": cost.food_budget_avg,
                    "transport_monthly": cost.public_transport_monthly,
                    "cost_of_living_index": cost.cost_of_living_index,
                }
            )

        return comparison

    async def get_student_budget_estimate(
        self, city: str, accommodation_type: str = "dormitory", year: int = 2024
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate estimated student budget for a city

        accommodation_type: "dormitory", "studio", "shared"
        """
        living_cost = await self.get_city_living_cost(city, year)
        if not living_cost:
            return None

        # Base budget
        budget = {
            "city": city,
            "year": year,
            "accommodation_type": accommodation_type,
            "monthly_costs": {},
            "total_monthly": 0,
            "total_annual": 0,
        }

        # Accommodation cost
        if accommodation_type == "dormitory":
            # Will be filled from dormitory data
            budget["monthly_costs"]["accommodation"] = 0
        elif accommodation_type == "studio":
            budget["monthly_costs"]["accommodation"] = living_cost.rent_studio_avg or 0
        elif accommodation_type == "shared":
            budget["monthly_costs"]["accommodation"] = living_cost.shared_room_avg or 0
        else:
            budget["monthly_costs"]["accommodation"] = living_cost.rent_1br_avg or 0

        # Other costs
        budget["monthly_costs"]["utilities"] = living_cost.utilities_avg or 0
        budget["monthly_costs"]["food"] = living_cost.food_budget_avg or 0
        budget["monthly_costs"]["transportation"] = (
            living_cost.public_transport_monthly or 0
        )
        budget["monthly_costs"]["entertainment"] = living_cost.entertainment_avg or 0
        budget["monthly_costs"]["books_supplies"] = living_cost.books_supplies_avg or 0
        budget["monthly_costs"]["personal_care"] = living_cost.personal_care_avg or 0
        budget["monthly_costs"]["phone_internet"] = living_cost.phone_internet_avg or 0

        # Calculate totals
        budget["total_monthly"] = sum(budget["monthly_costs"].values())
        budget["total_annual"] = budget["total_monthly"] * 12

        # Add breakdown percentages
        budget["breakdown_percentages"] = {}
        for category, amount in budget["monthly_costs"].items():
            if budget["total_monthly"] > 0:
                budget["breakdown_percentages"][category] = round(
                    (amount / budget["total_monthly"]) * 100, 1
                )

        return budget

    # ============================================================
    # Task 104.3: Dormitory Information
    # ============================================================

    async def get_dormitories(
        self,
        university_id: Optional[UUID] = None,
        city: Optional[str] = None,
        accommodation_type: Optional[AccommodationType] = None,
        max_price: Optional[int] = None,
    ) -> List[DormitoryInfo]:
        """Get dormitory information with filters"""
        conditions = []

        if university_id:
            conditions.append(DormitoryInfo.university_id == university_id)
        if city:
            conditions.append(DormitoryInfo.city == city)
        if accommodation_type:
            conditions.append(DormitoryInfo.accommodation_type == accommodation_type)
        if max_price:
            conditions.append(DormitoryInfo.price_avg <= max_price)

        query = select(DormitoryInfo)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(DormitoryInfo.price_avg)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_dormitory_by_id(self, dormitory_id: UUID) -> Optional[DormitoryInfo]:
        """Get specific dormitory information"""
        query = select(DormitoryInfo).where(DormitoryInfo.id == dormitory_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_dormitory_info(
        self,
        name: str,
        accommodation_type: AccommodationType,
        city: str,
        university_id: Optional[UUID] = None,
        **kwargs,
    ) -> DormitoryInfo:
        """Create new dormitory information"""
        dormitory = DormitoryInfo(
            name=name,
            accommodation_type=accommodation_type,
            city=city,
            university_id=university_id,
            **kwargs,
        )
        self.db.add(dormitory)
        await self.db.commit()
        await self.db.refresh(dormitory)
        return dormitory

    async def get_dormitory_statistics(
        self, university_id: Optional[UUID] = None, city: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregate dormitory statistics"""
        conditions = []
        if university_id:
            conditions.append(DormitoryInfo.university_id == university_id)
        if city:
            conditions.append(DormitoryInfo.city == city)

        query = select(DormitoryInfo)
        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        dormitories = result.scalars().all()

        if not dormitories:
            return {
                "total_dormitories": 0,
                "total_capacity": 0,
                "avg_price": 0,
                "price_range": {"min": 0, "max": 0},
                "types": [],
            }

        total_capacity = sum(d.total_capacity or 0 for d in dormitories)
        prices = [d.price_avg for d in dormitories if d.price_avg]
        avg_price = sum(prices) / len(prices) if prices else 0

        types = {}
        for d in dormitories:
            type_name = (
                d.accommodation_type.value if d.accommodation_type else "unknown"
            )
            if type_name not in types:
                types[type_name] = 0
            types[type_name] += 1

        return {
            "total_dormitories": len(dormitories),
            "total_capacity": total_capacity,
            "avg_price": int(avg_price),
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
            },
            "types": [{"type": k, "count": v} for k, v in types.items()],
        }

    # ============================================================
    # Task 104.4: Scholarship Programs
    # ============================================================

    async def get_scholarships(
        self,
        university_id: Optional[UUID] = None,
        scholarship_type: Optional[ScholarshipType] = None,
        min_coverage: Optional[float] = None,
        active_only: bool = True,
    ) -> List[ScholarshipProgram]:
        """Get scholarship programs with filters"""
        conditions = []

        if university_id:
            conditions.append(ScholarshipProgram.university_id == university_id)
        if scholarship_type:
            conditions.append(ScholarshipProgram.scholarship_type == scholarship_type)
        if min_coverage:
            conditions.append(ScholarshipProgram.coverage_percentage >= min_coverage)
        if active_only:
            conditions.append(ScholarshipProgram.active == True)

        query = select(ScholarshipProgram)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(ScholarshipProgram.coverage_percentage.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_scholarship_by_id(
        self, scholarship_id: UUID
    ) -> Optional[ScholarshipProgram]:
        """Get specific scholarship information"""
        query = select(ScholarshipProgram).where(
            ScholarshipProgram.id == scholarship_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_scholarship_program(
        self,
        name: str,
        scholarship_type: ScholarshipType,
        university_id: Optional[UUID] = None,
        **kwargs,
    ) -> ScholarshipProgram:
        """Create new scholarship program"""
        scholarship = ScholarshipProgram(
            name=name,
            scholarship_type=scholarship_type,
            university_id=university_id,
            **kwargs,
        )
        self.db.add(scholarship)
        await self.db.commit()
        await self.db.refresh(scholarship)
        return scholarship

    async def get_eligible_scholarships(
        self,
        university_id: UUID,
        exam_score: float,
        high_school_gpa: Optional[float] = None,
        family_income: Optional[int] = None,
    ) -> List[ScholarshipProgram]:
        """Get scholarships the student is eligible for"""
        conditions = [
            ScholarshipProgram.university_id == university_id,
            ScholarshipProgram.active == True,
        ]

        # Score requirement
        conditions.append(
            or_(
                ScholarshipProgram.min_exam_score == None,
                ScholarshipProgram.min_exam_score <= exam_score,
            )
        )

        # GPA requirement
        if high_school_gpa:
            conditions.append(
                or_(
                    ScholarshipProgram.min_high_school_gpa == None,
                    ScholarshipProgram.min_high_school_gpa <= high_school_gpa,
                )
            )

        # Income requirement
        if family_income:
            conditions.append(
                or_(
                    ScholarshipProgram.income_limit == None,
                    ScholarshipProgram.income_limit >= family_income,
                )
            )

        query = (
            select(ScholarshipProgram)
            .where(and_(*conditions))
            .order_by(ScholarshipProgram.coverage_percentage.desc())
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_scholarship_statistics(self, university_id: UUID) -> Dict[str, Any]:
        """Get aggregate scholarship statistics"""
        query = select(ScholarshipProgram).where(
            and_(
                ScholarshipProgram.university_id == university_id,
                ScholarshipProgram.active == True,
            )
        )

        result = await self.db.execute(query)
        scholarships = result.scalars().all()

        if not scholarships:
            return {
                "total_scholarships": 0,
                "full_scholarships": 0,
                "partial_scholarships": 0,
                "avg_coverage": 0,
                "avg_amount": 0,
                "types": [],
            }

        full_scholarships = sum(1 for s in scholarships if s.coverage_percentage == 100)
        partial_scholarships = len(scholarships) - full_scholarships

        coverages = [
            s.coverage_percentage for s in scholarships if s.coverage_percentage
        ]
        avg_coverage = sum(coverages) / len(coverages) if coverages else 0

        amounts = [s.amount_avg for s in scholarships if s.amount_avg]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0

        types = {}
        for s in scholarships:
            type_name = s.scholarship_type.value if s.scholarship_type else "unknown"
            if type_name not in types:
                types[type_name] = 0
            types[type_name] += 1

        return {
            "total_scholarships": len(scholarships),
            "full_scholarships": full_scholarships,
            "partial_scholarships": partial_scholarships,
            "avg_coverage": round(avg_coverage, 1),
            "avg_amount": int(avg_amount),
            "types": [{"type": k, "count": v} for k, v in types.items()],
        }

    # ============================================================
    # Comprehensive University Information
    # ============================================================

    async def get_comprehensive_university_info(
        self, university_id: UUID, year: int = 2024
    ) -> Dict[str, Any]:
        """Get all university information in one call"""

        # Get campus info
        campuses = await self.get_campus_info(university_id)
        facilities = await self.get_campus_facilities(university_id)

        # Get city (from first campus)
        city = campuses[0].city if campuses else None

        # Get living costs
        living_cost = None
        if city:
            living_cost = await self.get_city_living_cost(city, year)

        # Get dormitories
        dormitories = await self.get_dormitories(university_id=university_id)
        dormitory_stats = await self.get_dormitory_statistics(
            university_id=university_id
        )

        # Get scholarships
        scholarships = await self.get_scholarships(university_id=university_id)
        scholarship_stats = await self.get_scholarship_statistics(university_id)

        # Get or generate statistics
        stats = await self.get_university_statistics(university_id, year)

        return {
            "campuses": [self._campus_to_dict(c) for c in campuses],
            "facilities": facilities,
            "living_cost": self._living_cost_to_dict(living_cost)
            if living_cost
            else None,
            "dormitories": [self._dormitory_to_dict(d) for d in dormitories],
            "dormitory_statistics": dormitory_stats,
            "scholarships": [self._scholarship_to_dict(s) for s in scholarships],
            "scholarship_statistics": scholarship_stats,
            "statistics": self._statistics_to_dict(stats) if stats else None,
        }

    # ============================================================
    # University Statistics
    # ============================================================

    async def get_university_statistics(
        self, university_id: UUID, year: int = 2024
    ) -> Optional[UniversityStatistics]:
        """Get university statistics"""
        query = select(UniversityStatistics).where(
            and_(
                UniversityStatistics.university_id == university_id,
                UniversityStatistics.year == year,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def generate_university_statistics(
        self, university_id: UUID, year: int = 2024
    ) -> UniversityStatistics:
        """Generate or update university statistics"""

        # Get campus data
        campuses = await self.get_campus_info(university_id)
        total_campuses = len(campuses)
        total_area = sum(c.total_area_sqm or 0 for c in campuses)
        total_clubs = sum(c.total_student_clubs or 0 for c in campuses)
        has_health = any(c.health_center for c in campuses)
        has_career = any(c.career_center for c in campuses)

        # Get city
        city = campuses[0].city if campuses else None

        # Get living cost
        living_cost = None
        if city:
            living_cost = await self.get_city_living_cost(city, year)

        # Get dormitory stats
        dorm_stats = await self.get_dormitory_statistics(university_id=university_id)

        # Get scholarship stats
        scholarship_stats = await self.get_scholarship_statistics(university_id)

        # Calculate affordability score (1-10, higher is more affordable)
        affordability_score = 5.0  # Default
        if living_cost and living_cost.cost_of_living_index:
            # Lower cost of living index = higher affordability
            affordability_score = max(
                1.0, min(10.0, 10.0 - (living_cost.cost_of_living_index / 20))
            )

        # Check if statistics already exist
        existing_stats = await self.get_university_statistics(university_id, year)

        if existing_stats:
            # Update existing
            existing_stats.total_campuses = total_campuses
            existing_stats.total_campus_area_sqm = total_area
            existing_stats.total_student_clubs = total_clubs
            existing_stats.has_health_center = has_health
            existing_stats.has_career_center = has_career
            existing_stats.city = city
            existing_stats.avg_monthly_cost = (
                living_cost.total_avg_budget if living_cost else None
            )
            existing_stats.avg_rent = (
                living_cost.rent_studio_avg if living_cost else None
            )
            existing_stats.cost_of_living_index = (
                living_cost.cost_of_living_index if living_cost else None
            )
            existing_stats.total_dormitory_capacity = dorm_stats["total_capacity"]
            existing_stats.avg_dormitory_cost = dorm_stats["avg_price"]
            existing_stats.total_scholarships = scholarship_stats["total_scholarships"]
            existing_stats.full_scholarships = scholarship_stats["full_scholarships"]
            existing_stats.partial_scholarships = scholarship_stats[
                "partial_scholarships"
            ]
            existing_stats.avg_scholarship_amount = scholarship_stats["avg_amount"]
            existing_stats.affordability_score = affordability_score

            await self.db.commit()
            await self.db.refresh(existing_stats)
            return existing_stats
        else:
            # Create new
            stats = UniversityStatistics(
                university_id=university_id,
                year=year,
                total_campuses=total_campuses,
                total_campus_area_sqm=total_area,
                total_student_clubs=total_clubs,
                has_health_center=has_health,
                has_career_center=has_career,
                city=city,
                avg_monthly_cost=living_cost.total_avg_budget if living_cost else None,
                avg_rent=living_cost.rent_studio_avg if living_cost else None,
                cost_of_living_index=living_cost.cost_of_living_index
                if living_cost
                else None,
                total_dormitory_capacity=dorm_stats["total_capacity"],
                avg_dormitory_cost=dorm_stats["avg_price"],
                total_scholarships=scholarship_stats["total_scholarships"],
                full_scholarships=scholarship_stats["full_scholarships"],
                partial_scholarships=scholarship_stats["partial_scholarships"],
                avg_scholarship_amount=scholarship_stats["avg_amount"],
                affordability_score=affordability_score,
            )
            self.db.add(stats)
            await self.db.commit()
            await self.db.refresh(stats)
            return stats

    # ============================================================
    # Helper methods to convert models to dicts
    # ============================================================

    def _campus_to_dict(self, campus: CampusInfo) -> Dict[str, Any]:
        """Convert CampusInfo to dict"""
        return {
            "id": campus.id,
            "name": campus.campus_name,
            "type": campus.campus_type.value if campus.campus_type else None,
            "city": campus.city,
            "total_area_sqm": campus.total_area_sqm,
            "student_clubs": campus.total_student_clubs,
            "has_health_center": campus.health_center,
            "has_career_center": campus.career_center,
            "wifi_available": campus.wifi_available,
            "shuttle_service": campus.shuttle_service,
        }

    def _living_cost_to_dict(self, cost: CityLivingCost) -> Dict[str, Any]:
        """Convert CityLivingCost to dict"""
        return {
            "city": cost.city,
            "avg_monthly_budget": cost.total_avg_budget,
            "avg_rent": cost.rent_studio_avg,
            "food_budget": cost.food_budget_avg,
            "transport_monthly": cost.public_transport_monthly,
            "cost_of_living_index": cost.cost_of_living_index,
        }

    def _dormitory_to_dict(self, dorm: DormitoryInfo) -> Dict[str, Any]:
        """Convert DormitoryInfo to dict"""
        return {
            "id": dorm.id,
            "name": dorm.name,
            "type": dorm.accommodation_type.value if dorm.accommodation_type else None,
            "price_avg": dorm.price_avg,
            "total_capacity": dorm.total_capacity,
            "meals_included": dorm.meals_included,
            "distance_to_campus_km": dorm.distance_to_campus_km,
        }

    def _scholarship_to_dict(self, scholarship: ScholarshipProgram) -> Dict[str, Any]:
        """Convert ScholarshipProgram to dict"""
        return {
            "id": scholarship.id,
            "name": scholarship.name,
            "type": scholarship.scholarship_type.value
            if scholarship.scholarship_type
            else None,
            "coverage_percentage": scholarship.coverage_percentage,
            "amount_avg": scholarship.amount_avg,
            "covers_tuition": scholarship.covers_tuition,
            "covers_accommodation": scholarship.covers_accommodation,
        }

    def _statistics_to_dict(self, stats: UniversityStatistics) -> Dict[str, Any]:
        """Convert UniversityStatistics to dict"""
        return {
            "total_campuses": stats.total_campuses,
            "total_student_clubs": stats.total_student_clubs,
            "avg_monthly_cost": stats.avg_monthly_cost,
            "total_dormitory_capacity": stats.total_dormitory_capacity,
            "total_scholarships": stats.total_scholarships,
            "affordability_score": stats.affordability_score,
        }
