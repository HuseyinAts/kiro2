"""
Task 101: University Advisory Service

Service for university search, base score analysis, and recommendations
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from models.university import (
    University,
    Department,
    UniversityProgram,
    ProgramScoreHistory,
    UserUniversityPreference,
    UniversityType,
    ProgramType,
    ScoreType,
)


class UniversityAdvisoryService:
    """
    Task 101: University Advisory Service

    Handles university search, base score queries, and recommendations
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 101.1: University Database
    # ============================================================

    async def create_university(
        self, name: str, university_type: UniversityType, city: str, **kwargs
    ) -> University:
        """Create a new university"""
        university = University(
            name=name, university_type=university_type, city=city, **kwargs
        )

        self.db.add(university)
        await self.db.commit()
        await self.db.refresh(university)

        return university

    async def get_university(self, university_id: UUID) -> Optional[University]:
        """Get university by ID"""
        result = await self.db.execute(
            select(University).where(University.id == university_id)
        )
        return result.scalar_one_or_none()

    async def search_universities(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        university_type: Optional[UniversityType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[University]:
        """
        Search universities with filters

        Args:
            query: Search in name
            city: Filter by city
            university_type: Filter by type (devlet/vakif)
            limit: Max results
            offset: Pagination offset

        Returns:
            List of universities
        """
        conditions = [University.is_active == True]

        if query:
            conditions.append(University.name.ilike(f"%{query}%"))

        if city:
            conditions.append(University.city == city)

        if university_type:
            conditions.append(University.university_type == university_type)

        stmt = select(University).where(and_(*conditions)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_all_cities(self) -> List[str]:
        """Get all cities with universities"""
        result = await self.db.execute(
            select(University.city)
            .distinct()
            .where(University.is_active == True)
            .order_by(University.city)
        )
        return [row[0] for row in result.fetchall()]

    # ============================================================
    # Task 101.2: Department Database
    # ============================================================

    async def create_department(
        self, name: str, degree_type: str, **kwargs
    ) -> Department:
        """Create a new department"""
        department = Department(name=name, degree_type=degree_type, **kwargs)

        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)

        return department

    async def get_department(self, department_id: UUID) -> Optional[Department]:
        """Get department by ID"""
        result = await self.db.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def search_departments(
        self,
        query: Optional[str] = None,
        degree_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Department]:
        """
        Search departments with filters

        Args:
            query: Search in name
            degree_type: Filter by degree type
            limit: Max results
            offset: Pagination offset

        Returns:
            List of departments
        """
        conditions = [Department.is_active == True]

        if query:
            conditions.append(Department.name.ilike(f"%{query}%"))

        if degree_type:
            conditions.append(Department.degree_type == degree_type)

        stmt = select(Department).where(and_(*conditions)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ============================================================
    # Task 101.3: Base Score Data
    # ============================================================

    async def create_program(
        self,
        university_id: UUID,
        department_id: UUID,
        program_name: str,
        year: int,
        score_type: ScoreType,
        **kwargs,
    ) -> UniversityProgram:
        """Create a new university program"""
        program = UniversityProgram(
            university_id=university_id,
            department_id=department_id,
            program_name=program_name,
            year=year,
            score_type=score_type,
            **kwargs,
        )

        self.db.add(program)
        await self.db.commit()
        await self.db.refresh(program)

        return program

    async def get_program(self, program_id: UUID) -> Optional[UniversityProgram]:
        """Get program by ID with relationships"""
        result = await self.db.execute(
            select(UniversityProgram).where(UniversityProgram.id == program_id)
        )
        return result.scalar_one_or_none()

    async def search_programs(
        self,
        year: int = 2024,
        score_type: Optional[ScoreType] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        city: Optional[str] = None,
        university_type: Optional[UniversityType] = None,
        department_name: Optional[str] = None,
        program_type: Optional[ProgramType] = None,
        has_scholarship: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "base_score",
        order_desc: bool = True,
    ) -> List[UniversityProgram]:
        """
        Search programs with comprehensive filters

        Args:
            year: Academic year
            score_type: Score type (SAY, EA, SOZ, DIL)
            min_score: Minimum base score
            max_score: Maximum base score
            city: University city
            university_type: University type
            department_name: Department name filter
            program_type: Program type
            has_scholarship: Scholarship filter
            limit: Max results
            offset: Pagination offset
            order_by: Sort field
            order_desc: Sort descending

        Returns:
            List of programs with university and department info
        """
        # Build query with joins
        stmt = (
            select(UniversityProgram)
            .join(University, UniversityProgram.university_id == University.id)
            .join(Department, UniversityProgram.department_id == Department.id)
        )

        conditions = [
            UniversityProgram.is_active == True,
            UniversityProgram.year == year,
        ]

        if score_type:
            conditions.append(UniversityProgram.score_type == score_type)

        if min_score is not None:
            conditions.append(UniversityProgram.base_score >= min_score)

        if max_score is not None:
            conditions.append(UniversityProgram.base_score <= max_score)

        if city:
            conditions.append(University.city == city)

        if university_type:
            conditions.append(University.university_type == university_type)

        if department_name:
            conditions.append(Department.name.ilike(f"%{department_name}%"))

        if program_type:
            conditions.append(UniversityProgram.program_type == program_type)

        if has_scholarship is not None:
            conditions.append(UniversityProgram.scholarship == has_scholarship)

        stmt = stmt.where(and_(*conditions))

        # Order by
        order_column = getattr(
            UniversityProgram, order_by, UniversityProgram.base_score
        )
        if order_desc:
            stmt = stmt.order_by(desc(order_column))
        else:
            stmt = stmt.order_by(asc(order_column))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_base_score_statistics(
        self, year: int, score_type: ScoreType
    ) -> Dict[str, Any]:
        """
        Get base score statistics for a year and score type

        Returns min, max, avg, median, percentiles
        """
        result = await self.db.execute(
            select(
                func.min(UniversityProgram.base_score),
                func.max(UniversityProgram.base_score),
                func.avg(UniversityProgram.base_score),
                func.count(UniversityProgram.id),
            ).where(
                and_(
                    UniversityProgram.year == year,
                    UniversityProgram.score_type == score_type,
                    UniversityProgram.base_score.isnot(None),
                )
            )
        )

        min_score, max_score, avg_score, count = result.first()

        return {
            "year": year,
            "score_type": score_type.value,
            "min_score": float(min_score) if min_score else None,
            "max_score": float(max_score) if max_score else None,
            "avg_score": float(avg_score) if avg_score else None,
            "total_programs": count,
        }

    async def get_historical_scores(
        self, program_id: UUID, years: int = 5
    ) -> List[ProgramScoreHistory]:
        """
        Get historical base scores for trend analysis

        Args:
            program_id: Program ID
            years: Number of years to fetch

        Returns:
            List of historical scores ordered by year
        """
        result = await self.db.execute(
            select(ProgramScoreHistory)
            .where(ProgramScoreHistory.program_id == program_id)
            .order_by(desc(ProgramScoreHistory.year))
            .limit(years)
        )
        return result.scalars().all()

    async def predict_base_score(
        self, program_id: UUID, target_year: int
    ) -> Optional[float]:
        """
        Predict base score for target year using linear regression on historical data

        Args:
            program_id: Program ID
            target_year: Year to predict

        Returns:
            Predicted base score or None if insufficient data
        """
        # Get historical data
        history = await self.get_historical_scores(program_id, years=5)

        if len(history) < 2:
            return None

        # Simple linear regression
        years = [h.year for h in history]
        scores = [h.base_score for h in history if h.base_score]

        if len(scores) < 2:
            return None

        # Calculate slope and intercept
        n = len(years)
        sum_x = sum(years)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(years, scores))
        sum_x2 = sum(x * x for x in years)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        # Predict
        predicted_score = slope * target_year + intercept

        return round(predicted_score, 2)

    # ============================================================
    # Task 101.4: Quota Information
    # ============================================================

    async def get_quota_statistics(
        self, year: int, score_type: Optional[ScoreType] = None
    ) -> Dict[str, Any]:
        """
        Get quota statistics

        Returns total quotas, filled quotas, acceptance rates
        """
        conditions = [
            UniversityProgram.year == year,
            UniversityProgram.total_quota.isnot(None),
        ]

        if score_type:
            conditions.append(UniversityProgram.score_type == score_type)

        result = await self.db.execute(
            select(
                func.sum(UniversityProgram.total_quota),
                func.sum(UniversityProgram.filled_quota),
                func.avg(UniversityProgram.acceptance_rate),
                func.count(UniversityProgram.id),
            ).where(and_(*conditions))
        )

        total_quota, filled_quota, avg_acceptance, count = result.first()

        return {
            "year": year,
            "score_type": score_type.value if score_type else "all",
            "total_quota": int(total_quota) if total_quota else 0,
            "filled_quota": int(filled_quota) if filled_quota else 0,
            "avg_acceptance_rate": float(avg_acceptance) if avg_acceptance else 0,
            "total_programs": count,
            "utilization_rate": (filled_quota / total_quota * 100)
            if total_quota and filled_quota
            else 0,
        }

    async def get_competitive_programs(
        self, year: int, score_type: ScoreType, limit: int = 50
    ) -> List[UniversityProgram]:
        """
        Get most competitive programs (highest acceptance rate / lowest quota)

        Args:
            year: Academic year
            score_type: Score type
            limit: Max results

        Returns:
            List of most competitive programs
        """
        result = await self.db.execute(
            select(UniversityProgram)
            .where(
                and_(
                    UniversityProgram.year == year,
                    UniversityProgram.score_type == score_type,
                    UniversityProgram.competition_ratio.isnot(None),
                )
            )
            .order_by(desc(UniversityProgram.competition_ratio))
            .limit(limit)
        )
        return result.scalars().all()

    # ============================================================
    # Recommendation Engine
    # ============================================================

    async def get_personalized_recommendations(
        self,
        user_id: UUID,
        student_score: float,
        score_type: ScoreType,
        year: int = 2024,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized program recommendations

        Args:
            user_id: User ID
            student_score: Student's YKS score
            score_type: Score type
            year: Academic year
            limit: Max recommendations

        Returns:
            List of recommended programs with match scores
        """
        # Get user preferences
        pref_result = await self.db.execute(
            select(UserUniversityPreference).where(
                UserUniversityPreference.user_id == user_id
            )
        )
        preferences = pref_result.scalar_one_or_none()

        # Build base query
        conditions = [
            UniversityProgram.year == year,
            UniversityProgram.score_type == score_type,
            UniversityProgram.is_active == True,
            UniversityProgram.base_score.isnot(None),
        ]

        # Score range: ±30 points from student score
        conditions.append(UniversityProgram.base_score >= student_score - 30)
        conditions.append(UniversityProgram.base_score <= student_score + 30)

        # Apply user preferences
        if preferences:
            if preferences.preferred_cities:
                stmt = select(UniversityProgram).join(University)
                conditions.append(University.city.in_(preferences.preferred_cities))

            if preferences.preferred_university_types:
                stmt = select(UniversityProgram).join(University)
                conditions.append(
                    University.university_type.in_(
                        preferences.preferred_university_types
                    )
                )

            if preferences.max_tuition_fee:
                conditions.append(
                    or_(
                        UniversityProgram.tuition_fee.is_(None),
                        UniversityProgram.tuition_fee <= preferences.max_tuition_fee,
                    )
                )

            if preferences.needs_scholarship:
                conditions.append(UniversityProgram.scholarship == True)

        # Execute query
        stmt = (
            select(UniversityProgram).where(and_(*conditions)).limit(limit * 2)
        )  # Get more for filtering
        result = await self.db.execute(stmt)
        programs = result.scalars().all()

        # Calculate match scores
        recommendations = []
        for program in programs:
            match_score = self._calculate_match_score(
                program, student_score, preferences
            )
            recommendations.append(
                {
                    "program": program,
                    "match_score": match_score,
                    "score_diff": abs(program.base_score - student_score),
                    "placement_probability": self._calculate_placement_probability(
                        program, student_score
                    ),
                }
            )

        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)

        return recommendations[:limit]

    def _calculate_match_score(
        self,
        program: UniversityProgram,
        student_score: float,
        preferences: Optional[UserUniversityPreference],
    ) -> float:
        """
        Calculate match score (0-100) for a program

        Considers:
        - Score proximity
        - User preferences
        - Acceptance rate
        - Scholarship availability
        """
        score = 50.0  # Base score

        # Score proximity (max +25 points)
        score_diff = abs(program.base_score - student_score)
        if score_diff <= 5:
            score += 25
        elif score_diff <= 15:
            score += 15
        elif score_diff <= 30:
            score += 5

        # User preferences (max +25 points)
        if preferences:
            pref_score = 0

            # City match
            if preferences.preferred_cities and program.university:
                if program.university.city in preferences.preferred_cities:
                    pref_score += 8

            # University type match
            if preferences.preferred_university_types and program.university:
                if (
                    program.university.university_type.value
                    in preferences.preferred_university_types
                ):
                    pref_score += 8

            # Scholarship match
            if preferences.needs_scholarship and program.scholarship:
                pref_score += 9

            score += pref_score

        return min(score, 100)

    def _calculate_placement_probability(
        self, program: UniversityProgram, student_score: float
    ) -> float:
        """
        Calculate placement probability (0-100%)

        Based on score difference and acceptance rate
        """
        if not program.base_score:
            return 50.0

        score_diff = student_score - program.base_score

        # Base probability based on score difference
        if score_diff >= 20:
            probability = 95.0
        elif score_diff >= 10:
            probability = 85.0
        elif score_diff >= 5:
            probability = 75.0
        elif score_diff >= 0:
            probability = 60.0
        elif score_diff >= -5:
            probability = 40.0
        elif score_diff >= -10:
            probability = 20.0
        else:
            probability = 5.0

        # Adjust by acceptance rate
        if program.acceptance_rate:
            probability *= program.acceptance_rate / 100

        return min(probability, 100)

    # ============================================================
    # User Preferences
    # ============================================================

    async def save_user_preferences(
        self, user_id: UUID, **preferences
    ) -> UserUniversityPreference:
        """Save or update user preferences"""
        # Check if exists
        result = await self.db.execute(
            select(UserUniversityPreference).where(
                UserUniversityPreference.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update
            for key, value in preferences.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create
            new_pref = UserUniversityPreference(user_id=user_id, **preferences)
            self.db.add(new_pref)
            await self.db.commit()
            await self.db.refresh(new_pref)
            return new_pref

    async def get_user_preferences(
        self, user_id: UUID
    ) -> Optional[UserUniversityPreference]:
        """Get user preferences"""
        result = await self.db.execute(
            select(UserUniversityPreference).where(
                UserUniversityPreference.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
