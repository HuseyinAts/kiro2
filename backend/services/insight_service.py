"""
Claude Diary Plugin - Insight Service

Pattern detection ve insight extraction servisi (REQ-2).
scikit-learn ile pattern analysis, confidence scoring ve recommendation generation.
"""

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from models.diary import DiaryEntry, Insight, InsightCategory
from api.schemas.diary import (
    InsightCreate,
)


class InsightService:
    """
    Insight extraction servisi (REQ-2)

    Pattern detection ve insight generation:
    - Recurring success factors (REQ-2.1)
    - Failure root causes (REQ-2.2)
    - Correlations (REQ-2.3)
    - Confidence scoring >= 0.8 (REQ-2.4)
    - Actionable recommendations (REQ-2.5)
    - Categorization (REQ-2.6)
    """

    # Minimum confidence threshold (REQ-2.4)
    MIN_CONFIDENCE = 0.8

    # Categories (REQ-2.6)
    CATEGORIES = {
        InsightCategory.TECHNICAL: ["code", "bug", "test", "api", "database", "error"],
        InsightCategory.PROCESS: ["workflow", "planning", "time", "deadline", "task"],
        InsightCategory.COMMUNICATION: ["team", "review", "feedback", "discuss", "meeting"],
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize InsightService.

        Args:
            db: AsyncSession - SQLAlchemy async session
        """
        self.db = db

    # =========================================================================
    # REQ-2.1: Success Pattern Detection
    # =========================================================================

    def detect_success_patterns(
        self,
        entries: List[DiaryEntry],
        min_occurrences: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Tekrarlayan basari faktorlerini tespit et (REQ-2.1).

        Args:
            entries: List[DiaryEntry] - Gunluk kayitlari
            min_occurrences: int - Minimum tekrar sayisi

        Returns:
            List[Dict] - Basari patternleri
        """
        patterns: List[Dict[str, Any]] = []

        # Task tiplerini analiz et
        task_type_success: Dict[str, List[int]] = {}
        task_type_total: Dict[str, int] = Counter()

        for entry in entries:
            tasks_data = entry.tasks_data or []
            for task in tasks_data:
                task_type = task.get("task_type", "unknown")
                status = task.get("status", "unknown")

                task_type_total[task_type] += 1

                if task_type not in task_type_success:
                    task_type_success[task_type] = []

                task_type_success[task_type].append(1 if status == "success" else 0)

        # Success rate pattern'lerini hesapla
        for task_type, successes in task_type_success.items():
            total = task_type_total[task_type]
            if total >= min_occurrences:
                success_rate = sum(successes) / len(successes)
                if success_rate >= 0.7:  # %70+ basari orani
                    confidence = self._calculate_confidence(
                        evidence_count=total,
                        pattern_strength=success_rate
                    )
                    if confidence >= self.MIN_CONFIDENCE:
                        patterns.append({
                            "type": "task_type_success",
                            "task_type": task_type,
                            "success_rate": round(success_rate, 3),
                            "evidence_count": total,
                            "confidence": round(confidence, 3),
                            "description": f"'{task_type}' task tipi %{int(success_rate * 100)} basari oranina sahip",
                        })

        # Zaman bazli pattern'ler
        time_success = self._analyze_time_patterns(entries)
        patterns.extend(time_success)

        return patterns

    def _analyze_time_patterns(self, entries: List[DiaryEntry]) -> List[Dict[str, Any]]:
        """
        Zaman bazli basari patternlerini analiz et.

        Args:
            entries: List[DiaryEntry] - Gunluk kayitlari

        Returns:
            List[Dict] - Zaman patternleri
        """
        patterns: List[Dict[str, Any]] = []

        # Gun bazli basari oranlari
        day_success: Dict[int, List[float]] = {i: [] for i in range(7)}

        for entry in entries:
            day_of_week = entry.date.weekday()
            if entry.total_tasks > 0:
                success_rate = entry.success_count / entry.total_tasks
                day_success[day_of_week].append(success_rate)

        day_names = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]

        for day_idx, rates in day_success.items():
            if len(rates) >= 3:
                avg_rate = sum(rates) / len(rates)
                if avg_rate >= 0.75:  # %75+ basari orani
                    confidence = self._calculate_confidence(
                        evidence_count=len(rates),
                        pattern_strength=avg_rate
                    )
                    if confidence >= self.MIN_CONFIDENCE:
                        patterns.append({
                            "type": "day_success_pattern",
                            "day": day_names[day_idx],
                            "day_index": day_idx,
                            "success_rate": round(avg_rate, 3),
                            "evidence_count": len(rates),
                            "confidence": round(confidence, 3),
                            "description": f"{day_names[day_idx]} gunleri %{int(avg_rate * 100)} basari oranina sahip",
                        })

        return patterns

    # =========================================================================
    # REQ-2.2: Failure Root Cause Identification
    # =========================================================================

    def identify_failure_root_causes(
        self,
        entries: List[DiaryEntry],
        min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Basarisizlik root cause'larini belirle (REQ-2.2).

        Args:
            entries: List[DiaryEntry] - Gunluk kayitlari
            min_occurrences: int - Minimum tekrar sayisi

        Returns:
            List[Dict] - Root cause'lar
        """
        root_causes: List[Dict[str, Any]] = []

        # Challenge'lari analiz et
        challenge_keywords: Dict[str, int] = Counter()
        challenge_tasks: Dict[str, List[str]] = {}

        for entry in entries:
            challenges = entry.challenges or []
            for challenge in challenges:
                # Anahtar kelime cikar
                keywords = self._extract_keywords(challenge)
                for keyword in keywords:
                    challenge_keywords[keyword] += 1
                    if keyword not in challenge_tasks:
                        challenge_tasks[keyword] = []
                    challenge_tasks[keyword].append(challenge)

        # Pattern'leri olustur
        for keyword, count in challenge_keywords.items():
            if count >= min_occurrences:
                confidence = self._calculate_confidence(
                    evidence_count=count,
                    pattern_strength=min(count / 10, 1.0)  # Normalize
                )
                if confidence >= self.MIN_CONFIDENCE:
                    root_causes.append({
                        "type": "recurring_challenge",
                        "keyword": keyword,
                        "occurrence_count": count,
                        "examples": challenge_tasks[keyword][:3],
                        "confidence": round(confidence, 3),
                        "description": f"'{keyword}' ile ilgili {count} tekrarlayan sorun",
                        "root_cause": f"'{keyword}' kaynaklı tekrarlayan zorluklar tespit edildi",
                    })

        # Task failure pattern'leri
        failure_patterns = self._analyze_failure_patterns(entries, min_occurrences)
        root_causes.extend(failure_patterns)

        return root_causes

    def _analyze_failure_patterns(
        self,
        entries: List[DiaryEntry],
        min_occurrences: int
    ) -> List[Dict[str, Any]]:
        """
        Task failure patternlerini analiz et.

        Args:
            entries: List[DiaryEntry] - Gunluk kayitlari
            min_occurrences: int - Minimum tekrar sayisi

        Returns:
            List[Dict] - Failure patternleri
        """
        patterns: List[Dict[str, Any]] = []

        # Task tipi bazli failure'lar
        task_type_failures: Dict[str, int] = Counter()
        task_type_total: Dict[str, int] = Counter()

        for entry in entries:
            tasks_data = entry.tasks_data or []
            for task in tasks_data:
                task_type = task.get("task_type", "unknown")
                status = task.get("status", "unknown")
                task_type_total[task_type] += 1
                if status == "failure":
                    task_type_failures[task_type] += 1

        for task_type, failure_count in task_type_failures.items():
            total = task_type_total[task_type]
            if total >= min_occurrences and failure_count >= min_occurrences:
                failure_rate = failure_count / total
                if failure_rate >= 0.3:  # %30+ failure rate
                    confidence = self._calculate_confidence(
                        evidence_count=failure_count,
                        pattern_strength=failure_rate
                    )
                    if confidence >= self.MIN_CONFIDENCE:
                        patterns.append({
                            "type": "task_type_failure",
                            "task_type": task_type,
                            "failure_rate": round(failure_rate, 3),
                            "failure_count": failure_count,
                            "total_count": total,
                            "confidence": round(confidence, 3),
                            "description": f"'{task_type}' task tipi %{int(failure_rate * 100)} basarisizlik oranina sahip",
                            "root_cause": f"'{task_type}' task tipinde sistematik sorun",
                        })

        return patterns

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Metinden anahtar kelimeleri cikar.

        Args:
            text: str - Metin

        Returns:
            List[str] - Anahtar kelimeler
        """
        # Stop words (Turkce)
        stop_words = {
            "ve", "ile", "icin", "de", "da", "bu", "bir", "olan", "mi",
            "mu", "ise", "ama", "fakat", "ancak", "gibi", "kadar", "daha"
        }

        # Temizle ve tokenize et
        text_lower = text.lower()
        words = text_lower.split()

        # Filtreleme
        keywords = [
            word.strip(".,!?:;()[]{}\"'")
            for word in words
            if len(word) > 3 and word not in stop_words
        ]

        return keywords[:5]  # En fazla 5 keyword

    # =========================================================================
    # REQ-2.3: Correlation Detection
    # =========================================================================

    def detect_correlations(
        self,
        entries: List[DiaryEntry],
    ) -> List[Dict[str, Any]]:
        """
        Cause-effect iliskilerini tespit et (REQ-2.3).

        Args:
            entries: List[DiaryEntry] - Gunluk kayitlari

        Returns:
            List[Dict] - Korelasyonlar
        """
        correlations: List[Dict[str, Any]] = []

        if len(entries) < 5:
            return correlations

        # Duration vs Success correlation
        duration_correlation = self._calculate_duration_success_correlation(entries)
        if duration_correlation:
            correlations.append(duration_correlation)

        # Task count vs Success correlation
        count_correlation = self._calculate_count_success_correlation(entries)
        if count_correlation:
            correlations.append(count_correlation)

        return correlations

    def _calculate_duration_success_correlation(
        self,
        entries: List[DiaryEntry]
    ) -> Optional[Dict[str, Any]]:
        """
        Sure ile basari arasindaki korelasyonu hesapla.

        Args:
            entries: List[DiaryEntry] - Gunluk kayitlari

        Returns:
            Optional[Dict] - Korelasyon sonucu veya None
        """
        if len(entries) < 5:
            return None

        durations = []
        success_rates = []

        for entry in entries:
            if entry.total_tasks > 0:
                durations.append(entry.total_duration_minutes)
                success_rates.append(entry.success_count / entry.total_tasks)

        if len(durations) < 5:
            return None

        # Pearson correlation
        correlation = np.corrcoef(durations, success_rates)[0, 1]

        if np.isnan(correlation):
            return None

        # Anlamli korelasyon (|r| >= 0.5)
        if abs(correlation) >= 0.5:
            confidence = self._calculate_confidence(
                evidence_count=len(durations),
                pattern_strength=abs(correlation)
            )
            if confidence >= self.MIN_CONFIDENCE:
                direction = "pozitif" if correlation > 0 else "negatif"
                description = (
                    f"Calisma suresi ile basari arasinda {direction} korelasyon "
                    f"(r={round(correlation, 2)})"
                )
                return {
                    "type": "duration_success_correlation",
                    "correlation": round(correlation, 3),
                    "direction": direction,
                    "evidence_count": len(durations),
                    "confidence": round(confidence, 3),
                    "description": description,
                    "correlation_text": (
                        "Daha uzun calisma suresi daha yuksek basari getiriyor"
                        if correlation > 0
                        else "Daha kisa calisma suresi daha yuksek basari getiriyor"
                    ),
                }

        return None

    def _calculate_count_success_correlation(
        self,
        entries: List[DiaryEntry]
    ) -> Optional[Dict[str, Any]]:
        """
        Task sayisi ile basari arasindaki korelasyonu hesapla.

        Args:
            entries: List[DiaryEntry] - Gunluk kayitlari

        Returns:
            Optional[Dict] - Korelasyon sonucu veya None
        """
        if len(entries) < 5:
            return None

        counts = []
        success_rates = []

        for entry in entries:
            if entry.total_tasks > 0:
                counts.append(entry.total_tasks)
                success_rates.append(entry.success_count / entry.total_tasks)

        if len(counts) < 5:
            return None

        # Pearson correlation
        correlation = np.corrcoef(counts, success_rates)[0, 1]

        if np.isnan(correlation):
            return None

        # Anlamli korelasyon (|r| >= 0.5)
        if abs(correlation) >= 0.5:
            confidence = self._calculate_confidence(
                evidence_count=len(counts),
                pattern_strength=abs(correlation)
            )
            if confidence >= self.MIN_CONFIDENCE:
                direction = "pozitif" if correlation > 0 else "negatif"
                description = (
                    f"Task sayisi ile basari arasinda {direction} korelasyon "
                    f"(r={round(correlation, 2)})"
                )
                return {
                    "type": "count_success_correlation",
                    "correlation": round(correlation, 3),
                    "direction": direction,
                    "evidence_count": len(counts),
                    "confidence": round(confidence, 3),
                    "description": description,
                    "correlation_text": (
                        "Daha fazla task daha yuksek basari getiriyor"
                        if correlation > 0
                        else "Daha az task daha yuksek basari getiriyor (odaklanma etkisi)"
                    ),
                }

        return None

    # =========================================================================
    # REQ-2.4: Confidence Scoring
    # =========================================================================

    def _calculate_confidence(
        self,
        evidence_count: int,
        pattern_strength: float,
        base_confidence: float = 0.5
    ) -> float:
        """
        Confidence skoru hesapla (REQ-2.4).

        Confidence = base + (evidence_factor * strength_factor)

        Args:
            evidence_count: int - Kanit sayisi
            pattern_strength: float - Pattern gucü (0-1)
            base_confidence: float - Temel confidence (default: 0.5)

        Returns:
            float - Confidence skoru (0-1)
        """
        # Evidence factor: log scale, maksimum 0.25 katki
        evidence_factor = min(np.log(evidence_count + 1) / 10, 0.25)

        # Strength factor: dogrudan etki, maksimum 0.25 katki
        strength_factor = pattern_strength * 0.25

        confidence = base_confidence + evidence_factor + strength_factor

        return min(max(confidence, 0.0), 1.0)

    # =========================================================================
    # REQ-2.5: Actionable Recommendations
    # =========================================================================

    def generate_recommendations(
        self,
        patterns: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]],
        correlations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Actionable recommendationlar olustur (REQ-2.5).

        Args:
            patterns: List[Dict] - Basari patternleri
            root_causes: List[Dict] - Root cause'lar
            correlations: List[Dict] - Korelasyonlar

        Returns:
            List[Dict] - Recommendation'lar
        """
        recommendations: List[Dict[str, Any]] = []

        # Success pattern'lerden recommendation
        for pattern in patterns:
            if pattern["type"] == "task_type_success":
                recommendations.append({
                    "source": "success_pattern",
                    "priority": 2,
                    "recommendation": (
                        f"'{pattern['task_type']}' task tipinde yuksek basari gosteriyorsunuz. "
                        f"Bu tip tasklara daha fazla odaklanmayi dusunun."
                    ),
                    "confidence": pattern["confidence"],
                    "evidence_count": pattern["evidence_count"],
                })
            elif pattern["type"] == "day_success_pattern":
                recommendations.append({
                    "source": "time_pattern",
                    "priority": 2,
                    "recommendation": (
                        f"{pattern['day']} gunleri daha verimli calisiyorsunuz. "
                        f"Onemli tasklari bu gune planlayabilirsiniz."
                    ),
                    "confidence": pattern["confidence"],
                    "evidence_count": pattern["evidence_count"],
                })

        # Root cause'lardan recommendation
        for root_cause in root_causes:
            if root_cause["type"] == "recurring_challenge":
                recommendations.append({
                    "source": "root_cause",
                    "priority": 1,  # Yuksek oncelik
                    "recommendation": (
                        f"'{root_cause['keyword']}' ile ilgili tekrarlayan sorunlar var. "
                        f"Bu alana yonelik egitim veya arac gelistirmeyi dusunun."
                    ),
                    "confidence": root_cause["confidence"],
                    "evidence_count": root_cause["occurrence_count"],
                })
            elif root_cause["type"] == "task_type_failure":
                recommendations.append({
                    "source": "failure_pattern",
                    "priority": 1,
                    "recommendation": (
                        f"'{root_cause['task_type']}' task tipinde sistematik basarisizlik var. "
                        f"Bu tip tasklar icin yaklasimi gozden gecirin veya destek isteyin."
                    ),
                    "confidence": root_cause["confidence"],
                    "evidence_count": root_cause["failure_count"],
                })

        # Correlation'lardan recommendation
        for corr in correlations:
            if corr["type"] == "duration_success_correlation":
                if corr["direction"] == "negatif":
                    recommendations.append({
                        "source": "correlation",
                        "priority": 2,
                        "recommendation": (
                            "Kisa ve odakli calisma seanslarinda daha basarili oluyorsunuz. "
                            "Pomodoro teknigini deneyebilirsiniz."
                        ),
                        "confidence": corr["confidence"],
                        "evidence_count": corr["evidence_count"],
                    })
            elif corr["type"] == "count_success_correlation":
                if corr["direction"] == "negatif":
                    recommendations.append({
                        "source": "correlation",
                        "priority": 1,
                        "recommendation": (
                            "Daha az task ile daha basarili oluyorsunuz. "
                            "Gunluk task sayinizi sinirlamayi dusunun (3-5 task ideal)."
                        ),
                        "confidence": corr["confidence"],
                        "evidence_count": corr["evidence_count"],
                    })

        # Oncelik sirasina gore sirala
        recommendations.sort(key=lambda x: (x["priority"], -x["confidence"]))

        return recommendations

    # =========================================================================
    # REQ-2.6: Categorization
    # =========================================================================

    def categorize_insight(self, pattern: Dict[str, Any]) -> InsightCategory:
        """
        Insight'i kategorize et (REQ-2.6).

        Args:
            pattern: Dict - Pattern bilgisi

        Returns:
            InsightCategory - Kategori
        """
        # Description'dan anahtar kelime cikar
        description = pattern.get("description", "").lower()
        task_type = pattern.get("task_type", "").lower()
        keyword = pattern.get("keyword", "").lower()

        text_to_analyze = f"{description} {task_type} {keyword}"

        # Kategori eslesme skoru
        scores: Dict[InsightCategory, int] = {
            InsightCategory.TECHNICAL: 0,
            InsightCategory.PROCESS: 0,
            InsightCategory.COMMUNICATION: 0,
        }

        for category, keywords in self.CATEGORIES.items():
            for kw in keywords:
                if kw in text_to_analyze:
                    scores[category] += 1

        # En yuksek skorlu kategori
        max_category = max(scores, key=lambda k: scores[k])

        # Eger hicbir skor yoksa default PROCESS
        if scores[max_category] == 0:
            return InsightCategory.PROCESS

        return max_category

    # =========================================================================
    # Main Analysis Method
    # =========================================================================

    async def analyze_entries(
        self,
        user_id: UUID,
        entries: Optional[List[DiaryEntry]] = None,
        days: int = 30,
    ) -> List[Insight]:
        """
        Diary entry'leri analiz et ve insight'lar olustur.

        Args:
            user_id: UUID - Kullanici ID
            entries: Optional[List[DiaryEntry]] - Entry'ler (None ise DB'den cek)
            days: int - Analiz edilecek gun sayisi

        Returns:
            List[Insight] - Olusturulan insight'lar
        """
        # Entry'leri getir
        if entries is None:
            from datetime import timedelta
            from_date = datetime.now().date() - timedelta(days=days)

            query = select(DiaryEntry).where(
                and_(
                    DiaryEntry.user_id == user_id,
                    DiaryEntry.date >= from_date
                )
            ).order_by(desc(DiaryEntry.date))

            result = await self.db.execute(query)
            entries = list(result.scalars().all())

        if not entries:
            return []

        # Pattern'leri tespit et
        success_patterns = self.detect_success_patterns(entries)
        root_causes = self.identify_failure_root_causes(entries)
        correlations = self.detect_correlations(entries)

        # Recommendation'lar olustur
        recommendations = self.generate_recommendations(
            success_patterns, root_causes, correlations
        )

        # Insight'lar olustur
        insights: List[Insight] = []

        # Success pattern insight'lari
        for pattern in success_patterns:
            if pattern["confidence"] >= self.MIN_CONFIDENCE:
                category = self.categorize_insight(pattern)
                recommendation = next(
                    (r["recommendation"] for r in recommendations
                     if r.get("source") == "success_pattern" and
                     pattern.get("task_type") in r.get("recommendation", "")),
                    f"'{pattern.get('task_type', 'bu tip')}' tasklerle devam edin"
                )

                insight = Insight(
                    user_id=user_id,
                    diary_entry_id=entries[0].id,  # En son entry
                    category=category,
                    pattern=pattern["description"],
                    confidence=pattern["confidence"],
                    evidence_count=pattern["evidence_count"],
                    recommendation=recommendation,
                    priority=2,
                    evidence_data=[pattern],
                )
                insights.append(insight)

        # Root cause insight'lari
        for rc in root_causes:
            if rc["confidence"] >= self.MIN_CONFIDENCE:
                category = self.categorize_insight(rc)
                recommendation = next(
                    (r["recommendation"] for r in recommendations
                     if r.get("source") in ("root_cause", "failure_pattern")),
                    f"'{rc.get('keyword', 'bu alan')}' uzerine calisin"
                )

                insight = Insight(
                    user_id=user_id,
                    diary_entry_id=entries[0].id,
                    category=category,
                    pattern=rc["description"],
                    root_cause=rc.get("root_cause"),
                    confidence=rc["confidence"],
                    evidence_count=rc.get("occurrence_count", rc.get("failure_count", 1)),
                    recommendation=recommendation,
                    priority=1,
                    evidence_data=[rc],
                )
                insights.append(insight)

        # Correlation insight'lari
        for corr in correlations:
            if corr["confidence"] >= self.MIN_CONFIDENCE:
                recommendation = next(
                    (r["recommendation"] for r in recommendations
                     if r.get("source") == "correlation"),
                    "Calisma duzeni optimize edin"
                )

                insight = Insight(
                    user_id=user_id,
                    diary_entry_id=entries[0].id,
                    category=InsightCategory.PROCESS,
                    pattern=corr["description"],
                    correlation=corr.get("correlation_text"),
                    confidence=corr["confidence"],
                    evidence_count=corr["evidence_count"],
                    recommendation=recommendation,
                    priority=2,
                    evidence_data=[corr],
                )
                insights.append(insight)

        # Veritabanina kaydet
        for insight in insights:
            self.db.add(insight)

        await self.db.commit()

        # Refresh
        for insight in insights:
            await self.db.refresh(insight)

        return insights

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def get_insights(
        self,
        user_id: UUID,
        category: Optional[InsightCategory] = None,
        min_confidence: float = 0.8,
        limit: int = 20,
    ) -> List[Insight]:
        """
        Kullanici insight'larini getir.

        Args:
            user_id: UUID - Kullanici ID
            category: Optional[InsightCategory] - Kategori filtresi
            min_confidence: float - Minimum confidence
            limit: int - Maksimum kayit sayisi

        Returns:
            List[Insight] - Insight listesi
        """
        conditions = [
            Insight.user_id == user_id,
            Insight.confidence >= min_confidence
        ]

        if category:
            conditions.append(Insight.category == category)

        query = (
            select(Insight)
            .where(and_(*conditions))
            .order_by(desc(Insight.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_insight(
        self,
        user_id: UUID,
        data: InsightCreate,
    ) -> Insight:
        """
        Yeni insight olustur.

        Args:
            user_id: UUID - Kullanici ID
            data: InsightCreate - Insight verileri

        Returns:
            Insight - Olusturulan insight
        """
        insight = Insight(
            user_id=user_id,
            diary_entry_id=data.diary_entry_id,
            category=data.category,
            pattern=data.pattern,
            confidence=data.confidence,
            recommendation=data.recommendation,
            root_cause=data.root_cause,
            correlation=data.correlation,
            evidence_data=data.evidence_data or [],
            evidence_count=len(data.evidence_data) if data.evidence_data else 1,
        )

        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)

        return insight

    async def get_insight_by_id(
        self,
        insight_id: UUID,
        user_id: UUID,
    ) -> Optional[Insight]:
        """
        ID ile insight getir.

        Args:
            insight_id: UUID - Insight ID
            user_id: UUID - Kullanici ID

        Returns:
            Optional[Insight] - Insight veya None
        """
        query = select(Insight).where(
            and_(
                Insight.id == insight_id,
                Insight.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_insight(self, insight_id: UUID, user_id: UUID) -> bool:
        """
        Insight sil.

        Args:
            insight_id: UUID - Insight ID
            user_id: UUID - Kullanici ID

        Returns:
            bool - Basari durumu
        """
        insight = await self.get_insight_by_id(insight_id, user_id)
        if not insight:
            return False

        await self.db.delete(insight)
        await self.db.commit()
        return True
