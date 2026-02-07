"""
KIRO2 Resource Manager
Sistem kaynaklarını yöneten ve optimize eden modül.
CPU, bellek, GPU, API rate limit ve ajan kaynaklarını kontrol eder.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Kaynak tipleri"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    API_CALLS = "api_calls"
    AGENTS = "agents"
    DISK_IO = "disk_io"
    NETWORK = "network"


class ResourceState(Enum):
    """Kaynak durumları"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    EXHAUSTED = "exhausted"
    THROTTLED = "throttled"
    ERROR = "error"


class AllocationPriority(Enum):
    """Kaynak tahsis öncelikleri"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ResourceQuota:
    """Kaynak kotası tanımı"""
    resource_type: ResourceType
    max_amount: float
    current_usage: float = 0.0
    reserved: float = 0.0
    unit: str = "units"
    refresh_interval: Optional[float] = None  # saniye
    last_refresh: Optional[datetime] = None
    
    @property
    def available(self) -> float:
        return max(0, self.max_amount - self.current_usage - self.reserved)
    
    @property
    def usage_percent(self) -> float:
        if self.max_amount == 0:
            return 100.0
        return (self.current_usage / self.max_amount) * 100


@dataclass
class ResourceAllocation:
    """Kaynak tahsisi"""
    allocation_id: str
    resource_type: ResourceType
    amount: float
    priority: AllocationPriority
    requester_id: str
    allocated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceRequest:
    """Kaynak talebi"""
    request_id: str
    resource_type: ResourceType
    amount: float
    priority: AllocationPriority
    requester_id: str
    timeout: float = 30.0
    can_partial: bool = False
    min_amount: Optional[float] = None




class ResourcePool:
    """Kaynak havuzu yöneticisi"""
    
    def __init__(self, resource_type: ResourceType, max_capacity: float, unit: str = "units"):
        self.resource_type = resource_type
        self.max_capacity = max_capacity
        self.unit = unit
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.waiting_queue: List[ResourceRequest] = []
        self._lock = asyncio.Lock()
        
    @property
    def current_usage(self) -> float:
        return sum(a.amount for a in self.allocations.values())
    
    @property
    def available(self) -> float:
        return max(0, self.max_capacity - self.current_usage)
    
    async def allocate(self, request: ResourceRequest) -> Optional[ResourceAllocation]:
        """Kaynak tahsis et"""
        async with self._lock:
            if request.amount <= self.available:
                allocation = ResourceAllocation(
                    allocation_id=f"alloc_{request.request_id}_{int(time.time()*1000)}",
                    resource_type=request.resource_type,
                    amount=request.amount,
                    priority=request.priority,
                    requester_id=request.requester_id
                )
                self.allocations[allocation.allocation_id] = allocation
                logger.info(f"Kaynak tahsis edildi: {allocation.allocation_id}, miktar: {request.amount}")
                return allocation
            elif request.can_partial and request.min_amount:
                if request.min_amount <= self.available:
                    allocation = ResourceAllocation(
                        allocation_id=f"alloc_{request.request_id}_{int(time.time()*1000)}",
                        resource_type=request.resource_type,
                        amount=self.available,
                        priority=request.priority,
                        requester_id=request.requester_id,
                        metadata={"partial": True, "requested": request.amount}
                    )
                    self.allocations[allocation.allocation_id] = allocation
                    return allocation
            return None
    
    async def release(self, allocation_id: str) -> bool:
        """Kaynak serbest bırak"""
        async with self._lock:
            if allocation_id in self.allocations:
                del self.allocations[allocation_id]
                logger.info(f"Kaynak serbest bırakıldı: {allocation_id}")
                await self._process_waiting_queue()
                return True
            return False
    
    async def _process_waiting_queue(self):
        """Bekleyen talepleri işle"""
        if not self.waiting_queue:
            return
        self.waiting_queue.sort(key=lambda r: r.priority.value)
        processed = []
        for request in self.waiting_queue:
            if request.amount <= self.available:
                await self.allocate(request)
                processed.append(request)
        for req in processed:
            self.waiting_queue.remove(req)




class RateLimiter:
    """API rate limiter"""
    
    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Rate limit kontrolü ve slot alma"""
        async with self._lock:
            now = time.time()
            self.requests = [t for t in self.requests if now - t < self.window_seconds]
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    async def wait_for_slot(self, timeout: float = 30.0) -> bool:
        """Slot bekle"""
        start = time.time()
        while time.time() - start < timeout:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        return False
    
    @property
    def remaining(self) -> int:
        now = time.time()
        active = len([t for t in self.requests if now - t < self.window_seconds])
        return max(0, self.max_requests - active)


class AgentPool:
    """Ajan havuzu yöneticisi"""
    
    def __init__(self, max_agents: int = 10):
        self.max_agents = max_agents
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_stats: Dict[str, Dict[str, float]] = {}
        self._lock = asyncio.Lock()
    
    async def spawn_agent(self, agent_id: str, agent_type: str, config: Dict[str, Any] = None) -> bool:
        """Yeni ajan başlat"""
        async with self._lock:
            if len(self.active_agents) >= self.max_agents:
                logger.warning(f"Maksimum ajan sayısına ulaşıldı: {self.max_agents}")
                return False
            self.active_agents[agent_id] = {
                "type": agent_type,
                "config": config or {},
                "started_at": datetime.now(),
                "status": "running"
            }
            self.agent_stats[agent_id] = {"tasks_completed": 0, "errors": 0, "uptime": 0}
            logger.info(f"Ajan başlatıldı: {agent_id} ({agent_type})")
            return True
    
    async def terminate_agent(self, agent_id: str) -> bool:
        """Ajanı sonlandır"""
        async with self._lock:
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]
                logger.info(f"Ajan sonlandırıldı: {agent_id}")
                return True
            return False
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self.active_agents.get(agent_id)
    
    @property
    def active_count(self) -> int:
        return len(self.active_agents)
    
    @property
    def available_slots(self) -> int:
        return self.max_agents - len(self.active_agents)




class ResourceManager:
    """Ana kaynak yöneticisi - tüm kaynakları koordine eder"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.resource_pools: Dict[ResourceType, ResourcePool] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.agent_pool = AgentPool(max_agents=self.config.get("max_agents", 10))
        self.quotas: Dict[str, ResourceQuota] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._initialized = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Kaynak yöneticisini başlat"""
        if self._initialized:
            return
        
        # Varsayılan kaynak havuzları
        defaults = {
            ResourceType.CPU: ("cpu_pool", 100.0, "percent"),
            ResourceType.MEMORY: ("memory_pool", 8192.0, "MB"),
            ResourceType.GPU: ("gpu_pool", 100.0, "percent"),
            ResourceType.API_CALLS: ("api_pool", 1000.0, "calls/min"),
            ResourceType.AGENTS: ("agent_pool", 10.0, "agents"),
        }
        
        for rtype, (name, capacity, unit) in defaults.items():
            cfg_capacity = self.config.get(f"{rtype.value}_capacity", capacity)
            self.resource_pools[rtype] = ResourcePool(rtype, cfg_capacity, unit)
        
        # Varsayılan rate limiter'lar
        self.rate_limiters["claude_api"] = RateLimiter(
            self.config.get("claude_rate_limit", 60), 60.0
        )
        self.rate_limiters["codex_api"] = RateLimiter(
            self.config.get("codex_rate_limit", 100), 60.0
        )
        self.rate_limiters["openai_api"] = RateLimiter(
            self.config.get("openai_rate_limit", 60), 60.0
        )
        
        self._initialized = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("ResourceManager başlatıldı")
    
    async def shutdown(self):
        """Kaynak yöneticisini kapat"""
        if self._monitor_task:
            self._monitor_task.cancel()
        for pool in self.resource_pools.values():
            pool.allocations.clear()
        for agent_id in list(self.agent_pool.active_agents.keys()):
            await self.agent_pool.terminate_agent(agent_id)
        self._initialized = False
        logger.info("ResourceManager kapatıldı")
    
    async def request_resource(self, request: ResourceRequest) -> Optional[ResourceAllocation]:
        """Kaynak talep et"""
        if request.resource_type not in self.resource_pools:
            logger.error(f"Bilinmeyen kaynak tipi: {request.resource_type}")
            return None
        
        pool = self.resource_pools[request.resource_type]
        allocation = await pool.allocate(request)
        
        if allocation:
            await self._trigger_callback("resource_allocated", allocation)
        else:
            await self._trigger_callback("resource_denied", request)
        
        return allocation


