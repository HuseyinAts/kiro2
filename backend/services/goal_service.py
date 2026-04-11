"""
Claude Diary Plugin - Goal Service

Hedef izleme servisi (REQ-6).
SMART validation, progress tracking, milestone celebration, risk detection.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.diary import (
    GoalCreate,
    GoalProgressUpdate,
    GoalRiskResponse,
    GoalUpdate,
)
from models.diary import Goal, GoalStatus


class GoalService:
    """
    Hedef izleme servisi (REQ-6)

    Hedef yonetimi:
    - SMART criteria validation (REQ-6.1)
    - Progress tracking (REQ-6.2)
    - Milestone celebration (REQ-6.3)
    - Risk detection (REQ-6.4)
    - Goal adjustment (REQ-6.5)
    - Retrospective (REQ-6.6)
    """

    # Milestone thresholds
    DEFAULT_MILESTONES = [25, 50, 75, 100]

    # Risk thresholds
    RISK_VELOCITY_THRESHOLD = 0.5  # Beklenenin %50'sinin altinda
    RISK_DAYS_THRESHOLD = 7  # 7 gun kaldi ama %70'in altinda

    def __init__(self, db: AsyncSession):
        """
        Initialize GoalService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db

    # =========================================================================
    # REQ-6.1: SMART Validation
    # =========================================================================

    def validate_smart(self, goal: GoalCreate) -> dict[str, Any]:
        """
        SMART kriterlerini dogrula (REQ-6.1).

        SMART:
        - Specific: Ozgu mu?
        - Measurable: Olculebilir mi?
        - Achievable: Ulasilabilir mi?
        - Relevant: Ilgili mi?
        - Time-bound: Zaman sinirli mi?

        Args:
            goal: GoalCreate - Hedef verisi

        Returns:
            Dict containing:
            - is_valid: bool
            - score: int (0-5)
            - missing: List[str]
            - warnings: List[str]
        """
        score = 0
        missing: list[str] = []
        warnings: list[str] = []

        # Specific: Title ve description kontrolu
        if goal.title and len(goal.title) >= 10:
            score += 1
        else:
            missing.append(
                "Specific: Hedef basligi daha detayli olmali (min 10 karakter)"
            )

        if goal.specific:
            score += 0.5
        else:
            warnings.append("Specific: 'Tam olarak ne?' alani bos")

        # Measurable: target_value ve unit kontrolu
        if goal.target_value and goal.target_value > 0:
            score += 1
        else:
            missing.append("Measurable: Olculebilir hedef degeri belirlenmeli")

        if goal.measurable:
            score += 0.5
        else:
            warnings.append("Measurable: 'Nasil olculecek?' alani bos")

        # Achievable: Realistic check
        if goal.achievable:
            score += 1
        else:
            warnings.append("Achievable: 'Gercekci mi?' alani bos")

        # Relevant: Why it matters
        if goal.relevant:
            score += 1
        else:
            warnings.append("Relevant: 'Neden onemli?' alani bos")

        # Time-bound: Target date kontrolu
        # Pydantic parses ISO datetimes with `Z` suffix as tz-aware; normalize
        # the "now" side to the same tzinfo to avoid TypeError on comparison.
        if goal.target_date:
            now = (
                datetime.now(goal.target_date.tzinfo)
                if goal.target_date.tzinfo
                else datetime.now()
            )
            if goal.target_date > now:
                score += 1
            else:
                missing.append("Time-bound: Hedef tarihi gelecekte olmali")
        else:
            missing.append("Time-bound: Hedef tarihi belirlenmeli")

        is_valid = score >= 3 and len(missing) == 0

        return {
            "is_valid": is_valid,
            "score": int(score),
            "missing": missing,
            "warnings": warnings,
            "max_score": 5,
        }

    # =========================================================================
    # REQ-6.2: Progress Tracking
    # =========================================================================

    def calculate_progress(self, current_value: float, target_value: float) -> int:
        """
        Ilerleme yuzdesini hesapla (REQ-6.2).

        Args:
            current_value: float - Mevcut deger
            target_value: float - Hedef deger

        Returns:
            int - Ilerleme yuzdesi (0-100)
        """
        if target_value <= 0:
            return 0
        progress = (current_value / target_value) * 100
        return min(100, max(0, int(progress)))

    def calculate_velocity(self, goal: Goal) -> float:
        """
        Ilerleme hizini hesapla (gunluk).

        Args:
            goal: Goal - Hedef

        Returns:
            float - Gunluk ilerleme hizi
        """
        if not goal.start_date:
            return 0.0

        days_elapsed = (datetime.now(goal.start_date.tzinfo) - goal.start_date).days
        if days_elapsed <= 0:
            return 0.0

        return goal.progress / days_elapsed

    def predict_completion(self, goal: Goal) -> datetime | None:
        """
        Tahmini tamamlanma tarihini hesapla.

        Args:
            goal: Goal - Hedef

        Returns:
            Optional[datetime] - Tahmini tarih veya None
        """
        velocity = self.calculate_velocity(goal)
        if velocity <= 0:
            return None

        remaining_progress = 100 - goal.progress
        days_needed = remaining_progress / velocity

        return datetime.now() + timedelta(days=int(days_needed))

    # =========================================================================
    # REQ-6.3: Milestone Celebration
    # =========================================================================

    def check_milestones(self, goal: Goal, new_progress: int) -> list[dict[str, Any]]:
        """
        Ulasilan kilometre taslarini kontrol et (REQ-6.3).

        Args:
            goal: Goal - Hedef
            new_progress: int - Yeni ilerleme yuzdesi

        Returns:
            List[Dict] - Ulasilan milestone'lar ve kutlama mesajlari
        """
        achieved: list[dict[str, Any]] = []
        old_progress = goal.progress

        # Mevcut milestone'lari kontrol et
        milestones = goal.milestones or []

        for milestone in milestones:
            percentage = milestone.get("percentage", 0)

            # Eski ilerleme altinda, yeni ilerleme ustunde mi?
            if old_progress < percentage <= new_progress:
                celebration = self._generate_celebration(
                    milestone_title=milestone.get("title", f"%{percentage} tamamlandi"),
                    percentage=percentage,
                )
                achieved.append(
                    {
                        "percentage": percentage,
                        "title": milestone.get("title"),
                        "celebration": celebration,
                        "achieved_at": datetime.now().isoformat(),
                    }
                )

        # Default milestone'lar
        for pct in self.DEFAULT_MILESTONES:
            if old_progress < pct <= new_progress:
                # Zaten milestone listesinde yoksa
                if not any(m.get("percentage") == pct for m in milestones):
                    celebration = self._generate_celebration(
                        milestone_title=f"%{pct} tamamlandi",
                        percentage=pct,
                    )
                    achieved.append(
                        {
                            "percentage": pct,
                            "title": f"%{pct} tamamlandi",
                            "celebration": celebration,
                            "achieved_at": datetime.now().isoformat(),
                        }
                    )

        return achieved

    def _generate_celebration(self, milestone_title: str, percentage: int) -> str:
        """Kutlama mesaji olustur"""
        celebrations = {
            25: "🚀 Harika baslangiç! Ceyreği tamamladın!",
            50: "🎯 Yarı yoldasın! Devam et!",
            75: "💪 Son çeyreğe girdin! Hedefe çok yakınsın!",
            100: "🎉 TEBRIKLER! Hedefini tamamladin! 🏆",
        }

        if percentage in celebrations:
            return celebrations[percentage]

        return f"✨ {milestone_title} - Harika gidiyorsun!"

    # =========================================================================
    # REQ-6.4: Risk Detection
    # =========================================================================

    def detect_risk(self, goal: Goal) -> GoalRiskResponse:
        """
        Hedef risklerini tespit et (REQ-6.4).

        Risk faktörleri:
        - Düşük velocity
        - Zaman baskısı
        - Uzun süre güncelleme yok

        Args:
            goal: Goal - Hedef

        Returns:
            GoalRiskResponse - Risk analizi
        """
        risk_factors: list[str] = []
        recommendations: list[str] = []
        is_at_risk = False

        # 1. Velocity kontrolü
        velocity = self.calculate_velocity(goal)
        expected_velocity = self._calculate_expected_velocity(goal)

        if velocity < expected_velocity * self.RISK_VELOCITY_THRESHOLD:
            is_at_risk = True
            risk_factors.append(
                f"Ilerleme hizi beklenenin %{int(velocity / expected_velocity * 100)}'i"
            )
            recommendations.append("Gunluk hedefler belirle ve takip et")

        # 2. Zaman baskısı
        if goal.target_date:
            days_remaining = (
                goal.target_date - datetime.now(goal.target_date.tzinfo)
            ).days

            if days_remaining <= self.RISK_DAYS_THRESHOLD and goal.progress < 70:
                is_at_risk = True
                risk_factors.append(
                    f"Sadece {days_remaining} gun kaldi, ilerleme %{goal.progress}"
                )
                recommendations.append("Hedefi gozden gecir veya tarihi uzat")

            if days_remaining < 0:
                is_at_risk = True
                risk_factors.append("Hedef tarihi gecmis")
                recommendations.append("Hedefi yeniden degerlendir")

        # 3. Güncelleme kontrolü
        if goal.updated_at:
            days_since_update = (
                datetime.now(goal.updated_at.tzinfo) - goal.updated_at
            ).days
            if days_since_update > 7 and goal.progress < 100:
                is_at_risk = True
                risk_factors.append(f"{days_since_update} gundur guncelleme yok")
                recommendations.append("Hedef ilerlemesini guncelle")

        # Risk seviyesi
        risk_level = "low"
        if len(risk_factors) >= 2:
            risk_level = "high"
        elif len(risk_factors) == 1:
            risk_level = "medium"

        # Tahmini tamamlanma
        predicted = self.predict_completion(goal) if not is_at_risk else None

        return GoalRiskResponse(
            goal_id=goal.id,
            is_at_risk=is_at_risk,
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendations=recommendations,
            predicted_completion=predicted,
            on_track=not is_at_risk,
        )

    def _calculate_expected_velocity(self, goal: Goal) -> float:
        """Beklenen velocity'yi hesapla"""
        if not goal.target_date or not goal.start_date:
            return 1.0

        total_days = (goal.target_date - goal.start_date).days
        if total_days <= 0:
            return 100.0

        return 100.0 / total_days

    # =========================================================================
    # REQ-6.5: Goal Adjustment
    # =========================================================================

    async def adjust_goal(
        self,
        goal_id: UUID,
        reason: str,
        new_target_value: float | None = None,
        new_target_date: datetime | None = None,
    ) -> Goal | None:
        """
        Hedefi ayarla ve kayit tut (REQ-6.5).

        Args:
            goal_id: UUID - Hedef ID
            reason: str - Ayarlama nedeni
            new_target_value: Optional[float] - Yeni hedef degeri
            new_target_date: Optional[datetime] - Yeni hedef tarihi

        Returns:
            Optional[Goal] - Guncellenmis hedef veya None
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        adjustment = {
            "date": datetime.now().isoformat(),
            "reason": reason,
            "changes": {},
        }

        if new_target_value is not None:
            adjustment["changes"]["target_value"] = {
                "old": goal.target_value,
                "new": new_target_value,
            }
            goal.target_value = new_target_value

        if new_target_date is not None:
            adjustment["changes"]["target_date"] = {
                "old": goal.target_date.isoformat() if goal.target_date else None,
                "new": new_target_date.isoformat(),
            }
            goal.target_date = new_target_date

        # Adjustment kaydi
        adjustments = goal.adjustments or []
        adjustments.append(adjustment)
        goal.adjustments = adjustments

        # Progress yeniden hesapla
        goal.progress = self.calculate_progress(goal.current_value, goal.target_value)

        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    # =========================================================================
    # REQ-6.6: Retrospective
    # =========================================================================

    async def create_retrospective(
        self,
        goal_id: UUID,
        lessons_learned: list[str],
        success_factors: list[str],
        challenges_faced: list[str],
    ) -> Goal | None:
        """
        Retrospektif olustur (REQ-6.6).

        Args:
            goal_id: UUID - Hedef ID
            lessons_learned: List[str] - Ogrenilen dersler
            success_factors: List[str] - Basari faktorleri
            challenges_faced: List[str] - Karsilasilan zorluklar

        Returns:
            Optional[Goal] - Guncellenmis hedef veya None
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        goal.lessons_learned = lessons_learned
        goal.success_factors = success_factors
        goal.challenges_faced = challenges_faced

        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def create_goal(self, user_id: UUID, goal_data: GoalCreate) -> Goal:
        """
        Yeni hedef olustur.

        Args:
            user_id: UUID - Kullanici ID
            goal_data: GoalCreate - Hedef verisi

        Returns:
            Goal - Olusturulan hedef
        """
        # Milestone'lari formatla
        milestones = []
        for m in goal_data.milestones:
            milestones.append(
                {
                    "percentage": m.percentage,
                    "title": m.title,
                    "achieved": False,
                    "achieved_at": None,
                }
            )

        # Default milestone'lar ekle (yoksa)
        for pct in self.DEFAULT_MILESTONES:
            if not any(m["percentage"] == pct for m in milestones):
                milestones.append(
                    {
                        "percentage": pct,
                        "title": f"%{pct} tamamlandi",
                        "achieved": False,
                        "achieved_at": None,
                    }
                )

        milestones.sort(key=lambda x: x["percentage"])

        # GF26 fix: Goal.id is a String PK with `default=uuid4`, which hands
        # asyncpg a raw `UUID` object. asyncpg binds VARCHAR parameters
        # strictly and rejects non-str values with
        #     DataError: invalid input for query argument $1 (expected str, got UUID)
        # so we must coerce the primary key to a plain string at creation
        # time. Fixing it in the model's `default=` would require a touch
        # of every caller's test fixtures, so we pre-generate it here. See
        # GF26 in golden-flows.md.
        from uuid import uuid4 as _uuid4

        goal = Goal(
            id=str(_uuid4()),
            user_id=str(user_id),
            title=goal_data.title,
            description=goal_data.description,
            target_value=goal_data.target_value,
            target_date=goal_data.target_date,
            unit=goal_data.unit,
            category=goal_data.category,
            priority=goal_data.priority,
            milestones=milestones,
            specific=goal_data.specific,
            measurable=goal_data.measurable,
            achievable=goal_data.achievable,
            relevant=goal_data.relevant,
            time_bound=goal_data.target_date,
            status=GoalStatus.ACTIVE,
        )

        # `get_async_session()` wraps us in `db_manager.get_session()` which
        # commits on successful handler return, so we only flush here to
        # populate server-side defaults (created_at, updated_at) and let
        # the outer wrapper own the commit. A second inner commit here
        # surfaced as MissingGreenlet on the already-released connection.
        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal

    async def get_goal(self, goal_id: UUID) -> Goal | None:
        """
        Hedef getir.

        Args:
            goal_id: UUID - Hedef ID

        Returns:
            Optional[Goal] - Hedef veya None
        """
        query = select(Goal).where(Goal.id == goal_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_goals(
        self,
        user_id: UUID,
        status: GoalStatus | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[Goal]:
        """
        Hedef listesi getir.

        Args:
            user_id: UUID - Kullanici ID
            status: Optional[GoalStatus] - Durum filtresi
            category: Optional[str] - Kategori filtresi
            limit: int - Maksimum kayit sayisi

        Returns:
            List[Goal] - Hedef listesi
        """
        conditions = [Goal.user_id == user_id]

        if status:
            conditions.append(Goal.status == status)
        if category:
            conditions.append(Goal.category == category)

        query = (
            select(Goal)
            .where(and_(*conditions))
            .order_by(desc(Goal.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_goals(self, user_id: UUID) -> list[Goal]:
        """Aktif hedefleri getir"""
        return await self.get_goals(user_id, status=GoalStatus.ACTIVE)

    async def get_at_risk_goals(self, user_id: UUID) -> list[Goal]:
        """Risk altindaki hedefleri getir"""
        query = (
            select(Goal)
            .where(
                and_(
                    Goal.user_id == user_id,
                    Goal.status == GoalStatus.ACTIVE,
                    Goal.is_at_risk == True,
                )
            )
            .order_by(Goal.target_date)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_goal(self, goal_id: UUID, update_data: GoalUpdate) -> Goal | None:
        """
        Hedef guncelle.

        Args:
            goal_id: UUID - Hedef ID
            update_data: GoalUpdate - Guncelleme verisi

        Returns:
            Optional[Goal] - Guncellenmis hedef veya None
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == "milestones" and value is not None:
                # Milestone'lari formatla
                milestones = []
                for m in value:
                    milestones.append(
                        {
                            "percentage": m.percentage,
                            "title": m.title,
                            "achieved": False,
                            "achieved_at": None,
                        }
                    )
                setattr(goal, key, milestones)
            elif hasattr(goal, key):
                setattr(goal, key, value)

        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def update_progress(
        self, goal_id: UUID, progress_data: GoalProgressUpdate
    ) -> dict[str, Any] | None:
        """
        Ilerleme guncelle ve milestone kontrolu yap.

        Args:
            goal_id: UUID - Hedef ID
            progress_data: GoalProgressUpdate - Ilerleme verisi

        Returns:
            Optional[Dict] - Guncelleme sonucu (milestone celebrations dahil)
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        old_progress = goal.progress

        # Ilerleme guncelle
        if progress_data.current_value is not None:
            goal.current_value = progress_data.current_value
            goal.progress = self.calculate_progress(
                progress_data.current_value, goal.target_value
            )
        elif progress_data.progress is not None:
            goal.progress = progress_data.progress
            goal.current_value = (progress_data.progress / 100) * goal.target_value

        # Velocity guncelle
        goal.velocity = self.calculate_velocity(goal)

        # Tahmini tamamlanma
        predicted = self.predict_completion(goal)
        if predicted:
            goal.predicted_completion = predicted

        # Milestone kontrolu
        celebrations = self.check_milestones(goal, goal.progress)

        # Milestone kayitlarini guncelle
        if celebrations:
            milestone_celebrations = goal.milestone_celebrations or []
            milestone_celebrations.extend(celebrations)
            goal.milestone_celebrations = milestone_celebrations

            # Milestone'lari achieved olarak isaretle
            milestones = goal.milestones or []
            for c in celebrations:
                for m in milestones:
                    if m.get("percentage") == c["percentage"]:
                        m["achieved"] = True
                        m["achieved_at"] = c["achieved_at"]
            goal.milestones = milestones

        # Tamamlanma kontrolu
        if goal.progress >= 100:
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = datetime.now()

        # Risk kontrolu
        risk = self.detect_risk(goal)
        goal.is_at_risk = risk.is_at_risk
        goal.risk_factors = risk.risk_factors

        await self.db.commit()
        await self.db.refresh(goal)

        return {
            "goal": goal,
            "old_progress": old_progress,
            "new_progress": goal.progress,
            "celebrations": celebrations,
            "risk": risk,
        }

    async def delete_goal(self, goal_id: UUID) -> bool:
        """
        Hedef sil.

        Args:
            goal_id: UUID - Hedef ID

        Returns:
            bool - Basari durumu
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            return False

        await self.db.delete(goal)
        await self.db.commit()
        return True

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_goal_statistics(self, user_id: UUID) -> dict[str, Any]:
        """
        Kullanici hedef istatistiklerini getir.

        Args:
            user_id: UUID - Kullanici ID

        Returns:
            Dict - Istatistikler
        """
        goals = await self.get_goals(user_id, limit=1000)

        total = len(goals)
        completed = sum(1 for g in goals if g.status == GoalStatus.COMPLETED)
        active = sum(1 for g in goals if g.status == GoalStatus.ACTIVE)
        at_risk = sum(1 for g in goals if g.is_at_risk)
        cancelled = sum(1 for g in goals if g.status == GoalStatus.CANCELLED)

        completion_rate = (completed / total * 100) if total > 0 else 0

        # Kategori dagilimi
        categories: dict[str, int] = {}
        for g in goals:
            cat = g.category or "Diger"
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_goals": total,
            "completed": completed,
            "active": active,
            "at_risk": at_risk,
            "cancelled": cancelled,
            "completion_rate": round(completion_rate, 1),
            "category_distribution": categories,
        }
