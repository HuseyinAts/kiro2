"""
KIRO2 Policy Change Log - Politika Değişiklik Kaydı
===================================================
Tüm politika değişikliklerinin audit trail'i.
Değişiklik geçmişi, rollback ve analiz desteği sağlar.

Özellikler:
- Değişiklik kaydı (add, remove, modify, toggle)
- Rollback desteği
- Değişiklik analizi ve raporlama
- JSON export/import
- Retention policy
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import hashlib
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Değişiklik tipleri"""
    POLICY_ADDED = "policy_added"
    POLICY_REMOVED = "policy_removed"
    POLICY_MODIFIED = "policy_modified"
    POLICY_ENABLED = "policy_enabled"
    POLICY_DISABLED = "policy_disabled"
    SEVERITY_CHANGED = "severity_changed"
    THRESHOLD_CHANGED = "threshold_changed"
    AUTO_FIX_TOGGLED = "auto_fix_toggled"
    CATEGORY_CHANGED = "category_changed"
    BULK_UPDATE = "bulk_update"
    ROLLBACK = "rollback"
    SYSTEM_RESET = "system_reset"


class ChangeSource(Enum):
    """Değişiklik kaynağı"""
    MANUAL = "manual"
    AUTOMATED = "automated"
    LEARNING = "learning"
    ROLLBACK = "rollback"
    MIGRATION = "migration"
    EMERGENCY = "emergency"
    SCHEDULED = "scheduled"


@dataclass
class PolicySnapshot:
    """Politika anlık durumu (rollback için)"""
    policy_id: str
    enabled: bool
    severity: str
    category: str
    thresholds: dict = field(default_factory=dict)
    auto_fix_enabled: bool = False
    custom_config: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "PolicySnapshot":
        return cls(**data)


@dataclass
class ChangeRecord:
    """Tek bir değişiklik kaydı"""
    change_id: str
    timestamp: datetime
    change_type: ChangeType
    source: ChangeSource
    policy_id: str
    before_state: Optional[PolicySnapshot]
    after_state: Optional[PolicySnapshot]
    reason: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "change_id": self.change_id,
            "timestamp": self.timestamp.isoformat(),
            "change_type": self.change_type.value,
            "source": self.source.value,
            "policy_id": self.policy_id,
            "before_state": self.before_state.to_dict() if self.before_state else None,
            "after_state": self.after_state.to_dict() if self.after_state else None,
            "reason": self.reason,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChangeRecord":
        return cls(
            change_id=data["change_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            change_type=ChangeType(data["change_type"]),
            source=ChangeSource(data["source"]),
            policy_id=data["policy_id"],
            before_state=PolicySnapshot.from_dict(data["before_state"]) if data.get("before_state") else None,
            after_state=PolicySnapshot.from_dict(data["after_state"]) if data.get("after_state") else None,
            reason=data.get("reason", ""),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ChangeStats:
    """Değişiklik istatistikleri"""
    total_changes: int = 0
    changes_by_type: dict = field(default_factory=dict)
    changes_by_source: dict = field(default_factory=dict)
    changes_by_policy: dict = field(default_factory=dict)
    rollback_count: int = 0
    last_change: Optional[datetime] = None
    most_changed_policy: Optional[str] = None


class PolicyChangeLog:
    """
    Politika değişiklik kaydı yöneticisi.
    
    Tüm politika değişikliklerini takip eder, audit trail sağlar,
    rollback desteği ve analiz yetenekleri sunar.
    """
    
    DEFAULT_RETENTION_DAYS = 90
    MAX_MEMORY_RECORDS = 10000
    
    def __init__(
        self,
        log_dir: Optional[Path] = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        auto_persist: bool = True
    ):
        self.log_dir = log_dir or Path("logs/policy_changes")
        self.retention_days = retention_days
        self.auto_persist = auto_persist
        
        self._records: list[ChangeRecord] = []
        self._policy_history: dict[str, list[str]] = defaultdict(list)
        self._snapshots: dict[str, PolicySnapshot] = {}
        self._lock = threading.RLock()
        self._change_counter = 0
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._load_existing_logs()
    
    def _generate_change_id(self) -> str:
        """Benzersiz değişiklik ID'si üret"""
        self._change_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        hash_input = f"{timestamp}-{self._change_counter}"
        return f"CHG-{hashlib.md5(hash_input.encode()).hexdigest()[:12].upper()}"
    
    def _load_existing_logs(self) -> None:
        """Mevcut log dosyalarını yükle"""
        try:
            for log_file in sorted(self.log_dir.glob("*.jsonl")):
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                record = ChangeRecord.from_dict(data)
                                self._records.append(record)
                                self._policy_history[record.policy_id].append(record.change_id)
                            except (json.JSONDecodeError, KeyError) as e:
                                logger.warning(f"Geçersiz log satırı: {e}")
            
            if len(self._records) > self.MAX_MEMORY_RECORDS:
                self._records = self._records[-self.MAX_MEMORY_RECORDS:]
            
            logger.info(f"PolicyChangeLog: {len(self._records)} kayıt yüklendi")
        except Exception as e:
            logger.error(f"Log yükleme hatası: {e}")
    
    def log_change(
        self,
        change_type: ChangeType,
        source: ChangeSource,
        policy_id: str,
        before_state: Optional[PolicySnapshot] = None,
        after_state: Optional[PolicySnapshot] = None,
        reason: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Değişiklik kaydet.
        
        Returns:
            Değişiklik ID'si
        """
        with self._lock:
            change_id = self._generate_change_id()
            
            record = ChangeRecord(
                change_id=change_id,
                timestamp=datetime.now(),
                change_type=change_type,
                source=source,
                policy_id=policy_id,
                before_state=before_state,
                after_state=after_state,
                reason=reason,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {}
            )
            
            self._records.append(record)
            self._policy_history[policy_id].append(change_id)
            
            if after_state:
                self._snapshots[policy_id] = after_state
            
            if self.auto_persist:
                self._persist_record(record)
            
            logger.info(f"Değişiklik kaydedildi: {change_id} - {change_type.value} - {policy_id}")
            return change_id
    
    def _persist_record(self, record: ChangeRecord) -> None:
        """Kaydı dosyaya yaz"""
        try:
            log_file = self.log_dir / f"changes_{record.timestamp.strftime('%Y%m%d')}.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Kayıt persist hatası: {e}")
    
    def get_change(self, change_id: str) -> Optional[ChangeRecord]:
        """Belirli bir değişikliği getir"""
        with self._lock:
            for record in reversed(self._records):
                if record.change_id == change_id:
                    return record
            return None
    
    def get_policy_history(
        self,
        policy_id: str,
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> list[ChangeRecord]:
        """Politika değişiklik geçmişini getir"""
        with self._lock:
            change_ids = self._policy_history.get(policy_id, [])
            records = []
            
            for cid in reversed(change_ids):
                if len(records) >= limit:
                    break
                record = self.get_change(cid)
                if record:
                    if since and record.timestamp < since:
                        continue
                    records.append(record)
            
            return records
    
    def get_recent_changes(
        self,
        limit: int = 100,
        change_type: Optional[ChangeType] = None,
        source: Optional[ChangeSource] = None,
        policy_id: Optional[str] = None
    ) -> list[ChangeRecord]:
        """Son değişiklikleri getir (filtreli)"""
        with self._lock:
            results = []
            
            for record in reversed(self._records):
                if len(results) >= limit:
                    break
                
                if change_type and record.change_type != change_type:
                    continue
                if source and record.source != source:
                    continue
                if policy_id and record.policy_id != policy_id:
                    continue
                
                results.append(record)
            
            return results
    
    def get_changes_in_range(
        self,
        start: datetime,
        end: datetime
    ) -> list[ChangeRecord]:
        """Belirli zaman aralığındaki değişiklikleri getir"""
        with self._lock:
            return [
                r for r in self._records
                if start <= r.timestamp <= end
            ]
    
    def get_snapshot(self, policy_id: str) -> Optional[PolicySnapshot]:
        """Politikanın son durumunu getir"""
        with self._lock:
            return self._snapshots.get(policy_id)
    
    def get_snapshot_at(
        self,
        policy_id: str,
        timestamp: datetime
    ) -> Optional[PolicySnapshot]:
        """Belirli bir zamandaki politika durumunu getir"""
        with self._lock:
            history = self.get_policy_history(policy_id, limit=1000)
            
            for record in history:
                if record.timestamp <= timestamp:
                    return record.after_state or record.before_state
            
            return None
    
    def can_rollback(self, policy_id: str) -> bool:
        """Politika rollback edilebilir mi?"""
        with self._lock:
            history = self.get_policy_history(policy_id, limit=2)
            return len(history) >= 2
    
    def get_rollback_target(self, policy_id: str) -> Optional[PolicySnapshot]:
        """Rollback hedef durumunu getir"""
        with self._lock:
            history = self.get_policy_history(policy_id, limit=2)
            
            if len(history) >= 2:
                return history[1].before_state or history[1].after_state
            
            return None
    
    def prepare_rollback(
        self,
        policy_id: str,
        reason: str = "Manuel rollback"
    ) -> Optional[dict]:
        """
        Rollback hazırla (önizleme).
        
        Returns:
            Rollback bilgileri veya None
        """
        with self._lock:
            if not self.can_rollback(policy_id):
                return None
            
            current = self._snapshots.get(policy_id)
            target = self.get_rollback_target(policy_id)
            
            if not target:
                return None
            
            return {
                "policy_id": policy_id,
                "current_state": current.to_dict() if current else None,
                "target_state": target.to_dict(),
                "reason": reason,
                "changes": self._compare_snapshots(current, target)
            }
    
    def _compare_snapshots(
        self,
        before: Optional[PolicySnapshot],
        after: Optional[PolicySnapshot]
    ) -> dict:
        """İki snapshot'ı karşılaştır"""
        changes = {}
        
        if not before and after:
            return {"action": "create", "fields": after.to_dict()}
        if before and not after:
            return {"action": "delete", "fields": before.to_dict()}
        if not before and not after:
            return {"action": "none"}
        
        before_dict = before.to_dict()
        after_dict = after.to_dict()
        
        for key in set(before_dict.keys()) | set(after_dict.keys()):
            if before_dict.get(key) != after_dict.get(key):
                changes[key] = {
                    "before": before_dict.get(key),
                    "after": after_dict.get(key)
                }
        
        return {"action": "modify", "fields": changes}
    
    def get_stats(
        self,
        since: Optional[datetime] = None
    ) -> ChangeStats:
        """Değişiklik istatistiklerini hesapla"""
        with self._lock:
            stats = ChangeStats()
            type_counts = defaultdict(int)
            source_counts = defaultdict(int)
            policy_counts = defaultdict(int)
            
            records = self._records
            if since:
                records = [r for r in records if r.timestamp >= since]
            
            for record in records:
                stats.total_changes += 1
                type_counts[record.change_type.value] += 1
                source_counts[record.source.value] += 1
                policy_counts[record.policy_id] += 1
                
                if record.change_type == ChangeType.ROLLBACK:
                    stats.rollback_count += 1
            
            stats.changes_by_type = dict(type_counts)
            stats.changes_by_source = dict(source_counts)
            stats.changes_by_policy = dict(policy_counts)
            
            if records:
                stats.last_change = max(r.timestamp for r in records)
            
            if policy_counts:
                stats.most_changed_policy = max(policy_counts, key=policy_counts.get)
            
            return stats
    
    def cleanup_old_records(self) -> int:
        """Eski kayıtları temizle (retention policy)"""
        with self._lock:
            cutoff = datetime.now() - timedelta(days=self.retention_days)
            
            old_count = len(self._records)
            self._records = [r for r in self._records if r.timestamp >= cutoff]
            
            removed = old_count - len(self._records)
            
            if removed > 0:
                self._rebuild_policy_history()
                logger.info(f"{removed} eski kayıt temizlendi")
            
            return removed
    
    def _rebuild_policy_history(self) -> None:
        """Policy history index'ini yeniden oluştur"""
        self._policy_history.clear()
        for record in self._records:
            self._policy_history[record.policy_id].append(record.change_id)
    
    def export_to_json(self, filepath: Path) -> int:
        """Tüm kayıtları JSON'a aktar"""
        with self._lock:
            data = {
                "exported_at": datetime.now().isoformat(),
                "total_records": len(self._records),
                "records": [r.to_dict() for r in self._records]
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"{len(self._records)} kayıt {filepath}'a aktarıldı")
            return len(self._records)
    
    def import_from_json(self, filepath: Path) -> int:
        """JSON'dan kayıtları içe aktar"""
        with self._lock:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            imported = 0
            existing_ids = {r.change_id for r in self._records}
            
            for record_data in data.get("records", []):
                if record_data["change_id"] not in existing_ids:
                    record = ChangeRecord.from_dict(record_data)
                    self._records.append(record)
                    self._policy_history[record.policy_id].append(record.change_id)
                    imported += 1
            
            self._records.sort(key=lambda r: r.timestamp)
            logger.info(f"{imported} kayıt içe aktarıldı")
            return imported
    
    def generate_audit_report(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> dict:
        """Audit raporu oluştur"""
        with self._lock:
            if not start:
                start = datetime.now() - timedelta(days=30)
            if not end:
                end = datetime.now()
            
            records = self.get_changes_in_range(start, end)
            stats = self.get_stats(since=start)
            
            critical_changes = [
                r for r in records
                if r.change_type in (
                    ChangeType.POLICY_REMOVED,
                    ChangeType.SYSTEM_RESET,
                    ChangeType.ROLLBACK
                ) or r.source == ChangeSource.EMERGENCY
            ]
            
            return {
                "report_generated": datetime.now().isoformat(),
                "period": {
                    "start": start.isoformat(),
                    "end": end.isoformat()
                },
                "summary": {
                    "total_changes": stats.total_changes,
                    "rollbacks": stats.rollback_count,
                    "critical_changes": len(critical_changes),
                    "most_changed_policy": stats.most_changed_policy,
                    "changes_by_type": stats.changes_by_type,
                    "changes_by_source": stats.changes_by_source
                },
                "critical_changes": [c.to_dict() for c in critical_changes],
                "top_changed_policies": dict(
                    sorted(
                        stats.changes_by_policy.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                )
            }
    
    def search_changes(
        self,
        query: str,
        fields: Optional[list[str]] = None
    ) -> list[ChangeRecord]:
        """Değişikliklerde arama yap"""
        with self._lock:
            if not fields:
                fields = ["policy_id", "reason", "change_type"]
            
            query_lower = query.lower()
            results = []
            
            for record in self._records:
                for field in fields:
                    value = getattr(record, field, None)
                    if value:
                        if isinstance(value, Enum):
                            value = value.value
                        if query_lower in str(value).lower():
                            results.append(record)
                            break
            
            return results
    
    def __len__(self) -> int:
        return len(self._records)
    
    def __repr__(self) -> str:
        return f"PolicyChangeLog(records={len(self._records)}, retention={self.retention_days}d)"


# Singleton instance
_change_log: Optional[PolicyChangeLog] = None


def get_change_log(
    log_dir: Optional[Path] = None,
    **kwargs
) -> PolicyChangeLog:
    """Global PolicyChangeLog instance'ı al"""
    global _change_log
    if _change_log is None:
        _change_log = PolicyChangeLog(log_dir=log_dir, **kwargs)
    return _change_log


def reset_change_log() -> None:
    """Change log'u sıfırla (test için)"""
    global _change_log
    _change_log = None
