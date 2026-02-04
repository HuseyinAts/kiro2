"""
KIRO2 Memory Management and Resource Optimization System
Advanced memory and system resource optimization for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Bellek ve Kaynak Optimizasyon Sistemi
"""

import asyncio
import gc
import sys
import os
import psutil
import resource
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from enum import Enum
import json
import uuid
import threading
import weakref
from collections import defaultdict, deque
import tracemalloc
import linecache
import statistics
import time
from functools import wraps
import warnings
import logging

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.PERFORMANCE)
config = get_unified_config()


class ResourceType(Enum):
    """System resource types"""
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"
    FILE_DESCRIPTORS = "file_descriptors"
    DATABASE_CONNECTIONS = "database_connections"
    CACHE_ENTRIES = "cache_entries"


class MemoryRegion(Enum):
    """Memory regions for optimization"""
    HEAP = "heap"
    STACK = "stack"
    CACHE = "cache"
    TEMPORARY = "temporary"
    EXAM_DATA = "exam_data"  # Turkish exam-specific data
    USER_SESSIONS = "user_sessions"
    STATIC_CONTENT = "static_content"


class OptimizationStrategy(Enum):
    """Resource optimization strategies"""
    LAZY_LOADING = "lazy_loading"
    EAGER_CLEANUP = "eager_cleanup"
    MEMORY_POOLING = "memory_pooling"
    COMPRESSION = "compression"
    GARBAGE_COLLECTION = "garbage_collection"
    RESOURCE_LIMITING = "resource_limiting"
    EXAM_MODE_OPTIMIZATION = "exam_mode_optimization"


class MemoryPressureLevel(Enum):
    """Memory pressure levels"""
    LOW = "low"        # < 60% usage
    MODERATE = "moderate"  # 60-75% usage
    HIGH = "high"      # 75-85% usage
    CRITICAL = "critical"  # > 85% usage


@dataclass
class MemoryUsage:
    """Memory usage statistics"""
    total_mb: float
    available_mb: float
    used_mb: float
    cached_mb: float
    buffers_mb: float
    
    # Process-specific
    process_rss_mb: float = 0.0  # Resident Set Size
    process_vms_mb: float = 0.0  # Virtual Memory Size
    process_shared_mb: float = 0.0
    
    # Python-specific
    python_heap_mb: float = 0.0
    gc_objects_count: int = 0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    
    # Turkish exam specific tracking
    exam_data_mb: float = 0.0
    user_session_mb: float = 0.0
    cached_questions_mb: float = 0.0
    
    # Timestamps
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def usage_percent(self) -> float:
        """Calculate memory usage percentage"""
        return (self.used_mb / self.total_mb) * 100 if self.total_mb > 0 else 0.0
    
    @property
    def available_percent(self) -> float:
        """Calculate available memory percentage"""
        return (self.available_mb / self.total_mb) * 100 if self.total_mb > 0 else 0.0
    
    def get_pressure_level(self) -> MemoryPressureLevel:
        """Determine current memory pressure level"""
        usage = self.usage_percent
        
        if usage < 60:
            return MemoryPressureLevel.LOW
        elif usage < 75:
            return MemoryPressureLevel.MODERATE
        elif usage < 85:
            return MemoryPressureLevel.HIGH
        else:
            return MemoryPressureLevel.CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "system_memory": {
                "total_mb": self.total_mb,
                "available_mb": self.available_mb,
                "used_mb": self.used_mb,
                "cached_mb": self.cached_mb,
                "buffers_mb": self.buffers_mb,
                "usage_percent": self.usage_percent,
                "available_percent": self.available_percent,
                "pressure_level": self.get_pressure_level().value
            },
            "process_memory": {
                "rss_mb": self.process_rss_mb,
                "vms_mb": self.process_vms_mb,
                "shared_mb": self.process_shared_mb
            },
            "python_memory": {
                "heap_mb": self.python_heap_mb,
                "gc_objects": self.gc_objects_count,
                "gc_collections": self.gc_collections
            },
            "exam_specific": {
                "exam_data_mb": self.exam_data_mb,
                "user_sessions_mb": self.user_session_mb,
                "cached_questions_mb": self.cached_questions_mb
            },
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ResourceLimit:
    """Resource usage limits and thresholds"""
    resource_type: ResourceType
    soft_limit: float  # Warning threshold
    hard_limit: float  # Maximum allowed
    current_usage: float = 0.0
    
    # Auto-scaling thresholds
    scale_up_threshold: float = 0.8  # 80% of hard limit
    scale_down_threshold: float = 0.4  # 40% of hard limit
    
    # Turkish exam specific
    exam_mode_multiplier: float = 1.5  # Allow 50% more during exams
    
    # Actions on limit breach
    warning_callback: Optional[Callable] = None
    limit_callback: Optional[Callable] = None
    
    @property
    def usage_percent(self) -> float:
        """Current usage as percentage of hard limit"""
        return (self.current_usage / self.hard_limit) * 100 if self.hard_limit > 0 else 0.0
    
    @property
    def is_warning_exceeded(self) -> bool:
        """Check if warning threshold is exceeded"""
        return self.current_usage > self.soft_limit
    
    @property
    def is_limit_exceeded(self) -> bool:
        """Check if hard limit is exceeded"""
        return self.current_usage > self.hard_limit
    
    def should_scale_up(self) -> bool:
        """Check if should trigger scale up"""
        return self.current_usage > (self.hard_limit * self.scale_up_threshold)
    
    def should_scale_down(self) -> bool:
        """Check if should trigger scale down"""
        return self.current_usage < (self.hard_limit * self.scale_down_threshold)


@dataclass
class MemoryAllocation:
    """Track memory allocations for optimization"""
    allocation_id: str
    size_bytes: int
    memory_region: MemoryRegion
    
    # Allocation metadata
    allocated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    
    # Optimization hints
    is_temporary: bool = False
    can_compress: bool = False
    can_swap: bool = False
    priority: int = 5  # 1-10, higher = more important
    
    # Turkish exam context
    exam_related: bool = False
    exam_type: Optional[str] = None  # TYT, AYT, YKS
    user_id: Optional[str] = None
    
    # Lifecycle management
    ttl_seconds: Optional[int] = None
    reference_count: int = 1
    
    def __post_init__(self):
        if not self.allocation_id:
            self.allocation_id = str(uuid.uuid4())
    
    @property
    def size_mb(self) -> float:
        """Size in megabytes"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def age_seconds(self) -> float:
        """Age in seconds"""
        return (datetime.now(timezone.utc) - self.allocated_at).total_seconds()
    
    @property
    def is_expired(self) -> bool:
        """Check if allocation is expired"""
        if self.ttl_seconds is None:
            return False
        return self.age_seconds > self.ttl_seconds
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for garbage collection"""
        age_factor = min(self.age_seconds / 3600, 10.0)  # Age in hours, capped at 10
        access_factor = self.access_count / max(self.age_seconds / 60, 1.0)  # Accesses per minute
        priority_factor = self.priority / 10.0
        exam_factor = 2.0 if self.exam_related else 1.0
        reference_factor = 1.0 / max(self.reference_count, 1.0)
        
        # Lower score = higher priority for collection
        score = (age_factor * 0.3 + (1.0 - access_factor) * 0.3 + 
                (1.0 - priority_factor) * 0.2 + reference_factor * 0.2) / exam_factor
        
        return score
    
    def update_access(self) -> None:
        """Update access statistics"""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1


class MemoryProfiler:
    """Advanced memory profiling and tracking"""
    
    def __init__(self):
        self.profiling_enabled = False
        self.trace_malloc_enabled = False
        self.allocations: Dict[str, MemoryAllocation] = {}
        self.allocation_history: deque = deque(maxlen=10000)
        
        # Memory snapshots for comparison
        self.snapshots: List[Tuple[datetime, Any]] = []
        self.max_snapshots = 100
        
        # Tracking weak references to avoid memory leaks
        self.tracked_objects: weakref.WeakSet = weakref.WeakSet()
        
        # Performance impact minimization
        self.sample_rate = 0.1  # Sample 10% of allocations
        self.profile_interval = 30  # Seconds between snapshots
        
    async def start_profiling(self, detailed: bool = False) -> bool:
        """Start memory profiling"""
        try:
            if not self.profiling_enabled:
                # Start tracemalloc for detailed tracking
                if detailed and not self.trace_malloc_enabled:
                    tracemalloc.start(10)  # Keep 10 frames
                    self.trace_malloc_enabled = True
                
                self.profiling_enabled = True
                
                # Start background profiling task
                asyncio.create_task(self._profile_loop())
                
                logger.info(f"Memory profiling started (detailed: {detailed})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start memory profiling: {e}")
            return False
    
    async def stop_profiling(self) -> bool:
        """Stop memory profiling"""
        try:
            self.profiling_enabled = False
            
            if self.trace_malloc_enabled:
                tracemalloc.stop()
                self.trace_malloc_enabled = False
            
            logger.info("Memory profiling stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop memory profiling: {e}")
            return False
    
    async def _profile_loop(self) -> None:
        """Background profiling loop"""
        while self.profiling_enabled:
            try:
                await self._take_memory_snapshot()
                await asyncio.sleep(self.profile_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Profiling loop error: {e}")
                await asyncio.sleep(5)
    
    async def _take_memory_snapshot(self) -> None:
        """Take memory snapshot for analysis"""
        try:
            if self.trace_malloc_enabled:
                snapshot = tracemalloc.take_snapshot()
                self.snapshots.append((datetime.now(timezone.utc), snapshot))
                
                # Keep only recent snapshots
                if len(self.snapshots) > self.max_snapshots:
                    self.snapshots.pop(0)
            
        except Exception as e:
            logger.error(f"Failed to take memory snapshot: {e}")
    
    def track_allocation(
        self, 
        obj: Any, 
        size_bytes: int, 
        memory_region: MemoryRegion,
        **metadata
    ) -> str:
        """Track memory allocation"""
        if not self.profiling_enabled:
            return ""
        
        # Sample allocations to reduce overhead
        if hash(id(obj)) % 10 >= (self.sample_rate * 10):
            return ""
        
        try:
            allocation = MemoryAllocation(
                size_bytes=size_bytes,
                memory_region=memory_region,
                **metadata
            )
            
            allocation_id = allocation.allocation_id
            self.allocations[allocation_id] = allocation
            
            # Track weak reference to object
            try:
                self.tracked_objects.add(obj)
            except TypeError:
                # Object doesn't support weak references
                pass
            
            # Add to history
            self.allocation_history.append({
                "allocation_id": allocation_id,
                "timestamp": allocation.allocated_at.isoformat(),
                "size_mb": allocation.size_mb,
                "region": memory_region.value,
                "action": "allocated"
            })
            
            return allocation_id
            
        except Exception as e:
            logger.error(f"Failed to track allocation: {e}")
            return ""
    
    def track_deallocation(self, allocation_id: str) -> None:
        """Track memory deallocation"""
        if allocation_id in self.allocations:
            allocation = self.allocations[allocation_id]
            
            # Add to history
            self.allocation_history.append({
                "allocation_id": allocation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "size_mb": allocation.size_mb,
                "region": allocation.memory_region.value,
                "action": "deallocated",
                "age_seconds": allocation.age_seconds
            })
            
            del self.allocations[allocation_id]
    
    def get_memory_leaks(self, min_age_hours: float = 1.0) -> List[MemoryAllocation]:
        """Detect potential memory leaks"""
        min_age_seconds = min_age_hours * 3600
        current_time = datetime.now(timezone.utc)
        
        potential_leaks = []
        
        for allocation in self.allocations.values():
            age = (current_time - allocation.allocated_at).total_seconds()
            
            # Potential leak criteria
            if (age > min_age_seconds and 
                allocation.access_count == 0 and
                not allocation.exam_related and  # Don't flag exam data as leaks
                allocation.reference_count <= 1):
                
                potential_leaks.append(allocation)
        
        # Sort by age (oldest first)
        potential_leaks.sort(key=lambda a: a.age_seconds, reverse=True)
        
        return potential_leaks
    
    def analyze_memory_usage(self) -> Dict[str, Any]:
        """Analyze current memory usage patterns"""
        if not self.allocations:
            return {"error": "No allocation data available"}
        
        analysis = {
            "total_allocations": len(self.allocations),
            "total_size_mb": sum(a.size_mb for a in self.allocations.values()),
            "by_region": defaultdict(lambda: {"count": 0, "size_mb": 0.0}),
            "by_age": {"<1min": 0, "1-10min": 0, "10-60min": 0, ">1hour": 0},
            "by_priority": defaultdict(int),
            "exam_related": {"count": 0, "size_mb": 0.0},
            "potential_optimizations": []
        }
        
        current_time = datetime.now(timezone.utc)
        
        for allocation in self.allocations.values():
            # By region
            region_stats = analysis["by_region"][allocation.memory_region.value]
            region_stats["count"] += 1
            region_stats["size_mb"] += allocation.size_mb
            
            # By age
            age_minutes = allocation.age_seconds / 60
            if age_minutes < 1:
                analysis["by_age"]["<1min"] += 1
            elif age_minutes < 10:
                analysis["by_age"]["1-10min"] += 1
            elif age_minutes < 60:
                analysis["by_age"]["10-60min"] += 1
            else:
                analysis["by_age"][">1hour"] += 1
            
            # By priority
            analysis["by_priority"][allocation.priority] += 1
            
            # Exam related
            if allocation.exam_related:
                analysis["exam_related"]["count"] += 1
                analysis["exam_related"]["size_mb"] += allocation.size_mb
        
        # Optimization suggestions
        total_size = analysis["total_size_mb"]
        
        if total_size > 1000:  # > 1GB
            analysis["potential_optimizations"].append(
                "High memory usage detected - consider memory cleanup"
            )
        
        if analysis["by_age"][">1hour"] > 100:
            analysis["potential_optimizations"].append(
                "Many old allocations found - potential memory leaks"
            )
        
        temp_region_size = analysis["by_region"].get("temporary", {}).get("size_mb", 0)
        if temp_region_size > 500:  # > 500MB in temporary
            analysis["potential_optimizations"].append(
                "Large temporary memory usage - increase cleanup frequency"
            )
        
        return analysis
    
    def get_top_memory_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory consuming allocations"""
        sorted_allocations = sorted(
            self.allocations.values(),
            key=lambda a: a.size_bytes,
            reverse=True
        )
        
        return [
            {
                "allocation_id": alloc.allocation_id,
                "size_mb": alloc.size_mb,
                "memory_region": alloc.memory_region.value,
                "age_seconds": alloc.age_seconds,
                "access_count": alloc.access_count,
                "priority": alloc.priority,
                "exam_related": alloc.exam_related,
                "can_optimize": alloc.can_compress or alloc.can_swap
            }
            for alloc in sorted_allocations[:limit]
        ]


class GarbageCollectionOptimizer:
    """Intelligent garbage collection optimization"""
    
    def __init__(self):
        self.gc_enabled = True
        self.auto_gc_thresholds = gc.get_threshold()
        self.custom_thresholds = (1000, 15, 15)  # More aggressive
        
        # Statistics tracking
        self.gc_stats = {
            "total_collections": 0,
            "objects_collected": 0,
            "time_spent_seconds": 0.0,
            "generations": {0: 0, 1: 0, 2: 0}
        }
        
        # Optimization settings
        self.exam_mode_active = False
        self.aggressive_cleanup = False
        self.memory_pressure_response = True
        
        # Turkish exam specific
        self.preserve_exam_data = True
        self.exam_data_refs = weakref.WeakSet()
    
    def optimize_gc_settings(self, memory_pressure: MemoryPressureLevel) -> None:
        """Optimize GC settings based on memory pressure"""
        try:
            if memory_pressure == MemoryPressureLevel.LOW:
                # Relaxed GC for better performance
                gc.set_threshold(1500, 20, 20)
                
            elif memory_pressure == MemoryPressureLevel.MODERATE:
                # Balanced GC
                gc.set_threshold(1000, 15, 15)
                
            elif memory_pressure == MemoryPressureLevel.HIGH:
                # More aggressive GC
                gc.set_threshold(700, 10, 10)
                
            elif memory_pressure == MemoryPressureLevel.CRITICAL:
                # Very aggressive GC
                gc.set_threshold(500, 5, 5)
                self.aggressive_cleanup = True
            
            logger.debug(f"GC thresholds adjusted for {memory_pressure.value} pressure")
            
        except Exception as e:
            logger.error(f"Failed to optimize GC settings: {e}")
    
    async def force_garbage_collection(self, generation: Optional[int] = None) -> Dict[str, Any]:
        """Force garbage collection with statistics"""
        start_time = time.time()
        
        try:
            if generation is not None:
                collected = gc.collect(generation)
            else:
                collected = gc.collect()
            
            collection_time = time.time() - start_time
            
            # Update statistics
            self.gc_stats["total_collections"] += 1
            self.gc_stats["objects_collected"] += collected
            self.gc_stats["time_spent_seconds"] += collection_time
            
            if generation is not None:
                self.gc_stats["generations"][generation] += 1
            
            result = {
                "objects_collected": collected,
                "collection_time_seconds": collection_time,
                "generation": generation,
                "memory_freed_estimate_mb": collected * 0.001,  # Rough estimate
                "gc_stats": self.gc_stats.copy()
            }
            
            logger.debug(f"Garbage collection completed: {collected} objects in {collection_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Garbage collection failed: {e}")
            return {"error": str(e)}
    
    def protect_exam_data(self, obj: Any) -> None:
        """Protect exam-related data from aggressive cleanup"""
        if self.preserve_exam_data:
            try:
                self.exam_data_refs.add(obj)
            except TypeError:
                # Object doesn't support weak references
                pass
    
    def enable_exam_mode(self) -> None:
        """Enable exam mode GC optimizations"""
        self.exam_mode_active = True
        self.preserve_exam_data = True
        
        # More conservative GC during exams
        gc.set_threshold(2000, 25, 25)
        
        logger.info("GC exam mode enabled - preserving exam data")
    
    def disable_exam_mode(self) -> None:
        """Disable exam mode GC optimizations"""
        self.exam_mode_active = False
        self.aggressive_cleanup = False
        
        # Restore normal GC settings
        gc.set_threshold(*self.custom_thresholds)
        
        logger.info("GC exam mode disabled")
    
    def get_gc_statistics(self) -> Dict[str, Any]:
        """Get garbage collection statistics"""
        gc_counts = gc.get_count()
        gc_threshold = gc.get_threshold()
        
        return {
            "current_settings": {
                "thresholds": gc_threshold,
                "enabled": gc.isenabled(),
                "exam_mode": self.exam_mode_active
            },
            "current_counts": {
                "generation_0": gc_counts[0],
                "generation_1": gc_counts[1],
                "generation_2": gc_counts[2]
            },
            "statistics": self.gc_stats.copy(),
            "protected_objects": len(self.exam_data_refs),
            "efficiency_metrics": {
                "avg_collection_time": (
                    self.gc_stats["time_spent_seconds"] / 
                    max(self.gc_stats["total_collections"], 1)
                ),
                "avg_objects_per_collection": (
                    self.gc_stats["objects_collected"] / 
                    max(self.gc_stats["total_collections"], 1)
                )
            }
        }


class ResourceMonitor:
    """Comprehensive system resource monitoring"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitoring_interval = 5.0  # seconds
        
        # Resource limits
        self.resource_limits: Dict[ResourceType, ResourceLimit] = {}
        
        # Historical data
        self.resource_history: Dict[ResourceType, deque] = {
            resource_type: deque(maxlen=1000) 
            for resource_type in ResourceType
        }
        
        # Alert callbacks
        self.alert_callbacks: Dict[ResourceType, List[Callable]] = defaultdict(list)
        
        # Process information
        self.process = psutil.Process()
        self.pid = os.getpid()
        
        # Turkish exam specific monitoring
        self.exam_mode_multipliers = {
            ResourceType.MEMORY: 1.5,
            ResourceType.CPU: 1.3,
            ResourceType.DATABASE_CONNECTIONS: 2.0,
            ResourceType.CACHE_ENTRIES: 1.8
        }
        
        self._initialize_default_limits()
    
    def _initialize_default_limits(self) -> None:
        """Initialize default resource limits"""
        # Get system totals for percentage-based limits
        memory_total = psutil.virtual_memory().total / (1024**3)  # GB
        cpu_count = psutil.cpu_count()
        
        self.resource_limits = {
            ResourceType.MEMORY: ResourceLimit(
                resource_type=ResourceType.MEMORY,
                soft_limit=memory_total * 0.6,  # 60% warning
                hard_limit=memory_total * 0.8   # 80% limit
            ),
            ResourceType.CPU: ResourceLimit(
                resource_type=ResourceType.CPU,
                soft_limit=70.0,  # 70% warning
                hard_limit=90.0   # 90% limit
            ),
            ResourceType.DISK: ResourceLimit(
                resource_type=ResourceType.DISK,
                soft_limit=80.0,  # 80% warning
                hard_limit=95.0   # 95% limit
            ),
            ResourceType.FILE_DESCRIPTORS: ResourceLimit(
                resource_type=ResourceType.FILE_DESCRIPTORS,
                soft_limit=8192,  # Warning at 8K
                hard_limit=16384  # Limit at 16K
            ),
            ResourceType.DATABASE_CONNECTIONS: ResourceLimit(
                resource_type=ResourceType.DATABASE_CONNECTIONS,
                soft_limit=80,    # Warning at 80 connections
                hard_limit=100    # Limit at 100 connections
            )
        }
    
    async def start_monitoring(self) -> bool:
        """Start resource monitoring"""
        try:
            if not self.monitoring_active:
                self.monitoring_active = True
                asyncio.create_task(self._monitoring_loop())
                logger.info("Resource monitoring started")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start resource monitoring: {e}")
            return False
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring"""
        self.monitoring_active = False
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_resource_metrics()
                await self._check_resource_limits()
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring loop error: {e}")
                await asyncio.sleep(10)
    
    async def _collect_resource_metrics(self) -> None:
        """Collect current resource metrics"""
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Memory metrics
            memory_info = psutil.virtual_memory()
            process_memory = self.process.memory_info()
            
            memory_usage = MemoryUsage(
                total_mb=memory_info.total / (1024**2),
                available_mb=memory_info.available / (1024**2),
                used_mb=memory_info.used / (1024**2),
                cached_mb=getattr(memory_info, 'cached', 0) / (1024**2),
                buffers_mb=getattr(memory_info, 'buffers', 0) / (1024**2),
                process_rss_mb=process_memory.rss / (1024**2),
                process_vms_mb=process_memory.vms / (1024**2),
                python_heap_mb=sys.getsizeof(gc.get_objects()) / (1024**2),
                gc_objects_count=len(gc.get_objects()),
                gc_collections={i: gc.get_stats()[i]['collections'] for i in range(3)},
                timestamp=timestamp
            )
            
            self.resource_history[ResourceType.MEMORY].append(memory_usage)
            self.resource_limits[ResourceType.MEMORY].current_usage = memory_usage.used_mb
            
            # CPU metrics
            cpu_percent = self.process.cpu_percent()
            self.resource_history[ResourceType.CPU].append({
                "timestamp": timestamp,
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            })
            self.resource_limits[ResourceType.CPU].current_usage = cpu_percent
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            self.resource_history[ResourceType.DISK].append({
                "timestamp": timestamp,
                "total_gb": disk_usage.total / (1024**3),
                "used_gb": disk_usage.used / (1024**3),
                "free_gb": disk_usage.free / (1024**3),
                "usage_percent": disk_percent
            })
            self.resource_limits[ResourceType.DISK].current_usage = disk_percent
            
            # File descriptor metrics
            try:
                fd_count = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
                self.resource_history[ResourceType.FILE_DESCRIPTORS].append({
                    "timestamp": timestamp,
                    "open_files": fd_count,
                    "connections": len(self.process.connections())
                })
                self.resource_limits[ResourceType.FILE_DESCRIPTORS].current_usage = fd_count
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
        except Exception as e:
            logger.error(f"Failed to collect resource metrics: {e}")
    
    async def _check_resource_limits(self) -> None:
        """Check resource limits and trigger alerts"""
        for resource_type, limit in self.resource_limits.items():
            try:
                # Check warning threshold
                if limit.is_warning_exceeded and not limit.is_limit_exceeded:
                    await self._trigger_alert(resource_type, "warning", limit)
                
                # Check hard limit
                if limit.is_limit_exceeded:
                    await self._trigger_alert(resource_type, "limit", limit)
                
                # Check scaling thresholds
                if limit.should_scale_up():
                    await self._trigger_alert(resource_type, "scale_up", limit)
                elif limit.should_scale_down():
                    await self._trigger_alert(resource_type, "scale_down", limit)
                
            except Exception as e:
                logger.error(f"Failed to check limits for {resource_type}: {e}")
    
    async def _trigger_alert(self, resource_type: ResourceType, alert_type: str, limit: ResourceLimit) -> None:
        """Trigger resource alert"""
        alert_data = {
            "resource_type": resource_type.value,
            "alert_type": alert_type,
            "current_usage": limit.current_usage,
            "usage_percent": limit.usage_percent,
            "soft_limit": limit.soft_limit,
            "hard_limit": limit.hard_limit,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Log alert
        if alert_type == "warning":
            logger.warning(f"Resource warning: {resource_type.value} at {limit.usage_percent:.1f}%")
        elif alert_type == "limit":
            logger.error(f"Resource limit exceeded: {resource_type.value} at {limit.usage_percent:.1f}%")
        else:
            logger.info(f"Resource {alert_type}: {resource_type.value} at {limit.usage_percent:.1f}%")
        
        # Execute callbacks
        callbacks = self.alert_callbacks.get(resource_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def add_alert_callback(self, resource_type: ResourceType, callback: Callable) -> None:
        """Add alert callback for resource type"""
        self.alert_callbacks[resource_type].append(callback)
    
    def enable_exam_mode(self) -> None:
        """Enable exam mode resource limits"""
        for resource_type, multiplier in self.exam_mode_multipliers.items():
            if resource_type in self.resource_limits:
                limit = self.resource_limits[resource_type]
                limit.hard_limit *= multiplier
                limit.soft_limit *= multiplier
        
        logger.info("Resource monitoring exam mode enabled")
    
    def disable_exam_mode(self) -> None:
        """Disable exam mode resource limits"""
        for resource_type, multiplier in self.exam_mode_multipliers.items():
            if resource_type in self.resource_limits:
                limit = self.resource_limits[resource_type]
                limit.hard_limit /= multiplier
                limit.soft_limit /= multiplier
        
        logger.info("Resource monitoring exam mode disabled")
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current resource usage summary"""
        current_usage = {}
        
        for resource_type in ResourceType:
            if resource_type in self.resource_limits:
                limit = self.resource_limits[resource_type]
                current_usage[resource_type.value] = {
                    "current": limit.current_usage,
                    "usage_percent": limit.usage_percent,
                    "soft_limit": limit.soft_limit,
                    "hard_limit": limit.hard_limit,
                    "status": "critical" if limit.is_limit_exceeded else
                             "warning" if limit.is_warning_exceeded else "normal"
                }
        
        return current_usage
    
    def get_resource_trends(self, resource_type: ResourceType, hours: int = 1) -> Dict[str, Any]:
        """Get resource usage trends"""
        if resource_type not in self.resource_history:
            return {}
        
        history = list(self.resource_history[resource_type])
        if not history:
            return {}
        
        # Filter by time range
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_history = []
        
        for entry in history:
            entry_time = entry.timestamp if hasattr(entry, 'timestamp') else entry.get('timestamp')
            if isinstance(entry_time, str):
                entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
            
            if entry_time >= cutoff_time:
                recent_history.append(entry)
        
        if not recent_history:
            return {}
        
        # Calculate trends
        if resource_type == ResourceType.MEMORY:
            values = [entry.usage_percent for entry in recent_history]
        elif resource_type == ResourceType.CPU:
            values = [entry.get('cpu_percent', 0) for entry in recent_history]
        elif resource_type == ResourceType.DISK:
            values = [entry.get('usage_percent', 0) for entry in recent_history]
        else:
            return {}
        
        if values:
            return {
                "min": min(values),
                "max": max(values),
                "average": statistics.mean(values),
                "current": values[-1],
                "trend": "increasing" if values[-1] > values[0] else "decreasing",
                "data_points": len(values),
                "time_range_hours": hours
            }
        
        return {}


class MemoryResourceOptimizer:
    """Main memory and resource optimization manager"""
    
    def __init__(self):
        self.memory_profiler = MemoryProfiler()
        self.gc_optimizer = GarbageCollectionOptimizer()
        self.resource_monitor = ResourceMonitor()
        
        # Optimization state
        self.optimization_active = False
        self.exam_mode_active = False
        
        # Optimization strategies
        self.enabled_strategies = {
            OptimizationStrategy.GARBAGE_COLLECTION: True,
            OptimizationStrategy.MEMORY_POOLING: True,
            OptimizationStrategy.LAZY_LOADING: True,
            OptimizationStrategy.COMPRESSION: False,  # Disabled by default
            OptimizationStrategy.RESOURCE_LIMITING: True
        }
        
        # Performance impact tracking
        self.optimization_history: deque = deque(maxlen=1000)
        
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize memory and resource optimization"""
        try:
            config = config or {}
            
            # Start components
            await self.memory_profiler.start_profiling(
                detailed=config.get("detailed_profiling", False)
            )
            
            await self.resource_monitor.start_monitoring()
            
            # Configure optimization strategies
            if "strategies" in config:
                for strategy_name, enabled in config["strategies"].items():
                    try:
                        strategy = OptimizationStrategy(strategy_name)
                        self.enabled_strategies[strategy] = enabled
                    except ValueError:
                        logger.warning(f"Unknown optimization strategy: {strategy_name}")
            
            # Set up alert callbacks
            self.resource_monitor.add_alert_callback(
                ResourceType.MEMORY, self._handle_memory_pressure
            )
            
            self.optimization_active = True
            
            logger.info("Memory and resource optimization initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize optimization: {e}")
            return False
    
    async def _handle_memory_pressure(self, alert_data: Dict[str, Any]) -> None:
        """Handle memory pressure alerts"""
        try:
            alert_type = alert_data.get("alert_type")
            usage_percent = alert_data.get("usage_percent", 0)
            
            if alert_type == "warning" and usage_percent > 70:
                await self._trigger_memory_cleanup("moderate")
            
            elif alert_type == "limit" or usage_percent > 85:
                await self._trigger_memory_cleanup("aggressive")
            
        except Exception as e:
            logger.error(f"Failed to handle memory pressure: {e}")
    
    async def _trigger_memory_cleanup(self, intensity: str = "moderate") -> Dict[str, Any]:
        """Trigger memory cleanup based on intensity"""
        cleanup_result = {
            "intensity": intensity,
            "actions_taken": [],
            "memory_freed_mb": 0.0,
            "optimization_time_seconds": 0.0
        }
        
        start_time = time.time()
        
        try:
            if intensity == "aggressive":
                # Aggressive cleanup
                gc_result = await self.gc_optimizer.force_garbage_collection()
                cleanup_result["actions_taken"].append("forced_gc")
                cleanup_result["memory_freed_mb"] += gc_result.get("memory_freed_estimate_mb", 0)
                
                # Clean up old allocations
                if self.enabled_strategies.get(OptimizationStrategy.EAGER_CLEANUP):
                    await self._cleanup_old_allocations()
                    cleanup_result["actions_taken"].append("allocation_cleanup")
                
                # Adjust GC thresholds
                current_memory = list(self.resource_monitor.resource_history[ResourceType.MEMORY])
                if current_memory:
                    pressure_level = current_memory[-1].get_pressure_level()
                    self.gc_optimizer.optimize_gc_settings(pressure_level)
                    cleanup_result["actions_taken"].append("gc_optimization")
            
            else:
                # Moderate cleanup
                gc_result = await self.gc_optimizer.force_garbage_collection(generation=0)
                cleanup_result["actions_taken"].append("gen0_gc")
                cleanup_result["memory_freed_mb"] += gc_result.get("memory_freed_estimate_mb", 0)
            
            cleanup_result["optimization_time_seconds"] = time.time() - start_time
            
            # Record optimization event
            self.optimization_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "memory_cleanup",
                "result": cleanup_result.copy()
            })
            
            logger.info(f"Memory cleanup ({intensity}): {cleanup_result['memory_freed_mb']:.2f}MB freed")
            
        except Exception as e:
            cleanup_result["error"] = str(e)
            logger.error(f"Memory cleanup failed: {e}")
        
        return cleanup_result
    
    async def _cleanup_old_allocations(self) -> int:
        """Clean up old memory allocations"""
        cleaned_count = 0
        
        try:
            # Get potential cleanup candidates
            for allocation in list(self.memory_profiler.allocations.values()):
                # Skip exam-related data during exams
                if self.exam_mode_active and allocation.exam_related:
                    continue
                
                # Clean up expired allocations
                if allocation.is_expired or allocation.calculate_priority_score() > 8.0:
                    self.memory_profiler.track_deallocation(allocation.allocation_id)
                    cleaned_count += 1
            
            logger.debug(f"Cleaned up {cleaned_count} old allocations")
            
        except Exception as e:
            logger.error(f"Allocation cleanup failed: {e}")
        
        return cleaned_count
    
    async def enable_exam_mode(self) -> None:
        """Enable exam mode optimizations"""
        self.exam_mode_active = True
        
        # Enable exam mode in components
        self.gc_optimizer.enable_exam_mode()
        self.resource_monitor.enable_exam_mode()
        
        # Adjust optimization strategies for exams
        self.enabled_strategies[OptimizationStrategy.EXAM_MODE_OPTIMIZATION] = True
        self.enabled_strategies[OptimizationStrategy.EAGER_CLEANUP] = False  # Less aggressive during exams
        
        logger.info("Memory optimization exam mode enabled")
    
    async def disable_exam_mode(self) -> None:
        """Disable exam mode optimizations"""
        self.exam_mode_active = False
        
        # Disable exam mode in components
        self.gc_optimizer.disable_exam_mode()
        self.resource_monitor.disable_exam_mode()
        
        # Restore normal optimization strategies
        self.enabled_strategies[OptimizationStrategy.EXAM_MODE_OPTIMIZATION] = False
        self.enabled_strategies[OptimizationStrategy.EAGER_CLEANUP] = True
        
        # Perform post-exam cleanup
        await self._trigger_memory_cleanup("moderate")
        
        logger.info("Memory optimization exam mode disabled")
    
    async def analyze_memory_leaks(self) -> Dict[str, Any]:
        """Analyze potential memory leaks"""
        analysis = {
            "potential_leaks": [],
            "leak_summary": {},
            "recommendations": []
        }
        
        try:
            # Get potential leaks from profiler
            leaks = self.memory_profiler.get_memory_leaks(min_age_hours=2.0)
            
            for leak in leaks[:20]:  # Top 20 leaks
                analysis["potential_leaks"].append({
                    "allocation_id": leak.allocation_id,
                    "size_mb": leak.size_mb,
                    "age_hours": leak.age_seconds / 3600,
                    "memory_region": leak.memory_region.value,
                    "access_count": leak.access_count,
                    "exam_related": leak.exam_related
                })
            
            # Leak summary
            if leaks:
                total_leak_size = sum(leak.size_mb for leak in leaks)
                analysis["leak_summary"] = {
                    "total_leaks": len(leaks),
                    "total_size_mb": total_leak_size,
                    "avg_age_hours": statistics.mean(leak.age_seconds / 3600 for leak in leaks),
                    "oldest_leak_hours": max(leak.age_seconds / 3600 for leak in leaks)
                }
                
                # Recommendations
                if total_leak_size > 100:  # > 100MB
                    analysis["recommendations"].append("High memory leak detected - immediate cleanup recommended")
                
                if len(leaks) > 50:
                    analysis["recommendations"].append("Many small leaks - review object lifecycle management")
                
                exam_leaks = [leak for leak in leaks if leak.exam_related]
                if exam_leaks and not self.exam_mode_active:
                    analysis["recommendations"].append("Exam data leaks detected - consider cleanup of old exam sessions")
            
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Memory leak analysis failed: {e}")
        
        return analysis
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        try:
            # Get component statistics
            memory_analysis = self.memory_profiler.analyze_memory_usage()
            gc_stats = self.gc_optimizer.get_gc_statistics()
            resource_usage = self.resource_monitor.get_current_usage()
            
            # Calculate optimization impact
            recent_optimizations = list(self.optimization_history)[-50:]  # Last 50 optimizations
            total_memory_freed = sum(
                opt.get("result", {}).get("memory_freed_mb", 0)
                for opt in recent_optimizations
            )
            
            # Resource trends
            memory_trends = self.resource_monitor.get_resource_trends(ResourceType.MEMORY, hours=24)
            cpu_trends = self.resource_monitor.get_resource_trends(ResourceType.CPU, hours=24)
            
            return {
                "system_overview": {
                    "optimization_active": self.optimization_active,
                    "exam_mode_active": self.exam_mode_active,
                    "enabled_strategies": {
                        strategy.value: enabled
                        for strategy, enabled in self.enabled_strategies.items()
                    }
                },
                "memory_analysis": memory_analysis,
                "garbage_collection": gc_stats,
                "resource_usage": resource_usage,
                "optimization_impact": {
                    "total_optimizations": len(self.optimization_history),
                    "recent_optimizations": len(recent_optimizations),
                    "total_memory_freed_mb": total_memory_freed,
                    "avg_optimization_time": statistics.mean([
                        opt.get("result", {}).get("optimization_time_seconds", 0)
                        for opt in recent_optimizations
                    ]) if recent_optimizations else 0
                },
                "resource_trends": {
                    "memory": memory_trends,
                    "cpu": cpu_trends
                },
                "profiling_stats": {
                    "total_allocations": len(self.memory_profiler.allocations),
                    "tracked_objects": len(self.memory_profiler.tracked_objects),
                    "snapshots_taken": len(self.memory_profiler.snapshots)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate optimization report: {e}")
            return {"error": str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown optimization system"""
        try:
            await self.memory_profiler.stop_profiling()
            await self.resource_monitor.stop_monitoring()
            
            self.optimization_active = False
            
            logger.info("Memory and resource optimization shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")


# Decorator for automatic memory tracking
def track_memory(memory_region: MemoryRegion = MemoryRegion.HEAP, **metadata):
    """Decorator to automatically track memory usage of functions"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if hasattr(track_memory, '_optimizer'):
                profiler = track_memory._optimizer.memory_profiler
                
                # Track function entry
                start_objects = len(gc.get_objects())
                result = await func(*args, **kwargs)
                end_objects = len(gc.get_objects())
                
                # Estimate memory allocation
                object_diff = end_objects - start_objects
                if object_diff > 0:
                    estimated_size = object_diff * 100  # Rough estimate
                    profiler.track_allocation(
                        result, estimated_size, memory_region,
                        function_name=func.__name__, **metadata
                    )
                
                return result
            else:
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if hasattr(track_memory, '_optimizer'):
                profiler = track_memory._optimizer.memory_profiler
                
                start_objects = len(gc.get_objects())
                result = func(*args, **kwargs)
                end_objects = len(gc.get_objects())
                
                object_diff = end_objects - start_objects
                if object_diff > 0:
                    estimated_size = object_diff * 100
                    profiler.track_allocation(
                        result, estimated_size, memory_region,
                        function_name=func.__name__, **metadata
                    )
                
                return result
            else:
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Memory Management and Resource Optimization System")
    print("=" * 60)
    
    async def test_memory_optimization():
        """Test memory and resource optimization system"""
        
        # Create optimizer
        optimizer = MemoryResourceOptimizer()
        track_memory._optimizer = optimizer  # Set global reference for decorator
        
        # Initialize system
        config = {
            "detailed_profiling": True,
            "strategies": {
                "garbage_collection": True,
                "memory_pooling": True,
                "lazy_loading": True,
                "eager_cleanup": True
            }
        }
        
        await optimizer.initialize(config)
        
        # Test memory allocation tracking
        print("Testing memory allocation tracking...")
        
        @track_memory(memory_region=MemoryRegion.EXAM_DATA, exam_related=True)
        def create_exam_data():
            # Simulate exam data creation
            return {
                "questions": [f"Question {i}" for i in range(1000)],
                "answers": [f"Answer {i}" for i in range(1000)],
                "metadata": {"exam_type": "TYT", "subject": "Matematik"}
            }
        
        # Create some test data
        test_data = []
        for i in range(10):
            data = create_exam_data()
            test_data.append(data)
        
        # Wait for monitoring to collect data
        await asyncio.sleep(6)
        
        # Test memory cleanup
        print("Testing memory cleanup...")
        cleanup_result = await optimizer._trigger_memory_cleanup("moderate")
        print(f"Memory cleanup result: {cleanup_result['memory_freed_mb']:.2f}MB freed")
        
        # Test exam mode
        print("Testing exam mode...")
        await optimizer.enable_exam_mode()
        
        # Create more exam data during exam mode
        for i in range(5):
            exam_data = create_exam_data()
            test_data.append(exam_data)
        
        await asyncio.sleep(3)
        
        # Disable exam mode
        await optimizer.disable_exam_mode()
        
        # Test memory leak analysis
        print("Testing memory leak analysis...")
        leak_analysis = await optimizer.analyze_memory_leaks()
        
        print(f"Potential leaks found: {len(leak_analysis.get('potential_leaks', []))}")
        if leak_analysis.get("leak_summary"):
            summary = leak_analysis["leak_summary"]
            print(f"Total leak size: {summary['total_size_mb']:.2f}MB")
        
        # Generate comprehensive report
        print("Generating optimization report...")
        report = optimizer.get_optimization_report()
        
        print("\nOptimization Report Summary:")
        
        # System overview
        system = report["system_overview"]
        print(f"Optimization active: {system['optimization_active']}")
        print(f"Exam mode active: {system['exam_mode_active']}")
        print(f"Enabled strategies: {len([s for s in system['enabled_strategies'].values() if s])}")
        
        # Memory analysis
        if "memory_analysis" in report and "total_size_mb" in report["memory_analysis"]:
            memory = report["memory_analysis"]
            print(f"\nMemory Analysis:")
            print(f"Total allocations: {memory['total_allocations']}")
            print(f"Total size: {memory['total_size_mb']:.2f}MB")
            print(f"Exam-related: {memory['exam_related']['size_mb']:.2f}MB")
        
        # Resource usage
        if "resource_usage" in report:
            resources = report["resource_usage"]
            for resource_name, resource_data in resources.items():
                print(f"{resource_name}: {resource_data['usage_percent']:.1f}% ({resource_data['status']})")
        
        # Optimization impact
        impact = report["optimization_impact"]
        print(f"\nOptimization Impact:")
        print(f"Total optimizations: {impact['total_optimizations']}")
        print(f"Memory freed: {impact['total_memory_freed_mb']:.2f}MB")
        print(f"Avg optimization time: {impact['avg_optimization_time']:.3f}s")
        
        # Resource trends
        if "resource_trends" in report and "memory" in report["resource_trends"]:
            memory_trend = report["resource_trends"]["memory"]
            if memory_trend:
                print(f"\nMemory Trends (24h):")
                print(f"Current: {memory_trend['current']:.1f}%")
                print(f"Average: {memory_trend['average']:.1f}%")
                print(f"Peak: {memory_trend['max']:.1f}%")
                print(f"Trend: {memory_trend['trend']}")
        
        # Cleanup
        await optimizer.shutdown()
        
        print("\nMemory and resource optimization test completed!")
    
    # Run test
    asyncio.run(test_memory_optimization())