"""
Claude Diary Plugin - Emotional Service

Duygusal durum takibi ve analiz servisi (REQ-5).
Confidence tracking, frustration detection, flow state ve mood visualization.
"""

import io
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4  # uuid4 used for GF49 fix below

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from api.schemas.diary import (
    EmotionalStateCreate,
    MoodTrendResponse,
)
from models.diary import EmotionalState


class EmotionalService:
    """
    Emotional tracking servisi (REQ-5)

    Agent state awareness:
    - Confidence level tracking (REQ-5.1)
    - Frustration detection (REQ-5.2)
    - Flow state identification (REQ-5.3)
    - Emotional pattern analysis (REQ-5.4)
    - Mood trend visualization (REQ-5.5)
    - Self-awareness scoring (REQ-5.6)
    """

    # Frustration thresholds
    FRUSTRATION_RETRY_THRESHOLD = 3  # 3+ retry = yuksek frustration
    FRUSTRATION_ERROR_THRESHOLD = 5  # 5+ error = yuksek frustration

    # Flow state thresholds
    FLOW_CONFIDENCE_MIN = 7  # Min confidence for flow
    FLOW_PRODUCTIVITY_MIN = 0.7  # Min productivity for flow
    FLOW_TASKS_MIN = 3  # Min completed tasks for flow

    def __init__(self, db: AsyncSession):
        """
        Initialize EmotionalService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db

    # =========================================================================
    # REQ-5.1: Confidence Level Tracking
    # =========================================================================

    async def track_state(
        self,
        user_id: UUID,
        data: EmotionalStateCreate,
    ) -> EmotionalState:
        """
        Duygusal durum kaydet (REQ-5.1).

        Args:
            user_id: UUID - Kullanici ID
            data: EmotionalStateCreate - Durum verileri

        Returns:
            EmotionalState - Olusturulan kayit
        """
        # Frustration score hesapla (REQ-5.2)
        frustration_score = self._calculate_frustration(
            retry_count=data.retry_count,
            error_count=data.error_count,
            provided_score=data.frustration_score,
        )

        # Flow state belirle (REQ-5.3)
        flow_state = self._identify_flow_state(
            confidence=data.confidence_level,
            productivity=data.productivity_score,
            tasks_completed=data.tasks_completed,
            provided_flow=data.flow_state,
        )

        # Self-awareness score hesapla (REQ-5.6)
        self_awareness = await self._calculate_self_awareness(user_id)

        # GF49 fix: ``EmotionalState.id`` and ``user_id`` are declared as
        # VARCHAR (``Column(String, default=uuid4)``), but asyncpg refuses to
        # bind a Python ``UUID`` object into a VARCHAR parameter with
        # ``DataError: expected str, got UUID``. Coerce both at the caller —
        # same pattern as GF26 (Goal model) and GF36 (LiveSession model).
        state = EmotionalState(
            id=str(uuid4()),
            user_id=str(user_id),
            confidence_level=data.confidence_level,
            frustration_score=frustration_score,
            retry_count=data.retry_count,
            error_count=data.error_count,
            flow_state=flow_state,
            productivity_score=data.productivity_score,
            tasks_completed=data.tasks_completed,
            task_type=data.task_type,
            trigger_factors=data.trigger_factors or {},
            self_awareness_score=self_awareness,
            context_notes=data.context_notes,
        )

        self.db.add(state)
        await self.db.commit()
        await self.db.refresh(state)

        return state

    # =========================================================================
    # REQ-5.2: Frustration Detection
    # =========================================================================

    def _calculate_frustration(
        self,
        retry_count: int,
        error_count: int,
        provided_score: float = 0.0,
    ) -> float:
        """
        Frustration skoru hesapla (REQ-5.2).

        Args:
            retry_count: int - Tekrar sayisi
            error_count: int - Hata sayisi
            provided_score: float - Kullanici tarafindan saglanmis skor

        Returns:
            float - Frustration skoru (0-1)
        """
        # Retry bazli frustration
        retry_frustration = (
            min(retry_count / self.FRUSTRATION_RETRY_THRESHOLD, 1.0) * 0.4
        )

        # Error bazli frustration
        error_frustration = (
            min(error_count / self.FRUSTRATION_ERROR_THRESHOLD, 1.0) * 0.4
        )

        # Kullanici skoru (eger verilmisse)
        user_contribution = provided_score * 0.2

        total = retry_frustration + error_frustration + user_contribution

        return min(1.0, max(0.0, total))

    async def detect_frustration_patterns(
        self,
        user_id: UUID,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Frustration patternlerini tespit et (REQ-5.2).

        Args:
            user_id: UUID - Kullanici ID
            days: int - Analiz edilecek gun sayisi

        Returns:
            Dict - Frustration analizi
        """
        start_date = datetime.now() - timedelta(days=days)

        query = (
            select(EmotionalState)
            .where(
                and_(
                    EmotionalState.user_id == user_id,
                    EmotionalState.timestamp >= start_date,
                )
            )
            .order_by(EmotionalState.timestamp)
        )

        result = await self.db.execute(query)
        states = list(result.scalars().all())

        if not states:
            return {
                "total_states": 0,
                "high_frustration_events": 0,
                "trigger_patterns": [],
                "recommendation": "Yeterli veri yok",
            }

        # Yuksek frustration olaylari (> 0.6)
        high_frustration = [s for s in states if s.frustration_score > 0.6]

        # Trigger analizi
        trigger_counts: dict[str, int] = {}
        for state in high_frustration:
            for trigger in (state.trigger_factors or {}).keys():
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

        # Task type analizi
        task_frustration: dict[str, list[float]] = {}
        for state in states:
            if state.task_type:
                if state.task_type not in task_frustration:
                    task_frustration[state.task_type] = []
                task_frustration[state.task_type].append(state.frustration_score)

        problematic_tasks = [
            {"task_type": tt, "avg_frustration": round(sum(scores) / len(scores), 2)}
            for tt, scores in task_frustration.items()
            if sum(scores) / len(scores) > 0.5
        ]

        return {
            "total_states": len(states),
            "high_frustration_events": len(high_frustration),
            "high_frustration_percentage": round(
                len(high_frustration) / len(states) * 100, 1
            ),
            "avg_frustration": round(
                sum(s.frustration_score for s in states) / len(states), 3
            ),
            "trigger_patterns": sorted(
                [{"trigger": t, "count": c} for t, c in trigger_counts.items()],
                key=lambda x: x["count"],
                reverse=True,
            )[:5],
            "problematic_task_types": problematic_tasks,
            "recommendation": self._generate_frustration_recommendation(
                high_frustration, problematic_tasks
            ),
        }

    def _generate_frustration_recommendation(
        self,
        high_frustration_events: list[EmotionalState],
        problematic_tasks: list[dict],
    ) -> str:
        """Frustration icin oneri olustur."""
        if not high_frustration_events:
            return "Frustration seviyeniz kontrol altinda. Boyle devam edin!"

        if problematic_tasks:
            task = problematic_tasks[0]["task_type"]
            return f"'{task}' tipindeki isler sizi zorluyorŷ. Bu alanda destek alin veya yaklasimi degistirin."

        return "Frustration olaylarinda mola vermeyi ve problemi parcalara bolmeyi deneyin."

    # =========================================================================
    # REQ-5.3: Flow State Identification
    # =========================================================================

    def _identify_flow_state(
        self,
        confidence: int,
        productivity: float,
        tasks_completed: int,
        provided_flow: bool = False,
    ) -> bool:
        """
        Flow state belirle (REQ-5.3).

        Args:
            confidence: int - Confidence seviyesi (1-10)
            productivity: float - Productivity skoru (0-1)
            tasks_completed: int - Tamamlanan task sayisi
            provided_flow: bool - Kullanici flow'da oldugunu belirtmis mi

        Returns:
            bool - Flow state durumu
        """
        if provided_flow:
            return True

        # Otomatik tespit
        is_flow = (
            confidence >= self.FLOW_CONFIDENCE_MIN
            and productivity >= self.FLOW_PRODUCTIVITY_MIN
            and tasks_completed >= self.FLOW_TASKS_MIN
        )

        return is_flow

    async def get_flow_statistics(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Flow state istatistiklerini getir (REQ-5.3).

        Args:
            user_id: UUID - Kullanici ID
            days: int - Gun sayisi

        Returns:
            Dict - Flow istatistikleri
        """
        start_date = datetime.now() - timedelta(days=days)

        query = select(EmotionalState).where(
            and_(
                EmotionalState.user_id == user_id,
                EmotionalState.timestamp >= start_date,
            )
        )

        result = await self.db.execute(query)
        states = list(result.scalars().all())

        if not states:
            return {
                "total_states": 0,
                "flow_count": 0,
                "flow_percentage": 0,
                "avg_flow_duration": 0,
                "flow_triggers": [],
            }

        flow_states = [s for s in states if s.flow_state]

        # Flow trigger analizi
        flow_triggers: dict[str, int] = {}
        for state in flow_states:
            if state.task_type:
                flow_triggers[state.task_type] = (
                    flow_triggers.get(state.task_type, 0) + 1
                )

        return {
            "total_states": len(states),
            "flow_count": len(flow_states),
            "flow_percentage": round(len(flow_states) / len(states) * 100, 1),
            "avg_confidence_in_flow": round(
                sum(s.confidence_level for s in flow_states) / len(flow_states), 1
            )
            if flow_states
            else 0,
            "avg_productivity_in_flow": round(
                sum(s.productivity_score for s in flow_states) / len(flow_states), 2
            )
            if flow_states
            else 0,
            "flow_triggers": sorted(
                [{"task_type": t, "count": c} for t, c in flow_triggers.items()],
                key=lambda x: x["count"],
                reverse=True,
            )[:5],
        }

    # =========================================================================
    # REQ-5.4: Emotional Pattern Analysis
    # =========================================================================

    async def analyze_emotional_patterns(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Duygusal patternleri analiz et (REQ-5.4).

        Args:
            user_id: UUID - Kullanici ID
            days: int - Gun sayisi

        Returns:
            Dict - Pattern analizi
        """
        start_date = datetime.now() - timedelta(days=days)

        query = (
            select(EmotionalState)
            .where(
                and_(
                    EmotionalState.user_id == user_id,
                    EmotionalState.timestamp >= start_date,
                )
            )
            .order_by(EmotionalState.timestamp)
        )

        result = await self.db.execute(query)
        states = list(result.scalars().all())

        if len(states) < 5:
            return {
                "patterns": [],
                "cycles": [],
                "insights": ["Yeterli veri yok (en az 5 kayit gerekli)"],
            }

        patterns: list[dict[str, Any]] = []
        insights: list[str] = []

        # Hafta ici vs hafta sonu analizi
        weekday_states = [s for s in states if s.timestamp.weekday() < 5]
        weekend_states = [s for s in states if s.timestamp.weekday() >= 5]

        if weekday_states and weekend_states:
            weekday_conf = sum(s.confidence_level for s in weekday_states) / len(
                weekday_states
            )
            weekend_conf = sum(s.confidence_level for s in weekend_states) / len(
                weekend_states
            )

            if weekday_conf > weekend_conf + 1:
                patterns.append(
                    {
                        "type": "weekday_preference",
                        "description": "Hafta ici daha yuksek confidence",
                        "weekday_avg": round(weekday_conf, 1),
                        "weekend_avg": round(weekend_conf, 1),
                    }
                )
                insights.append("Hafta ici daha verimli calisiyorsunuz")
            elif weekend_conf > weekday_conf + 1:
                patterns.append(
                    {
                        "type": "weekend_preference",
                        "description": "Hafta sonu daha yuksek confidence",
                        "weekday_avg": round(weekday_conf, 1),
                        "weekend_avg": round(weekend_conf, 1),
                    }
                )
                insights.append("Hafta sonu daha verimli calisiyorsunuz")

        # Task type bazli pattern
        task_confidence: dict[str, list[int]] = {}
        for state in states:
            if state.task_type:
                if state.task_type not in task_confidence:
                    task_confidence[state.task_type] = []
                task_confidence[state.task_type].append(state.confidence_level)

        high_conf_tasks = [
            (tt, sum(confs) / len(confs))
            for tt, confs in task_confidence.items()
            if len(confs) >= 3 and sum(confs) / len(confs) >= 7
        ]

        for task_type, avg_conf in high_conf_tasks:
            patterns.append(
                {
                    "type": "high_confidence_task",
                    "task_type": task_type,
                    "avg_confidence": round(avg_conf, 1),
                }
            )
            insights.append(f"'{task_type}' islerinde kendinize guveniyor sunuz")

        # Trend analizi
        if len(states) >= 14:
            recent = states[-7:]
            older = states[-14:-7]

            recent_conf = sum(s.confidence_level for s in recent) / len(recent)
            older_conf = sum(s.confidence_level for s in older) / len(older)

            if recent_conf > older_conf + 0.5:
                insights.append("Son hafta confidence seviyeniz yukseldi")
            elif recent_conf < older_conf - 0.5:
                insights.append("Son hafta confidence seviyeniz dustu")

        return {
            "patterns": patterns,
            "insights": insights,
            "total_states_analyzed": len(states),
        }

    # =========================================================================
    # REQ-5.5: Mood Trend Visualization
    # =========================================================================

    async def get_mood_trend(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> MoodTrendResponse:
        """
        Mood trend verilerini getir (REQ-5.5).

        Args:
            user_id: UUID - Kullanici ID
            days: int - Gun sayisi

        Returns:
            MoodTrendResponse - Trend verileri
        """
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()

        query = (
            select(EmotionalState)
            .where(
                and_(
                    EmotionalState.user_id == user_id,
                    EmotionalState.timestamp >= start_date,
                )
            )
            .order_by(EmotionalState.timestamp)
        )

        result = await self.db.execute(query)
        states = list(result.scalars().all())

        data_points: list[dict[str, Any]] = []

        for state in states:
            data_points.append(
                {
                    "timestamp": state.timestamp.isoformat(),
                    "date": state.timestamp.date().isoformat(),
                    "confidence_level": state.confidence_level,
                    "frustration_score": state.frustration_score,
                    "flow_state": state.flow_state,
                    "productivity_score": state.productivity_score,
                }
            )

        # Ortalamalar
        avg_confidence = (
            sum(s.confidence_level for s in states) / len(states) if states else 0
        )
        flow_percentage = (
            (sum(1 for s in states if s.flow_state) / len(states) * 100)
            if states
            else 0
        )
        frustration_events = sum(1 for s in states if s.frustration_score > 0.6)

        return MoodTrendResponse(
            period_start=start_date.date(),
            period_end=end_date.date(),
            data_points=data_points,
            average_confidence=round(avg_confidence, 2),
            flow_state_percentage=round(flow_percentage, 1),
            frustration_events=frustration_events,
        )

    async def generate_mood_chart(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> bytes | None:
        """
        Mood chart PNG olustur (REQ-5.5).

        Args:
            user_id: UUID - Kullanici ID
            days: int - Gun sayisi

        Returns:
            Optional[bytes] - PNG veri veya None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        trend = await self.get_mood_trend(user_id, days)

        if not trend.data_points:
            return None

        # Verileri hazirla
        dates = [datetime.fromisoformat(dp["timestamp"]) for dp in trend.data_points]
        confidence = [dp["confidence_level"] for dp in trend.data_points]
        frustration = [
            dp["frustration_score"] * 10 for dp in trend.data_points
        ]  # 0-10 scale

        # Chart olustur
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(dates, confidence, "b-", label="Guven (1-10)", linewidth=2)
        ax.plot(
            dates,
            frustration,
            "r--",
            label="Frustration (x10)",
            linewidth=1.5,
            alpha=0.7,
        )

        # Flow state noktalari
        flow_dates = [
            datetime.fromisoformat(dp["timestamp"])
            for dp in trend.data_points
            if dp["flow_state"]
        ]
        flow_confidence = [
            dp["confidence_level"] for dp in trend.data_points if dp["flow_state"]
        ]

        if flow_dates:
            ax.scatter(
                flow_dates,
                flow_confidence,
                c="green",
                s=100,
                label="Flow State",
                zorder=5,
            )

        # Formatting
        ax.set_xlabel("Tarih")
        ax.set_ylabel("Deger")
        ax.set_title(f"Mood Trendi (Son {days} Gun)")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

        # X-axis formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
        plt.xticks(rotation=45)

        ax.set_ylim(0, 11)

        plt.tight_layout()

        # PNG olarak kaydet
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        buf.seek(0)
        plt.close(fig)

        return buf.read()

    # =========================================================================
    # REQ-5.6: Self-Awareness Scoring
    # =========================================================================

    async def _calculate_self_awareness(
        self,
        user_id: UUID,
    ) -> float:
        """
        Self-awareness skoru hesapla (REQ-5.6).

        Prediction accuracy + emotional regulation.

        Args:
            user_id: UUID - Kullanici ID

        Returns:
            float - Self-awareness skoru (0-100)
        """
        # Son 30 gunun kayitlarini al
        start_date = datetime.now() - timedelta(days=30)

        query = select(EmotionalState).where(
            and_(
                EmotionalState.user_id == user_id,
                EmotionalState.timestamp >= start_date,
            )
        )

        result = await self.db.execute(query)
        states = list(result.scalars().all())

        if len(states) < 5:
            return 50.0  # Default

        # Prediction accuracy (predicted vs actual durumu var mi?)
        prediction_scores: list[float] = []
        for state in states:
            if state.predicted_state and state.actual_state:
                # Basit esleme: ayni = 1, farkli = 0
                match = 1.0 if state.predicted_state == state.actual_state else 0.0
                prediction_scores.append(match)

        prediction_accuracy = (
            (sum(prediction_scores) / len(prediction_scores) * 40)
            if prediction_scores
            else 20
        )

        # Emotional regulation: Frustration recovery
        high_frustration_indices = [
            i for i, s in enumerate(states) if s.frustration_score > 0.6
        ]

        recovery_scores: list[float] = []
        for idx in high_frustration_indices:
            if idx + 1 < len(states):
                next_state = states[idx + 1]
                if next_state.frustration_score < 0.4:
                    recovery_scores.append(1.0)
                elif next_state.frustration_score < 0.6:
                    recovery_scores.append(0.5)
                else:
                    recovery_scores.append(0.0)

        regulation_score = (
            (sum(recovery_scores) / len(recovery_scores) * 30)
            if recovery_scores
            else 15
        )

        # Consistency: Confidence variance
        conf_values = [s.confidence_level for s in states]
        if len(conf_values) >= 2:
            import statistics

            variance = statistics.variance(conf_values)
            # Dusuk variance = yuksek consistency
            consistency_score = max(0, 30 - variance * 3)
        else:
            consistency_score = 15

        total = prediction_accuracy + regulation_score + consistency_score
        return round(min(100, max(0, total)), 1)

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def get_states(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list[EmotionalState]:
        """
        Duygusal durumlari getir.

        Args:
            user_id: UUID - Kullanici ID
            from_date: Optional[datetime] - Baslangic tarihi
            to_date: Optional[datetime] - Bitis tarihi
            limit: int - Maksimum kayit sayisi

        Returns:
            List[EmotionalState] - Durum listesi
        """
        conditions = [EmotionalState.user_id == user_id]

        if from_date:
            conditions.append(EmotionalState.timestamp >= from_date)
        if to_date:
            conditions.append(EmotionalState.timestamp <= to_date)

        query = (
            select(EmotionalState)
            .where(and_(*conditions))
            .order_by(desc(EmotionalState.timestamp))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_state_by_id(
        self,
        state_id: UUID,
        user_id: UUID,
    ) -> EmotionalState | None:
        """
        ID ile durum getir.

        Args:
            state_id: UUID - Durum ID
            user_id: UUID - Kullanici ID

        Returns:
            Optional[EmotionalState] - Durum veya None
        """
        query = select(EmotionalState).where(
            and_(EmotionalState.id == state_id, EmotionalState.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_state(
        self,
        state_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Durumu sil.

        Args:
            state_id: UUID - Durum ID
            user_id: UUID - Kullanici ID

        Returns:
            bool - Basari durumu
        """
        state = await self.get_state_by_id(state_id, user_id)
        if not state:
            return False

        await self.db.delete(state)
        await self.db.commit()
        return True
