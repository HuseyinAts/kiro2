"""
Claude Diary Plugin - Peer Comparison Service

Akran karsilastirma servisi (REQ-7).
Differential privacy ile anonymized performance benchmarking.
"""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from diffprivlib.mechanisms import Laplace
    DIFFPRIV_AVAILABLE = True
except ImportError:
    DIFFPRIV_AVAILABLE = False

from models.diary import DiaryEntry, PeerComparison


class PeerComparisonService:
    """
    Peer comparison servisi (REQ-7)

    Anonymized performance benchmarking:
    - Anonymized peer data (REQ-7.1)
    - Percentile calculation (REQ-7.2)
    - Strength areas (REQ-7.3)
    - Improvement areas (REQ-7.4)
    - Best practice learning (REQ-7.5)
    - Differential privacy (REQ-7.6)
    """

    # Privacy settings
    K_ANONYMITY = 5  # Minimum peer group size
    EPSILON = 1.0  # Differential privacy epsilon
    SENSITIVITY = 10.0  # Query sensitivity

    # Percentile thresholds
    STRENGTH_THRESHOLD = 75  # Top 25%
    IMPROVEMENT_THRESHOLD = 25  # Bottom 25%

    def __init__(self, db: AsyncSession):
        """
        Initialize PeerComparisonService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db

    # =========================================================================
    # REQ-7.1: Anonymized Peer Data
    # =========================================================================

    async def _get_peer_data(
        self,
        period_start: date,
        period_end: date,
        exclude_user_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """
        Anonymized peer verilerini getir (REQ-7.1).

        Args:
            period_start: date - Baslangic tarihi
            period_end: date - Bitis tarihi
            exclude_user_id: Optional[UUID] - Haric tutulacak kullanici

        Returns:
            List[Dict] - Anonymized peer metrikleri
        """
        conditions = [
            DiaryEntry.date >= period_start,
            DiaryEntry.date <= period_end,
        ]

        if exclude_user_id:
            conditions.append(DiaryEntry.user_id != exclude_user_id)

        # Kullanici bazli aggregation
        query = (
            select(
                DiaryEntry.user_id,
                func.count(DiaryEntry.id).label("entry_count"),
                func.sum(DiaryEntry.success_count).label("total_success"),
                func.sum(DiaryEntry.failure_count).label("total_failure"),
                func.sum(DiaryEntry.total_tasks).label("total_tasks"),
                func.sum(DiaryEntry.total_duration_minutes).label("total_duration"),
            )
            .where(and_(*conditions))
            .group_by(DiaryEntry.user_id)
            .having(func.count(DiaryEntry.id) >= 3)  # En az 3 entry
        )

        result = await self.db.execute(query)
        rows = result.all()

        peer_data: list[dict[str, Any]] = []

        for row in rows:
            total_tasks = row.total_tasks or 0
            total_success = row.total_success or 0
            total_duration = row.total_duration or 0

            if total_tasks > 0:
                success_rate = (total_success / total_tasks) * 100
                avg_duration_per_task = total_duration / total_tasks

                # Speed score (normalize: faster = higher)
                # Max 120 dk/task = 0, 10 dk/task = 100
                speed_score = max(0, 100 - (avg_duration_per_task - 10) * 0.9)

                peer_data.append({
                    "success_rate": success_rate,
                    "speed_score": speed_score,
                    "total_tasks": total_tasks,
                    "entry_count": row.entry_count,
                })

        return peer_data

    # =========================================================================
    # REQ-7.2: Percentile Calculation
    # =========================================================================

    def _calculate_percentile(
        self,
        value: float,
        all_values: list[float],
    ) -> float:
        """
        Percentile hesapla (REQ-7.2).

        Args:
            value: float - Kullanici degeri
            all_values: List[float] - Tum degerler

        Returns:
            float - Percentile (0-100)
        """
        if not all_values:
            return 50.0

        # Daha dusuk olan deger sayisi
        lower_count = sum(1 for v in all_values if v < value)
        equal_count = sum(1 for v in all_values if v == value)

        # Percentile formulu
        percentile = ((lower_count + 0.5 * equal_count) / len(all_values)) * 100

        return round(percentile, 1)

    async def calculate_percentiles(
        self,
        user_id: UUID,
        period_start: date,
        period_end: date,
    ) -> dict[str, float]:
        """
        Kullanici percentile'larini hesapla (REQ-7.2).

        Args:
            user_id: UUID - Kullanici ID
            period_start: date - Baslangic
            period_end: date - Bitis

        Returns:
            Dict - Percentile'lar
        """
        # Kullanici verilerini getir
        user_query = (
            select(
                func.sum(DiaryEntry.success_count).label("total_success"),
                func.sum(DiaryEntry.failure_count).label("total_failure"),
                func.sum(DiaryEntry.total_tasks).label("total_tasks"),
                func.sum(DiaryEntry.total_duration_minutes).label("total_duration"),
            )
            .where(
                and_(
                    DiaryEntry.user_id == user_id,
                    DiaryEntry.date >= period_start,
                    DiaryEntry.date <= period_end,
                )
            )
        )

        result = await self.db.execute(user_query)
        user_row = result.first()

        if not user_row or not user_row.total_tasks:
            return {
                "success_rate_percentile": None,
                "speed_percentile": None,
                "quality_percentile": None,
                "overall_percentile": None,
            }

        # Kullanici metrikleri
        user_total_tasks = user_row.total_tasks
        user_success_rate = (user_row.total_success / user_total_tasks) * 100
        user_avg_duration = user_row.total_duration / user_total_tasks
        user_speed_score = max(0, 100 - (user_avg_duration - 10) * 0.9)

        # Peer verilerini getir
        peer_data = await self._get_peer_data(period_start, period_end, user_id)

        if len(peer_data) < self.K_ANONYMITY:
            return {
                "success_rate_percentile": None,
                "speed_percentile": None,
                "quality_percentile": None,
                "overall_percentile": None,
                "error": f"Yetersiz peer sayisi (min {self.K_ANONYMITY} gerekli)",
            }

        # Percentile'lari hesapla
        success_rates = [p["success_rate"] for p in peer_data]
        speed_scores = [p["speed_score"] for p in peer_data]

        success_percentile = self._calculate_percentile(user_success_rate, success_rates)
        speed_percentile = self._calculate_percentile(user_speed_score, speed_scores)

        # Quality: Success rate + consistency (simplified)
        quality_percentile = (success_percentile + speed_percentile) / 2

        # Overall
        overall_percentile = (success_percentile * 0.5 + speed_percentile * 0.3 + quality_percentile * 0.2)

        return {
            "success_rate_percentile": success_percentile,
            "speed_percentile": speed_percentile,
            "quality_percentile": round(quality_percentile, 1),
            "overall_percentile": round(overall_percentile, 1),
        }

    # =========================================================================
    # REQ-7.3: Strength Areas (Top 25%)
    # =========================================================================

    def _identify_strengths(
        self,
        percentiles: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        Guclu alanlari belirle (REQ-7.3).

        Top 25% (percentile >= 75)

        Args:
            percentiles: Dict - Percentile'lar

        Returns:
            List[Dict] - Guclu alanlar
        """
        strengths: list[dict[str, Any]] = []

        metrics = {
            "success_rate": ("Başarı Oranı", percentiles.get("success_rate_percentile")),
            "speed": ("Hız/Verimlilik", percentiles.get("speed_percentile")),
            "quality": ("Kalite", percentiles.get("quality_percentile")),
        }

        for metric_key, (metric_name, percentile) in metrics.items():
            if percentile is not None and percentile >= self.STRENGTH_THRESHOLD:
                strengths.append({
                    "skill": metric_key,
                    "name": metric_name,
                    "percentile": percentile,
                    "description": f"{metric_name}'nda üst %{100 - int(percentile)}'desiniz",
                })

        return strengths

    # =========================================================================
    # REQ-7.4: Improvement Areas (Bottom 25%)
    # =========================================================================

    def _identify_improvements(
        self,
        percentiles: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        Gelisim alanlarini belirle (REQ-7.4).

        Bottom 25% (percentile <= 25)

        Args:
            percentiles: Dict - Percentile'lar

        Returns:
            List[Dict] - Gelisim alanlari
        """
        improvements: list[dict[str, Any]] = []

        metrics = {
            "success_rate": (
                "Başarı Oranı",
                percentiles.get("success_rate_percentile"),
                "Görevleri daha küçük parçalara bölmeyi deneyin"
            ),
            "speed": (
                "Hız/Verimlilik",
                percentiles.get("speed_percentile"),
                "Pomodoro tekniği ile odaklanmayı artırın"
            ),
            "quality": (
                "Kalite",
                percentiles.get("quality_percentile"),
                "İşe başlamadan önce planlama yapın"
            ),
        }

        for metric_key, (metric_name, percentile, recommendation) in metrics.items():
            if percentile is not None and percentile <= self.IMPROVEMENT_THRESHOLD:
                improvements.append({
                    "skill": metric_key,
                    "name": metric_name,
                    "percentile": percentile,
                    "recommendation": recommendation,
                    "description": f"{metric_name}'nda alt %{int(percentile)}'desiniz",
                })

        return improvements

    # =========================================================================
    # REQ-7.5: Best Practice Learning
    # =========================================================================

    async def get_best_practices(
        self,
        period_start: date,
        period_end: date,
    ) -> list[str]:
        """
        Top performer stratejilerini analiz et (REQ-7.5).

        Args:
            period_start: date - Baslangic
            period_end: date - Bitis

        Returns:
            List[str] - Best practice'ler
        """
        # Peer verilerini getir
        peer_data = await self._get_peer_data(period_start, period_end)

        if len(peer_data) < self.K_ANONYMITY:
            return []

        # Top performers (success rate top 20%)
        sorted_peers = sorted(peer_data, key=lambda x: x["success_rate"], reverse=True)
        top_count = max(1, len(sorted_peers) // 5)
        top_performers = sorted_peers[:top_count]

        best_practices: list[str] = []

        # Analiz
        avg_tasks_top = sum(p["total_tasks"] for p in top_performers) / len(top_performers)
        avg_tasks_all = sum(p["total_tasks"] for p in peer_data) / len(peer_data)

        if avg_tasks_top < avg_tasks_all * 0.8:
            best_practices.append(
                "Yüksek performanslı kullanıcılar daha az görev alıyor ama daha odaklı çalışıyor"
            )
        elif avg_tasks_top > avg_tasks_all * 1.2:
            best_practices.append(
                "Yüksek performanslı kullanıcılar daha fazla görev tamamlıyor"
            )

        # Speed analizi
        avg_speed_top = sum(p["speed_score"] for p in top_performers) / len(top_performers)
        avg_speed_all = sum(p["speed_score"] for p in peer_data) / len(peer_data)

        if avg_speed_top > avg_speed_all * 1.1:
            best_practices.append(
                "Başarılı kullanıcılar görevleri daha hızlı tamamlıyor - küçük parçalara bölün"
            )

        # Entry count analizi
        avg_entries_top = sum(p["entry_count"] for p in top_performers) / len(top_performers)
        avg_entries_all = sum(p["entry_count"] for p in peer_data) / len(peer_data)

        if avg_entries_top > avg_entries_all * 1.2:
            best_practices.append(
                "Başarılı kullanıcılar günlüklerini daha düzenli tutuyor"
            )

        # Genel oneriler
        if not best_practices:
            best_practices = [
                "Günlük hedeflerinizi belirleyin ve takip edin",
                "Zorlayıcı görevleri sabah saatlerine planlayın",
                "Her gün için 3-5 ana görev belirleyin",
            ]

        return best_practices[:5]  # Max 5

    # =========================================================================
    # REQ-7.6: Differential Privacy
    # =========================================================================

    def _apply_differential_privacy(
        self,
        value: float,
    ) -> float:
        """
        Differential privacy uygula (REQ-7.6).

        Laplace mechanism ile noise ekle.

        Args:
            value: float - Orijinal deger

        Returns:
            float - Noise eklenmis deger
        """
        if DIFFPRIV_AVAILABLE:
            mechanism = Laplace(epsilon=self.EPSILON, sensitivity=self.SENSITIVITY)
            return mechanism.randomise(value)
        # Fallback: Basit noise
        noise = np.random.laplace(0, self.SENSITIVITY / self.EPSILON)
        return value + noise

    def _verify_k_anonymity(
        self,
        peer_count: int,
    ) -> bool:
        """
        K-anonymity dogrula (REQ-7.6).

        Args:
            peer_count: int - Peer sayisi

        Returns:
            bool - K-anonymity saglaniyor mu
        """
        return peer_count >= self.K_ANONYMITY

    # =========================================================================
    # Main Comparison Method
    # =========================================================================

    async def compare_performance(
        self,
        user_id: UUID,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> PeerComparison | None:
        """
        Performans karsilastirmasi yap ve kaydet.

        Args:
            user_id: UUID - Kullanici ID
            period_start: Optional[date] - Baslangic (default: 30 gun once)
            period_end: Optional[date] - Bitis (default: bugun)

        Returns:
            Optional[PeerComparison] - Karsilastirma sonucu veya None
        """
        # Default tarih araligi
        if not period_end:
            period_end = date.today()
        if not period_start:
            period_start = period_end - timedelta(days=30)

        # Peer verilerini getir
        peer_data = await self._get_peer_data(period_start, period_end, user_id)

        # K-anonymity kontrolu
        if not self._verify_k_anonymity(len(peer_data)):
            return None

        # Percentile'lari hesapla
        percentiles = await self.calculate_percentiles(user_id, period_start, period_end)

        if percentiles.get("error"):
            return None

        # Guclu ve gelisim alanlarini belirle
        strengths = self._identify_strengths(percentiles)
        improvements = self._identify_improvements(percentiles)

        # Best practice'leri getir
        best_practices = await self.get_best_practices(period_start, period_end)

        # Peer group bilgileri (privacy ile)
        peer_avg_success = sum(p["success_rate"] for p in peer_data) / len(peer_data)
        peer_avg_success_noisy = self._apply_differential_privacy(peer_avg_success)

        # Karsilastirma kaydi olustur
        comparison = PeerComparison(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            success_rate_percentile=percentiles.get("success_rate_percentile"),
            speed_percentile=percentiles.get("speed_percentile"),
            quality_percentile=percentiles.get("quality_percentile"),
            overall_percentile=percentiles.get("overall_percentile"),
            strengths=strengths,
            improvements=improvements,
            best_practices=best_practices,
            is_anonymized=True,
            noise_added=True,
            k_anonymity=self.K_ANONYMITY,
            peer_group_size=len(peer_data),
            peer_group_avg_success_rate=round(peer_avg_success_noisy, 1),
        )

        self.db.add(comparison)
        await self.db.commit()
        await self.db.refresh(comparison)

        return comparison

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def get_comparisons(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> list[PeerComparison]:
        """
        Karsilastirma gecmisini getir.

        Args:
            user_id: UUID - Kullanici ID
            limit: int - Maksimum kayit sayisi

        Returns:
            List[PeerComparison] - Karsilastirma listesi
        """
        from sqlalchemy import desc

        query = (
            select(PeerComparison)
            .where(PeerComparison.user_id == user_id)
            .order_by(desc(PeerComparison.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_comparison_by_id(
        self,
        comparison_id: UUID,
        user_id: UUID,
    ) -> PeerComparison | None:
        """
        ID ile karsilastirma getir.

        Args:
            comparison_id: UUID - Karsilastirma ID
            user_id: UUID - Kullanici ID

        Returns:
            Optional[PeerComparison] - Karsilastirma veya None
        """
        query = select(PeerComparison).where(
            and_(
                PeerComparison.id == comparison_id,
                PeerComparison.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_comparison(
        self,
        user_id: UUID,
    ) -> PeerComparison | None:
        """
        En son karsilastirmayi getir.

        Args:
            user_id: UUID - Kullanici ID

        Returns:
            Optional[PeerComparison] - Karsilastirma veya None
        """
        from sqlalchemy import desc

        query = (
            select(PeerComparison)
            .where(PeerComparison.user_id == user_id)
            .order_by(desc(PeerComparison.created_at))
            .limit(1)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
