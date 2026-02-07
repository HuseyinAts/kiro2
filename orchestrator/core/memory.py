"""
KIRO2 Orchestrator - Memory Management (Project-Scoped, Kalıcı)
===============================================================
Memory = Kalıcı öğrenimler (ADVISORY ONLY)

KRİTİK KURAL: Memory SADECE kanıtlanmış sonuçlardan yazılır.
- Green test + review geçtiyse → Memory'ye yazılabilir
- Tahmin/varsayım → Memory'ye YAZILMAZ
"""

from __future__ import annotations
import json
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field, asdict

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

Base = declarative_base()


class LessonType(str, Enum):
    """Öğrenilen ders tipleri"""
    ERROR_RESOLUTION = "error_resolution"  # Hata nasıl çözüldü
    PATTERN_RISK = "pattern_risk"          # Riskli dosya/modül desenleri
    STRATEGY_SUCCESS = "strategy_success"  # Başarılı strateji
    ROUTING_PREFERENCE = "routing_preference"  # Model/ajan tercihi
    QUALITY_GATE_INSIGHT = "quality_gate_insight"  # Kalite kapısı öğrenimi


class ConfidenceLevel(str, Enum):
    """Güven seviyesi (kanıt gücü)"""
    LOW = "low"        # 1-2 başarılı örnek
    MEDIUM = "medium"  # 3-5 başarılı örnek
    HIGH = "high"      # 6+ başarılı örnek
    VERIFIED = "verified"  # Manuel doğrulanmış


@dataclass
class LessonEvidence:
    """Bir dersin kanıtı"""
    run_id: str
    task_id: str
    timestamp: datetime
    gates_passed: list[str]
    iterations_to_green: int
    cost: float
    
    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "gates_passed": self.gates_passed,
            "iterations_to_green": self.iterations_to_green,
            "cost": self.cost,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> LessonEvidence:
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class LessonModel(Base):
    """SQLAlchemy model for lessons"""
    __tablename__ = "orchestrator_lessons"
    
    id = Column(String(64), primary_key=True)
    lesson_type = Column(String(32), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)  # error_type, file_pattern, etc.
    description = Column(Text, nullable=False)
    
    # Kanıt ve güven
    evidence_count = Column(Integer, default=1)
    confidence = Column(String(16), default="low")
    evidence_data = Column(JSON, default=list)
    
    # Uygulama
    suggested_action = Column(Text)
    success_rate = Column(Integer, default=0)  # 0-100
    
    # Meta
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Denetim
    last_applied_run_id = Column(String(64))
    times_applied = Column(Integer, default=0)
    times_successful = Column(Integer, default=0)


class RoutingPolicyModel(Base):
    """Routing policy kayıtları (self-improvement)"""
    __tablename__ = "orchestrator_routing_policies"
    
    id = Column(String(64), primary_key=True)
    task_type = Column(String(32), nullable=False, index=True)
    
    # Model tercihleri
    primary_model = Column(String(32), nullable=False)
    fallback_model = Column(String(32))
    
    # Performans metrikleri
    success_rate = Column(Integer, default=50)  # 0-100
    avg_iterations = Column(Integer, default=3)
    avg_cost = Column(Integer, default=50)  # cents
    sample_count = Column(Integer, default=0)
    
    # Son güncelleme
    updated_at = Column(DateTime, default=datetime.utcnow)
    updated_reason = Column(Text)


@dataclass
class Lesson:
    """Öğrenilen bir ders (Memory item)"""
    id: str
    lesson_type: LessonType
    category: str
    description: str
    
    evidence: list[LessonEvidence] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    suggested_action: Optional[str] = None
    success_rate: int = 0
    
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_evidence(self, evidence: LessonEvidence) -> None:
        """Kanıt ekle ve güven seviyesini güncelle"""
        self.evidence.append(evidence)
        count = len(self.evidence)
        
        # Güven seviyesi hesaplama
        if count >= 6:
            self.confidence = ConfidenceLevel.HIGH
        elif count >= 3:
            self.confidence = ConfidenceLevel.MEDIUM
        else:
            self.confidence = ConfidenceLevel.LOW
        
        # Başarı oranı güncelle
        successful = sum(1 for e in self.evidence if e.iterations_to_green <= 3)
        self.success_rate = int((successful / count) * 100) if count > 0 else 0


class MemoryStore:
    """
    PostgreSQL tabanlı Memory (kalıcı öğrenim) deposu.
    
    KRİTİK: Bu sınıf SADECE kanıtlanmış sonuçları saklar.
    Bir dersin Memory'ye yazılabilmesi için:
    1. İlgili run'ın TÜM quality gate'leri geçmiş olmalı
    2. Kanıt (evidence) sağlanmış olmalı
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self._session_factory: Optional[sessionmaker] = None
    
    async def initialize(self) -> None:
        """Tabloları oluştur"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    def _get_session(self) -> AsyncSession:
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._session_factory()
    
    async def save_lesson(
        self,
        lesson: Lesson,
        evidence: LessonEvidence,
        gates_all_passed: bool
    ) -> bool:
        """
        Ders kaydet - SADECE kanıtlanmış sonuçlar için.
        
        Args:
            lesson: Kaydedilecek ders
            evidence: Kanıt verisi
            gates_all_passed: Tüm kalite kapıları geçti mi?
            
        Returns:
            True if saved, False if rejected
        """
        # KRİTİK KONTROL: Kanıt olmadan yazma YOK
        if not gates_all_passed:
            return False
        
        lesson.add_evidence(evidence)
        
        async with self._get_session() as session:
            # Mevcut kaydı bul veya yeni oluştur
            existing = await session.get(LessonModel, lesson.id)
            
            if existing:
                existing.evidence_count = len(lesson.evidence)
                existing.confidence = lesson.confidence.value
                existing.evidence_data = [e.to_dict() for e in lesson.evidence]
                existing.success_rate = lesson.success_rate
                existing.updated_at = datetime.utcnow()
            else:
                model = LessonModel(
                    id=lesson.id,
                    lesson_type=lesson.lesson_type.value,
                    category=lesson.category,
                    description=lesson.description,
                    evidence_count=len(lesson.evidence),
                    confidence=lesson.confidence.value,
                    evidence_data=[e.to_dict() for e in lesson.evidence],
                    suggested_action=lesson.suggested_action,
                    success_rate=lesson.success_rate,
                )
                session.add(model)
            
            await session.commit()
        
        return True
    
    async def get_lessons_for_task(
        self,
        task_type: str,
        file_patterns: list[str],
        min_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    ) -> list[Lesson]:
        """
        Görev için ilgili dersleri getir (ADVISORY ONLY).
        
        Bu bilgiler SADECE öneri amaçlıdır.
        Kararlar STATE'e bakılarak alınır, bu bilgiler sadece bağlam sağlar.
        """
        async with self._get_session() as session:
            stmt = select(LessonModel).where(
                LessonModel.is_active == True,
                LessonModel.confidence.in_([
                    c.value for c in ConfidenceLevel 
                    if list(ConfidenceLevel).index(c) >= list(ConfidenceLevel).index(min_confidence)
                ])
            )
            
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            lessons = []
            for m in models:
                lesson = Lesson(
                    id=m.id,
                    lesson_type=LessonType(m.lesson_type),
                    category=m.category,
                    description=m.description,
                    confidence=ConfidenceLevel(m.confidence),
                    suggested_action=m.suggested_action,
                    success_rate=m.success_rate,
                    is_active=m.is_active,
                    created_at=m.created_at,
                )
                # Evidence'ları yükle
                for e_data in (m.evidence_data or []):
                    lesson.evidence.append(LessonEvidence.from_dict(e_data))
                lessons.append(lesson)
            
            return lessons
    
    async def get_routing_policy(self, task_type: str) -> Optional[dict]:
        """Routing policy getir (self-improvement sonucu)"""
        async with self._get_session() as session:
            policy = await session.get(RoutingPolicyModel, task_type)
            if policy:
                return {
                    "task_type": policy.task_type,
                    "primary_model": policy.primary_model,
                    "fallback_model": policy.fallback_model,
                    "success_rate": policy.success_rate,
                    "avg_iterations": policy.avg_iterations,
                    "avg_cost": policy.avg_cost,
                    "sample_count": policy.sample_count,
                }
            return None
    
    async def update_routing_policy(
        self,
        task_type: str,
        model: str,
        success: bool,
        iterations: int,
        cost: float,
        reason: str
    ) -> None:
        """
        Routing policy güncelle (self-improvement).
        
        Bu fonksiyon SADECE kanıtlanmış sonuçlara dayanarak çağrılmalı.
        """
        async with self._get_session() as session:
            policy = await session.get(RoutingPolicyModel, task_type)
            
            if policy:
                # Mevcut istatistikleri güncelle
                total = policy.sample_count + 1
                policy.success_rate = int(
                    (policy.success_rate * policy.sample_count + (100 if success else 0)) / total
                )
                policy.avg_iterations = int(
                    (policy.avg_iterations * policy.sample_count + iterations) / total
                )
                policy.avg_cost = int(
                    (policy.avg_cost * policy.sample_count + int(cost * 100)) / total
                )
                policy.sample_count = total
                policy.updated_reason = reason
            else:
                policy = RoutingPolicyModel(
                    id=task_type,
                    task_type=task_type,
                    primary_model=model,
                    success_rate=100 if success else 0,
                    avg_iterations=iterations,
                    avg_cost=int(cost * 100),
                    sample_count=1,
                    updated_reason=reason,
                )
                session.add(policy)
            
            await session.commit()
    
    async def close(self) -> None:
        """Bağlantıyı kapat"""
        await self.engine.dispose()


# Singleton instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store(database_url: str = None) -> MemoryStore:
    """Memory store singleton'ını al"""
    global _memory_store
    if _memory_store is None:
        if database_url is None:
            from orchestrator.config import get_config
            database_url = get_config().postgres.async_url
        _memory_store = MemoryStore(database_url)
    return _memory_store
