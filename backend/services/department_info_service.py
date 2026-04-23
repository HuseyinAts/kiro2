"""
Task 103: Department Information Service

Service for curriculum, career opportunities, salary expectations, and sector analysis
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.department_info import (
    CareerOpportunity,
    DepartmentCurriculum,
    DepartmentStatistics,
    ExperienceLevel,
    IndustryType,
    SalaryExpectation,
    SectorAnalysis,
)


class DepartmentInfoService:
    """
    Task 103: Department Information Service

    Handles curriculum, career, salary, and sector data
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 103.1: Curriculum Information
    # ============================================================

    async def get_department_curriculum(
        self, department_id: UUID
    ) -> DepartmentCurriculum | None:
        """Get curriculum information for a department"""
        result = await self.db.execute(
            select(DepartmentCurriculum).where(
                DepartmentCurriculum.department_id == department_id
            )
        )
        return result.scalar_one_or_none()

    async def create_curriculum(
        self, department_id: UUID, **curriculum_data
    ) -> DepartmentCurriculum:
        """Create curriculum information"""
        curriculum = DepartmentCurriculum(
            department_id=department_id, **curriculum_data
        )

        self.db.add(curriculum)
        await self.db.commit()
        await self.db.refresh(curriculum)

        return curriculum

    async def get_specialization_options(self, department_id: UUID) -> list[str]:
        """Get specialization tracks for a department"""
        curriculum = await self.get_department_curriculum(department_id)

        if not curriculum:
            return []

        return curriculum.specialization_tracks or []

    # ============================================================
    # Task 103.2: Career Opportunities
    # ============================================================

    async def get_career_opportunities(
        self,
        department_id: UUID,
        industry_type: IndustryType | None = None,
        demand_level: str | None = None,
    ) -> list[CareerOpportunity]:
        """
        Get career opportunities for a department

        Args:
            department_id: Department ID
            industry_type: Filter by industry
            demand_level: Filter by demand ("high", "medium", "low")

        Returns:
            List of career opportunities
        """
        conditions = [CareerOpportunity.department_id == department_id]

        if industry_type:
            conditions.append(CareerOpportunity.industry_type == industry_type)

        if demand_level:
            conditions.append(CareerOpportunity.demand_level == demand_level)

        result = await self.db.execute(
            select(CareerOpportunity).where(and_(*conditions))
        )
        return result.scalars().all()

    async def create_career_opportunity(
        self, department_id: UUID, job_title: str, **opportunity_data
    ) -> CareerOpportunity:
        """Create a career opportunity"""
        opportunity = CareerOpportunity(
            department_id=department_id, job_title=job_title, **opportunity_data
        )

        self.db.add(opportunity)
        await self.db.commit()
        await self.db.refresh(opportunity)

        return opportunity

    async def get_employment_statistics(self, department_id: UUID) -> dict[str, Any]:
        """
        Get employment statistics for a department

        Returns aggregate employment data
        """
        opportunities = await self.get_career_opportunities(department_id)

        if not opportunities:
            return {
                "total_career_paths": 0,
                "average_employment_rate": 0.0,
                "average_hiring_time_days": 0,
                "high_demand_careers": 0,
            }

        employment_rates = [
            o.employment_rate for o in opportunities if o.employment_rate
        ]
        hiring_times = [
            o.average_hiring_time_days
            for o in opportunities
            if o.average_hiring_time_days
        ]

        return {
            "total_career_paths": len(opportunities),
            "average_employment_rate": sum(employment_rates) / len(employment_rates)
            if employment_rates
            else 0.0,
            "average_hiring_time_days": int(sum(hiring_times) / len(hiring_times))
            if hiring_times
            else 0,
            "high_demand_careers": sum(
                1 for o in opportunities if o.demand_level == "high"
            ),
            "top_industries": self._get_top_industries(opportunities),
            "career_growth_high": sum(
                1 for o in opportunities if o.career_growth_potential == "high"
            ),
        }

    def _get_top_industries(
        self, opportunities: list[CareerOpportunity]
    ) -> list[dict[str, Any]]:
        """Get top industries from career opportunities"""
        industry_counts = {}
        for opp in opportunities:
            if opp.industry_type:
                industry = opp.industry_type.value
                industry_counts[industry] = industry_counts.get(industry, 0) + 1

        return [
            {"industry": industry, "count": count}
            for industry, count in sorted(
                industry_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

    # ============================================================
    # Task 103.3: Salary Expectations
    # ============================================================

    async def get_salary_expectations(
        self,
        department_id: UUID,
        experience_level: ExperienceLevel | None = None,
        city: str | None = None,
        year: int = 2024,
    ) -> list[SalaryExpectation]:
        """
        Get salary expectations for a department

        Args:
            department_id: Department ID
            experience_level: Filter by experience level
            city: Filter by city
            year: Year for data

        Returns:
            List of salary expectations
        """
        conditions = [
            SalaryExpectation.department_id == department_id,
            SalaryExpectation.year == year,
        ]

        if experience_level:
            conditions.append(SalaryExpectation.experience_level == experience_level)

        if city:
            conditions.append(SalaryExpectation.city == city)

        result = await self.db.execute(
            select(SalaryExpectation).where(and_(*conditions))
        )
        return result.scalars().all()

    async def get_salary_progression(
        self, department_id: UUID, city: str | None = None, year: int = 2024
    ) -> dict[str, Any]:
        """
        Get salary progression by experience level

        Returns salary ranges for each experience level
        """
        salaries = await self.get_salary_expectations(
            department_id=department_id, city=city, year=year
        )

        progression = {}
        for exp_level in ExperienceLevel:
            level_salaries = [s for s in salaries if s.experience_level == exp_level]

            if level_salaries:
                avg_salary = sum(s.average_salary for s in level_salaries) / len(
                    level_salaries
                )
                min_salary = min(s.min_salary for s in level_salaries)
                max_salary = max(s.max_salary for s in level_salaries)

                progression[exp_level.value] = {
                    "average": int(avg_salary),
                    "min": min_salary,
                    "max": max_salary,
                    "count": len(level_salaries),
                }

        return progression

    async def get_regional_salary_comparison(
        self,
        department_id: UUID,
        experience_level: ExperienceLevel = ExperienceLevel.ENTRY,
        year: int = 2024,
    ) -> list[dict[str, Any]]:
        """
        Compare salaries across different regions

        Returns salary data for each city
        """
        salaries = await self.get_salary_expectations(
            department_id=department_id, experience_level=experience_level, year=year
        )

        # Group by city
        city_data = {}
        for salary in salaries:
            city = salary.city or "National"
            if city not in city_data:
                city_data[city] = []
            city_data[city].append(salary)

        # Calculate averages
        comparison = []
        for city, city_salaries in city_data.items():
            avg_salary = sum(s.average_salary for s in city_salaries) / len(
                city_salaries
            )
            comparison.append(
                {
                    "city": city,
                    "average_salary": int(avg_salary),
                    "min_salary": min(s.min_salary for s in city_salaries),
                    "max_salary": max(s.max_salary for s in city_salaries),
                    "data_points": len(city_salaries),
                }
            )

        # Sort by average salary descending
        comparison.sort(key=lambda x: x["average_salary"], reverse=True)

        return comparison

    # ============================================================
    # Task 103.4: Sector Analysis
    # ============================================================

    async def get_sector_analysis(
        self, industry_type: IndustryType, year: int = 2024
    ) -> SectorAnalysis | None:
        """Get sector analysis for an industry"""
        result = await self.db.execute(
            select(SectorAnalysis).where(
                and_(
                    SectorAnalysis.industry_type == industry_type,
                    SectorAnalysis.year == year,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_related_sectors(
        self, department_id: UUID, year: int = 2024
    ) -> list[SectorAnalysis]:
        """
        Get sector analyses related to a department

        Returns sectors where this department's graduates work
        """
        # Get career opportunities to find related industries
        opportunities = await self.get_career_opportunities(department_id)

        industry_types = list(
            set(o.industry_type for o in opportunities if o.industry_type)
        )

        if not industry_types:
            return []

        result = await self.db.execute(
            select(SectorAnalysis).where(
                and_(
                    SectorAnalysis.industry_type.in_(industry_types),
                    SectorAnalysis.year == year,
                )
            )
        )
        return result.scalars().all()

    async def get_job_market_trends(
        self, department_id: UUID, year: int = 2024
    ) -> dict[str, Any]:
        """
        Get comprehensive job market trends for a department

        Combines sector analyses and employment data
        """
        sectors = await self.get_related_sectors(department_id, year)
        employment_stats = await self.get_employment_statistics(department_id)

        if not sectors:
            return {"overall_growth": "unknown", "job_demand": "unknown", "sectors": []}

        # Aggregate sector data
        total_growth = (
            sum(s.annual_growth_rate for s in sectors if s.annual_growth_rate)
            / len(sectors)
            if sectors
            else 0
        )
        total_jobs = (
            sum(s.total_job_openings for s in sectors if s.total_job_openings) or 0
        )

        # In-demand skills across all sectors
        all_skills = []
        for sector in sectors:
            all_skills.extend(sector.in_demand_skills or [])

        # Count skill frequency
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "overall_growth": self._categorize_growth(total_growth),
            "annual_growth_rate": round(total_growth, 2),
            "total_job_openings": total_jobs,
            "sectors_analyzed": len(sectors),
            "top_skills": [skill for skill, count in top_skills],
            "employment_rate": employment_stats.get("average_employment_rate", 0),
            "sectors": [
                {
                    "name": s.sector_name,
                    "growth_rate": s.annual_growth_rate,
                    "job_openings": s.total_job_openings,
                    "future_demand": s.future_demand_prediction,
                }
                for s in sectors
            ],
        }

    def _categorize_growth(self, growth_rate: float) -> str:
        """Categorize growth rate"""
        if growth_rate >= 10:
            return "high"
        if growth_rate >= 5:
            return "medium"
        if growth_rate >= 0:
            return "low"
        return "declining"

    # ============================================================
    # Department Statistics (Aggregate)
    # ============================================================

    async def get_department_statistics(
        self, department_id: UUID, year: int = 2024
    ) -> DepartmentStatistics | None:
        """Get aggregate statistics for a department"""
        result = await self.db.execute(
            select(DepartmentStatistics).where(
                and_(
                    DepartmentStatistics.department_id == department_id,
                    DepartmentStatistics.year == year,
                )
            )
        )
        return result.scalar_one_or_none()

    async def generate_department_statistics(
        self, department_id: UUID, year: int = 2024
    ) -> DepartmentStatistics:
        """
        Generate/update aggregate statistics for a department

        Combines data from careers, salaries, and sectors
        """
        # Get employment data
        employment_stats = await self.get_employment_statistics(department_id)

        # Get salary progression
        salary_progression = await self.get_salary_progression(department_id, year=year)

        # Get entry level salary data
        entry_data = salary_progression.get(ExperienceLevel.ENTRY.value, {})
        mid_data = salary_progression.get(ExperienceLevel.MID.value, {})
        senior_data = salary_progression.get(ExperienceLevel.SENIOR.value, {})

        # Calculate salary growth rate
        salary_growth_rate = 0.0
        if entry_data.get("average") and senior_data.get("average"):
            # Approximate annual growth over 10 years (entry to senior)
            entry_avg = entry_data["average"]
            senior_avg = senior_data["average"]
            years_diff = 10  # Entry to senior
            salary_growth_rate = (
                (senior_avg / entry_avg) ** (1 / years_diff) - 1
            ) * 100

        # Check if exists
        existing = await self.get_department_statistics(department_id, year)

        if existing:
            # Update
            existing.overall_employment_rate = employment_stats.get(
                "average_employment_rate"
            )
            existing.average_hiring_time_days = employment_stats.get(
                "average_hiring_time_days"
            )
            existing.entry_level_avg_salary = entry_data.get("average")
            existing.entry_level_min_salary = entry_data.get("min")
            existing.entry_level_max_salary = entry_data.get("max")
            existing.mid_career_avg_salary = mid_data.get("average")
            existing.senior_avg_salary = senior_data.get("average")
            existing.salary_growth_rate = round(salary_growth_rate, 2)
            existing.top_industries = employment_stats.get("top_industries", [])
            existing.last_updated = datetime.now()

            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        # Create
        stats = DepartmentStatistics(
            department_id=department_id,
            year=year,
            overall_employment_rate=employment_stats.get("average_employment_rate"),
            average_hiring_time_days=employment_stats.get(
                "average_hiring_time_days"
            ),
            entry_level_avg_salary=entry_data.get("average"),
            entry_level_min_salary=entry_data.get("min"),
            entry_level_max_salary=entry_data.get("max"),
            mid_career_avg_salary=mid_data.get("average"),
            senior_avg_salary=senior_data.get("average"),
            salary_growth_rate=round(salary_growth_rate, 2),
            top_industries=employment_stats.get("top_industries", []),
        )

        self.db.add(stats)
        await self.db.commit()
        await self.db.refresh(stats)

        return stats

    # ============================================================
    # Comprehensive Department Info
    # ============================================================

    async def get_comprehensive_department_info(
        self, department_id: UUID, year: int = 2024
    ) -> dict[str, Any]:
        """
        Get all department information in one call

        Returns curriculum, careers, salaries, sectors, and statistics
        """
        # Get all data in parallel would be ideal, but for simplicity:
        curriculum = await self.get_department_curriculum(department_id)
        careers = await self.get_career_opportunities(department_id)
        salary_progression = await self.get_salary_progression(department_id, year=year)
        regional_salaries = await self.get_regional_salary_comparison(
            department_id, year=year
        )
        sectors = await self.get_related_sectors(department_id, year)
        job_trends = await self.get_job_market_trends(department_id, year)
        statistics = await self.get_department_statistics(department_id, year)

        return {
            "curriculum": {
                "total_credits": curriculum.total_credits if curriculum else None,
                "duration_years": curriculum.duration_years if curriculum else 4,
                "specializations": curriculum.specialization_tracks
                if curriculum
                else [],
                "internship_required": curriculum.internship_required
                if curriculum
                else False,
                "skills_gained": curriculum.skills_gained if curriculum else [],
            },
            "career_opportunities": [
                {
                    "job_title": c.job_title,
                    "industry": c.industry_type.value if c.industry_type else None,
                    "demand_level": c.demand_level,
                    "employment_rate": c.employment_rate,
                    "career_growth": c.career_growth_potential,
                }
                for c in careers
            ],
            "salary_progression": salary_progression,
            "regional_salaries": regional_salaries,
            "sectors": [
                {
                    "name": s.sector_name,
                    "growth_rate": s.annual_growth_rate,
                    "future_demand": s.future_demand_prediction,
                    "automation_risk": s.automation_risk,
                }
                for s in sectors
            ],
            "job_market_trends": job_trends,
            "statistics": {
                "employment_rate": statistics.overall_employment_rate
                if statistics
                else None,
                "avg_hiring_time": statistics.average_hiring_time_days
                if statistics
                else None,
                "entry_salary": statistics.entry_level_avg_salary
                if statistics
                else None,
                "salary_growth_rate": statistics.salary_growth_rate
                if statistics
                else None,
            }
            if statistics
            else {},
        }
