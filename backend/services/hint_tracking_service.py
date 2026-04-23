"""
İpucu Kullanım Takip Servisi
Requirements: REQ-51.35 (İpucu kullanım takibi)

Bu servis:
- İpucu kullanımını kaydeder
- Öğrenci bazlı istatistikler tutar
- İpucu kullanım paternlerini analiz eder
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class HintUsage:
    """İpucu kullanım kaydı"""

    student_id: str
    problem_id: str
    step_number: int
    hint_level: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "problem_id": self.problem_id,
            "step_number": self.step_number,
            "hint_level": self.hint_level,
            "timestamp": self.timestamp,
        }


@dataclass
class StudentHintStats:
    """Öğrenci ipucu istatistikleri"""

    student_id: str
    total_hints_used: int = 0
    hints_by_level: dict[int, int] = field(default_factory=lambda: {1: 0, 2: 0, 3: 0})
    problems_with_hints: list[str] = field(default_factory=list)
    average_hint_level: float = 0.0
    hint_dependency_score: float = 0.0  # 0-1 arası, yüksek = çok bağımlı

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "total_hints_used": self.total_hints_used,
            "hints_by_level": self.hints_by_level,
            "problems_with_hints": self.problems_with_hints,
            "average_hint_level": self.average_hint_level,
            "hint_dependency_score": self.hint_dependency_score,
        }


class HintTrackingService:
    """İpucu takip servisi"""

    def __init__(self):
        # In-memory storage (production'da database kullanılmalı)
        self.hint_usage_log: list[HintUsage] = []
        self.student_stats: dict[str, StudentHintStats] = {}
        logger.info("HintTrackingService initialized")

    def track_hint_usage(
        self, student_id: str, problem_id: str, step_number: int, hint_level: int
    ) -> HintUsage:
        """
        İpucu kullanımını kaydet

        Args:
            student_id: Öğrenci ID'si
            problem_id: Problem ID'si
            step_number: Adım numarası
            hint_level: İpucu seviyesi (1-3)

        Returns:
            HintUsage: Kayıt objesi
        """
        # Kayıt oluştur
        usage = HintUsage(
            student_id=student_id,
            problem_id=problem_id,
            step_number=step_number,
            hint_level=hint_level,
        )

        # Log'a ekle
        self.hint_usage_log.append(usage)

        # İstatistikleri güncelle
        self._update_student_stats(student_id, problem_id, hint_level)

        logger.info(
            f"Hint tracked: Student {student_id}, Problem {problem_id}, "
            f"Step {step_number}, Level {hint_level}"
        )

        return usage

    def _update_student_stats(self, student_id: str, problem_id: str, hint_level: int):
        """Öğrenci istatistiklerini güncelle"""
        if student_id not in self.student_stats:
            self.student_stats[student_id] = StudentHintStats(student_id=student_id)

        stats = self.student_stats[student_id]

        # Toplam ipucu sayısını artır
        stats.total_hints_used += 1

        # Seviye bazlı sayacı artır
        stats.hints_by_level[hint_level] = stats.hints_by_level.get(hint_level, 0) + 1

        # Problem listesine ekle (unique)
        if problem_id not in stats.problems_with_hints:
            stats.problems_with_hints.append(problem_id)

        # Ortalama ipucu seviyesini hesapla
        total_weighted = sum(
            level * count for level, count in stats.hints_by_level.items()
        )
        stats.average_hint_level = total_weighted / stats.total_hints_used

        # Bağımlılık skorunu hesapla (0-1 arası)
        # Yüksek seviye ipuçları daha fazla bağımlılık gösterir
        level_3_ratio = stats.hints_by_level.get(3, 0) / max(stats.total_hints_used, 1)
        stats.hint_dependency_score = min(1.0, level_3_ratio * 2)

    def get_student_stats(self, student_id: str) -> StudentHintStats | None:
        """Öğrenci istatistiklerini getir"""
        return self.student_stats.get(student_id)

    def get_problem_hint_usage(
        self, problem_id: str, student_id: str | None = None
    ) -> list[HintUsage]:
        """
        Belirli bir problem için ipucu kullanımlarını getir

        Args:
            problem_id: Problem ID'si
            student_id: Opsiyonel öğrenci filtresi

        Returns:
            List[HintUsage]: İpucu kullanım listesi
        """
        usages = [
            usage for usage in self.hint_usage_log if usage.problem_id == problem_id
        ]

        if student_id:
            usages = [u for u in usages if u.student_id == student_id]

        return usages

    def get_step_hint_usage(
        self, problem_id: str, step_number: int, student_id: str | None = None
    ) -> list[HintUsage]:
        """
        Belirli bir adım için ipucu kullanımlarını getir

        Args:
            problem_id: Problem ID'si
            step_number: Adım numarası
            student_id: Opsiyonel öğrenci filtresi

        Returns:
            List[HintUsage]: İpucu kullanım listesi
        """
        usages = [
            usage
            for usage in self.hint_usage_log
            if usage.problem_id == problem_id and usage.step_number == step_number
        ]

        if student_id:
            usages = [u for u in usages if u.student_id == student_id]

        return usages

    def get_hint_level_distribution(
        self, student_id: str | None = None
    ) -> dict[int, int]:
        """
        İpucu seviye dağılımını getir

        Args:
            student_id: Opsiyonel öğrenci filtresi

        Returns:
            Dict[int, int]: Seviye -> Kullanım sayısı
        """
        usages = self.hint_usage_log
        if student_id:
            usages = [u for u in usages if u.student_id == student_id]

        distribution = defaultdict(int)
        for usage in usages:
            distribution[usage.hint_level] += 1

        return dict(distribution)

    def get_hint_usage_trends(self, student_id: str, limit: int = 10) -> dict:
        """
        Öğrencinin ipucu kullanım trendlerini analiz et

        Args:
            student_id: Öğrenci ID'si
            limit: Son kaç problem analiz edilecek

        Returns:
            Dict: Trend analizi
        """
        student_usages = [u for u in self.hint_usage_log if u.student_id == student_id]

        if not student_usages:
            return {"trend": "no_data", "message": "Henüz ipucu kullanımı yok"}

        # Son N problemi al
        recent_problems = list(set([u.problem_id for u in student_usages]))[-limit:]
        recent_usages = [u for u in student_usages if u.problem_id in recent_problems]

        # Trend analizi
        total_hints = len(recent_usages)
        level_3_count = sum(1 for u in recent_usages if u.hint_level == 3)
        level_3_ratio = level_3_count / total_hints if total_hints > 0 else 0

        # Trend belirleme
        if level_3_ratio > 0.5:
            trend = "high_dependency"
            message = "Detaylı ipuçlarına çok bağımlı - Daha fazla pratik gerekli"
        elif level_3_ratio > 0.3:
            trend = "moderate_dependency"
            message = "Orta seviye bağımlılık - İyi ilerleme"
        else:
            trend = "low_dependency"
            message = "Düşük bağımlılık - Mükemmel ilerleme!"

        return {
            "trend": trend,
            "message": message,
            "total_hints_used": total_hints,
            "level_3_ratio": level_3_ratio,
            "recent_problems_count": len(recent_problems),
            "recommendation": self._get_recommendation(trend),
        }

    def _get_recommendation(self, trend: str) -> str:
        """Trend'e göre öneri ver"""
        recommendations = {
            "high_dependency": "Daha basit problemlerle başla ve ipuçlara bakmadan çözmeyi dene",
            "moderate_dependency": "İyi gidiyorsun! İpuçları kullanmadan önce biraz daha düşünmeyi dene",
            "low_dependency": "Harika! Bağımsız problem çözme becerilerin gelişiyor",
            "no_data": "Problemleri çözmeye başla ve gerektiğinde ipuçlarını kullan",
        }
        return recommendations.get(trend, "Çalışmaya devam et!")

    def clear_student_data(self, student_id: str):
        """Öğrenci verilerini temizle"""
        self.hint_usage_log = [
            u for u in self.hint_usage_log if u.student_id != student_id
        ]
        if student_id in self.student_stats:
            del self.student_stats[student_id]
        logger.info(f"Cleared hint data for student: {student_id}")


# Global instance
hint_tracking_service = HintTrackingService()
