"""
KIRO2 Event Schema Definitions
Mikroservisler arası iletişim için event şemaları
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MicroserviceEventType(Enum):
    """Mikroservisler arası event tipleri"""

    # Exam Service Events (Port 8001)
    EXAM_STARTED = "exam.started"
    EXAM_COMPLETED = "exam.completed"
    EXAM_PAUSED = "exam.paused"
    EXAM_RESUMED = "exam.resumed"
    ANSWER_SUBMITTED = "exam.answer.submitted"
    ANSWER_CHANGED = "exam.answer.changed"
    TIME_WARNING = "exam.time.warning"
    TIME_EXPIRED = "exam.time.expired"

    # Question Generation Events (Port 8002)
    QUESTION_GENERATED = "question.generated"
    QUESTION_APPROVED = "question.approved"
    QUESTION_REJECTED = "question.rejected"
    QUESTION_CALIBRATED = "question.calibrated"
    BATCH_GENERATION_STARTED = "question.batch.started"
    BATCH_GENERATION_COMPLETED = "question.batch.completed"
    QUALITY_SCORE_UPDATED = "question.quality.updated"

    # IRT/CAT Service Events (Port 8003)
    ABILITY_ESTIMATED = "irt.ability.estimated"
    CALIBRATION_STARTED = "irt.calibration.started"
    CALIBRATION_COMPLETED = "irt.calibration.completed"
    NEXT_ITEM_SELECTED = "cat.next_item.selected"
    STOPPING_RULE_MET = "cat.stopping_rule.met"
    THETA_UPDATED = "irt.theta.updated"
    ITEM_PARAMETERS_UPDATED = "irt.item_params.updated"

    # AI Service Events (Port 8004)
    CHAT_MESSAGE_RECEIVED = "ai.chat.received"
    CHAT_RESPONSE_GENERATED = "ai.chat.response"
    AGENT_INVOKED = "ai.agent.invoked"
    AGENT_COMPLETED = "ai.agent.completed"
    NLP_ANALYSIS_COMPLETED = "ai.nlp.completed"
    RAG_QUERY_PROCESSED = "ai.rag.processed"
    EMBEDDING_GENERATED = "ai.embedding.generated"

    # Learning Path Events (Port 8005)
    PATH_GENERATED = "learning.path.generated"
    PATH_UPDATED = "learning.path.updated"
    NODE_COMPLETED = "learning.node.completed"
    PROGRESS_UPDATED = "learning.progress.updated"
    RECOMMENDATION_GENERATED = "learning.recommendation.generated"
    ZPD_CALCULATED = "learning.zpd.calculated"
    FSRS_REVIEW_SCHEDULED = "learning.fsrs.scheduled"


class ServiceName(Enum):
    """Mikroservis isimleri"""
    GATEWAY = "api-gateway"
    EXAM = "exam-service"
    QUESTION = "question-service"
    IRT = "irt-service"
    AI = "ai-service"
    LEARNING_PATH = "learning-path-service"
    MONOLITH = "kiro2-monolith"


@dataclass
class ServiceEvent:
    """Mikroservisler arası event base class"""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: MicroserviceEventType = None
    source_service: ServiceName = ServiceName.MONOLITH
    target_service: ServiceName | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None
    causation_id: str | None = None
    user_id: int | None = None
    session_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if self.event_type else None,
            "source_service": self.source_service.value,
            "target_service": self.target_service.value if self.target_service else None,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "payload": self.payload,
            "metadata": self.metadata,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceEvent":
        data = data.copy()
        if data.get("event_type"):
            data["event_type"] = MicroserviceEventType(data["event_type"])
        data["source_service"] = ServiceName(data["source_service"])
        if data.get("target_service"):
            data["target_service"] = ServiceName(data["target_service"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


# Exam Service Events
@dataclass
class ExamStartedEvent(ServiceEvent):
    """Sınav başlatıldığında yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.EXAM_STARTED
    source_service: ServiceName = ServiceName.EXAM

    def __post_init__(self):
        self.metadata["exam_type"] = self.payload.get("exam_type", "TYT")
        self.metadata["question_count"] = self.payload.get("question_count", 0)


@dataclass
class ExamCompletedEvent(ServiceEvent):
    """Sınav tamamlandığında yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.EXAM_COMPLETED
    source_service: ServiceName = ServiceName.EXAM
    target_service: ServiceName = ServiceName.LEARNING_PATH


@dataclass
class AnswerSubmittedEvent(ServiceEvent):
    """Cevap gönderildiğinde yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.ANSWER_SUBMITTED
    source_service: ServiceName = ServiceName.EXAM
    target_service: ServiceName = ServiceName.IRT


# Question Service Events
@dataclass
class QuestionGeneratedEvent(ServiceEvent):
    """Yeni soru üretildiğinde yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.QUESTION_GENERATED
    source_service: ServiceName = ServiceName.QUESTION


@dataclass
class QuestionCalibratedEvent(ServiceEvent):
    """Soru IRT parametreleri kalibre edildiğinde yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.QUESTION_CALIBRATED
    source_service: ServiceName = ServiceName.IRT
    target_service: ServiceName = ServiceName.QUESTION


# IRT/CAT Service Events
@dataclass
class AbilityEstimatedEvent(ServiceEvent):
    """Öğrenci yetenek tahmini yapıldığında yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.ABILITY_ESTIMATED
    source_service: ServiceName = ServiceName.IRT
    target_service: ServiceName = ServiceName.LEARNING_PATH

    def __post_init__(self):
        self.metadata["theta"] = self.payload.get("theta", 0.0)
        self.metadata["se"] = self.payload.get("standard_error", 0.5)


@dataclass
class NextItemSelectedEvent(ServiceEvent):
    """CAT algoritması sonraki soruyu seçtiğinde yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.NEXT_ITEM_SELECTED
    source_service: ServiceName = ServiceName.IRT
    target_service: ServiceName = ServiceName.EXAM


# AI Service Events
@dataclass
class ChatResponseGeneratedEvent(ServiceEvent):
    """AI chat yanıtı üretildiğinde yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.CHAT_RESPONSE_GENERATED
    source_service: ServiceName = ServiceName.AI


@dataclass
class NLPAnalysisCompletedEvent(ServiceEvent):
    """NLP analizi tamamlandığında yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.NLP_ANALYSIS_COMPLETED
    source_service: ServiceName = ServiceName.AI


# Learning Path Events
@dataclass
class PathGeneratedEvent(ServiceEvent):
    """Öğrenme yolu oluşturulduğunda yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.PATH_GENERATED
    source_service: ServiceName = ServiceName.LEARNING_PATH


@dataclass
class ProgressUpdatedEvent(ServiceEvent):
    """Öğrenci ilerlemesi güncellendiğinde yayınlanır"""
    event_type: MicroserviceEventType = MicroserviceEventType.PROGRESS_UPDATED
    source_service: ServiceName = ServiceName.LEARNING_PATH


# Event Registry
EVENT_REGISTRY = {
    MicroserviceEventType.EXAM_STARTED: ExamStartedEvent,
    MicroserviceEventType.EXAM_COMPLETED: ExamCompletedEvent,
    MicroserviceEventType.ANSWER_SUBMITTED: AnswerSubmittedEvent,
    MicroserviceEventType.QUESTION_GENERATED: QuestionGeneratedEvent,
    MicroserviceEventType.QUESTION_CALIBRATED: QuestionCalibratedEvent,
    MicroserviceEventType.ABILITY_ESTIMATED: AbilityEstimatedEvent,
    MicroserviceEventType.NEXT_ITEM_SELECTED: NextItemSelectedEvent,
    MicroserviceEventType.CHAT_RESPONSE_GENERATED: ChatResponseGeneratedEvent,
    MicroserviceEventType.NLP_ANALYSIS_COMPLETED: NLPAnalysisCompletedEvent,
    MicroserviceEventType.PATH_GENERATED: PathGeneratedEvent,
    MicroserviceEventType.PROGRESS_UPDATED: ProgressUpdatedEvent,
}


def create_event(event_type: MicroserviceEventType, **kwargs) -> ServiceEvent:
    """Event factory"""
    event_class = EVENT_REGISTRY.get(event_type, ServiceEvent)
    return event_class(event_type=event_type, **kwargs)


__all__ = [
    "EVENT_REGISTRY",
    "AbilityEstimatedEvent",
    "AnswerSubmittedEvent",
    "ChatResponseGeneratedEvent",
    "ExamCompletedEvent",
    "ExamStartedEvent",
    "MicroserviceEventType",
    "NLPAnalysisCompletedEvent",
    "NextItemSelectedEvent",
    "PathGeneratedEvent",
    "ProgressUpdatedEvent",
    "QuestionCalibratedEvent",
    "QuestionGeneratedEvent",
    "ServiceEvent",
    "ServiceName",
    "create_event",
]
