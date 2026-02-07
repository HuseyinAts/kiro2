"""
Task 102: Preference Simulation Service

Service for university preference simulation, score calculation, placement prediction
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.university import UniversityProgram, ScoreType
from services.university_advisory_service import UniversityAdvisoryService


class PreferenceSimulationService:
    """
    Task 102: Preference Simulation Service

    Handles score calculation, placement prediction, recommendations, and rank estimation
    """

    # YKS score coefficients (2024 katsayılar)
    COEFFICIENTS = {
        ScoreType.SAY: {
            "TYT": {"turkish": 3.0, "math": 3.0, "science": 3.0, "social": 3.0},
            "AYT": {"math": 5.0, "physics": 5.0, "chemistry": 5.0, "biology": 5.0},
        },
        ScoreType.EA: {
            "TYT": {"turkish": 3.0, "math": 3.0, "science": 3.0, "social": 3.0},
            "AYT": {"math": 5.0, "literature": 5.0, "history": 5.0, "geography": 5.0},
        },
        ScoreType.SOZ: {
            "TYT": {"turkish": 3.0, "math": 3.0, "science": 3.0, "social": 3.0},
            "AYT": {
                "literature": 5.0,
                "history": 5.0,
                "geography": 5.0,
                "philosophy": 5.0,
            },
        },
        ScoreType.DIL: {
            "TYT": {"turkish": 3.0, "math": 3.0, "science": 3.0, "social": 3.0},
            "AYT": {"foreign_language": 5.0},
        },
    }

    # Risk levels for placement prediction
    RISK_LEVELS = {
        "very_low": (0, 20),  # Very risky
        "low": (20, 40),  # Risky
        "medium": (40, 60),  # Medium risk
        "high": (60, 80),  # Good chance
        "very_high": (80, 100),  # Very good chance
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.advisory_service = UniversityAdvisoryService(db)

    # ============================================================
    # Task 102.1: Score Calculation
    # ============================================================

    def calculate_yks_score(
        self,
        score_type: ScoreType,
        tyt_scores: Dict[str, float],
        ayt_scores: Dict[str, float],
        bonus_points: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate YKS score with coefficients and bonus points

        Args:
            score_type: Score type (SAY, EA, SOZ, DIL)
            tyt_scores: TYT net scores {turkish: 35.5, math: 28.0, ...}
            ayt_scores: AYT net scores {math: 30.0, physics: 25.0, ...}
            bonus_points: Bonus points (ek puan)

        Returns:
            Dict with total score, TYT score, AYT score, breakdown
        """
        coeffs = self.COEFFICIENTS.get(score_type)
        if not coeffs:
            raise ValueError(f"Invalid score type: {score_type}")

        # Calculate TYT score
        tyt_total = 0.0
        tyt_breakdown = {}
        for subject, coeff in coeffs["TYT"].items():
            net = tyt_scores.get(subject, 0.0)
            score = net * coeff
            tyt_total += score
            tyt_breakdown[subject] = {"net": net, "coefficient": coeff, "score": score}

        # Calculate AYT score
        ayt_total = 0.0
        ayt_breakdown = {}
        for subject, coeff in coeffs["AYT"].items():
            net = ayt_scores.get(subject, 0.0)
            score = net * coeff
            ayt_total += score
            ayt_breakdown[subject] = {"net": net, "coefficient": coeff, "score": score}

        # Total score = TYT*0.4 + AYT*0.6 + bonus
        base_score = (tyt_total * 0.4) + (ayt_total * 0.6)
        total_score = base_score + bonus_points

        return {
            "score_type": score_type.value,
            "total_score": round(total_score, 2),
            "base_score": round(base_score, 2),
            "tyt_score": round(tyt_total, 2),
            "ayt_score": round(ayt_total, 2),
            "bonus_points": bonus_points,
            "tyt_breakdown": tyt_breakdown,
            "ayt_breakdown": ayt_breakdown,
        }

    def apply_bonus_points(
        self,
        base_score: float,
        diploma_grade: Optional[float] = None,
        language_certificate: Optional[str] = None,
        special_talent: bool = False,
    ) -> float:
        """
        Apply bonus points based on various criteria

        Args:
            base_score: Base YKS score
            diploma_grade: High school diploma grade (0-100)
            language_certificate: Language certificate (TOEFL, IELTS, etc.)
            special_talent: Special talent status

        Returns:
            Total bonus points
        """
        bonus = 0.0

        # Diploma bonus (max 60 points)
        if diploma_grade:
            # 100 üzerinden diploma notu = 0.6 * diploma_grade
            bonus += min(diploma_grade * 0.6, 60.0)

        # Language certificate bonus
        if language_certificate:
            cert_bonus = {"TOEFL": 20.0, "IELTS": 20.0, "YDS": 15.0, "Cambridge": 20.0}
            bonus += cert_bonus.get(language_certificate, 0.0)

        # Special talent bonus
        if special_talent:
            bonus += 30.0

        return round(bonus, 2)

    # ============================================================
    # Task 102.2: Placement Prediction
    # ============================================================

    async def predict_placement(
        self, student_score: float, program_id: UUID, year: int = 2024
    ) -> Dict[str, Any]:
        """
        Predict placement probability for a program

        Args:
            student_score: Student's YKS score
            program_id: Program ID
            year: Academic year

        Returns:
            Placement prediction with probability and risk assessment
        """
        # Get program
        program = await self.advisory_service.get_program(program_id)
        if not program:
            raise ValueError(f"Program {program_id} not found")

        # Get historical scores for better prediction
        history = await self.advisory_service.get_historical_scores(program_id, years=3)

        # Calculate placement probability
        probability = self._calculate_placement_probability(
            student_score, program, history
        )

        # Risk assessment
        risk_level = self._assess_risk(probability)

        # Score analysis
        score_diff = student_score - (program.base_score or 0)

        return {
            "program_id": str(program_id),
            "program_name": program.program_name,
            "university_name": program.university.name if program.university else "N/A",
            "student_score": student_score,
            "base_score": program.base_score,
            "top_score": program.top_score,
            "median_score": program.median_score,
            "score_difference": round(score_diff, 2),
            "placement_probability": round(probability, 2),
            "risk_level": risk_level,
            "risk_description": self._get_risk_description(risk_level),
            "recommendation": self._get_placement_recommendation(
                probability, score_diff
            ),
            "historical_trend": self._analyze_historical_trend(history),
        }

    def _calculate_placement_probability(
        self, student_score: float, program: UniversityProgram, history: List[Any]
    ) -> float:
        """
        Calculate placement probability using multiple factors

        Factors:
        1. Score difference from base score (50%)
        2. Acceptance rate (30%)
        3. Historical trend (20%)
        """
        if not program.base_score:
            return 50.0

        # Factor 1: Score difference (50% weight)
        score_diff = student_score - program.base_score

        if score_diff >= 30:
            score_factor = 100.0
        elif score_diff >= 20:
            score_factor = 95.0
        elif score_diff >= 10:
            score_factor = 85.0
        elif score_diff >= 5:
            score_factor = 75.0
        elif score_diff >= 0:
            score_factor = 60.0
        elif score_diff >= -5:
            score_factor = 40.0
        elif score_diff >= -10:
            score_factor = 25.0
        elif score_diff >= -15:
            score_factor = 15.0
        else:
            score_factor = 5.0

        # Factor 2: Acceptance rate (30% weight)
        acceptance_factor = program.acceptance_rate or 50.0

        # Factor 3: Historical trend (20% weight)
        trend_factor = 50.0  # Default
        if history and len(history) >= 2:
            # Check if base score is increasing or decreasing
            recent_scores = [h.base_score for h in history[:2] if h.base_score]
            if len(recent_scores) >= 2:
                trend = recent_scores[0] - recent_scores[1]  # Most recent - previous
                if trend > 0:  # Increasing (harder)
                    trend_factor = 45.0
                elif trend < 0:  # Decreasing (easier)
                    trend_factor = 55.0

        # Weighted average
        probability = score_factor * 0.5 + acceptance_factor * 0.3 + trend_factor * 0.2

        return min(probability, 100.0)

    def _assess_risk(self, probability: float) -> str:
        """Assess risk level based on probability"""
        for level, (min_p, max_p) in self.RISK_LEVELS.items():
            if min_p <= probability < max_p:
                return level
        return "very_high"

    def _get_risk_description(self, risk_level: str) -> str:
        """Get risk description in Turkish"""
        descriptions = {
            "very_low": "Çok riskli - Yerleşme şansı düşük",
            "low": "Riskli - Dikkatli olun",
            "medium": "Orta risk - Şansınızı deneyebilirsiniz",
            "high": "İyi şans - Yerleşme olasılığı yüksek",
            "very_high": "Çok iyi şans - Yerleşme neredeyse kesin",
        }
        return descriptions.get(risk_level, "Bilinmiyor")

    def _get_placement_recommendation(
        self, probability: float, score_diff: float
    ) -> str:
        """Get placement recommendation"""
        if probability >= 80:
            return (
                "Bu program için çok uygunsunuz! Kesinlikle tercih listenize ekleyin."
            )
        elif probability >= 60:
            return "İyi bir seçim. Tercih listenizin üst sıralarında değerlendirebilirsiniz."
        elif probability >= 40:
            return "Orta derece risk var. Tercih listenizin orta sıralarında değerlendirin."
        elif probability >= 20:
            return "Riskli bir tercih. Yedek olarak listenizin alt sıralarına ekleyebilirsiniz."
        else:
            return "Çok riskli. Bu programı tercih etmemenizi öneriyoruz."

    def _analyze_historical_trend(self, history: List[Any]) -> str:
        """Analyze historical trend"""
        if not history or len(history) < 2:
            return "Yetersiz veri"

        scores = [h.base_score for h in history if h.base_score]
        if len(scores) < 2:
            return "Yetersiz veri"

        # Calculate average change
        changes = [scores[i] - scores[i + 1] for i in range(len(scores) - 1)]
        avg_change = sum(changes) / len(changes)

        if avg_change > 5:
            return "Taban puan hızla yükseliyor"
        elif avg_change > 2:
            return "Taban puan artış eğiliminde"
        elif avg_change > -2:
            return "Taban puan stabil"
        elif avg_change > -5:
            return "Taban puan azalış eğiliminde"
        else:
            return "Taban puan hızla düşüyor"

    # ============================================================
    # Task 102.3: Department Recommendations (Interest Matching)
    # ============================================================

    async def get_department_recommendations(
        self,
        student_score: float,
        score_type: ScoreType,
        interests: List[str],
        career_goals: List[str],
        preferred_cities: Optional[List[str]] = None,
        year: int = 2024,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized department recommendations based on interests and career goals

        Args:
            student_score: Student's YKS score
            score_type: Score type
            interests: Student interests (e.g., ["matematik", "bilgisayar", "tasarım"])
            career_goals: Career goals (e.g., ["yazılım geliştirici", "veri bilimci"])
            preferred_cities: Preferred cities
            year: Academic year
            limit: Max recommendations

        Returns:
            List of recommended programs with match scores
        """
        # Search programs in score range
        programs = await self.advisory_service.search_programs(
            year=year,
            score_type=score_type,
            min_score=student_score - 40,
            max_score=student_score + 40,
            city=preferred_cities[0] if preferred_cities else None,
            limit=200,
        )

        # Calculate match scores
        recommendations = []
        for program in programs:
            match_score = await self._calculate_interest_match(
                program, interests, career_goals, student_score
            )

            if match_score > 30:  # Minimum match threshold
                recommendations.append(
                    {
                        "program": program,
                        "match_score": match_score,
                        "interest_alignment": match_score,
                        "career_alignment": await self._calculate_career_alignment(
                            program, career_goals
                        ),
                    }
                )

        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)

        return recommendations[:limit]

    async def _calculate_interest_match(
        self,
        program: UniversityProgram,
        interests: List[str],
        career_goals: List[str],
        student_score: float,
    ) -> float:
        """
        Calculate how well program matches student interests

        Scoring:
        - Department name match with interests: 40 points
        - Career opportunities match: 30 points
        - Score proximity: 30 points
        """
        score = 0.0

        # Department name matching (40 points)
        if program.department:
            dept_name_lower = program.department.name.lower()
            for interest in interests:
                if interest.lower() in dept_name_lower:
                    score += 15.0

            # Check SEO keywords
            if hasattr(program.department, "seo_keywords"):
                for interest in interests:
                    if interest.lower() in [
                        k.lower() for k in program.department.seo_keywords or []
                    ]:
                        score += 10.0

        score = min(score, 40.0)

        # Career opportunities match (30 points)
        if program.department and hasattr(program.department, "career_opportunities"):
            career_opps = program.department.career_opportunities or []
            for goal in career_goals:
                for opp in career_opps:
                    if goal.lower() in opp.lower():
                        score += 10.0

        score = min(score, 70.0)  # 40 + 30

        # Score proximity (30 points)
        if program.base_score:
            score_diff = abs(student_score - program.base_score)
            if score_diff <= 5:
                score += 30.0
            elif score_diff <= 15:
                score += 20.0
            elif score_diff <= 30:
                score += 10.0
            elif score_diff <= 40:
                score += 5.0

        return min(score, 100.0)

    async def _calculate_career_alignment(
        self, program: UniversityProgram, career_goals: List[str]
    ) -> float:
        """Calculate career alignment score (0-100)"""
        if not program.department or not hasattr(
            program.department, "career_opportunities"
        ):
            return 50.0

        career_opps = program.department.career_opportunities or []
        if not career_opps:
            return 50.0

        matches = 0
        for goal in career_goals:
            for opp in career_opps:
                if goal.lower() in opp.lower():
                    matches += 1

        if not career_goals:
            return 50.0

        alignment = (matches / len(career_goals)) * 100
        return min(alignment, 100.0)

    # ============================================================
    # Task 102.4: Rank Prediction
    # ============================================================

    async def predict_rank(
        self, student_score: float, score_type: ScoreType, year: int = 2024
    ) -> Dict[str, Any]:
        """
        Predict student's rank based on score

        Args:
            student_score: Student's YKS score
            score_type: Score type
            year: Academic year

        Returns:
            Rank prediction with percentile and peer comparison
        """
        # Get all programs to estimate score distribution
        stats = await self.advisory_service.get_base_score_statistics(year, score_type)

        # Estimate rank based on score distribution
        # Simplified model: assume normal distribution
        min_score = stats.get("min_score", 180.0)
        max_score = stats.get("max_score", 560.0)
        avg_score = stats.get("avg_score", 350.0)

        # Calculate percentile (0-100)
        percentile = self._calculate_percentile(
            student_score, min_score, max_score, avg_score
        )

        # Estimate rank (assuming ~2.5M test takers)
        total_test_takers = 2_500_000
        estimated_rank = int((100 - percentile) / 100 * total_test_takers)

        # Peer comparison
        peer_comparison = self._get_peer_comparison(percentile)

        return {
            "student_score": student_score,
            "score_type": score_type.value,
            "year": year,
            "estimated_rank": estimated_rank,
            "percentile": round(percentile, 2),
            "total_test_takers": total_test_takers,
            "peer_comparison": peer_comparison,
            "score_range": {"min": min_score, "max": max_score, "avg": avg_score},
            "interpretation": self._get_rank_interpretation(percentile),
        }

    def _calculate_percentile(
        self, score: float, min_score: float, max_score: float, avg_score: float
    ) -> float:
        """
        Calculate percentile using simplified normal distribution

        Returns: Percentile (0-100)
        """
        # Normalize score to 0-1 range
        if max_score - min_score == 0:
            return 50.0

        normalized = (score - min_score) / (max_score - min_score)

        # Convert to percentile (higher score = higher percentile)
        percentile = normalized * 100

        return max(0.0, min(100.0, percentile))

    def _get_peer_comparison(self, percentile: float) -> str:
        """Get peer comparison description"""
        if percentile >= 99:
            return "Top 1% - Mükemmel performans"
        elif percentile >= 95:
            return "Top 5% - Çok iyi performans"
        elif percentile >= 90:
            return "Top 10% - İyi performans"
        elif percentile >= 75:
            return "Top 25% - Ortanın üstü performans"
        elif percentile >= 50:
            return "Top 50% - Ortalama üstü performans"
        elif percentile >= 25:
            return "Ortalama performans"
        else:
            return "Ortalama altı performans"

    def _get_rank_interpretation(self, percentile: float) -> str:
        """Get rank interpretation"""
        if percentile >= 95:
            return "Tüm üniversitelerin tüm bölümlerini tercih edebilirsiniz."
        elif percentile >= 85:
            return "Çoğu prestijli üniversite ve bölümü tercih edebilirsiniz."
        elif percentile >= 70:
            return "İyi üniversitelerin çoğu bölümünü tercih edebilirsiniz."
        elif percentile >= 50:
            return "Orta derece üniversiteleri ve bölümleri tercih edebilirsiniz."
        else:
            return "Taban puanlı programları tercih etmelisiniz."

    # ============================================================
    # Batch Simulation
    # ============================================================

    async def simulate_preferences(
        self,
        student_score: float,
        score_type: ScoreType,
        preference_list: List[UUID],
        year: int = 2024,
    ) -> List[Dict[str, Any]]:
        """
        Simulate placement for a list of preferences

        Args:
            student_score: Student's YKS score
            score_type: Score type
            preference_list: List of program IDs in order
            year: Academic year

        Returns:
            List of simulation results for each preference
        """
        results = []

        for order, program_id in enumerate(preference_list, 1):
            prediction = await self.predict_placement(student_score, program_id, year)

            prediction["preference_order"] = order
            results.append(prediction)

        return results
