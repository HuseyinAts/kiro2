"""
Error Reporter and Improvement System

Bu modül, AI yanıt doğrulama hatalarını kategorize eder,
analiz eder ve iyileştirme önerileri sunar.

Features:
- Error categorization (agent, model, data)
- Error source identification
- Error frequency analysis
- Trend analysis
- Improvement suggestions with examples

Requirements: REQ-8.1 - REQ-8.6
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Hata kategorileri"""
    AGENT = "agent"           # Agent-specific hatalar
    MODEL = "model"           # LLM model hataları
    DATA = "data"             # Veri kaynaklı hatalar
    VALIDATION = "validation" # Doğrulama hataları
    CONSISTENCY = "consistency" # Tutarlılık hataları
    FACT_CHECK = "fact_check"   # Fact-checking hataları
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Hata şiddeti"""
    CRITICAL = "critical"  # Sistemin çalışmasını etkileyen
    HIGH = "high"          # Kullanıcı deneyimini ciddi etkileyen
    MEDIUM = "medium"      # Orta düzey etkili
    LOW = "low"            # Düşük etkili


class ValidationErrorRecord(BaseModel):
    """Doğrulama hatası kaydı"""
    error_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    category: ErrorCategory
    severity: ErrorSeverity
    agent_type: str
    error_message: str
    source: str  # Hatanın kaynağı (validator adı)
    response_id: str | None = None
    user_id: str | None = None
    context: dict = Field(default_factory=dict)


class ErrorTrend(BaseModel):
    """Hata trendi"""
    category: ErrorCategory
    count: int
    percentage_change: float  # Önceki döneme göre değişim
    period: str  # "daily", "weekly", "monthly"
    top_sources: list[str]


class ImprovementSuggestion(BaseModel):
    """İyileştirme önerisi"""
    category: ErrorCategory
    suggestion: str
    priority: int  # 1-5 (5 en yüksek)
    examples: list[str]
    estimated_impact: str  # "high", "medium", "low"


class TopErrorMessage(BaseModel):
    """Top hata mesajı"""
    message: str
    count: int


class ErrorReport(BaseModel):
    """Hata raporu"""
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: datetime
    period_end: datetime
    total_errors: int
    errors_by_category: dict[str, int]
    errors_by_severity: dict[str, int]
    errors_by_agent: dict[str, int]
    trends: list[ErrorTrend]
    suggestions: list[ImprovementSuggestion]
    top_error_messages: list[TopErrorMessage]


class ErrorReporter:
    """
    Hata raporlama ve iyileştirme sistemi.

    Doğrulama hatalarını toplar, kategorize eder,
    analiz eder ve iyileştirme önerileri sunar.
    """

    # Hata mesajı → kategori eşleştirmeleri
    ERROR_PATTERNS = {
        ErrorCategory.AGENT: [
            "agent", "validator", "learning_path", "study_buddy", "exam",
        ],
        ErrorCategory.MODEL: [
            "llm", "model", "generation", "inference", "token",
        ],
        ErrorCategory.DATA: [
            "database", "redis", "cache", "data", "storage",
        ],
        ErrorCategory.VALIDATION: [
            "validation", "invalid", "score", "threshold",
        ],
        ErrorCategory.CONSISTENCY: [
            "consistency", "contradiction", "history", "previous",
        ],
        ErrorCategory.FACT_CHECK: [
            "fact", "claim", "wikipedia", "meb", "rag", "verification",
        ],
    }

    # Kategori → iyileştirme önerileri
    IMPROVEMENT_TEMPLATES = {
        ErrorCategory.AGENT: [
            {
                "suggestion": "Agent-specific validation kurallarını gözden geçirin",
                "priority": 4,
                "examples": [
                    "LearningPathValidator'da MEB müfredat kontrolü eklendi",
                    "StudyBuddyValidator'da matematik doğrulama iyileştirildi",
                ],
                "estimated_impact": "high",
            },
        ],
        ErrorCategory.MODEL: [
            {
                "suggestion": "LLM model parametrelerini optimize edin",
                "priority": 5,
                "examples": [
                    "Temperature değeri düşürüldü (0.7 → 0.5)",
                    "Max tokens limiti artırıldı",
                ],
                "estimated_impact": "high",
            },
        ],
        ErrorCategory.DATA: [
            {
                "suggestion": "Veri kaynaklarının erişilebilirliğini kontrol edin",
                "priority": 3,
                "examples": [
                    "Redis bağlantı havuzu genişletildi",
                    "Database index'leri optimize edildi",
                ],
                "estimated_impact": "medium",
            },
        ],
        ErrorCategory.CONSISTENCY: [
            {
                "suggestion": "Tutarlılık kontrolü eşiklerini ayarlayın",
                "priority": 4,
                "examples": [
                    "Contradiction threshold 0.85'e çıkarıldı",
                    "History limit 10'dan 15'e artırıldı",
                ],
                "estimated_impact": "medium",
            },
        ],
        ErrorCategory.FACT_CHECK: [
            {
                "suggestion": "Fact-checking kaynaklarını güncelleyin",
                "priority": 5,
                "examples": [
                    "MEB müfredat verisi güncellendi",
                    "Wikipedia cache TTL artırıldı",
                ],
                "estimated_impact": "high",
            },
        ],
    }

    def __init__(self, max_history: int = 10000):
        """
        Args:
            max_history: Saklanacak maksimum hata sayısı
        """
        self.max_history = max_history
        self._errors: list[ValidationErrorRecord] = []
        self._error_counts: dict[str, int] = defaultdict(int)

    def record_error(
        self,
        error_message: str,
        source: str,
        agent_type: str,
        response_id: str | None = None,
        user_id: str | None = None,
        context: dict | None = None,
    ) -> ValidationErrorRecord:
        """
        Yeni hata kaydı oluştur.

        Args:
            error_message: Hata mesajı
            source: Hatanın kaynağı (validator adı)
            agent_type: Agent tipi
            response_id: İlgili yanıt ID'si
            user_id: İlgili kullanıcı ID'si
            context: Ek bağlam bilgisi

        Returns:
            ValidationErrorRecord: Oluşturulan hata kaydı
        """
        import uuid

        # Kategori belirle
        category = self._categorize_error(error_message, source)

        # Şiddet belirle
        severity = self._determine_severity(error_message, category)

        # Hata kaydı oluştur
        record = ValidationErrorRecord(
            error_id=str(uuid.uuid4()),
            category=category,
            severity=severity,
            agent_type=agent_type,
            error_message=error_message,
            source=source,
            response_id=response_id,
            user_id=user_id,
            context=context or {},
        )

        # Kaydet
        self._errors.append(record)
        self._error_counts[category.value] += 1

        # Limit kontrolü
        if len(self._errors) > self.max_history:
            self._errors = self._errors[-self.max_history:]

        logger.info(
            f"Error recorded: category={category.value}, "
            f"severity={severity.value}, source={source}"
        )

        return record

    def _categorize_error(
        self,
        error_message: str,
        source: str,
    ) -> ErrorCategory:
        """Hata mesajını kategorize et"""
        message_lower = error_message.lower()
        source_lower = source.lower()

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower or pattern in source_lower:
                    return category

        return ErrorCategory.UNKNOWN

    def _determine_severity(
        self,
        error_message: str,
        category: ErrorCategory,
    ) -> ErrorSeverity:
        """Hata şiddetini belirle"""
        message_lower = error_message.lower()

        # Kritik anahtar kelimeler
        critical_keywords = ["fatal", "critical", "crash", "fail", "exception"]
        if any(kw in message_lower for kw in critical_keywords):
            return ErrorSeverity.CRITICAL

        # Yüksek şiddet anahtar kelimeleri
        high_keywords = ["error", "invalid", "reject", "block"]
        if any(kw in message_lower for kw in high_keywords):
            return ErrorSeverity.HIGH

        # Orta şiddet - fact-check ve consistency hataları
        if category in [ErrorCategory.FACT_CHECK, ErrorCategory.CONSISTENCY]:
            return ErrorSeverity.MEDIUM

        return ErrorSeverity.LOW

    def get_error_frequency(
        self,
        period_hours: int = 24,
    ) -> dict[str, int]:
        """
        Belirli dönemdeki hata sıklığını al.

        Args:
            period_hours: Dönem (saat)

        Returns:
            Dict: Kategori → sayı
        """
        cutoff = datetime.now(UTC) - timedelta(hours=period_hours)

        frequency = defaultdict(int)
        for error in self._errors:
            if error.timestamp >= cutoff:
                frequency[error.category.value] += 1

        return dict(frequency)

    def analyze_trends(
        self,
        current_period_hours: int = 24,
        comparison_period_hours: int = 24,
    ) -> list[ErrorTrend]:
        """
        Hata trendlerini analiz et.

        Args:
            current_period_hours: Güncel dönem
            comparison_period_hours: Karşılaştırma dönemi

        Returns:
            List[ErrorTrend]: Trend listesi
        """
        now = datetime.now(UTC)
        current_cutoff = now - timedelta(hours=current_period_hours)
        comparison_cutoff = current_cutoff - timedelta(hours=comparison_period_hours)

        # Güncel dönem sayıları
        current_counts = defaultdict(int)
        current_sources = defaultdict(lambda: defaultdict(int))

        for error in self._errors:
            if error.timestamp >= current_cutoff:
                current_counts[error.category.value] += 1
                current_sources[error.category.value][error.source] += 1

        # Karşılaştırma dönemi sayıları
        comparison_counts = defaultdict(int)

        for error in self._errors:
            if comparison_cutoff <= error.timestamp < current_cutoff:
                comparison_counts[error.category.value] += 1

        # Trendleri hesapla
        trends = []
        for category in ErrorCategory:
            current = current_counts.get(category.value, 0)
            comparison = comparison_counts.get(category.value, 0)

            if comparison > 0:
                change = ((current - comparison) / comparison) * 100
            elif current > 0:
                change = 100.0
            else:
                change = 0.0

            # Top sources
            sources = current_sources.get(category.value, {})
            top_sources = sorted(
                sources.keys(),
                key=lambda x: sources[x],
                reverse=True,
            )[:3]

            trends.append(ErrorTrend(
                category=category,
                count=current,
                percentage_change=round(change, 2),
                period="daily" if current_period_hours == 24 else f"{current_period_hours}h",
                top_sources=top_sources,
            ))

        return trends

    def generate_suggestions(
        self,
        period_hours: int = 24,
    ) -> list[ImprovementSuggestion]:
        """
        İyileştirme önerileri oluştur.

        Args:
            period_hours: Analiz dönemi

        Returns:
            List[ImprovementSuggestion]: Öneri listesi
        """
        frequency = self.get_error_frequency(period_hours)
        suggestions = []

        # En sık hata kategorilerine göre öneriler
        sorted_categories = sorted(
            frequency.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for category_str, count in sorted_categories:
            if count == 0:
                continue

            try:
                category = ErrorCategory(category_str)
            except ValueError:
                continue

            templates = self.IMPROVEMENT_TEMPLATES.get(category, [])

            for template in templates:
                suggestions.append(ImprovementSuggestion(
                    category=category,
                    suggestion=template["suggestion"],
                    priority=template["priority"],
                    examples=template["examples"],
                    estimated_impact=template["estimated_impact"],
                ))

        # Önceliğe göre sırala
        suggestions.sort(key=lambda x: x.priority, reverse=True)

        return suggestions

    def generate_report(
        self,
        period_hours: int = 24,
    ) -> ErrorReport:
        """
        Kapsamlı hata raporu oluştur.

        Args:
            period_hours: Rapor dönemi

        Returns:
            ErrorReport: Hata raporu
        """
        import uuid

        now = datetime.now(UTC)
        cutoff = now - timedelta(hours=period_hours)

        # Dönem içindeki hatalar
        period_errors = [
            e for e in self._errors
            if e.timestamp >= cutoff
        ]

        # Kategori bazında sayımlar
        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        by_agent = defaultdict(int)
        message_counts = defaultdict(int)

        for error in period_errors:
            by_category[error.category.value] += 1
            by_severity[error.severity.value] += 1
            by_agent[error.agent_type] += 1
            # Mesajın ilk 100 karakterini say
            short_msg = error.error_message[:100]
            message_counts[short_msg] += 1

        # Top error messages
        top_messages = sorted(
            [TopErrorMessage(message=k, count=v) for k, v in message_counts.items()],
            key=lambda x: x.count,
            reverse=True,
        )[:10]

        # Trendler ve öneriler
        trends = self.analyze_trends(period_hours, period_hours)
        suggestions = self.generate_suggestions(period_hours)

        return ErrorReport(
            report_id=str(uuid.uuid4()),
            period_start=cutoff,
            period_end=now,
            total_errors=len(period_errors),
            errors_by_category=dict(by_category),
            errors_by_severity=dict(by_severity),
            errors_by_agent=dict(by_agent),
            trends=trends,
            suggestions=suggestions,
            top_error_messages=top_messages,
        )

    def get_errors_by_response(
        self,
        response_id: str,
    ) -> list[ValidationErrorRecord]:
        """Belirli yanıta ait hataları al"""
        return [
            e for e in self._errors
            if e.response_id == response_id
        ]

    def get_errors_by_user(
        self,
        user_id: str,
        limit: int = 100,
    ) -> list[ValidationErrorRecord]:
        """Belirli kullanıcıya ait hataları al"""
        user_errors = [
            e for e in self._errors
            if e.user_id == user_id
        ]
        return user_errors[-limit:]

    def clear_old_errors(
        self,
        older_than_hours: int = 168,  # 7 gün
    ):
        """Eski hataları temizle"""
        cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
        self._errors = [
            e for e in self._errors
            if e.timestamp >= cutoff
        ]
        logger.info(f"Cleared errors older than {older_than_hours} hours")


# Global instance
_global_reporter: ErrorReporter | None = None


def get_error_reporter() -> ErrorReporter:
    """Global error reporter instance'ı al"""
    global _global_reporter
    if _global_reporter is None:
        _global_reporter = ErrorReporter()
    return _global_reporter
