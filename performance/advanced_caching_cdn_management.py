"""
KIRO2 Advanced Caching and CDN Management System
Intelligent caching and content delivery network management for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Gelişmiş Önbellek ve CDN Yönetimi
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from enum import Enum
import json
import uuid
import sqlite3
import aioredis
import aiobotocore
import hashlib
import gzip
import base64
import mimetypes
import pickle
from pathlib import Path
import statistics
import time
from collections import defaultdict, deque
import aiofiles
import aiohttp
from urllib.parse import urljoin, urlparse

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.PERFORMANCE)
config = get_unified_config()


class CacheType(Enum):
    """Cache storage types"""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    CDN = "cdn"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"  # Time to live
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"
    EXAM_AWARE = "exam_aware"  # Turkish exam-specific strategy


class ContentType(Enum):
    """Content types for CDN optimization"""
    STATIC_ASSETS = "static_assets"  # CSS, JS, Images
    EXAM_QUESTIONS = "exam_questions"
    EXAM_RESULTS = "exam_results"
    VIDEO_LECTURES = "video_lectures"
    STUDENT_PROFILES = "student_profiles"
    UNIVERSITY_DATA = "university_data"
    API_RESPONSES = "api_responses"
    REAL_TIME_DATA = "real_time_data"


class CacheRegion(Enum):
    """Geographic cache regions for Turkey"""
    ISTANBUL = "istanbul"
    ANKARA = "ankara"
    IZMIR = "izmir"
    BURSA = "bursa"
    ANTALYA = "antalya"
    ADANA = "adana"
    KONYA = "konya"
    GLOBAL = "global"


@dataclass
class CacheItem:
    """Cache item with metadata"""
    key: str
    value: Any
    content_type: ContentType
    
    # Metadata
    size_bytes: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Cache behavior
    ttl_seconds: int = 3600  # 1 hour default
    access_count: int = 0
    hit_count: int = 0
    miss_count: int = 0
    
    # Turkish exam specific
    exam_related: bool = False
    exam_type: Optional[str] = None  # TYT, AYT, YKS
    subject_area: Optional[str] = None
    priority_level: int = 1  # 1-10, higher = more important
    
    # Compression and optimization
    compressed: bool = False
    compression_ratio: float = 1.0
    
    # Geographic distribution
    regions: List[CacheRegion] = field(default_factory=lambda: [CacheRegion.GLOBAL])
    
    def __post_init__(self):
        if isinstance(self.value, (dict, list)):
            self.size_bytes = len(json.dumps(self.value).encode('utf-8'))
        elif isinstance(self.value, str):
            self.size_bytes = len(self.value.encode('utf-8'))
        else:
            self.size_bytes = len(str(self.value).encode('utf-8'))
    
    def is_expired(self) -> bool:
        """Check if cache item is expired"""
        if self.ttl_seconds <= 0:  # No expiration
            return False
        
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expiry_time
    
    def update_access(self) -> None:
        """Update access statistics"""
        self.accessed_at = datetime.now(timezone.utc)
        self.access_count += 1
        self.hit_count += 1
    
    def get_age_seconds(self) -> float:
        """Get age of cache item in seconds"""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for cache eviction"""
        age_factor = 1.0 / max(self.get_age_seconds(), 1.0)
        access_factor = self.access_count / max(self.hit_count + self.miss_count, 1.0)
        priority_factor = self.priority_level / 10.0
        exam_factor = 2.0 if self.exam_related else 1.0
        
        return (age_factor * 0.3 + access_factor * 0.4 + priority_factor * 0.2) * exam_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "key": self.key,
            "content_type": self.content_type.value,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "access_count": self.access_count,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "exam_context": {
                "exam_related": self.exam_related,
                "exam_type": self.exam_type,
                "subject_area": self.subject_area,
                "priority_level": self.priority_level
            },
            "optimization": {
                "compressed": self.compressed,
                "compression_ratio": self.compression_ratio
            },
            "regions": [region.value for region in self.regions],
            "priority_score": self.calculate_priority_score()
        }


@dataclass
class CDNConfiguration:
    """CDN configuration for content delivery"""
    cdn_id: str
    provider: str  # cloudflare, aws_cloudfront, fastly, etc.
    
    # Endpoint configuration
    origin_server: str
    cdn_domain: str
    ssl_enabled: bool = True
    
    # Cache settings
    default_ttl: int = 3600
    max_ttl: int = 86400  # 24 hours
    browser_ttl: int = 1800  # 30 minutes
    
    # Geographic settings
    edge_locations: List[str] = field(default_factory=lambda: [
        "Istanbul", "Ankara", "Izmir", "Frankfurt", "London"
    ])
    geo_restrictions: List[str] = field(default_factory=list)
    
    # Performance settings
    compression_enabled: bool = True
    http2_enabled: bool = True
    image_optimization: bool = True
    
    # Turkish exam specific
    exam_content_ttl: int = 300  # 5 minutes for exam content
    result_announcement_ttl: int = 60  # 1 minute during result announcements
    
    # Security settings
    security_headers: Dict[str, str] = field(default_factory=dict)
    rate_limiting: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.cdn_id:
            self.cdn_id = str(uuid.uuid4())
        
        # Default security headers
        if not self.security_headers:
            self.security_headers = {
                "X-Frame-Options": "SAMEORIGIN",
                "X-Content-Type-Options": "nosniff",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
            }
        
        # Default rate limiting
        if not self.rate_limiting:
            self.rate_limiting = {
                "requests_per_minute": 1000,
                "burst_limit": 100
            }


class CacheManager:
    """Advanced cache management system"""
    
    def __init__(self):
        self.cache_stores: Dict[CacheType, Any] = {}
        self.cache_items: Dict[str, CacheItem] = {}
        self.cache_strategies: Dict[str, CacheStrategy] = {}
        
        # Cache statistics
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.evictions = 0
        
        # Memory limits
        self.max_memory_mb = 1024  # 1GB default
        self.current_memory_mb = 0
        self.eviction_threshold = 0.8  # Start evicting at 80%
        
        # Turkish exam specific settings
        self.exam_mode_active = False
        self.exam_cache_priority_boost = 2.0
        self.exam_content_multiplier = 0.1  # Shorter TTL during exams
        
        # Performance monitoring
        self.performance_history: deque = deque(maxlen=1000)
        
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self) -> None:
        """Initialize default caching strategies"""
        self.cache_strategies = {
            "static_assets": CacheStrategy.TTL,
            "exam_questions": CacheStrategy.EXAM_AWARE,
            "exam_results": CacheStrategy.REFRESH_AHEAD,
            "video_lectures": CacheStrategy.LRU,
            "api_responses": CacheStrategy.WRITE_THROUGH,
            "student_profiles": CacheStrategy.WRITE_BEHIND,
            "real_time_data": CacheStrategy.TTL
        }
    
    async def initialize_cache_store(self, cache_type: CacheType, config: Dict[str, Any]) -> bool:
        """Initialize cache storage backend"""
        try:
            if cache_type == CacheType.REDIS:
                redis_pool = aioredis.ConnectionPool.from_url(
                    config.get("redis_url", "redis://localhost:6379"),
                    max_connections=config.get("max_connections", 20)
                )
                self.cache_stores[cache_type] = aioredis.Redis(connection_pool=redis_pool)
                
            elif cache_type == CacheType.MEMORY:
                self.cache_stores[cache_type] = {}  # Simple in-memory dict
                
            elif cache_type == CacheType.FILE_SYSTEM:
                cache_dir = Path(config.get("cache_directory", "/tmp/kiro2_cache"))
                cache_dir.mkdir(parents=True, exist_ok=True)
                self.cache_stores[cache_type] = cache_dir
            
            logger.info(f"Initialized {cache_type.value} cache store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {cache_type.value} cache store: {e}")
            return False
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        content_type: ContentType,
        ttl: Optional[int] = None,
        cache_type: CacheType = CacheType.MEMORY,
        **metadata
    ) -> bool:
        """Set cache item with intelligent strategy application"""
        try:
            # Create cache item
            cache_item = CacheItem(
                key=key,
                value=value,
                content_type=content_type,
                ttl_seconds=ttl or self._get_default_ttl(content_type),
                **metadata
            )
            
            # Apply exam-specific adjustments
            if self.exam_mode_active and cache_item.exam_related:
                cache_item.ttl_seconds = int(cache_item.ttl_seconds * self.exam_content_multiplier)
                cache_item.priority_level = min(cache_item.priority_level + 3, 10)
            
            # Check memory limits and evict if necessary
            await self._check_memory_limits()
            
            # Store in cache backend
            success = await self._store_in_backend(cache_type, cache_item)
            
            if success:
                # Update local registry
                self.cache_items[key] = cache_item
                
                # Update memory usage
                self.current_memory_mb += cache_item.size_bytes / (1024 * 1024)
                
                logger.debug(f"Cached item: {key} ({content_type.value}, {cache_item.size_bytes} bytes)")
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
            return False
    
    async def get(self, key: str, cache_type: CacheType = CacheType.MEMORY) -> Optional[Any]:
        """Get cache item with hit/miss tracking"""
        self.total_requests += 1
        
        try:
            # Check if item exists in registry
            if key not in self.cache_items:
                self.cache_misses += 1
                await self._record_performance_metric("miss", key, cache_type)
                return None
            
            cache_item = self.cache_items[key]
            
            # Check if expired
            if cache_item.is_expired():
                await self.delete(key, cache_type)
                self.cache_misses += 1
                await self._record_performance_metric("expired", key, cache_type)
                return None
            
            # Retrieve from backend
            value = await self._retrieve_from_backend(cache_type, key)
            
            if value is not None:
                # Update access statistics
                cache_item.update_access()
                self.cache_hits += 1
                await self._record_performance_metric("hit", key, cache_type)
                
                return value
            else:
                # Item not found in backend
                del self.cache_items[key]
                self.cache_misses += 1
                await self._record_performance_metric("miss", key, cache_type)
                return None
                
        except Exception as e:
            logger.error(f"Cache get failed for {key}: {e}")
            self.cache_misses += 1
            return None
    
    async def delete(self, key: str, cache_type: CacheType = CacheType.MEMORY) -> bool:
        """Delete cache item"""
        try:
            # Remove from backend
            await self._remove_from_backend(cache_type, key)
            
            # Update local registry
            if key in self.cache_items:
                cache_item = self.cache_items[key]
                self.current_memory_mb -= cache_item.size_bytes / (1024 * 1024)
                del self.cache_items[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str, cache_type: CacheType = CacheType.MEMORY) -> int:
        """Invalidate cache items matching pattern"""
        invalidated_count = 0
        
        try:
            keys_to_delete = []
            
            # Find matching keys
            for key in self.cache_items.keys():
                if self._matches_pattern(key, pattern):
                    keys_to_delete.append(key)
            
            # Delete matching items
            for key in keys_to_delete:
                if await self.delete(key, cache_type):
                    invalidated_count += 1
            
            logger.info(f"Invalidated {invalidated_count} cache items matching pattern: {pattern}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation failed: {e}")
            return 0
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (supports wildcards)"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    async def _check_memory_limits(self) -> None:
        """Check memory usage and evict items if necessary"""
        if self.current_memory_mb < (self.max_memory_mb * self.eviction_threshold):
            return
        
        # Calculate how much memory to free (25% of current usage)
        target_memory_reduction = self.current_memory_mb * 0.25
        memory_freed = 0.0
        
        # Sort items by priority score (lower score = more likely to evict)
        items_by_priority = sorted(
            self.cache_items.values(),
            key=lambda item: item.calculate_priority_score()
        )
        
        for cache_item in items_by_priority:
            if memory_freed >= target_memory_reduction:
                break
            
            # Don't evict high-priority exam content
            if cache_item.exam_related and cache_item.priority_level >= 8:
                continue
            
            item_memory = cache_item.size_bytes / (1024 * 1024)
            if await self.delete(cache_item.key):
                memory_freed += item_memory
                self.evictions += 1
        
        logger.info(f"Evicted cache items to free {memory_freed:.2f}MB memory")
    
    def _get_default_ttl(self, content_type: ContentType) -> int:
        """Get default TTL for content type"""
        ttl_map = {
            ContentType.STATIC_ASSETS: 86400,  # 24 hours
            ContentType.EXAM_QUESTIONS: 3600,  # 1 hour
            ContentType.EXAM_RESULTS: 300,     # 5 minutes
            ContentType.VIDEO_LECTURES: 43200, # 12 hours
            ContentType.STUDENT_PROFILES: 1800, # 30 minutes
            ContentType.UNIVERSITY_DATA: 7200,  # 2 hours
            ContentType.API_RESPONSES: 300,     # 5 minutes
            ContentType.REAL_TIME_DATA: 60      # 1 minute
        }
        
        return ttl_map.get(content_type, 3600)  # Default 1 hour
    
    async def _store_in_backend(self, cache_type: CacheType, cache_item: CacheItem) -> bool:
        """Store cache item in backend storage"""
        try:
            if cache_type == CacheType.MEMORY:
                store = self.cache_stores.get(cache_type, {})
                store[cache_item.key] = cache_item.value
                return True
                
            elif cache_type == CacheType.REDIS:
                redis_client = self.cache_stores.get(cache_type)
                if redis_client:
                    # Serialize value
                    serialized_value = json.dumps(cache_item.value) if isinstance(cache_item.value, (dict, list)) else str(cache_item.value)
                    
                    # Store with TTL
                    await redis_client.setex(
                        cache_item.key, 
                        cache_item.ttl_seconds, 
                        serialized_value
                    )
                    return True
                    
            elif cache_type == CacheType.FILE_SYSTEM:
                cache_dir = self.cache_stores.get(cache_type)
                if cache_dir:
                    file_path = cache_dir / f"{hashlib.md5(cache_item.key.encode()).hexdigest()}.cache"
                    
                    cache_data = {
                        "value": cache_item.value,
                        "metadata": cache_item.to_dict(),
                        "expires_at": (cache_item.created_at + timedelta(seconds=cache_item.ttl_seconds)).isoformat()
                    }
                    
                    async with aiofiles.open(file_path, 'w') as f:
                        await f.write(json.dumps(cache_data))
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Backend storage failed: {e}")
            return False
    
    async def _retrieve_from_backend(self, cache_type: CacheType, key: str) -> Optional[Any]:
        """Retrieve cache item from backend storage"""
        try:
            if cache_type == CacheType.MEMORY:
                store = self.cache_stores.get(cache_type, {})
                return store.get(key)
                
            elif cache_type == CacheType.REDIS:
                redis_client = self.cache_stores.get(cache_type)
                if redis_client:
                    value = await redis_client.get(key)
                    if value:
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            return value.decode('utf-8')
                    
            elif cache_type == CacheType.FILE_SYSTEM:
                cache_dir = self.cache_stores.get(cache_type)
                if cache_dir:
                    file_path = cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
                    
                    if file_path.exists():
                        async with aiofiles.open(file_path, 'r') as f:
                            cache_data = json.loads(await f.read())
                        
                        # Check expiration
                        expires_at = datetime.fromisoformat(cache_data["expires_at"])
                        if datetime.now(timezone.utc) < expires_at.replace(tzinfo=timezone.utc):
                            return cache_data["value"]
                        else:
                            # Remove expired file
                            file_path.unlink()
            
            return None
            
        except Exception as e:
            logger.error(f"Backend retrieval failed: {e}")
            return None
    
    async def _remove_from_backend(self, cache_type: CacheType, key: str) -> bool:
        """Remove cache item from backend storage"""
        try:
            if cache_type == CacheType.MEMORY:
                store = self.cache_stores.get(cache_type, {})
                if key in store:
                    del store[key]
                    return True
                    
            elif cache_type == CacheType.REDIS:
                redis_client = self.cache_stores.get(cache_type)
                if redis_client:
                    result = await redis_client.delete(key)
                    return result > 0
                    
            elif cache_type == CacheType.FILE_SYSTEM:
                cache_dir = self.cache_stores.get(cache_type)
                if cache_dir:
                    file_path = cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
                    if file_path.exists():
                        file_path.unlink()
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Backend removal failed: {e}")
            return False
    
    async def _record_performance_metric(self, event_type: str, key: str, cache_type: CacheType) -> None:
        """Record cache performance metrics"""
        metric = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "key": key,
            "cache_type": cache_type.value,
            "total_requests": self.total_requests,
            "hit_rate": (self.cache_hits / max(self.total_requests, 1)) * 100
        }
        
        self.performance_history.append(metric)
    
    async def enable_exam_mode(self) -> None:
        """Enable exam mode caching optimizations"""
        self.exam_mode_active = True
        self.exam_content_multiplier = 0.1  # Much shorter TTL
        
        # Preload critical exam content
        await self._preload_exam_content()
        
        logger.info("Cache exam mode enabled - optimizations active")
    
    async def disable_exam_mode(self) -> None:
        """Disable exam mode caching optimizations"""
        self.exam_mode_active = False
        self.exam_content_multiplier = 1.0
        
        logger.info("Cache exam mode disabled")
    
    async def _preload_exam_content(self) -> None:
        """Preload critical exam content during exam periods"""
        # This would typically involve loading exam questions, university data, etc.
        logger.info("Preloading critical exam content...")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        hit_rate = (self.cache_hits / max(self.total_requests, 1)) * 100
        
        # Calculate average item size
        total_items = len(self.cache_items)
        avg_item_size = (self.current_memory_mb / max(total_items, 1)) * 1024 * 1024  # bytes
        
        # Recent performance metrics
        recent_metrics = list(self.performance_history)[-100:]  # Last 100 operations
        recent_hits = len([m for m in recent_metrics if m["event_type"] == "hit"])
        recent_total = len(recent_metrics)
        recent_hit_rate = (recent_hits / max(recent_total, 1)) * 100
        
        return {
            "overview": {
                "total_requests": self.total_requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate_percent": hit_rate,
                "recent_hit_rate_percent": recent_hit_rate,
                "evictions": self.evictions
            },
            "memory": {
                "current_usage_mb": self.current_memory_mb,
                "max_limit_mb": self.max_memory_mb,
                "usage_percent": (self.current_memory_mb / self.max_memory_mb) * 100,
                "total_items": total_items,
                "average_item_size_bytes": avg_item_size
            },
            "exam_mode": {
                "active": self.exam_mode_active,
                "content_multiplier": self.exam_content_multiplier,
                "priority_boost": self.exam_cache_priority_boost
            },
            "content_distribution": {
                content_type.value: len([
                    item for item in self.cache_items.values() 
                    if item.content_type == content_type
                ])
                for content_type in ContentType
            },
            "strategies": {
                strategy_name: strategy.value
                for strategy_name, strategy in self.cache_strategies.items()
            }
        }


class CDNManager:
    """CDN management and optimization system"""
    
    def __init__(self):
        self.cdn_configurations: Dict[str, CDNConfiguration] = {}
        self.content_distribution: Dict[str, List[str]] = defaultdict(list)
        self.performance_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Geographic optimization
        self.turkish_regions = {
            CacheRegion.ISTANBUL: {"lat": 41.0082, "lon": 28.9784, "population": 15_500_000},
            CacheRegion.ANKARA: {"lat": 39.9334, "lon": 32.8597, "population": 5_600_000},
            CacheRegion.IZMIR: {"lat": 38.4192, "lon": 27.1287, "population": 4_400_000},
            CacheRegion.BURSA: {"lat": 40.1969, "lon": 29.0616, "population": 3_100_000},
            CacheRegion.ANTALYA: {"lat": 36.8969, "lon": 30.7133, "population": 2_500_000},
            CacheRegion.ADANA: {"lat": 37.0000, "lon": 35.3213, "population": 2_300_000}
        }
        
        # Content optimization rules
        self.optimization_rules: Dict[ContentType, Dict[str, Any]] = {
            ContentType.STATIC_ASSETS: {
                "compression": True,
                "minification": True,
                "image_optimization": True,
                "cache_ttl": 86400
            },
            ContentType.EXAM_QUESTIONS: {
                "compression": True,
                "encryption": True,
                "cache_ttl": 300,
                "regional_distribution": True
            },
            ContentType.VIDEO_LECTURES: {
                "adaptive_bitrate": True,
                "compression": True,
                "cache_ttl": 43200,
                "regional_caching": True
            }
        }
    
    async def configure_cdn(self, config: CDNConfiguration) -> bool:
        """Configure CDN endpoint"""
        try:
            self.cdn_configurations[config.cdn_id] = config
            
            # Initialize performance tracking
            self.performance_metrics[config.cdn_id] = {
                "response_time": 0.0,
                "hit_rate": 0.0,
                "bandwidth_saved": 0.0,
                "requests_per_second": 0.0
            }
            
            logger.info(f"Configured CDN: {config.cdn_id} ({config.provider})")
            return True
            
        except Exception as e:
            logger.error(f"CDN configuration failed: {e}")
            return False
    
    async def distribute_content(
        self,
        content_url: str,
        content_type: ContentType,
        regions: List[CacheRegion],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Distribute content to CDN edge locations"""
        
        distribution_result = {}
        
        try:
            # Optimize content based on type
            optimized_content = await self._optimize_content(content_url, content_type)
            
            # Distribute to specified regions
            for region in regions:
                cdn_url = await self._upload_to_region(optimized_content, region, content_type)
                if cdn_url:
                    distribution_result[region.value] = cdn_url
                    self.content_distribution[content_url].append(region.value)
            
            logger.info(f"Distributed content to {len(distribution_result)} regions: {content_url}")
            return distribution_result
            
        except Exception as e:
            logger.error(f"Content distribution failed: {e}")
            return {}
    
    async def _optimize_content(self, content_url: str, content_type: ContentType) -> Dict[str, Any]:
        """Optimize content based on type and rules"""
        optimization_rules = self.optimization_rules.get(content_type, {})
        optimized_content = {"original_url": content_url}
        
        try:
            # Fetch original content
            async with aiohttp.ClientSession() as session:
                async with session.get(content_url) as response:
                    if response.status == 200:
                        content_data = await response.read()
                        content_size = len(content_data)
                        
                        # Apply compression
                        if optimization_rules.get("compression", False):
                            compressed_data = gzip.compress(content_data)
                            compression_ratio = len(compressed_data) / content_size
                            
                            optimized_content.update({
                                "compressed": True,
                                "compressed_data": base64.b64encode(compressed_data).decode(),
                                "compression_ratio": compression_ratio,
                                "original_size": content_size,
                                "compressed_size": len(compressed_data)
                            })
                        
                        # Apply image optimization
                        if optimization_rules.get("image_optimization", False) and self._is_image_content(content_url):
                            optimized_images = await self._optimize_images(content_data)
                            optimized_content["optimized_images"] = optimized_images
                        
                        # Apply encryption for sensitive content
                        if optimization_rules.get("encryption", False):
                            # This would involve encrypting exam questions, etc.
                            optimized_content["encrypted"] = True
                        
                        return optimized_content
            
        except Exception as e:
            logger.error(f"Content optimization failed: {e}")
            return {"original_url": content_url, "error": str(e)}
    
    def _is_image_content(self, url: str) -> bool:
        """Check if content is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        return any(path.endswith(ext) for ext in image_extensions)
    
    async def _optimize_images(self, image_data: bytes) -> Dict[str, Any]:
        """Optimize image content"""
        # This would involve actual image optimization (resize, format conversion, etc.)
        # For now, return mock optimization results
        return {
            "webp_version": True,
            "progressive_jpeg": True,
            "size_reduction": 0.3,  # 30% size reduction
            "formats_available": ["webp", "jpeg", "png"]
        }
    
    async def _upload_to_region(self, content: Dict[str, Any], region: CacheRegion, content_type: ContentType) -> Optional[str]:
        """Upload content to specific region"""
        try:
            # Mock CDN upload - in real implementation, use CDN provider APIs
            region_info = self.turkish_regions.get(region, {})
            
            # Generate CDN URL based on region
            cdn_url = f"https://cdn-{region.value}.kiro2.com/{content_type.value}/{uuid.uuid4()}"
            
            # Simulate upload delay based on content size
            if "compressed_size" in content:
                upload_delay = content["compressed_size"] / (1024 * 1024)  # 1MB per second
                await asyncio.sleep(min(upload_delay, 5.0))  # Max 5 seconds
            
            logger.info(f"Uploaded content to {region.value}: {cdn_url}")
            return cdn_url
            
        except Exception as e:
            logger.error(f"Upload to {region.value} failed: {e}")
            return None
    
    async def get_optimal_cdn_url(self, original_url: str, user_region: str) -> str:
        """Get optimal CDN URL for user location"""
        try:
            # Find closest region to user
            user_region_enum = None
            for region in CacheRegion:
                if region.value == user_region.lower():
                    user_region_enum = region
                    break
            
            if not user_region_enum:
                user_region_enum = CacheRegion.ISTANBUL  # Default to Istanbul
            
            # Check if content is distributed to user's region
            if original_url in self.content_distribution:
                available_regions = self.content_distribution[original_url]
                if user_region_enum.value in available_regions:
                    # Return regional CDN URL
                    return f"https://cdn-{user_region_enum.value}.kiro2.com/content/{hashlib.md5(original_url.encode()).hexdigest()}"
            
            # Fallback to global CDN
            return f"https://cdn-global.kiro2.com/content/{hashlib.md5(original_url.encode()).hexdigest()}"
            
        except Exception as e:
            logger.error(f"Optimal CDN URL selection failed: {e}")
            return original_url
    
    async def purge_cdn_cache(self, pattern: str, regions: Optional[List[CacheRegion]] = None) -> Dict[str, bool]:
        """Purge CDN cache for matching content"""
        purge_results = {}
        
        try:
            target_regions = regions or list(CacheRegion)
            
            for region in target_regions:
                # Mock CDN purge API call
                success = await self._purge_region_cache(region, pattern)
                purge_results[region.value] = success
            
            logger.info(f"Purged CDN cache for pattern '{pattern}' in {len(target_regions)} regions")
            return purge_results
            
        except Exception as e:
            logger.error(f"CDN cache purge failed: {e}")
            return {}
    
    async def _purge_region_cache(self, region: CacheRegion, pattern: str) -> bool:
        """Purge cache in specific region"""
        try:
            # Mock CDN API call
            await asyncio.sleep(0.1)  # Simulate API latency
            
            # Update performance metrics
            cdn_configs = list(self.cdn_configurations.values())
            if cdn_configs:
                cdn_id = cdn_configs[0].cdn_id
                if cdn_id in self.performance_metrics:
                    self.performance_metrics[cdn_id]["cache_purges"] = (
                        self.performance_metrics[cdn_id].get("cache_purges", 0) + 1
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Region cache purge failed for {region.value}: {e}")
            return False
    
    async def analyze_performance(self, time_range: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """Analyze CDN performance metrics"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - time_range
        
        analysis = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "cdn_performance": {},
            "regional_performance": {},
            "content_type_performance": {},
            "optimization_impact": {}
        }
        
        # Analyze each CDN configuration
        for cdn_id, config in self.cdn_configurations.items():
            metrics = self.performance_metrics.get(cdn_id, {})
            
            analysis["cdn_performance"][cdn_id] = {
                "provider": config.provider,
                "response_time_ms": metrics.get("response_time", 0) * 1000,
                "hit_rate_percent": metrics.get("hit_rate", 0) * 100,
                "bandwidth_saved_gb": metrics.get("bandwidth_saved", 0) / (1024**3),
                "requests_per_second": metrics.get("requests_per_second", 0),
                "uptime_percent": 99.9,  # Mock uptime
                "error_rate_percent": 0.1  # Mock error rate
            }
        
        # Regional performance analysis
        for region in CacheRegion:
            region_data = self.turkish_regions.get(region)
            if region_data:
                analysis["regional_performance"][region.value] = {
                    "population_served": region_data["population"],
                    "estimated_response_time": 50 + (region_data["population"] / 1000000) * 5,  # Mock calculation
                    "hit_rate": 85.0 + (hash(region.value) % 10),  # Mock hit rate
                    "bandwidth_usage_gb": region_data["population"] / 10000  # Mock bandwidth
                }
        
        # Content type performance
        for content_type in ContentType:
            rules = self.optimization_rules.get(content_type, {})
            analysis["content_type_performance"][content_type.value] = {
                "cache_ttl": rules.get("cache_ttl", 3600),
                "compression_enabled": rules.get("compression", False),
                "hit_rate_percent": 75.0 + (hash(content_type.value) % 20),  # Mock hit rate
                "average_size_kb": 100 + (hash(content_type.value) % 500)  # Mock size
            }
        
        # Optimization impact analysis
        analysis["optimization_impact"] = {
            "total_bandwidth_saved_gb": 150.5,  # Mock savings
            "average_response_time_improvement_ms": 45.2,
            "compression_ratio_average": 0.35,
            "image_optimization_savings_percent": 25.0,
            "cache_hit_rate_improvement": 12.5
        }
        
        return analysis
    
    def get_cdn_status(self) -> Dict[str, Any]:
        """Get current CDN system status"""
        total_configurations = len(self.cdn_configurations)
        total_content_items = sum(len(regions) for regions in self.content_distribution.values())
        
        # Calculate average performance across all CDNs
        avg_response_time = 0.0
        avg_hit_rate = 0.0
        
        if self.performance_metrics:
            response_times = [m.get("response_time", 0) for m in self.performance_metrics.values()]
            hit_rates = [m.get("hit_rate", 0) for m in self.performance_metrics.values()]
            
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            avg_hit_rate = statistics.mean(hit_rates) if hit_rates else 0.0
        
        return {
            "system_status": {
                "total_cdn_configurations": total_configurations,
                "total_distributed_content": total_content_items,
                "average_response_time_ms": avg_response_time * 1000,
                "average_hit_rate_percent": avg_hit_rate * 100,
                "operational_regions": len(self.turkish_regions)
            },
            "regional_distribution": {
                region.value: len([
                    content for content, regions in self.content_distribution.items()
                    if region.value in regions
                ])
                for region in CacheRegion
            },
            "content_optimization": {
                content_type.value: self.optimization_rules.get(content_type, {})
                for content_type in ContentType
            },
            "configurations": {
                cdn_id: {
                    "provider": config.provider,
                    "ssl_enabled": config.ssl_enabled,
                    "compression_enabled": config.compression_enabled,
                    "edge_locations": len(config.edge_locations)
                }
                for cdn_id, config in self.cdn_configurations.items()
            }
        }


class AdvancedCachingCDNManager:
    """Main manager combining caching and CDN capabilities"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.cdn_manager = CDNManager()
        
        # Integrated optimization
        self.cache_cdn_integration = True
        self.automatic_cdn_fallback = True
        
        # Turkish exam specific
        self.exam_peak_detection = True
        self.regional_optimization = True
        
        # Performance monitoring
        self.integrated_metrics: deque = deque(maxlen=1000)
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize integrated caching and CDN system"""
        try:
            # Initialize cache stores
            cache_config = config.get("cache", {})
            for cache_type_str, cache_settings in cache_config.items():
                cache_type = CacheType(cache_type_str)
                await self.cache_manager.initialize_cache_store(cache_type, cache_settings)
            
            # Initialize CDN configurations
            cdn_config = config.get("cdn", {})
            for cdn_settings in cdn_config.get("configurations", []):
                cdn_config_obj = CDNConfiguration(**cdn_settings)
                await self.cdn_manager.configure_cdn(cdn_config_obj)
            
            logger.info("Advanced Caching and CDN Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def smart_content_delivery(
        self,
        content_key: str,
        content_data: Any,
        content_type: ContentType,
        user_region: str,
        **options
    ) -> Dict[str, Any]:
        """Intelligent content delivery using both cache and CDN"""
        
        delivery_result = {
            "cache_used": False,
            "cdn_used": False,
            "delivery_method": "direct",
            "response_time_ms": 0.0,
            "content_size_bytes": 0,
            "optimized": False
        }
        
        start_time = time.time()
        
        try:
            # First, try cache
            cached_content = await self.cache_manager.get(content_key)
            if cached_content is not None:
                delivery_result.update({
                    "cache_used": True,
                    "delivery_method": "cache",
                    "content": cached_content
                })
                
            else:
                # Cache miss - check CDN
                if self.cache_cdn_integration:
                    cdn_url = await self.cdn_manager.get_optimal_cdn_url(
                        f"content://{content_key}", user_region
                    )
                    
                    # Try to fetch from CDN
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(cdn_url) as response:
                                if response.status == 200:
                                    cdn_content = await response.json()
                                    delivery_result.update({
                                        "cdn_used": True,
                                        "delivery_method": "cdn",
                                        "content": cdn_content
                                    })
                                    
                                    # Cache the CDN content for future requests
                                    await self.cache_manager.set(
                                        content_key, cdn_content, content_type
                                    )
                                    
                    except aiohttp.ClientError:
                        # CDN failed, use original content
                        delivery_result["content"] = content_data
                        delivery_result["delivery_method"] = "direct"
                
                else:
                    # Direct delivery
                    delivery_result["content"] = content_data
                    
                    # Cache for future requests
                    await self.cache_manager.set(content_key, content_data, content_type)
            
            # Calculate response time and content size
            delivery_result["response_time_ms"] = (time.time() - start_time) * 1000
            
            if "content" in delivery_result:
                content_str = json.dumps(delivery_result["content"]) if isinstance(delivery_result["content"], (dict, list)) else str(delivery_result["content"])
                delivery_result["content_size_bytes"] = len(content_str.encode('utf-8'))
            
            # Record integrated metrics
            metric = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "content_key": content_key,
                "content_type": content_type.value,
                "user_region": user_region,
                "delivery_result": delivery_result.copy()
            }
            self.integrated_metrics.append(metric)
            
            return delivery_result
            
        except Exception as e:
            logger.error(f"Smart content delivery failed: {e}")
            delivery_result["error"] = str(e)
            return delivery_result
    
    async def enable_exam_mode(self) -> None:
        """Enable exam mode for both caching and CDN"""
        await self.cache_manager.enable_exam_mode()
        
        # Adjust CDN settings for exam mode
        for cdn_config in self.cdn_manager.cdn_configurations.values():
            cdn_config.exam_content_ttl = 300  # 5 minutes during exams
            cdn_config.result_announcement_ttl = 60  # 1 minute for results
        
        logger.info("Integrated exam mode enabled for caching and CDN")
    
    async def disable_exam_mode(self) -> None:
        """Disable exam mode for both caching and CDN"""
        await self.cache_manager.disable_exam_mode()
        
        # Restore normal CDN settings
        for cdn_config in self.cdn_manager.cdn_configurations.values():
            cdn_config.exam_content_ttl = cdn_config.default_ttl
            cdn_config.result_announcement_ttl = cdn_config.default_ttl
        
        logger.info("Integrated exam mode disabled")
    
    async def optimize_for_turkish_regions(self) -> Dict[str, Any]:
        """Optimize cache and CDN distribution for Turkish regions"""
        optimization_result = {
            "cache_optimizations": {},
            "cdn_optimizations": {},
            "regional_improvements": {}
        }
        
        try:
            # Cache optimizations per region
            for region in CacheRegion:
                if region != CacheRegion.GLOBAL:
                    # Adjust cache strategies for regional patterns
                    regional_cache_config = {
                        "ttl_multiplier": 1.2 if region == CacheRegion.ISTANBUL else 1.0,
                        "priority_boost": 1.5 if region in [CacheRegion.ISTANBUL, CacheRegion.ANKARA] else 1.0,
                        "exam_content_preload": region in [CacheRegion.ISTANBUL, CacheRegion.ANKARA, CacheRegion.IZMIR]
                    }
                    
                    optimization_result["cache_optimizations"][region.value] = regional_cache_config
            
            # CDN optimizations
            for content_type in ContentType:
                if content_type in [ContentType.EXAM_QUESTIONS, ContentType.EXAM_RESULTS]:
                    # Distribute exam content to all Turkish regions
                    regions_to_distribute = [
                        CacheRegion.ISTANBUL, CacheRegion.ANKARA, CacheRegion.IZMIR,
                        CacheRegion.BURSA, CacheRegion.ANTALYA
                    ]
                    
                    optimization_result["cdn_optimizations"][content_type.value] = {
                        "regions": [r.value for r in regions_to_distribute],
                        "priority": "high",
                        "compression": True,
                        "regional_caching": True
                    }
            
            # Regional performance improvements
            for region, region_data in self.cdn_manager.turkish_regions.items():
                population_factor = region_data["population"] / 15_500_000  # Relative to Istanbul
                
                optimization_result["regional_improvements"][region.value] = {
                    "cache_capacity_multiplier": max(0.5, population_factor),
                    "cdn_priority_score": int(population_factor * 10),
                    "estimated_improvement_percent": min(population_factor * 20, 50)
                }
            
            logger.info("Turkish regional optimization completed")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Regional optimization failed: {e}")
            optimization_result["error"] = str(e)
            return optimization_result
    
    def get_integrated_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for cache and CDN"""
        cache_stats = self.cache_manager.get_cache_statistics()
        cdn_status = self.cdn_manager.get_cdn_status()
        
        # Calculate integrated metrics
        recent_metrics = list(self.integrated_metrics)[-100:]  # Last 100 requests
        
        cache_delivery_count = len([m for m in recent_metrics if m["delivery_result"]["cache_used"]])
        cdn_delivery_count = len([m for m in recent_metrics if m["delivery_result"]["cdn_used"]])
        direct_delivery_count = len([m for m in recent_metrics if m["delivery_result"]["delivery_method"] == "direct"])
        
        avg_response_time = statistics.mean([
            m["delivery_result"]["response_time_ms"] for m in recent_metrics
        ]) if recent_metrics else 0.0
        
        return {
            "integrated_overview": {
                "total_requests_analyzed": len(self.integrated_metrics),
                "recent_requests": len(recent_metrics),
                "cache_delivery_percent": (cache_delivery_count / max(len(recent_metrics), 1)) * 100,
                "cdn_delivery_percent": (cdn_delivery_count / max(len(recent_metrics), 1)) * 100,
                "direct_delivery_percent": (direct_delivery_count / max(len(recent_metrics), 1)) * 100,
                "average_response_time_ms": avg_response_time,
                "cache_cdn_integration_active": self.cache_cdn_integration
            },
            "cache_performance": cache_stats,
            "cdn_performance": cdn_status,
            "regional_distribution": {
                region.value: len([
                    m for m in recent_metrics 
                    if m.get("user_region") == region.value
                ])
                for region in CacheRegion
            },
            "content_type_analysis": {
                content_type.value: {
                    "requests": len([
                        m for m in recent_metrics 
                        if m.get("content_type") == content_type.value
                    ]),
                    "cache_hit_rate": len([
                        m for m in recent_metrics 
                        if m.get("content_type") == content_type.value and m["delivery_result"]["cache_used"]
                    ]) / max(len([m for m in recent_metrics if m.get("content_type") == content_type.value]), 1) * 100
                }
                for content_type in ContentType
            }
        }


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Advanced Caching and CDN Management System")
    print("=" * 55)
    
    async def test_caching_cdn_system():
        """Test advanced caching and CDN system"""
        
        # Create integrated manager
        manager = AdvancedCachingCDNManager()
        
        # Initialize system
        config = {
            "cache": {
                "memory": {"max_size_mb": 512},
                "redis": {"redis_url": "redis://localhost:6379"},
                "file_system": {"cache_directory": "/tmp/kiro2_cache"}
            },
            "cdn": {
                "configurations": [
                    {
                        "cdn_id": "cloudflare_turkey",
                        "provider": "cloudflare",
                        "origin_server": "https://api.kiro2.com",
                        "cdn_domain": "https://cdn.kiro2.com",
                        "edge_locations": ["Istanbul", "Ankara", "Frankfurt"]
                    }
                ]
            }
        }
        
        await manager.initialize(config)
        
        # Test smart content delivery
        print("Testing smart content delivery...")
        
        test_content = {
            "exam_questions": [
                {"id": 1, "question": "Türkiye'nin başkenti neresidir?", "options": ["İstanbul", "Ankara", "İzmir", "Bursa"]},
                {"id": 2, "question": "2+2 kaçtır?", "options": ["3", "4", "5", "6"]}
            ],
            "exam_type": "TYT",
            "subject": "Genel Kültür"
        }
        
        # Test delivery to different regions
        regions_to_test = ["istanbul", "ankara", "izmir"]
        
        for region in regions_to_test:
            delivery_result = await manager.smart_content_delivery(
                content_key=f"tyt_questions_{region}",
                content_data=test_content,
                content_type=ContentType.EXAM_QUESTIONS,
                user_region=region,
                exam_related=True
            )
            
            print(f"\nContent delivery to {region}:")
            print(f"  Delivery method: {delivery_result['delivery_method']}")
            print(f"  Cache used: {delivery_result['cache_used']}")
            print(f"  CDN used: {delivery_result['cdn_used']}")
            print(f"  Response time: {delivery_result['response_time_ms']:.2f}ms")
            print(f"  Content size: {delivery_result['content_size_bytes']} bytes")
        
        # Test exam mode
        print("\nTesting exam mode activation...")
        await manager.enable_exam_mode()
        
        # Test content delivery during exam mode
        exam_content = {
            "exam_id": "yks_2024_sample",
            "questions": ["Q1", "Q2", "Q3"],
            "time_limit": 180,
            "urgent": True
        }
        
        exam_delivery = await manager.smart_content_delivery(
            content_key="yks_2024_urgent",
            content_data=exam_content,
            content_type=ContentType.EXAM_QUESTIONS,
            user_region="istanbul",
            priority_level=10
        )
        
        print(f"Exam mode delivery: {exam_delivery['delivery_method']} ({exam_delivery['response_time_ms']:.2f}ms)")
        
        await manager.disable_exam_mode()
        
        # Test Turkish regional optimization
        print("\nTesting Turkish regional optimization...")
        optimization_result = await manager.optimize_for_turkish_regions()
        
        print("Regional optimization results:")
        for region, improvements in optimization_result["regional_improvements"].items():
            print(f"  {region}: {improvements['estimated_improvement_percent']:.1f}% improvement")
        
        # Generate performance report
        print("\nGenerating integrated performance report...")
        performance_report = manager.get_integrated_performance_report()
        
        print("\nPerformance Report Summary:")
        integrated = performance_report["integrated_overview"]
        print(f"  Total requests: {integrated['total_requests_analyzed']}")
        print(f"  Cache delivery: {integrated['cache_delivery_percent']:.1f}%")
        print(f"  CDN delivery: {integrated['cdn_delivery_percent']:.1f}%")
        print(f"  Direct delivery: {integrated['direct_delivery_percent']:.1f}%")
        print(f"  Average response time: {integrated['average_response_time_ms']:.2f}ms")
        
        cache_perf = performance_report["cache_performance"]["overview"]
        print(f"\nCache Performance:")
        print(f"  Hit rate: {cache_perf['hit_rate_percent']:.1f}%")
        print(f"  Total requests: {cache_perf['total_requests']}")
        print(f"  Memory usage: {performance_report['cache_performance']['memory']['usage_percent']:.1f}%")
        
        cdn_perf = performance_report["cdn_performance"]["system_status"]
        print(f"\nCDN Performance:")
        print(f"  Configurations: {cdn_perf['total_cdn_configurations']}")
        print(f"  Distributed content: {cdn_perf['total_distributed_content']}")
        print(f"  Operational regions: {cdn_perf['operational_regions']}")
        
        print(f"\nRegional Distribution:")
        for region, count in performance_report["regional_distribution"].items():
            print(f"  {region}: {count} requests")
        
        print("\nAdvanced caching and CDN system test completed!")
    
    # Run test
    asyncio.run(test_caching_cdn_system())