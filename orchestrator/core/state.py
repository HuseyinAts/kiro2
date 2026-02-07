"""
KIRO2 Orchestrator - State Management (Run-Scoped)
==================================================
State = O anki akışın gerçek durumu (SOURCE OF TRUTH)
Memory = Kalıcı öğrenimler (ADVISORY ONLY)

Prensip: Memory ASLA State'i override edemez.
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod

import redis.asyncio as redis


class TaskStatus(str, Enum):
    """Görev durumları"""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    QUALITY_GATES = "quality_gates"
    REVIEWING = "reviewing"
    FIXING = "fixing"
    BLOCKED = "blocked"  # Human intervention required
    COMPLETED = "completed"
    FAILED = "failed"


class GateResult(str, Enum):
    """Kalite kapısı sonuçları"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    AUTO_FIXED = "auto_fixed"


@dataclass
class QualityGateState:
    """Tek bir kalite kapısının durumu"""
    name: str
    status: GateResult = GateResult.SKIPPED
    attempts: int = 0
    max_attempts: int = 3
    error_fingerprint: Optional[str] = None
    last_error: Optional[str] = None
    auto_fix_applied: bool = False
    duration_ms: int = 0
    
    def record_failure(self, error: str) -> None:
        """Hatayı kaydet ve fingerprint oluştur"""
        self.attempts += 1
        self.last_error = error
        self.error_fingerprint = self._compute_fingerprint(error)
        self.status = GateResult.FAILED
    
    def _compute_fingerprint(self, error: str) -> str:
        """Hata fingerprint'i hesapla (no-progress detection için)"""
        # test_name + error_line + error_type hash'i
        normalized = error.strip().lower()[:500]
        return hashlib.sha256(f"{self.name}:{normalized}".encode()).hexdigest()[:16]
    
    def is_exhausted(self) -> bool:
        """Maksimum deneme sayısına ulaşıldı mı?"""
        return self.attempts >= self.max_attempts


@dataclass
class DiffStats:
    """Değişiklik istatistikleri"""
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    
    # Limitler (Doğru Kod prensibi)
    MAX_FILES_PER_ITERATION: int = 5
    MAX_LINES_PER_ITERATION: int = 200
    MAX_LINES_TOTAL: int = 500
    
    def is_within_limits(self) -> bool:
        """Diff limitleri içinde mi?"""
        return (
            self.files_changed <= self.MAX_FILES_PER_ITERATION and
            (self.lines_added + self.lines_removed) <= self.MAX_LINES_PER_ITERATION
        )
    
    def exceeds_total_limit(self, cumulative_lines: int) -> bool:
        """Toplam limit aşıldı mı?"""
        return cumulative_lines > self.MAX_LINES_TOTAL


@dataclass
class RunState:
    """
    Tek bir görev çalıştırmasının durumu (Run-Scoped State)
    
    Bu STATE objesi SOURCE OF TRUTH'tur.
    Tüm kararlar bu state'e bakılarak alınır.
    Memory sadece öneri/bağlam sağlar, STATE'i override EDEMEZ.
    """
    # Kimlik
    run_id: str
    task_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Durum
    status: TaskStatus = TaskStatus.PENDING
    current_iteration: int = 0
    max_iterations: int = 10
    
    # Plan
    plan_summary: Optional[str] = None
    scope_files: list[str] = field(default_factory=list)
    risk_level: str = "medium"  # low, medium, high, critical
    
    # Kalite Kapıları
    quality_gates: dict[str, QualityGateState] = field(default_factory=dict)
    
    # Diff Tracking
    current_diff: DiffStats = field(default_factory=DiffStats)
    cumulative_lines_changed: int = 0
    
    # Error Tracking (No-Progress Detection)
    errors: list[str] = field(default_factory=list)  # full error messages
    error_history: list[str] = field(default_factory=list)  # fingerprints
    consecutive_same_errors: int = 0
    NO_PROGRESS_THRESHOLD: int = 4  # Aynı hata 4 kez → BLOCKED
    
    # Seçilen Model/Ajan
    selected_model: Optional[str] = None
    selected_agent: Optional[str] = None
    
    # Sonuç
    result_summary: Optional[str] = None
    lesson_learned: Optional[str] = None
    lesson_written_to_memory: bool = False
    
    def __post_init__(self):
        """Varsayılan kalite kapılarını oluştur"""
        if not self.quality_gates:
            self.quality_gates = {
                "lint": QualityGateState(name="lint", max_attempts=3),
                "typecheck": QualityGateState(name="typecheck", max_attempts=3),
                "unit_test": QualityGateState(name="unit_test", max_attempts=3),
                "integration": QualityGateState(name="integration", max_attempts=2),
                "security": QualityGateState(name="security", max_attempts=1),
            }
    
    def record_error(self, gate_name: str, error: str) -> bool:
        """
        Hatayı kaydet ve no-progress kontrolü yap.
        Returns: True if should continue, False if BLOCKED
        """
        gate = self.quality_gates.get(gate_name)
        if not gate:
            return True
        
        gate.record_failure(error)
        fingerprint = gate.error_fingerprint
        
        # No-progress detection
        if self.error_history and self.error_history[-1] == fingerprint:
            self.consecutive_same_errors += 1
        else:
            self.consecutive_same_errors = 1
        
        self.error_history.append(fingerprint)
        
        # BLOCKED kontrolü
        if self.consecutive_same_errors >= self.NO_PROGRESS_THRESHOLD:
            self.status = TaskStatus.BLOCKED
            return False
        
        return True
    
    def can_continue(self) -> bool:
        """Devam edilebilir mi?"""
        if self.status == TaskStatus.BLOCKED:
            return False
        if self.current_iteration >= self.max_iterations:
            return False
        if self.current_diff.exceeds_total_limit(self.cumulative_lines_changed):
            return False
        return True
    
    def increment_iteration(self) -> None:
        """Yeni iterasyona geç"""
        self.current_iteration += 1
        self.cumulative_lines_changed += (
            self.current_diff.lines_added + self.current_diff.lines_removed
        )
        self.current_diff = DiffStats()
    
    def all_gates_passed(self) -> bool:
        """Tüm zorunlu kapılar geçti mi?"""
        required_gates = ["lint", "typecheck", "unit_test"]
        return all(
            self.quality_gates.get(g, QualityGateState(name=g)).status == GateResult.PASSED
            for g in required_gates
        )
    
    def to_dict(self) -> dict[str, Any]:
        """JSON serialization için"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["status"] = self.status.value
        # QualityGateState'leri düzelt
        data["quality_gates"] = {
            k: {**asdict(v), "status": v.status.value}
            for k, v in self.quality_gates.items()
        }
        return data
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunState:
        """JSON'dan oluştur"""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["status"] = TaskStatus(data["status"])
        data["current_diff"] = DiffStats(**data.get("current_diff", {}))
        
        # QualityGateState'leri yeniden oluştur
        gates = {}
        for k, v in data.get("quality_gates", {}).items():
            v["status"] = GateResult(v["status"])
            gates[k] = QualityGateState(**v)
        data["quality_gates"] = gates
        
        return cls(**data)


class StateStore(ABC):
    """State depolama arayüzü"""
    
    @abstractmethod
    async def save(self, state: RunState) -> None:
        """State'i kaydet"""
        pass
    
    @abstractmethod
    async def load(self, run_id: str) -> Optional[RunState]:
        """State'i yükle"""
        pass
    
    @abstractmethod
    async def delete(self, run_id: str) -> None:
        """State'i sil"""
        pass


class RedisStateStore(StateStore):
    """
    Redis tabanlı State depolama.
    TTL: 24 saat (run-scoped, geçici)
    """

    def __init__(self, redis_url: Optional[str] = None):
        # Use config if no URL provided
        if redis_url is None:
            try:
                from orchestrator.config import get_config
                redis_url = get_config().redis.url
            except ImportError:
                redis_url = "redis://localhost:6379/0"
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self.ttl = timedelta(hours=24)
        self.key_prefix = "kiro2:state:"
    
    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    def _key(self, run_id: str) -> str:
        return f"{self.key_prefix}{run_id}"
    
    async def save(self, state: RunState) -> None:
        """State'i Redis'e kaydet (TTL ile)"""
        client = await self._get_client()
        key = self._key(state.run_id)
        data = json.dumps(state.to_dict())
        await client.setex(key, self.ttl, data)
    
    async def load(self, run_id: str) -> Optional[RunState]:
        """State'i Redis'ten yükle"""
        client = await self._get_client()
        key = self._key(run_id)
        data = await client.get(key)
        if data is None:
            return None
        return RunState.from_dict(json.loads(data))
    
    async def delete(self, run_id: str) -> None:
        """State'i sil"""
        client = await self._get_client()
        await client.delete(self._key(run_id))
    
    async def close(self) -> None:
        """Bağlantıyı kapat"""
        if self._client:
            await self._client.close()


# Singleton instance
_state_store: Optional[StateStore] = None


def get_state_store() -> StateStore:
    """State store singleton'ını al"""
    global _state_store
    if _state_store is None:
        _state_store = RedisStateStore()
    return _state_store
