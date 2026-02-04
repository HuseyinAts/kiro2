"""
KIRO2 Offline-First Data Synchronization System
Advanced offline data management and synchronization for mobile apps
Türkiye Üniversite Sınavları Hazırlık Platformu - Çevrimdışı Veri Senkronizasyon Sistemi
"""

import asyncio
import sqlite3
import json
import hashlib
import gzip
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Set, Callable
from enum import Enum
import uuid
import os
from pathlib import Path

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.MOBILE)
config = get_unified_config()


class SyncStatus(Enum):
    """Data synchronization status"""
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"
    ERROR = "error"
    OFFLINE = "offline"


class SyncDirection(Enum):
    """Sync direction"""
    UP = "up"          # Local to server
    DOWN = "down"      # Server to local
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    LATEST_WINS = "latest_wins"
    MERGE = "merge"
    MANUAL = "manual"


class DataPriority(Enum):
    """Data synchronization priority"""
    CRITICAL = "critical"   # User progress, exam results
    HIGH = "high"          # Study content, questions
    MEDIUM = "medium"      # Analytics, preferences
    LOW = "low"           # Logs, cache data


@dataclass
class SyncableEntity:
    """Base class for synchronizable data entities"""
    entity_id: str
    entity_type: str
    
    # Data
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Sync metadata
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_synced_at: Optional[datetime] = None
    
    # Sync properties
    sync_status: SyncStatus = SyncStatus.PENDING
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    priority: DataPriority = DataPriority.MEDIUM
    
    # Checksums for conflict detection
    local_checksum: Optional[str] = None
    server_checksum: Optional[str] = None
    
    # Conflict resolution
    has_conflicts: bool = False
    conflict_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.entity_id:
            self.entity_id = str(uuid.uuid4())
        self.calculate_checksum()
    
    def calculate_checksum(self) -> str:
        """Calculate data checksum for conflict detection"""
        data_str = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        checksum = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        self.local_checksum = checksum
        return checksum
    
    def update_data(self, new_data: Dict[str, Any], increment_version: bool = True) -> None:
        """Update entity data"""
        self.data.update(new_data)
        self.updated_at = datetime.now(timezone.utc)
        
        if increment_version:
            self.version += 1
        
        self.calculate_checksum()
        self.sync_status = SyncStatus.PENDING
    
    def mark_synced(self, server_checksum: Optional[str] = None) -> None:
        """Mark entity as synced"""
        self.sync_status = SyncStatus.SYNCED
        self.last_synced_at = datetime.now(timezone.utc)
        
        if server_checksum:
            self.server_checksum = server_checksum
    
    def detect_conflict(self, server_data: Dict[str, Any], server_checksum: str) -> bool:
        """Detect sync conflicts"""
        if self.server_checksum and self.server_checksum != server_checksum:
            if self.local_checksum != self.server_checksum:
                # Both local and server have changes
                self.has_conflicts = True
                self.conflict_data = {
                    "local_data": self.data.copy(),
                    "server_data": server_data.copy(),
                    "local_checksum": self.local_checksum,
                    "server_checksum": server_checksum,
                    "conflict_detected_at": datetime.now(timezone.utc).isoformat()
                }
                self.sync_status = SyncStatus.CONFLICT
                return True
        
        return False
    
    def resolve_conflict(self, resolution: ConflictResolution) -> bool:
        """Resolve sync conflict"""
        if not self.has_conflicts or not self.conflict_data:
            return False
        
        try:
            if resolution == ConflictResolution.SERVER_WINS:
                self.data = self.conflict_data["server_data"].copy()
            elif resolution == ConflictResolution.CLIENT_WINS:
                # Keep local data
                pass
            elif resolution == ConflictResolution.LATEST_WINS:
                # Compare timestamps and use latest
                local_time = self.updated_at
                server_updated = self.conflict_data.get("server_updated_at")
                if server_updated and datetime.fromisoformat(server_updated) > local_time:
                    self.data = self.conflict_data["server_data"].copy()
            elif resolution == ConflictResolution.MERGE:
                # Attempt to merge data
                merged_data = self._merge_data(self.data, self.conflict_data["server_data"])
                self.data = merged_data
            
            # Clear conflict
            self.has_conflicts = False
            self.conflict_data = None
            self.calculate_checksum()
            self.sync_status = SyncStatus.PENDING
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict for {self.entity_id}: {e}")
            return False
    
    def _merge_data(self, local_data: Dict[str, Any], server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge local and server data"""
        merged = local_data.copy()
        
        for key, server_value in server_data.items():
            if key not in merged:
                # New key from server
                merged[key] = server_value
            elif isinstance(server_value, dict) and isinstance(merged[key], dict):
                # Recursive merge for nested objects
                merged[key] = self._merge_data(merged[key], server_value)
            elif isinstance(server_value, list) and isinstance(merged[key], list):
                # Merge lists (combine and deduplicate)
                merged[key] = list(set(merged[key] + server_value))
            # For conflicting scalar values, keep local value
        
        return merged
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "data": self.data,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "sync_status": self.sync_status.value,
            "sync_direction": self.sync_direction.value,
            "priority": self.priority.value,
            "local_checksum": self.local_checksum,
            "server_checksum": self.server_checksum,
            "has_conflicts": self.has_conflicts,
            "conflict_data": self.conflict_data
        }


@dataclass
class SyncBatch:
    """Batch of entities to sync"""
    batch_id: str
    entities: List[SyncableEntity] = field(default_factory=list)
    
    # Batch properties
    priority: DataPriority = DataPriority.MEDIUM
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Progress tracking
    total_entities: int = 0
    synced_entities: int = 0
    failed_entities: int = 0
    conflict_entities: int = 0
    
    def __post_init__(self):
        if not self.batch_id:
            self.batch_id = str(uuid.uuid4())
        self.total_entities = len(self.entities)
    
    def add_entity(self, entity: SyncableEntity) -> None:
        """Add entity to batch"""
        self.entities.append(entity)
        self.total_entities = len(self.entities)
    
    def get_progress_percentage(self) -> float:
        """Get sync progress percentage"""
        if self.total_entities == 0:
            return 100.0
        
        completed = self.synced_entities + self.failed_entities
        return (completed / self.total_entities) * 100
    
    def is_completed(self) -> bool:
        """Check if batch sync is completed"""
        return (self.synced_entities + self.failed_entities) >= self.total_entities
    
    def get_summary(self) -> Dict[str, Any]:
        """Get batch summary"""
        return {
            "batch_id": self.batch_id,
            "total_entities": self.total_entities,
            "synced_entities": self.synced_entities,
            "failed_entities": self.failed_entities,
            "conflict_entities": self.conflict_entities,
            "progress_percentage": self.get_progress_percentage(),
            "is_completed": self.is_completed(),
            "priority": self.priority.value,
            "sync_direction": self.sync_direction.value,
            "created_at": self.created_at.isoformat()
        }


class OfflineDataStore:
    """Local SQLite database for offline data storage"""
    
    def __init__(self, db_path: str = "kiro2_offline.db"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize local database"""
        try:
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            # Create tables
            await self._create_tables()
            
            logger.info(f"Initialized offline data store at {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize offline data store: {e}")
            return False
    
    async def _create_tables(self) -> None:
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Syncable entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS syncable_entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                data TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_synced_at TEXT,
                sync_status TEXT NOT NULL DEFAULT 'pending',
                sync_direction TEXT NOT NULL DEFAULT 'bidirectional',
                priority TEXT NOT NULL DEFAULT 'medium',
                local_checksum TEXT,
                server_checksum TEXT,
                has_conflicts BOOLEAN DEFAULT FALSE,
                conflict_data TEXT
            )
        """)
        
        # Sync batches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_batches (
                batch_id TEXT PRIMARY KEY,
                priority TEXT NOT NULL,
                sync_direction TEXT NOT NULL,
                created_at TEXT NOT NULL,
                total_entities INTEGER DEFAULT 0,
                synced_entities INTEGER DEFAULT 0,
                failed_entities INTEGER DEFAULT 0,
                conflict_entities INTEGER DEFAULT 0
            )
        """)
        
        # Batch entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_entities (
                batch_id TEXT,
                entity_id TEXT,
                FOREIGN KEY (batch_id) REFERENCES sync_batches(batch_id),
                FOREIGN KEY (entity_id) REFERENCES syncable_entities(entity_id),
                PRIMARY KEY (batch_id, entity_id)
            )
        """)
        
        # Sync logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                log_id TEXT PRIMARY KEY,
                entity_id TEXT,
                batch_id TEXT,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                created_at TEXT NOT NULL,
                details TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON syncable_entities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_status ON syncable_entities(sync_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_priority ON syncable_entities(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON syncable_entities(updated_at)")
        
        self.connection.commit()
    
    async def store_entity(self, entity: SyncableEntity) -> bool:
        """Store syncable entity"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO syncable_entities (
                    entity_id, entity_type, data, version, created_at, updated_at,
                    last_synced_at, sync_status, sync_direction, priority,
                    local_checksum, server_checksum, has_conflicts, conflict_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.entity_id,
                entity.entity_type,
                json.dumps(entity.data),
                entity.version,
                entity.created_at.isoformat(),
                entity.updated_at.isoformat(),
                entity.last_synced_at.isoformat() if entity.last_synced_at else None,
                entity.sync_status.value,
                entity.sync_direction.value,
                entity.priority.value,
                entity.local_checksum,
                entity.server_checksum,
                entity.has_conflicts,
                json.dumps(entity.conflict_data) if entity.conflict_data else None
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store entity {entity.entity_id}: {e}")
            return False
    
    async def get_entity(self, entity_id: str) -> Optional[SyncableEntity]:
        """Get entity by ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM syncable_entities WHERE entity_id = ?", (entity_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_entity(row)
            
        except Exception as e:
            logger.error(f"Failed to get entity {entity_id}: {e}")
            return None
    
    async def get_entities_by_status(self, status: SyncStatus, limit: int = 100) -> List[SyncableEntity]:
        """Get entities by sync status"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM syncable_entities 
                WHERE sync_status = ? 
                ORDER BY priority DESC, updated_at ASC 
                LIMIT ?
            """, (status.value, limit))
            
            entities = []
            for row in cursor.fetchall():
                entity = self._row_to_entity(row)
                if entity:
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to get entities by status {status}: {e}")
            return []
    
    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[SyncableEntity]:
        """Get entities by type"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM syncable_entities 
                WHERE entity_type = ? 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (entity_type, limit))
            
            entities = []
            for row in cursor.fetchall():
                entity = self._row_to_entity(row)
                if entity:
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to get entities by type {entity_type}: {e}")
            return []
    
    def _row_to_entity(self, row: sqlite3.Row) -> Optional[SyncableEntity]:
        """Convert database row to SyncableEntity"""
        try:
            entity = SyncableEntity(
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                data=json.loads(row["data"]),
                version=row["version"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                last_synced_at=datetime.fromisoformat(row["last_synced_at"]) if row["last_synced_at"] else None,
                sync_status=SyncStatus(row["sync_status"]),
                sync_direction=SyncDirection(row["sync_direction"]),
                priority=DataPriority(row["priority"]),
                local_checksum=row["local_checksum"],
                server_checksum=row["server_checksum"],
                has_conflicts=bool(row["has_conflicts"]),
                conflict_data=json.loads(row["conflict_data"]) if row["conflict_data"] else None
            )
            
            return entity
            
        except Exception as e:
            logger.error(f"Failed to convert row to entity: {e}")
            return None
    
    async def delete_entity(self, entity_id: str) -> bool:
        """Delete entity"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM syncable_entities WHERE entity_id = ?", (entity_id,))
            self.connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {e}")
            return False
    
    async def store_batch(self, batch: SyncBatch) -> bool:
        """Store sync batch"""
        try:
            cursor = self.connection.cursor()
            
            # Store batch
            cursor.execute("""
                INSERT OR REPLACE INTO sync_batches (
                    batch_id, priority, sync_direction, created_at,
                    total_entities, synced_entities, failed_entities, conflict_entities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch.batch_id,
                batch.priority.value,
                batch.sync_direction.value,
                batch.created_at.isoformat(),
                batch.total_entities,
                batch.synced_entities,
                batch.failed_entities,
                batch.conflict_entities
            ))
            
            # Store batch entities
            for entity in batch.entities:
                cursor.execute("""
                    INSERT OR IGNORE INTO batch_entities (batch_id, entity_id)
                    VALUES (?, ?)
                """, (batch.batch_id, entity.entity_id))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store batch {batch.batch_id}: {e}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            cursor = self.connection.cursor()
            
            # Count entities by status
            cursor.execute("""
                SELECT sync_status, COUNT(*) as count 
                FROM syncable_entities 
                GROUP BY sync_status
            """)
            status_counts = {row["sync_status"]: row["count"] for row in cursor.fetchall()}
            
            # Count entities by type
            cursor.execute("""
                SELECT entity_type, COUNT(*) as count 
                FROM syncable_entities 
                GROUP BY entity_type
            """)
            type_counts = {row["entity_type"]: row["count"] for row in cursor.fetchall()}
            
            # Get database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "total_entities": sum(status_counts.values()),
                "status_counts": status_counts,
                "type_counts": type_counts,
                "database_size_mb": db_size / (1024 * 1024),
                "database_path": str(self.db_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old synced data"""
        try:
            cursor = self.connection.cursor()
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
            
            cursor.execute("""
                DELETE FROM syncable_entities 
                WHERE sync_status = 'synced' 
                AND last_synced_at < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            self.connection.commit()
            
            logger.info(f"Cleaned up {deleted_count} old synced entities")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0


class DataSynchronizer:
    """Main data synchronization engine"""
    
    def __init__(self, data_store: OfflineDataStore):
        self.data_store = data_store
        self.is_online = False
        self.sync_in_progress = False
        self.sync_callbacks: List[Callable] = []
        
        # Configuration
        self.batch_size = 50
        self.max_retries = 3
        self.retry_delay_seconds = 5
        self.conflict_resolution_strategy = ConflictResolution.LATEST_WINS
        
        # Statistics
        self.sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "conflicts_resolved": 0,
            "last_sync_time": None
        }
    
    def add_sync_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for sync events"""
        self.sync_callbacks.append(callback)
    
    async def _notify_callbacks(self, event: str, data: Dict[str, Any]) -> None:
        """Notify sync callbacks"""
        for callback in self.sync_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event, data)
                else:
                    callback(event, data)
            except Exception as e:
                logger.error(f"Sync callback error: {e}")
    
    async def create_entity(
        self,
        entity_type: str,
        data: Dict[str, Any],
        priority: DataPriority = DataPriority.MEDIUM,
        sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> str:
        """Create new syncable entity"""
        entity = SyncableEntity(
            entity_id=str(uuid.uuid4()),
            entity_type=entity_type,
            data=data,
            priority=priority,
            sync_direction=sync_direction
        )
        
        await self.data_store.store_entity(entity)
        
        # Trigger sync if online
        if self.is_online and not self.sync_in_progress:
            asyncio.create_task(self.sync_pending_data())
        
        return entity.entity_id
    
    async def update_entity(
        self,
        entity_id: str,
        data: Dict[str, Any],
        increment_version: bool = True
    ) -> bool:
        """Update existing entity"""
        entity = await self.data_store.get_entity(entity_id)
        if not entity:
            return False
        
        entity.update_data(data, increment_version)
        await self.data_store.store_entity(entity)
        
        # Trigger sync if online
        if self.is_online and not self.sync_in_progress:
            asyncio.create_task(self.sync_pending_data())
        
        return True
    
    async def delete_entity(self, entity_id: str) -> bool:
        """Delete entity (mark for deletion sync)"""
        entity = await self.data_store.get_entity(entity_id)
        if not entity:
            return False
        
        # Mark for deletion instead of immediate delete
        entity.data["_deleted"] = True
        entity.update_data(entity.data)
        await self.data_store.store_entity(entity)
        
        return True
    
    async def set_online_status(self, is_online: bool) -> None:
        """Set online/offline status"""
        was_offline = not self.is_online
        self.is_online = is_online
        
        await self._notify_callbacks("network_status_changed", {
            "is_online": is_online,
            "was_offline": was_offline
        })
        
        # Start sync when coming back online
        if is_online and was_offline and not self.sync_in_progress:
            await self.sync_pending_data()
    
    async def sync_pending_data(self) -> Dict[str, Any]:
        """Sync all pending data with server"""
        if self.sync_in_progress:
            return {"status": "already_syncing"}
        
        if not self.is_online:
            return {"status": "offline"}
        
        self.sync_in_progress = True
        sync_start_time = datetime.now(timezone.utc)
        
        try:
            await self._notify_callbacks("sync_started", {
                "start_time": sync_start_time.isoformat()
            })
            
            # Get pending entities
            pending_entities = await self.data_store.get_entities_by_status(
                SyncStatus.PENDING, limit=self.batch_size * 5
            )
            
            if not pending_entities:
                return {"status": "no_data_to_sync"}
            
            # Group by priority and create batches
            priority_groups = self._group_entities_by_priority(pending_entities)
            sync_results = {
                "total_entities": len(pending_entities),
                "synced": 0,
                "failed": 0,
                "conflicts": 0,
                "batches_processed": 0
            }
            
            # Process each priority group
            for priority in [DataPriority.CRITICAL, DataPriority.HIGH, DataPriority.MEDIUM, DataPriority.LOW]:
                if priority not in priority_groups:
                    continue
                
                entities = priority_groups[priority]
                batches = self._create_batches(entities, self.batch_size)
                
                for batch in batches:
                    batch_result = await self._sync_batch(batch)
                    
                    sync_results["synced"] += batch_result["synced"]
                    sync_results["failed"] += batch_result["failed"]
                    sync_results["conflicts"] += batch_result["conflicts"]
                    sync_results["batches_processed"] += 1
                    
                    # Update sync stats
                    self.sync_stats["total_syncs"] += 1
                    if batch_result["failed"] == 0:
                        self.sync_stats["successful_syncs"] += 1
                    else:
                        self.sync_stats["failed_syncs"] += 1
                    
                    self.sync_stats["conflicts_resolved"] += batch_result["conflicts"]
            
            # Update last sync time
            self.sync_stats["last_sync_time"] = datetime.now(timezone.utc).isoformat()
            
            await self._notify_callbacks("sync_completed", sync_results)
            return sync_results
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            await self._notify_callbacks("sync_failed", {"error": str(e)})
            return {"status": "error", "error": str(e)}
        
        finally:
            self.sync_in_progress = False
    
    def _group_entities_by_priority(self, entities: List[SyncableEntity]) -> Dict[DataPriority, List[SyncableEntity]]:
        """Group entities by priority"""
        groups = {}
        for entity in entities:
            if entity.priority not in groups:
                groups[entity.priority] = []
            groups[entity.priority].append(entity)
        
        return groups
    
    def _create_batches(self, entities: List[SyncableEntity], batch_size: int) -> List[SyncBatch]:
        """Create sync batches from entities"""
        batches = []
        
        for i in range(0, len(entities), batch_size):
            batch_entities = entities[i:i + batch_size]
            
            batch = SyncBatch(
                batch_id=str(uuid.uuid4()),
                entities=batch_entities,
                priority=batch_entities[0].priority,
                sync_direction=batch_entities[0].sync_direction
            )
            
            batches.append(batch)
        
        return batches
    
    async def _sync_batch(self, batch: SyncBatch) -> Dict[str, int]:
        """Sync a batch of entities"""
        results = {"synced": 0, "failed": 0, "conflicts": 0}
        
        await self.data_store.store_batch(batch)
        
        # Process each entity in batch
        for entity in batch.entities:
            try:
                entity.sync_status = SyncStatus.SYNCING
                await self.data_store.store_entity(entity)
                
                # Simulate server sync (in real implementation, would call API)
                sync_result = await self._sync_entity_with_server(entity)
                
                if sync_result["status"] == "success":
                    entity.mark_synced(sync_result.get("server_checksum"))
                    results["synced"] += 1
                    batch.synced_entities += 1
                    
                elif sync_result["status"] == "conflict":
                    entity.sync_status = SyncStatus.CONFLICT
                    results["conflicts"] += 1
                    batch.conflict_entities += 1
                    
                    # Auto-resolve if strategy is set
                    if self.conflict_resolution_strategy != ConflictResolution.MANUAL:
                        if entity.resolve_conflict(self.conflict_resolution_strategy):
                            results["conflicts"] -= 1
                            results["synced"] += 1
                            batch.conflict_entities -= 1
                            batch.synced_entities += 1
                
                else:
                    entity.sync_status = SyncStatus.ERROR
                    results["failed"] += 1
                    batch.failed_entities += 1
                
                await self.data_store.store_entity(entity)
                
            except Exception as e:
                logger.error(f"Failed to sync entity {entity.entity_id}: {e}")
                entity.sync_status = SyncStatus.ERROR
                await self.data_store.store_entity(entity)
                results["failed"] += 1
                batch.failed_entities += 1
        
        # Update batch
        await self.data_store.store_batch(batch)
        
        return results
    
    async def _sync_entity_with_server(self, entity: SyncableEntity) -> Dict[str, Any]:
        """Sync individual entity with server (mock implementation)"""
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        # Simulate different sync outcomes
        import random
        
        rand = random.random()
        if rand < 0.8:  # 80% success
            return {
                "status": "success",
                "server_checksum": hashlib.sha256(
                    json.dumps(entity.data, sort_keys=True).encode()
                ).hexdigest()
            }
        elif rand < 0.9:  # 10% conflict
            return {
                "status": "conflict",
                "server_data": entity.data.copy(),  # Mock server data
                "server_checksum": "different_checksum"
            }
        else:  # 10% error
            return {
                "status": "error",
                "error": "Server temporarily unavailable"
            }
    
    async def resolve_conflicts(self, resolution_strategy: ConflictResolution = None) -> int:
        """Resolve all pending conflicts"""
        if resolution_strategy:
            self.conflict_resolution_strategy = resolution_strategy
        
        conflict_entities = await self.data_store.get_entities_by_status(SyncStatus.CONFLICT)
        resolved_count = 0
        
        for entity in conflict_entities:
            if entity.resolve_conflict(self.conflict_resolution_strategy):
                await self.data_store.store_entity(entity)
                resolved_count += 1
        
        logger.info(f"Resolved {resolved_count} conflicts using {self.conflict_resolution_strategy.value}")
        return resolved_count
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        db_stats = await self.data_store.get_database_stats()
        
        return {
            "is_online": self.is_online,
            "sync_in_progress": self.sync_in_progress,
            "database_stats": db_stats,
            "sync_stats": self.sync_stats,
            "conflict_resolution_strategy": self.conflict_resolution_strategy.value,
            "configuration": {
                "batch_size": self.batch_size,
                "max_retries": self.max_retries,
                "retry_delay_seconds": self.retry_delay_seconds
            }
        }
    
    async def force_full_sync(self) -> Dict[str, Any]:
        """Force full synchronization of all data"""
        if not self.is_online:
            return {"status": "offline"}
        
        # Reset all synced entities to pending
        all_entities = await self.data_store.get_entities_by_status(SyncStatus.SYNCED, limit=1000)
        
        for entity in all_entities:
            entity.sync_status = SyncStatus.PENDING
            await self.data_store.store_entity(entity)
        
        # Start full sync
        return await self.sync_pending_data()


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Offline-First Data Synchronization System")
    print("=" * 55)
    
    async def test_offline_sync():
        """Test offline data synchronization"""
        
        # Initialize data store
        data_store = OfflineDataStore("test_offline.db")
        await data_store.initialize()
        
        # Initialize synchronizer
        synchronizer = DataSynchronizer(data_store)
        
        # Add sync callback
        async def sync_callback(event: str, data: Dict[str, Any]):
            print(f"Sync Event: {event} - {data}")
        
        synchronizer.add_sync_callback(sync_callback)
        
        print("Creating test entities...")
        
        # Create test entities
        entity_ids = []
        
        # Student progress entity
        progress_id = await synchronizer.create_entity(
            "student_progress",
            {
                "student_id": 1001,
                "subject": "matematik",
                "completed_lessons": 15,
                "total_score": 850,
                "last_activity": datetime.now(timezone.utc).isoformat()
            },
            priority=DataPriority.CRITICAL
        )
        entity_ids.append(progress_id)
        
        # Exam results entity
        exam_id = await synchronizer.create_entity(
            "exam_result",
            {
                "student_id": 1001,
                "exam_type": "TYT",
                "score": 425,
                "correct_answers": 95,
                "total_questions": 120,
                "exam_date": datetime.now(timezone.utc).isoformat()
            },
            priority=DataPriority.CRITICAL
        )
        entity_ids.append(exam_id)
        
        # Study content entity
        content_id = await synchronizer.create_entity(
            "study_content",
            {
                "content_id": "content_123",
                "title": "Türev Alma Kuralları",
                "view_count": 1,
                "last_viewed": datetime.now(timezone.utc).isoformat()
            },
            priority=DataPriority.HIGH
        )
        entity_ids.append(content_id)
        
        print(f"Created {len(entity_ids)} entities")
        
        # Test offline mode
        print("\nTesting offline mode...")
        await synchronizer.set_online_status(False)
        
        # Update entity while offline
        await synchronizer.update_entity(progress_id, {
            "completed_lessons": 16,
            "total_score": 900
        })
        
        # Get sync status
        status = await synchronizer.get_sync_status()
        print(f"Offline status: {status['database_stats']['status_counts']}")
        
        # Test coming back online
        print("\nComing back online and syncing...")
        await synchronizer.set_online_status(True)
        
        # Manual sync
        sync_result = await synchronizer.sync_pending_data()
        print(f"Sync result: {sync_result}")
        
        # Test conflict resolution
        print("\nTesting conflict resolution...")
        
        # Create entity with conflict
        conflict_entity = await data_store.get_entity(progress_id)
        if conflict_entity:
            # Simulate server conflict
            conflict_entity.server_checksum = "different_checksum"
            conflict_entity.detect_conflict({
                "completed_lessons": 17,  # Different from local
                "total_score": 920
            }, "server_checksum_123")
            
            await data_store.store_entity(conflict_entity)
            
            # Resolve conflicts
            resolved_count = await synchronizer.resolve_conflicts(ConflictResolution.LATEST_WINS)
            print(f"Resolved {resolved_count} conflicts")
        
        # Get final stats
        final_status = await synchronizer.get_sync_status()
        print(f"\nFinal sync stats:")
        print(f"  Total syncs: {final_status['sync_stats']['total_syncs']}")
        print(f"  Successful: {final_status['sync_stats']['successful_syncs']}")
        print(f"  Failed: {final_status['sync_stats']['failed_syncs']}")
        print(f"  Conflicts resolved: {final_status['sync_stats']['conflicts_resolved']}")
        
        print(f"\nDatabase stats:")
        db_stats = final_status['database_stats']
        print(f"  Total entities: {db_stats['total_entities']}")
        print(f"  Database size: {db_stats['database_size_mb']:.2f} MB")
        print(f"  Entity types: {db_stats['type_counts']}")
        
        # Cleanup
        print("\nCleaning up test data...")
        await data_store.cleanup_old_data(days_old=0)  # Cleanup immediately for test
    
    # Run test
    asyncio.run(test_offline_sync())