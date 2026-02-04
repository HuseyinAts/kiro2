"""
KIRO2 Unified Load Balancing and Auto-Scaling System
Advanced load balancing and auto-scaling for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Birleşik Yük Dengeleme ve Otomatik Ölçeklendirme
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from enum import Enum
import json
import uuid
import sqlite3
from pathlib import Path
import hashlib
import statistics
import math
from collections import defaultdict, deque
import aiohttp
import psutil
import docker
import kubernetes
from kubernetes import client, config as k8s_config

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.PERFORMANCE)
config = get_unified_config()


class LoadBalancerType(Enum):
    """Load balancer types"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    GEOGRAPHIC = "geographic"
    RESOURCE_BASED = "resource_based"
    EXAM_AWARE = "exam_aware"  # Turkish exam-specific


class ScalingTrigger(Enum):
    """Auto-scaling trigger types"""
    CPU_THRESHOLD = "cpu_threshold"
    MEMORY_THRESHOLD = "memory_threshold"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"
    EXAM_SCHEDULE = "exam_schedule"  # Turkish exam schedule-based
    USER_REGISTRATION = "user_registration"  # Registration surge
    CONCURRENT_USERS = "concurrent_users"


class InstanceState(Enum):
    """Instance states"""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    SCALING_UP = "scaling_up"
    SCALING_DOWN = "scaling_down"
    TERMINATING = "terminating"
    MAINTENANCE = "maintenance"


class TrafficPattern(Enum):
    """Traffic pattern types for Turkish education"""
    NORMAL = "normal"
    EXAM_RUSH = "exam_rush"  # YKS, TYT, AYT rush periods
    REGISTRATION_SURGE = "registration_surge"
    RESULTS_ANNOUNCEMENT = "results_announcement"
    WEEKEND_STUDY = "weekend_study"
    EVENING_PEAK = "evening_peak"
    HOLIDAY_LOW = "holiday_low"


@dataclass
class ServerInstance:
    """Server instance definition"""
    instance_id: str
    instance_type: str
    region: str
    availability_zone: str
    
    # Network configuration
    ip_address: str
    port: int = 80
    weight: int = 100
    
    # Health metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: float = 0.0
    
    # Performance metrics
    active_connections: int = 0
    requests_per_second: float = 0.0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    
    # State management
    state: InstanceState = InstanceState.INITIALIZING
    last_health_check: Optional[datetime] = None
    uptime: timedelta = field(default_factory=timedelta)
    
    # Capacity and limits
    max_connections: int = 1000
    max_cpu_threshold: float = 80.0
    max_memory_threshold: float = 85.0
    
    # Turkish exam specific
    exam_capacity: int = 500  # Concurrent exam takers
    subject_specialization: List[str] = field(default_factory=list)
    
    # Geographic info for Turkish regions
    turkish_region: str = "istanbul"  # istanbul, ankara, izmir, etc.
    serves_provinces: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.instance_id:
            self.instance_id = str(uuid.uuid4())
        if not self.last_health_check:
            self.last_health_check = datetime.now(timezone.utc)
    
    def is_healthy(self) -> bool:
        """Check if instance is healthy"""
        if self.state == InstanceState.UNHEALTHY:
            return False
        
        # Check resource thresholds
        if self.cpu_usage > self.max_cpu_threshold:
            return False
        
        if self.memory_usage > self.max_memory_threshold:
            return False
        
        # Check error rate
        if self.error_rate > 5.0:  # 5% error rate threshold
            return False
        
        # Check if last health check is recent
        if self.last_health_check:
            time_since_check = datetime.now(timezone.utc) - self.last_health_check
            if time_since_check > timedelta(minutes=5):
                return False
        
        return True
    
    def can_handle_request(self) -> bool:
        """Check if instance can handle more requests"""
        if not self.is_healthy():
            return False
        
        if self.active_connections >= self.max_connections:
            return False
        
        return True
    
    def calculate_load_score(self) -> float:
        """Calculate overall load score (0-100)"""
        cpu_score = self.cpu_usage
        memory_score = self.memory_usage
        connection_score = (self.active_connections / self.max_connections) * 100
        response_time_score = min(self.average_response_time * 10, 100)
        
        # Weighted average
        load_score = (
            cpu_score * 0.3 +
            memory_score * 0.3 +
            connection_score * 0.25 +
            response_time_score * 0.15
        )
        
        return min(max(load_score, 0.0), 100.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "instance_id": self.instance_id,
            "instance_type": self.instance_type,
            "region": self.region,
            "availability_zone": self.availability_zone,
            "network": {
                "ip_address": self.ip_address,
                "port": self.port,
                "weight": self.weight
            },
            "health_metrics": {
                "cpu_usage": self.cpu_usage,
                "memory_usage": self.memory_usage,
                "disk_usage": self.disk_usage,
                "network_io": self.network_io
            },
            "performance_metrics": {
                "active_connections": self.active_connections,
                "requests_per_second": self.requests_per_second,
                "average_response_time": self.average_response_time,
                "error_rate": self.error_rate
            },
            "state": self.state.value,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "uptime_seconds": self.uptime.total_seconds(),
            "capacity": {
                "max_connections": self.max_connections,
                "exam_capacity": self.exam_capacity,
                "load_score": self.calculate_load_score()
            },
            "turkish_config": {
                "turkish_region": self.turkish_region,
                "serves_provinces": self.serves_provinces,
                "subject_specialization": self.subject_specialization
            }
        }


@dataclass
class LoadBalancingRule:
    """Load balancing rule configuration"""
    rule_id: str
    rule_name: str
    algorithm: LoadBalancerType
    
    # Rule conditions
    path_patterns: List[str] = field(default_factory=list)
    header_conditions: Dict[str, str] = field(default_factory=dict)
    geographic_conditions: List[str] = field(default_factory=list)
    
    # Turkish exam specific conditions
    exam_types: List[str] = field(default_factory=list)  # TYT, AYT, YKS
    subject_filters: List[str] = field(default_factory=list)
    user_types: List[str] = field(default_factory=list)  # student, teacher, admin
    
    # Weights and priorities
    weight: int = 100
    priority: int = 1
    
    # Health check configuration
    health_check_enabled: bool = True
    health_check_interval: int = 30
    health_check_timeout: int = 5
    health_check_path: str = "/health"
    
    # Failover configuration
    failover_enabled: bool = True
    max_retries: int = 3
    retry_timeout: int = 1
    
    def matches_request(self, request_data: Dict[str, Any]) -> bool:
        """Check if request matches this rule"""
        path = request_data.get("path", "")
        headers = request_data.get("headers", {})
        user_location = request_data.get("user_location", "")
        
        # Path pattern matching
        if self.path_patterns:
            if not any(pattern in path for pattern in self.path_patterns):
                return False
        
        # Header conditions
        for header_key, expected_value in self.header_conditions.items():
            if headers.get(header_key) != expected_value:
                return False
        
        # Geographic conditions
        if self.geographic_conditions:
            if user_location not in self.geographic_conditions:
                return False
        
        # Exam type matching
        exam_type = request_data.get("exam_type", "")
        if self.exam_types and exam_type not in self.exam_types:
            return False
        
        return True


@dataclass
class AutoScalingPolicy:
    """Auto-scaling policy configuration"""
    policy_id: str
    policy_name: str
    
    # Scaling triggers
    triggers: List[ScalingTrigger] = field(default_factory=list)
    trigger_thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Scaling parameters
    min_instances: int = 2
    max_instances: int = 50
    desired_capacity: int = 5
    
    # Scaling behavior
    scale_up_cooldown: int = 300  # seconds
    scale_down_cooldown: int = 600  # seconds
    scale_up_increment: int = 2
    scale_down_increment: int = 1
    
    # Turkish exam specific
    exam_schedule_scaling: bool = True
    pre_exam_scale_minutes: int = 60
    post_exam_scale_minutes: int = 30
    
    # Time-based scaling
    time_based_scaling: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Instance configuration
    instance_type: str = "t3.medium"
    instance_regions: List[str] = field(default_factory=lambda: ["istanbul", "ankara"])
    
    def __post_init__(self):
        if not self.policy_id:
            self.policy_id = str(uuid.uuid4())
        
        # Default thresholds
        if not self.trigger_thresholds:
            self.trigger_thresholds = {
                "cpu_threshold": 70.0,
                "memory_threshold": 80.0,
                "request_rate": 1000.0,
                "response_time": 2.0,
                "concurrent_users": 5000
            }
        
        # Default time-based scaling for Turkish student patterns
        if not self.time_based_scaling:
            self.time_based_scaling = {
                "weekdays": {
                    "19:00": 10,  # Evening study peak
                    "22:00": 5,   # Late evening
                    "02:00": 2    # Night minimum
                },
                "weekends": {
                    "14:00": 8,   # Afternoon peak
                    "20:00": 12,  # Evening peak
                    "00:00": 3    # Night minimum
                }
            }
    
    def should_scale_up(self, metrics: Dict[str, float]) -> bool:
        """Check if scaling up is needed"""
        for trigger in self.triggers:
            threshold = self.trigger_thresholds.get(trigger.value, 0)
            metric_value = metrics.get(trigger.value, 0)
            
            if metric_value > threshold:
                return True
        
        return False
    
    def should_scale_down(self, metrics: Dict[str, float]) -> bool:
        """Check if scaling down is needed"""
        for trigger in self.triggers:
            threshold = self.trigger_thresholds.get(trigger.value, 0)
            metric_value = metrics.get(trigger.value, 0)
            
            # Scale down thresholds are typically lower
            scale_down_threshold = threshold * 0.5
            
            if metric_value > scale_down_threshold:
                return False
        
        return True


class LoadBalancer:
    """Advanced load balancer implementation"""
    
    def __init__(self):
        self.instances: Dict[str, ServerInstance] = {}
        self.rules: Dict[str, LoadBalancingRule] = {}
        self.sticky_sessions: Dict[str, str] = {}  # session_id -> instance_id
        
        # Request routing cache
        self.routing_cache: Dict[str, str] = {}
        self.cache_ttl = timedelta(minutes=5)
        
        # Health monitoring
        self.health_check_interval = 30
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self.request_count = 0
        self.total_response_time = 0.0
        self.error_count = 0
        
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default load balancing rules"""
        
        # API requests rule
        api_rule = LoadBalancingRule(
            rule_id="api_rule",
            rule_name="API Requests",
            algorithm=LoadBalancerType.LEAST_RESPONSE_TIME,
            path_patterns=["/api/"],
            priority=1
        )
        
        # Static content rule
        static_rule = LoadBalancingRule(
            rule_id="static_rule",
            rule_name="Static Content",
            algorithm=LoadBalancerType.ROUND_ROBIN,
            path_patterns=["/static/", "/assets/", "/images/"],
            priority=2
        )
        
        # Exam-specific rule for Turkish exams
        exam_rule = LoadBalancingRule(
            rule_id="exam_rule",
            rule_name="Turkish Exam Requests",
            algorithm=LoadBalancerType.EXAM_AWARE,
            path_patterns=["/exam/", "/test/"],
            exam_types=["TYT", "AYT", "YKS"],
            priority=0  # Highest priority
        )
        
        self.rules = {
            "api_rule": api_rule,
            "static_rule": static_rule,
            "exam_rule": exam_rule
        }
    
    def add_instance(self, instance: ServerInstance) -> None:
        """Add server instance to load balancer"""
        self.instances[instance.instance_id] = instance
        logger.info(f"Added server instance: {instance.instance_id} ({instance.ip_address})")
    
    def remove_instance(self, instance_id: str) -> bool:
        """Remove server instance from load balancer"""
        if instance_id in self.instances:
            del self.instances[instance_id]
            
            # Clear routing cache entries for this instance
            cache_keys_to_remove = [
                key for key, value in self.routing_cache.items() 
                if value == instance_id
            ]
            for key in cache_keys_to_remove:
                del self.routing_cache[key]
            
            logger.info(f"Removed server instance: {instance_id}")
            return True
        
        return False
    
    async def route_request(self, request_data: Dict[str, Any]) -> Optional[ServerInstance]:
        """Route request to appropriate server instance"""
        try:
            # Find matching rule
            matching_rule = self._find_matching_rule(request_data)
            if not matching_rule:
                matching_rule = list(self.rules.values())[0]  # Default to first rule
            
            # Check for sticky session
            session_id = request_data.get("session_id")
            if session_id and session_id in self.sticky_sessions:
                instance_id = self.sticky_sessions[session_id]
                if instance_id in self.instances:
                    instance = self.instances[instance_id]
                    if instance.can_handle_request():
                        return instance
                    else:
                        # Remove sticky session if instance can't handle request
                        del self.sticky_sessions[session_id]
            
            # Check routing cache
            cache_key = self._create_cache_key(request_data, matching_rule)
            if cache_key in self.routing_cache:
                instance_id = self.routing_cache[cache_key]
                if instance_id in self.instances:
                    instance = self.instances[instance_id]
                    if instance.can_handle_request():
                        return instance
            
            # Select instance based on algorithm
            selected_instance = await self._select_instance(matching_rule, request_data)
            
            # Update cache and sticky session
            if selected_instance:
                self.routing_cache[cache_key] = selected_instance.instance_id
                if session_id:
                    self.sticky_sessions[session_id] = selected_instance.instance_id
            
            return selected_instance
            
        except Exception as e:
            logger.error(f"Request routing failed: {e}")
            return None
    
    def _find_matching_rule(self, request_data: Dict[str, Any]) -> Optional[LoadBalancingRule]:
        """Find the best matching rule for request"""
        matching_rules = []
        
        for rule in self.rules.values():
            if rule.matches_request(request_data):
                matching_rules.append(rule)
        
        if matching_rules:
            # Sort by priority (lower number = higher priority)
            matching_rules.sort(key=lambda r: r.priority)
            return matching_rules[0]
        
        return None
    
    def _create_cache_key(self, request_data: Dict[str, Any], rule: LoadBalancingRule) -> str:
        """Create cache key for request routing"""
        key_components = [
            request_data.get("path", ""),
            request_data.get("user_location", ""),
            request_data.get("exam_type", ""),
            rule.rule_id
        ]
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _select_instance(self, rule: LoadBalancingRule, request_data: Dict[str, Any]) -> Optional[ServerInstance]:
        """Select instance based on load balancing algorithm"""
        healthy_instances = [
            instance for instance in self.instances.values()
            if instance.can_handle_request()
        ]
        
        if not healthy_instances:
            return None
        
        algorithm = rule.algorithm
        
        if algorithm == LoadBalancerType.ROUND_ROBIN:
            return self._round_robin_selection(healthy_instances)
        
        elif algorithm == LoadBalancerType.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(healthy_instances)
        
        elif algorithm == LoadBalancerType.LEAST_CONNECTIONS:
            return min(healthy_instances, key=lambda i: i.active_connections)
        
        elif algorithm == LoadBalancerType.LEAST_RESPONSE_TIME:
            return min(healthy_instances, key=lambda i: i.average_response_time)
        
        elif algorithm == LoadBalancerType.IP_HASH:
            return self._ip_hash_selection(healthy_instances, request_data)
        
        elif algorithm == LoadBalancerType.GEOGRAPHIC:
            return self._geographic_selection(healthy_instances, request_data)
        
        elif algorithm == LoadBalancerType.RESOURCE_BASED:
            return self._resource_based_selection(healthy_instances)
        
        elif algorithm == LoadBalancerType.EXAM_AWARE:
            return self._exam_aware_selection(healthy_instances, request_data)
        
        else:
            return self._round_robin_selection(healthy_instances)
    
    def _round_robin_selection(self, instances: List[ServerInstance]) -> ServerInstance:
        """Round-robin instance selection"""
        if not hasattr(self, '_round_robin_index'):
            self._round_robin_index = 0
        
        instance = instances[self._round_robin_index % len(instances)]
        self._round_robin_index += 1
        
        return instance
    
    def _weighted_round_robin_selection(self, instances: List[ServerInstance]) -> ServerInstance:
        """Weighted round-robin instance selection"""
        if not hasattr(self, '_weighted_counts'):
            self._weighted_counts = {instance.instance_id: 0 for instance in instances}
        
        # Find instance with lowest weighted count
        best_instance = None
        best_ratio = float('inf')
        
        for instance in instances:
            if instance.weight > 0:
                current_count = self._weighted_counts.get(instance.instance_id, 0)
                ratio = current_count / instance.weight
                
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_instance = instance
        
        if best_instance:
            self._weighted_counts[best_instance.instance_id] += 1
        
        return best_instance or instances[0]
    
    def _ip_hash_selection(self, instances: List[ServerInstance], request_data: Dict[str, Any]) -> ServerInstance:
        """IP hash-based instance selection"""
        client_ip = request_data.get("client_ip", "127.0.0.1")
        hash_value = hash(client_ip)
        index = hash_value % len(instances)
        
        return instances[index]
    
    def _geographic_selection(self, instances: List[ServerInstance], request_data: Dict[str, Any]) -> ServerInstance:
        """Geographic proximity-based instance selection"""
        user_location = request_data.get("user_location", "istanbul")
        
        # Find instances in the same region first
        same_region_instances = [
            instance for instance in instances
            if instance.turkish_region == user_location or user_location in instance.serves_provinces
        ]
        
        if same_region_instances:
            # Use least connections among same region instances
            return min(same_region_instances, key=lambda i: i.active_connections)
        
        # Fallback to least connections overall
        return min(instances, key=lambda i: i.active_connections)
    
    def _resource_based_selection(self, instances: List[ServerInstance]) -> ServerInstance:
        """Resource-based instance selection (lowest load score)"""
        return min(instances, key=lambda i: i.calculate_load_score())
    
    def _exam_aware_selection(self, instances: List[ServerInstance], request_data: Dict[str, Any]) -> ServerInstance:
        """Turkish exam-aware instance selection"""
        exam_type = request_data.get("exam_type", "")
        subject = request_data.get("subject", "")
        
        # Find specialized instances for this exam/subject
        specialized_instances = []
        for instance in instances:
            if exam_type in instance.subject_specialization or subject in instance.subject_specialization:
                specialized_instances.append(instance)
        
        if specialized_instances:
            # Among specialized instances, choose least loaded
            return min(specialized_instances, key=lambda i: i.calculate_load_score())
        
        # Filter instances with available exam capacity
        available_instances = [
            instance for instance in instances
            if instance.active_connections < instance.exam_capacity
        ]
        
        if available_instances:
            return min(available_instances, key=lambda i: i.calculate_load_score())
        
        # Fallback to least loaded overall
        return min(instances, key=lambda i: i.calculate_load_score())
    
    async def update_instance_metrics(self, instance_id: str, metrics: Dict[str, Any]) -> None:
        """Update instance health and performance metrics"""
        if instance_id not in self.instances:
            return
        
        instance = self.instances[instance_id]
        
        # Update health metrics
        instance.cpu_usage = metrics.get("cpu_usage", instance.cpu_usage)
        instance.memory_usage = metrics.get("memory_usage", instance.memory_usage)
        instance.disk_usage = metrics.get("disk_usage", instance.disk_usage)
        instance.network_io = metrics.get("network_io", instance.network_io)
        
        # Update performance metrics
        instance.active_connections = metrics.get("active_connections", instance.active_connections)
        instance.requests_per_second = metrics.get("requests_per_second", instance.requests_per_second)
        instance.average_response_time = metrics.get("average_response_time", instance.average_response_time)
        instance.error_rate = metrics.get("error_rate", instance.error_rate)
        
        # Update health check timestamp
        instance.last_health_check = datetime.now(timezone.utc)
        
        # Update state based on health
        if instance.is_healthy():
            if instance.state == InstanceState.UNHEALTHY:
                instance.state = InstanceState.HEALTHY
                logger.info(f"Instance {instance_id} recovered to healthy state")
        else:
            if instance.state == InstanceState.HEALTHY:
                instance.state = InstanceState.UNHEALTHY
                logger.warning(f"Instance {instance_id} marked as unhealthy")
    
    async def start_health_monitoring(self) -> None:
        """Start health monitoring for all instances"""
        if self.health_check_task and not self.health_check_task.done():
            return
        
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health monitoring started")
    
    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring"""
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            await self.health_check_task
        
        logger.info("Health monitoring stopped")
    
    async def _health_check_loop(self) -> None:
        """Health check monitoring loop"""
        while True:
            try:
                for instance in self.instances.values():
                    await self._perform_health_check(instance)
                
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(10)
    
    async def _perform_health_check(self, instance: ServerInstance) -> None:
        """Perform health check on individual instance"""
        try:
            health_url = f"http://{instance.ip_address}:{instance.port}/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self.update_instance_metrics(instance.instance_id, data)
                    else:
                        logger.warning(f"Health check failed for {instance.instance_id}: HTTP {response.status}")
                        instance.state = InstanceState.UNHEALTHY
                        
        except Exception as e:
            logger.error(f"Health check error for {instance.instance_id}: {e}")
            instance.state = InstanceState.UNHEALTHY
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        healthy_instances = sum(1 for i in self.instances.values() if i.is_healthy())
        total_instances = len(self.instances)
        
        avg_response_time = (
            self.total_response_time / max(self.request_count, 1)
            if self.request_count > 0 else 0.0
        )
        
        error_rate = (
            (self.error_count / max(self.request_count, 1)) * 100
            if self.request_count > 0 else 0.0
        )
        
        return {
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate_percent": error_rate,
            "average_response_time": avg_response_time,
            "active_sessions": len(self.sticky_sessions),
            "cache_entries": len(self.routing_cache),
            "rules_configured": len(self.rules),
            "instances": {
                instance_id: instance.to_dict()
                for instance_id, instance in self.instances.items()
            }
        }


class AutoScalingManager:
    """Auto-scaling manager for dynamic capacity management"""
    
    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.policies: Dict[str, AutoScalingPolicy] = {}
        
        # Scaling history
        self.scaling_history: deque = deque(maxlen=1000)
        self.last_scale_up: Optional[datetime] = None
        self.last_scale_down: Optional[datetime] = None
        
        # Current metrics
        self.current_metrics: Dict[str, float] = {}
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Exam schedule awareness (Turkish education system)
        self.exam_schedules: Dict[str, List[datetime]] = {}
        
        # Kubernetes client (if using K8s)
        self.k8s_client: Optional[client.AppsV1Api] = None
        
        # Docker client (if using Docker)
        self.docker_client: Optional[docker.DockerClient] = None
        
        self._initialize_default_policy()
        self._load_exam_schedules()
    
    def _initialize_default_policy(self) -> None:
        """Initialize default auto-scaling policy"""
        default_policy = AutoScalingPolicy(
            policy_id="default_policy",
            policy_name="Default Auto-Scaling",
            triggers=[
                ScalingTrigger.CPU_THRESHOLD,
                ScalingTrigger.MEMORY_THRESHOLD,
                ScalingTrigger.CONCURRENT_USERS
            ],
            min_instances=3,
            max_instances=50,
            desired_capacity=5
        )
        
        self.policies["default"] = default_policy
    
    def _load_exam_schedules(self) -> None:
        """Load Turkish exam schedules for predictive scaling"""
        # Mock exam schedules - in real implementation, load from database
        now = datetime.now(timezone.utc)
        
        self.exam_schedules = {
            "YKS": [
                now + timedelta(days=30),  # Mock YKS date
                now + timedelta(days=120)  # Next YKS date
            ],
            "TYT": [
                now + timedelta(days=25),
                now + timedelta(days=115)
            ],
            "AYT": [
                now + timedelta(days=32),
                now + timedelta(days=122)
            ]
        }
    
    def add_policy(self, policy: AutoScalingPolicy) -> None:
        """Add auto-scaling policy"""
        self.policies[policy.policy_id] = policy
        logger.info(f"Added auto-scaling policy: {policy.policy_name}")
    
    async def update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update current system metrics"""
        self.current_metrics.update(metrics)
        
        # Store in history
        for metric_name, value in metrics.items():
            self.metrics_history[metric_name].append(value)
        
        # Trigger scaling evaluation
        await self._evaluate_scaling()
    
    async def _evaluate_scaling(self) -> None:
        """Evaluate if scaling is needed"""
        for policy in self.policies.values():
            try:
                # Check cooldown periods
                if not self._can_scale_up(policy) and not self._can_scale_down(policy):
                    continue
                
                # Check exam-based scaling
                await self._check_exam_based_scaling(policy)
                
                # Check metrics-based scaling
                if policy.should_scale_up(self.current_metrics):
                    if self._can_scale_up(policy):
                        await self._scale_up(policy)
                
                elif policy.should_scale_down(self.current_metrics):
                    if self._can_scale_down(policy):
                        await self._scale_down(policy)
                
            except Exception as e:
                logger.error(f"Scaling evaluation failed for policy {policy.policy_id}: {e}")
    
    def _can_scale_up(self, policy: AutoScalingPolicy) -> bool:
        """Check if can scale up (cooldown check)"""
        if self.last_scale_up:
            cooldown_elapsed = (datetime.now(timezone.utc) - self.last_scale_up).total_seconds()
            return cooldown_elapsed >= policy.scale_up_cooldown
        return True
    
    def _can_scale_down(self, policy: AutoScalingPolicy) -> bool:
        """Check if can scale down (cooldown check)"""
        if self.last_scale_down:
            cooldown_elapsed = (datetime.now(timezone.utc) - self.last_scale_down).total_seconds()
            return cooldown_elapsed >= policy.scale_down_cooldown
        return True
    
    async def _check_exam_based_scaling(self, policy: AutoScalingPolicy) -> None:
        """Check if exam-based scaling is needed"""
        if not policy.exam_schedule_scaling:
            return
        
        now = datetime.now(timezone.utc)
        
        for exam_type, dates in self.exam_schedules.items():
            for exam_date in dates:
                # Check if exam is approaching
                time_until_exam = (exam_date - now).total_seconds() / 60  # minutes
                
                if 0 < time_until_exam <= policy.pre_exam_scale_minutes:
                    # Scale up before exam
                    target_capacity = min(policy.max_instances, policy.desired_capacity * 2)
                    await self._scale_to_capacity(policy, target_capacity, f"Pre-{exam_type} scaling")
                
                elif -policy.post_exam_scale_minutes <= time_until_exam <= 0:
                    # Scale down after exam
                    target_capacity = policy.desired_capacity
                    await self._scale_to_capacity(policy, target_capacity, f"Post-{exam_type} scaling")
    
    async def _scale_up(self, policy: AutoScalingPolicy) -> None:
        """Scale up instances"""
        current_count = len([i for i in self.load_balancer.instances.values() if i.is_healthy()])
        target_count = min(policy.max_instances, current_count + policy.scale_up_increment)
        
        instances_to_add = target_count - current_count
        
        if instances_to_add > 0:
            await self._launch_instances(policy, instances_to_add)
            self.last_scale_up = datetime.now(timezone.utc)
            
            # Log scaling event
            scaling_event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "scale_up",
                "policy_id": policy.policy_id,
                "instances_added": instances_to_add,
                "total_instances": target_count,
                "trigger_metrics": self.current_metrics.copy()
            }
            self.scaling_history.append(scaling_event)
            
            logger.info(f"Scaled up: Added {instances_to_add} instances (total: {target_count})")
    
    async def _scale_down(self, policy: AutoScalingPolicy) -> None:
        """Scale down instances"""
        current_count = len([i for i in self.load_balancer.instances.values() if i.is_healthy()])
        target_count = max(policy.min_instances, current_count - policy.scale_down_increment)
        
        instances_to_remove = current_count - target_count
        
        if instances_to_remove > 0:
            await self._terminate_instances(policy, instances_to_remove)
            self.last_scale_down = datetime.now(timezone.utc)
            
            # Log scaling event
            scaling_event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "scale_down",
                "policy_id": policy.policy_id,
                "instances_removed": instances_to_remove,
                "total_instances": target_count,
                "trigger_metrics": self.current_metrics.copy()
            }
            self.scaling_history.append(scaling_event)
            
            logger.info(f"Scaled down: Removed {instances_to_remove} instances (total: {target_count})")
    
    async def _scale_to_capacity(self, policy: AutoScalingPolicy, target_capacity: int, reason: str) -> None:
        """Scale to specific capacity"""
        current_count = len([i for i in self.load_balancer.instances.values() if i.is_healthy()])
        
        if target_capacity > current_count:
            instances_to_add = target_capacity - current_count
            await self._launch_instances(policy, instances_to_add)
            self.last_scale_up = datetime.now(timezone.utc)
        elif target_capacity < current_count:
            instances_to_remove = current_count - target_capacity
            await self._terminate_instances(policy, instances_to_remove)
            self.last_scale_down = datetime.now(timezone.utc)
        
        # Log scaling event
        scaling_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "scale_to_capacity",
            "policy_id": policy.policy_id,
            "target_capacity": target_capacity,
            "current_capacity": current_count,
            "reason": reason
        }
        self.scaling_history.append(scaling_event)
        
        logger.info(f"Scaled to capacity: {target_capacity} ({reason})")
    
    async def _launch_instances(self, policy: AutoScalingPolicy, count: int) -> None:
        """Launch new instances"""
        for i in range(count):
            try:
                # Create new server instance
                instance = await self._create_server_instance(policy)
                if instance:
                    self.load_balancer.add_instance(instance)
                    logger.info(f"Launched new instance: {instance.instance_id}")
            except Exception as e:
                logger.error(f"Failed to launch instance: {e}")
    
    async def _create_server_instance(self, policy: AutoScalingPolicy) -> Optional[ServerInstance]:
        """Create a new server instance"""
        try:
            # Generate instance configuration
            instance_id = str(uuid.uuid4())
            
            # Mock instance creation - in real implementation, use cloud provider APIs
            instance = ServerInstance(
                instance_id=instance_id,
                instance_type=policy.instance_type,
                region=policy.instance_regions[0],
                availability_zone=f"{policy.instance_regions[0]}-1a",
                ip_address=f"10.0.{len(self.load_balancer.instances)}.{100 + len(self.load_balancer.instances)}",
                port=80,
                state=InstanceState.INITIALIZING,
                turkish_region=policy.instance_regions[0],
                serves_provinces=["İstanbul", "Kocaeli", "Sakarya"] if policy.instance_regions[0] == "istanbul" else ["Ankara", "Eskişehir"]
            )
            
            # Simulate initialization time
            await asyncio.sleep(2)
            instance.state = InstanceState.HEALTHY
            
            return instance
            
        except Exception as e:
            logger.error(f"Instance creation failed: {e}")
            return None
    
    async def _terminate_instances(self, policy: AutoScalingPolicy, count: int) -> None:
        """Terminate instances"""
        # Find least loaded instances to terminate
        healthy_instances = [
            i for i in self.load_balancer.instances.values()
            if i.is_healthy() and i.state != InstanceState.TERMINATING
        ]
        
        # Sort by load score (terminate least loaded first)
        healthy_instances.sort(key=lambda i: i.calculate_load_score())
        
        instances_to_terminate = healthy_instances[:count]
        
        for instance in instances_to_terminate:
            try:
                instance.state = InstanceState.TERMINATING
                
                # Wait for current requests to complete (graceful shutdown)
                await asyncio.sleep(5)
                
                # Remove from load balancer
                self.load_balancer.remove_instance(instance.instance_id)
                
                logger.info(f"Terminated instance: {instance.instance_id}")
                
            except Exception as e:
                logger.error(f"Failed to terminate instance {instance.instance_id}: {e}")
    
    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get auto-scaling statistics"""
        recent_events = list(self.scaling_history)[-10:]  # Last 10 events
        
        scale_up_events = len([e for e in self.scaling_history if e["action"] == "scale_up"])
        scale_down_events = len([e for e in self.scaling_history if e["action"] == "scale_down"])
        
        return {
            "policies_configured": len(self.policies),
            "current_metrics": self.current_metrics,
            "scaling_history_count": len(self.scaling_history),
            "scale_up_events": scale_up_events,
            "scale_down_events": scale_down_events,
            "last_scale_up": self.last_scale_up.isoformat() if self.last_scale_up else None,
            "last_scale_down": self.last_scale_down.isoformat() if self.last_scale_down else None,
            "recent_scaling_events": recent_events,
            "exam_schedules": {
                exam_type: [date.isoformat() for date in dates]
                for exam_type, dates in self.exam_schedules.items()
            },
            "metrics_trends": {
                metric_name: {
                    "current": values[-1] if values else 0,
                    "average": statistics.mean(values) if values else 0,
                    "trend": "increasing" if len(values) >= 2 and values[-1] > values[-2] else "stable"
                }
                for metric_name, values in self.metrics_history.items()
            }
        }


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Unified Load Balancing and Auto-Scaling System")
    print("=" * 60)
    
    async def test_load_balancing_autoscaling():
        """Test load balancing and auto-scaling system"""
        
        # Create load balancer
        load_balancer = LoadBalancer()
        
        # Add some server instances
        instances = [
            ServerInstance(
                instance_id="instance-1",
                instance_type="t3.medium",
                region="istanbul",
                availability_zone="istanbul-1a",
                ip_address="10.0.1.100",
                turkish_region="istanbul",
                serves_provinces=["İstanbul", "Kocaeli", "Sakarya"]
            ),
            ServerInstance(
                instance_id="instance-2",
                instance_type="t3.large",
                region="ankara",
                availability_zone="ankara-1a",
                ip_address="10.0.2.100",
                turkish_region="ankara",
                serves_provinces=["Ankara", "Eskişehir"]
            ),
            ServerInstance(
                instance_id="instance-3",
                instance_type="t3.medium",
                region="istanbul",
                availability_zone="istanbul-1b",
                ip_address="10.0.1.101",
                turkish_region="istanbul",
                serves_provinces=["İstanbul", "Bursa"]
            )
        ]
        
        for instance in instances:
            load_balancer.add_instance(instance)
        
        # Create auto-scaling manager
        autoscaler = AutoScalingManager(load_balancer)
        
        # Test request routing
        print("Testing request routing...")
        test_requests = [
            {
                "path": "/api/exam/start",
                "client_ip": "78.166.123.45",
                "user_location": "istanbul",
                "exam_type": "TYT",
                "subject": "matematik"
            },
            {
                "path": "/static/images/logo.png",
                "client_ip": "85.96.45.123",
                "user_location": "ankara"
            },
            {
                "path": "/exam/results",
                "client_ip": "94.123.67.89",
                "user_location": "izmir",
                "exam_type": "AYT"
            }
        ]
        
        for i, request in enumerate(test_requests):
            selected_instance = await load_balancer.route_request(request)
            if selected_instance:
                print(f"Request {i+1}: Routed to {selected_instance.instance_id} ({selected_instance.turkish_region})")
            else:
                print(f"Request {i+1}: No available instance")
        
        # Test metrics update
        print("\nTesting metrics updates...")
        test_metrics = {
            "cpu_usage": 75.5,
            "memory_usage": 68.2,
            "active_connections": 150,
            "requests_per_second": 45.2,
            "average_response_time": 0.8
        }
        
        for instance in instances:
            await load_balancer.update_instance_metrics(instance.instance_id, test_metrics)
        
        # Test auto-scaling
        print("Testing auto-scaling...")
        scaling_metrics = {
            "cpu_threshold": 80.0,  # Above threshold
            "memory_threshold": 70.0,  # Above threshold
            "concurrent_users": 3000.0,
            "request_rate": 500.0
        }
        
        await autoscaler.update_metrics(scaling_metrics)
        
        # Wait for scaling to process
        await asyncio.sleep(3)
        
        # Get statistics
        lb_stats = load_balancer.get_load_balancer_stats()
        scaling_stats = autoscaler.get_scaling_stats()
        
        print(f"\nLoad Balancer Stats:")
        print(f"- Total instances: {lb_stats['total_instances']}")
        print(f"- Healthy instances: {lb_stats['healthy_instances']}")
        print(f"- Rules configured: {lb_stats['rules_configured']}")
        
        print(f"\nAuto-Scaling Stats:")
        print(f"- Policies configured: {scaling_stats['policies_configured']}")
        print(f"- Scaling events: {scaling_stats['scaling_history_count']}")
        print(f"- Scale up events: {scaling_stats['scale_up_events']}")
        print(f"- Scale down events: {scaling_stats['scale_down_events']}")
        
        print(f"\nCurrent metrics trends:")
        for metric, trend_data in scaling_stats['metrics_trends'].items():
            print(f"- {metric}: {trend_data['current']:.1f} (trend: {trend_data['trend']})")
        
        print("\nLoad balancing and auto-scaling test completed!")
    
    # Run test
    asyncio.run(test_load_balancing_autoscaling())