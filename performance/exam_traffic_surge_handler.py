"""
KIRO2 Exam Traffic Surge Handling System
Advanced traffic surge management for Turkish university entrance exams
Türkiye Üniversite Sınavları Hazırlık Platformu - Sınav Trafiği Artış Yönetim Sistemi
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from enum import Enum
import json
import uuid
from collections import defaultdict, deque
import statistics
import time
import math
import aiohttp
import aioredis
from pathlib import Path

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.PERFORMANCE)
config = get_unified_config()


class ExamEvent(Enum):
    """Turkish exam events that cause traffic surges"""
    YKS_REGISTRATION = "yks_registration"          # YKS kayıt
    TYT_EXAM_START = "tyt_exam_start"             # TYT sınav başlangıcı
    AYT_EXAM_START = "ayt_exam_start"             # AYT sınav başlangıcı
    RESULTS_ANNOUNCEMENT = "results_announcement"  # Sonuç açıklaması
    UNIVERSITY_PLACEMENT = "university_placement" # Üniversite yerleşim
    MOCK_EXAM_SEASON = "mock_exam_season"         # Deneme sınav dönemi
    STUDY_PEAK_HOURS = "study_peak_hours"         # Çalışma yoğun saatleri
    WEEKEND_RUSH = "weekend_rush"                 # Hafta sonu yoğunluğu


class TrafficPattern(Enum):
    """Traffic pattern types"""
    GRADUAL_INCREASE = "gradual_increase"      # Kademeli artış
    SUDDEN_SPIKE = "sudden_spike"              # Ani artış
    SUSTAINED_HIGH = "sustained_high"          # Sürekli yüksek
    PERIODIC_WAVES = "periodic_waves"          # Periyodik dalgalar
    FLASH_CROWD = "flash_crowd"                # Ani kalabalık


class SurgeAction(Enum):
    """Traffic surge response actions"""
    SCALE_UP = "scale_up"                      # Kapasite artırma
    ENABLE_CACHING = "enable_caching"          # Önbellekleme aktifleştirme
    RATE_LIMITING = "rate_limiting"            # Hız sınırlama
    QUEUE_MANAGEMENT = "queue_management"      # Kuyruk yönetimi
    RESOURCE_PRIORITIZATION = "resource_prioritization"  # Kaynak önceliklendirme
    FAILOVER_ACTIVATION = "failover_activation"  # Yedekleme sistemi aktifleştirme
    CONTENT_COMPRESSION = "content_compression"  # İçerik sıkıştırma
    DATABASE_OPTIMIZATION = "database_optimization"  # Veritabanı optimizasyonu


class PriorityLevel(Enum):
    """Request priority levels during surges"""
    CRITICAL = "critical"    # Kritik (Sınav işlemleri)
    HIGH = "high"           # Yüksek (Sonuç sorgulama)
    NORMAL = "normal"       # Normal (Genel erişim)
    LOW = "low"             # Düşük (İstatistikler)
    DEFERRED = "deferred"   # Ertelenebilir (Analytics)


@dataclass
class TrafficMetrics:
    """Traffic metrics and statistics"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Request metrics
    requests_per_second: float = 0.0
    concurrent_users: int = 0
    active_connections: int = 0
    queue_length: int = 0
    
    # Response metrics
    average_response_time: float = 0.0
    error_rate_percent: float = 0.0
    timeout_rate_percent: float = 0.0
    
    # Resource utilization
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    bandwidth_mbps: float = 0.0
    
    # Exam-specific metrics
    exam_requests_per_second: float = 0.0
    result_queries_per_second: float = 0.0
    registration_requests: int = 0
    
    # Geographic distribution (Turkish regions)
    regional_distribution: Dict[str, int] = field(default_factory=dict)
    
    @property
    def is_surge_condition(self) -> bool:
        """Detect if current metrics indicate a traffic surge"""
        return (
            self.requests_per_second > 1000 or
            self.concurrent_users > 10000 or
            self.queue_length > 500 or
            self.error_rate_percent > 5.0 or
            self.average_response_time > 2.0
        )
    
    @property
    def surge_severity(self) -> str:
        """Calculate surge severity level"""
        score = 0
        
        if self.requests_per_second > 2000:
            score += 3
        elif self.requests_per_second > 1000:
            score += 2
        elif self.requests_per_second > 500:
            score += 1
        
        if self.concurrent_users > 20000:
            score += 3
        elif self.concurrent_users > 10000:
            score += 2
        elif self.concurrent_users > 5000:
            score += 1
        
        if self.error_rate_percent > 10:
            score += 3
        elif self.error_rate_percent > 5:
            score += 2
        elif self.error_rate_percent > 2:
            score += 1
        
        if score >= 6:
            return "critical"
        elif score >= 4:
            return "high"
        elif score >= 2:
            return "moderate"
        else:
            return "low"
    
    def calculate_capacity_needed(self) -> float:
        """Calculate capacity multiplier needed"""
        base_multiplier = 1.0
        
        # Based on requests per second
        if self.requests_per_second > 0:
            normal_rps = 500  # Normal baseline
            rps_multiplier = self.requests_per_second / normal_rps
            base_multiplier = max(base_multiplier, rps_multiplier)
        
        # Based on concurrent users
        if self.concurrent_users > 0:
            normal_users = 5000  # Normal baseline
            user_multiplier = self.concurrent_users / normal_users
            base_multiplier = max(base_multiplier, user_multiplier)
        
        # Add overhead for error recovery
        if self.error_rate_percent > 5:
            base_multiplier *= 1.5
        
        return min(base_multiplier, 10.0)  # Cap at 10x capacity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "requests": {
                "requests_per_second": self.requests_per_second,
                "concurrent_users": self.concurrent_users,
                "active_connections": self.active_connections,
                "queue_length": self.queue_length
            },
            "response": {
                "average_response_time": self.average_response_time,
                "error_rate_percent": self.error_rate_percent,
                "timeout_rate_percent": self.timeout_rate_percent
            },
            "resources": {
                "cpu_usage_percent": self.cpu_usage_percent,
                "memory_usage_percent": self.memory_usage_percent,
                "bandwidth_mbps": self.bandwidth_mbps
            },
            "exam_specific": {
                "exam_requests_per_second": self.exam_requests_per_second,
                "result_queries_per_second": self.result_queries_per_second,
                "registration_requests": self.registration_requests
            },
            "regional_distribution": self.regional_distribution,
            "analysis": {
                "is_surge": self.is_surge_condition,
                "severity": self.surge_severity,
                "capacity_needed": self.calculate_capacity_needed()
            }
        }


@dataclass
class ExamSchedule:
    """Turkish exam schedule for predictive scaling"""
    exam_id: str
    exam_type: ExamEvent
    exam_name: str
    scheduled_datetime: datetime
    
    # Expected traffic characteristics
    expected_concurrent_users: int = 50000
    expected_duration_hours: int = 4
    pre_surge_hours: int = 2
    post_surge_hours: int = 1
    
    # Regional distribution
    regional_weights: Dict[str, float] = field(default_factory=lambda: {
        "istanbul": 0.25,
        "ankara": 0.15,
        "izmir": 0.10,
        "bursa": 0.08,
        "antalya": 0.06,
        "other": 0.36
    })
    
    # Traffic pattern
    traffic_pattern: TrafficPattern = TrafficPattern.SUDDEN_SPIKE
    
    def __post_init__(self):
        if not self.exam_id:
            self.exam_id = str(uuid.uuid4())
    
    @property
    def is_approaching(self, hours_ahead: int = 24) -> bool:
        """Check if exam is approaching within specified hours"""
        time_until = (self.scheduled_datetime - datetime.now(timezone.utc)).total_seconds() / 3600
        return 0 < time_until <= hours_ahead
    
    @property
    def is_active(self) -> bool:
        """Check if exam is currently active"""
        now = datetime.now(timezone.utc)
        end_time = self.scheduled_datetime + timedelta(hours=self.expected_duration_hours)
        return self.scheduled_datetime <= now <= end_time
    
    @property
    def surge_start_time(self) -> datetime:
        """Get expected surge start time"""
        return self.scheduled_datetime - timedelta(hours=self.pre_surge_hours)
    
    @property
    def surge_end_time(self) -> datetime:
        """Get expected surge end time"""
        return self.scheduled_datetime + timedelta(hours=self.expected_duration_hours + self.post_surge_hours)
    
    def calculate_expected_load(self, current_time: datetime) -> float:
        """Calculate expected load multiplier at given time"""
        if current_time < self.surge_start_time or current_time > self.surge_end_time:
            return 1.0  # Normal load
        
        # Calculate position in surge timeline
        total_surge_duration = (self.surge_end_time - self.surge_start_time).total_seconds()
        time_in_surge = (current_time - self.surge_start_time).total_seconds()
        surge_position = time_in_surge / total_surge_duration
        
        if self.traffic_pattern == TrafficPattern.SUDDEN_SPIKE:
            # Quick ramp up to peak, then gradual decline
            if surge_position < 0.1:  # First 10% - rapid increase
                return 1.0 + (surge_position * 10) * 9  # 1x to 10x
            elif surge_position < 0.6:  # Next 50% - sustained peak
                return 10.0
            else:  # Last 40% - gradual decline
                return 10.0 * (1.0 - (surge_position - 0.6) / 0.4 * 0.8)  # 10x to 2x
        
        elif self.traffic_pattern == TrafficPattern.GRADUAL_INCREASE:
            # Smooth bell curve
            peak_multiplier = 6.0
            return 1.0 + (peak_multiplier - 1.0) * math.sin(surge_position * math.pi)
        
        elif self.traffic_pattern == TrafficPattern.SUSTAINED_HIGH:
            # Consistent high load throughout
            return 5.0
        
        else:
            return 3.0  # Default moderate increase


@dataclass
class SurgeResponse:
    """Traffic surge response configuration"""
    response_id: str
    trigger_conditions: Dict[str, float]
    actions: List[SurgeAction]
    
    # Response timing
    response_delay_seconds: int = 30
    ramp_up_duration_seconds: int = 300  # 5 minutes
    cooldown_duration_seconds: int = 600  # 10 minutes
    
    # Action parameters
    scaling_multiplier: float = 2.0
    rate_limit_factor: float = 0.8
    cache_ttl_multiplier: float = 0.5
    
    # Priority handling
    priority_queue_enabled: bool = True
    low_priority_throttle: float = 0.3  # Throttle low priority to 30%
    
    # Turkish exam specific
    exam_request_priority_boost: bool = True
    regional_load_balancing: bool = True
    
    def __post_init__(self):
        if not self.response_id:
            self.response_id = str(uuid.uuid4())
    
    def should_trigger(self, metrics: TrafficMetrics) -> bool:
        """Check if response should be triggered based on metrics"""
        for condition_name, threshold in self.trigger_conditions.items():
            metric_value = getattr(metrics, condition_name, 0)
            
            if metric_value >= threshold:
                return True
        
        return False
    
    def calculate_action_intensity(self, metrics: TrafficMetrics) -> float:
        """Calculate action intensity based on surge severity"""
        severity = metrics.surge_severity
        
        if severity == "critical":
            return 1.0
        elif severity == "high":
            return 0.8
        elif severity == "moderate":
            return 0.6
        else:
            return 0.4


class TrafficPredictor:
    """Predictive traffic analysis for Turkish exams"""
    
    def __init__(self):
        self.exam_schedules: Dict[str, ExamSchedule] = {}
        self.historical_patterns: Dict[ExamEvent, List[Dict[str, Any]]] = defaultdict(list)
        self.traffic_history: deque = deque(maxlen=10000)
        
        # Machine learning models (simplified)
        self.pattern_weights = {
            ExamEvent.YKS_REGISTRATION: 8.0,      # Very high traffic
            ExamEvent.RESULTS_ANNOUNCEMENT: 10.0,  # Extreme traffic
            ExamEvent.TYT_EXAM_START: 6.0,        # High traffic
            ExamEvent.AYT_EXAM_START: 6.0,        # High traffic
            ExamEvent.MOCK_EXAM_SEASON: 4.0,      # Moderate traffic
            ExamEvent.STUDY_PEAK_HOURS: 3.0,      # Moderate traffic
            ExamEvent.WEEKEND_RUSH: 2.5           # Light increase
        }
        
        # Seasonal patterns
        self.seasonal_multipliers = {
            1: 0.8,   # January - Lower activity
            2: 0.9,   # February
            3: 1.2,   # March - Mock exam season
            4: 1.5,   # April - Preparation intensifies
            5: 1.8,   # May - Peak season
            6: 2.0,   # June - YKS exams
            7: 1.5,   # July - Results and placement
            8: 0.7,   # August - Summer break
            9: 1.1,   # September - New academic year
            10: 1.3,  # October - Preparation begins
            11: 1.2,  # November
            12: 0.8   # December - Holiday break
        }
    
    def add_exam_schedule(self, schedule: ExamSchedule) -> None:
        """Add exam schedule for predictive analysis"""
        self.exam_schedules[schedule.exam_id] = schedule
        logger.info(f"Added exam schedule: {schedule.exam_name} on {schedule.scheduled_datetime}")
    
    def record_traffic_pattern(self, exam_type: ExamEvent, metrics: TrafficMetrics) -> None:
        """Record traffic pattern for learning"""
        pattern_data = {
            "timestamp": metrics.timestamp.isoformat(),
            "requests_per_second": metrics.requests_per_second,
            "concurrent_users": metrics.concurrent_users,
            "duration_minutes": 60,  # Assumed duration
            "regional_distribution": metrics.regional_distribution.copy()
        }
        
        self.historical_patterns[exam_type].append(pattern_data)
        
        # Keep only recent patterns (last 50)
        if len(self.historical_patterns[exam_type]) > 50:
            self.historical_patterns[exam_type].pop(0)
    
    def predict_traffic_surge(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Predict traffic surges in the next N hours"""
        predictions = []
        current_time = datetime.now(timezone.utc)
        
        # Check scheduled exams
        for schedule in self.exam_schedules.values():
            if schedule.is_approaching(hours_ahead):
                surge_prediction = self._predict_exam_surge(schedule, current_time)
                if surge_prediction:
                    predictions.append(surge_prediction)
        
        # Check for pattern-based predictions
        pattern_predictions = self._predict_pattern_surges(current_time, hours_ahead)
        predictions.extend(pattern_predictions)
        
        # Sort by expected intensity
        predictions.sort(key=lambda p: p.get("expected_intensity", 0), reverse=True)
        
        return predictions
    
    def _predict_exam_surge(self, schedule: ExamSchedule, current_time: datetime) -> Optional[Dict[str, Any]]:
        """Predict surge for specific exam"""
        time_until_surge = (schedule.surge_start_time - current_time).total_seconds() / 3600
        
        if time_until_surge > 24 or time_until_surge < 0:
            return None
        
        # Get historical data for this exam type
        historical_data = self.historical_patterns.get(schedule.exam_type, [])
        
        # Calculate expected metrics based on historical patterns
        if historical_data:
            avg_rps = statistics.mean([d["requests_per_second"] for d in historical_data[-10:]])
            avg_users = statistics.mean([d["concurrent_users"] for d in historical_data[-10:]])
        else:
            # Use base estimates
            base_weight = self.pattern_weights.get(schedule.exam_type, 3.0)
            avg_rps = 500 * base_weight
            avg_users = schedule.expected_concurrent_users
        
        # Apply seasonal multiplier
        current_month = current_time.month
        seasonal_factor = self.seasonal_multipliers.get(current_month, 1.0)
        
        return {
            "prediction_id": str(uuid.uuid4()),
            "exam_id": schedule.exam_id,
            "exam_name": schedule.exam_name,
            "exam_type": schedule.exam_type.value,
            "surge_start_time": schedule.surge_start_time.isoformat(),
            "surge_end_time": schedule.surge_end_time.isoformat(),
            "hours_until_surge": time_until_surge,
            "expected_intensity": min(avg_rps * seasonal_factor / 500, 10.0),
            "expected_metrics": {
                "requests_per_second": avg_rps * seasonal_factor,
                "concurrent_users": int(avg_users * seasonal_factor),
                "duration_hours": schedule.expected_duration_hours + schedule.pre_surge_hours + schedule.post_surge_hours
            },
            "regional_distribution": schedule.regional_weights,
            "traffic_pattern": schedule.traffic_pattern.value,
            "confidence": min(len(historical_data) / 10.0, 1.0)  # Higher confidence with more data
        }
    
    def _predict_pattern_surges(self, current_time: datetime, hours_ahead: int) -> List[Dict[str, Any]]:
        """Predict surges based on recurring patterns"""
        predictions = []
        
        # Weekend rush prediction
        if current_time.weekday() >= 5:  # Saturday or Sunday
            # Check for weekend study rush (14:00-20:00)
            for hour_offset in range(0, hours_ahead):
                check_time = current_time + timedelta(hours=hour_offset)
                
                if 14 <= check_time.hour <= 20 and check_time.weekday() >= 5:
                    predictions.append({
                        "prediction_id": str(uuid.uuid4()),
                        "surge_type": "weekend_rush",
                        "surge_start_time": check_time.replace(hour=14, minute=0).isoformat(),
                        "surge_end_time": check_time.replace(hour=20, minute=0).isoformat(),
                        "hours_until_surge": hour_offset,
                        "expected_intensity": 2.5,
                        "expected_metrics": {
                            "requests_per_second": 1250,
                            "concurrent_users": 12500,
                            "duration_hours": 6
                        },
                        "traffic_pattern": "gradual_increase",
                        "confidence": 0.7
                    })
                    break
        
        # Evening study peak (19:00-22:00 on weekdays)
        if current_time.weekday() < 5:  # Weekdays
            for hour_offset in range(0, min(hours_ahead, 48)):  # Next 48 hours
                check_time = current_time + timedelta(hours=hour_offset)
                
                if 19 <= check_time.hour <= 22 and check_time.weekday() < 5:
                    predictions.append({
                        "prediction_id": str(uuid.uuid4()),
                        "surge_type": "evening_peak",
                        "surge_start_time": check_time.replace(hour=19, minute=0).isoformat(),
                        "surge_end_time": check_time.replace(hour=22, minute=0).isoformat(),
                        "hours_until_surge": hour_offset,
                        "expected_intensity": 3.5,
                        "expected_metrics": {
                            "requests_per_second": 1750,
                            "concurrent_users": 15000,
                            "duration_hours": 3
                        },
                        "traffic_pattern": "sustained_high",
                        "confidence": 0.8
                    })
                    break
        
        return predictions
    
    def analyze_traffic_trends(self) -> Dict[str, Any]:
        """Analyze historical traffic trends"""
        if not self.traffic_history:
            return {"error": "No traffic history available"}
        
        recent_history = list(self.traffic_history)[-1000:]  # Last 1000 data points
        
        # Calculate trends
        rps_values = [h.get("requests_per_second", 0) for h in recent_history]
        user_values = [h.get("concurrent_users", 0) for h in recent_history]
        
        return {
            "analysis_period": {
                "data_points": len(recent_history),
                "time_span_hours": len(recent_history) / 12  # Assuming 5-minute intervals
            },
            "traffic_trends": {
                "requests_per_second": {
                    "current": rps_values[-1] if rps_values else 0,
                    "average": statistics.mean(rps_values) if rps_values else 0,
                    "peak": max(rps_values) if rps_values else 0,
                    "trend": "increasing" if len(rps_values) >= 2 and rps_values[-1] > rps_values[-10] else "stable"
                },
                "concurrent_users": {
                    "current": user_values[-1] if user_values else 0,
                    "average": statistics.mean(user_values) if user_values else 0,
                    "peak": max(user_values) if user_values else 0,
                    "trend": "increasing" if len(user_values) >= 2 and user_values[-1] > user_values[-10] else "stable"
                }
            },
            "pattern_recognition": {
                exam_type.value: {
                    "recorded_events": len(patterns),
                    "avg_intensity": statistics.mean([p.get("requests_per_second", 0) for p in patterns]) if patterns else 0,
                    "last_event": patterns[-1]["timestamp"] if patterns else None
                }
                for exam_type, patterns in self.historical_patterns.items()
            },
            "upcoming_predictions": len(self.predict_traffic_surge(24))
        }


class QueueManager:
    """Advanced queue management for traffic surges"""
    
    def __init__(self):
        self.request_queues: Dict[PriorityLevel, deque] = {
            priority: deque() for priority in PriorityLevel
        }
        
        # Queue limits per priority
        self.queue_limits = {
            PriorityLevel.CRITICAL: 1000,
            PriorityLevel.HIGH: 2000,
            PriorityLevel.NORMAL: 5000,
            PriorityLevel.LOW: 3000,
            PriorityLevel.DEFERRED: 1000
        }
        
        # Processing rates (requests per second)
        self.processing_rates = {
            PriorityLevel.CRITICAL: 100,
            PriorityLevel.HIGH: 80,
            PriorityLevel.NORMAL: 50,
            PriorityLevel.LOW: 20,
            PriorityLevel.DEFERRED: 5
        }
        
        # Queue statistics
        self.queue_stats = {
            priority: {
                "total_queued": 0,
                "total_processed": 0,
                "total_dropped": 0,
                "avg_wait_time": 0.0
            }
            for priority in PriorityLevel
        }
        
        # Active processing
        self.processing_active = False
    
    async def enqueue_request(
        self,
        request_data: Dict[str, Any],
        priority: PriorityLevel,
        exam_related: bool = False
    ) -> Dict[str, Any]:
        """Enqueue request with priority handling"""
        
        # Boost priority for exam-related requests
        if exam_related and priority not in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            priority = PriorityLevel.HIGH
        
        queue = self.request_queues[priority]
        limit = self.queue_limits[priority]
        
        # Check queue capacity
        if len(queue) >= limit:
            self.queue_stats[priority]["total_dropped"] += 1
            return {
                "queued": False,
                "reason": "queue_full",
                "queue_length": len(queue),
                "estimated_wait": -1
            }
        
        # Add request to queue
        request_entry = {
            "request_id": str(uuid.uuid4()),
            "data": request_data,
            "priority": priority.value,
            "queued_at": datetime.now(timezone.utc),
            "exam_related": exam_related
        }
        
        queue.append(request_entry)
        self.queue_stats[priority]["total_queued"] += 1
        
        # Calculate estimated wait time
        queue_position = len(queue)
        processing_rate = self.processing_rates[priority]
        estimated_wait = queue_position / processing_rate if processing_rate > 0 else 0
        
        return {
            "queued": True,
            "request_id": request_entry["request_id"],
            "queue_position": queue_position,
            "estimated_wait_seconds": estimated_wait,
            "priority": priority.value
        }
    
    async def process_queues(self) -> Dict[str, Any]:
        """Process requests from queues with priority ordering"""
        if self.processing_active:
            return {"error": "Processing already active"}
        
        self.processing_active = True
        processing_results = {
            "processed_count": 0,
            "processing_time": 0.0,
            "by_priority": {}
        }
        
        start_time = time.time()
        
        try:
            # Process queues in priority order
            for priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH, 
                           PriorityLevel.NORMAL, PriorityLevel.LOW, PriorityLevel.DEFERRED]:
                
                queue = self.request_queues[priority]
                rate = self.processing_rates[priority]
                processed = 0
                
                # Process up to rate limit
                while queue and processed < rate:
                    request_entry = queue.popleft()
                    
                    # Simulate request processing
                    await self._process_request(request_entry)
                    
                    processed += 1
                    self.queue_stats[priority]["total_processed"] += 1
                    
                    # Update wait time statistics
                    wait_time = (datetime.now(timezone.utc) - request_entry["queued_at"]).total_seconds()
                    current_avg = self.queue_stats[priority]["avg_wait_time"]
                    total_processed = self.queue_stats[priority]["total_processed"]
                    
                    # Update running average
                    new_avg = ((current_avg * (total_processed - 1)) + wait_time) / total_processed
                    self.queue_stats[priority]["avg_wait_time"] = new_avg
                
                processing_results["by_priority"][priority.value] = {
                    "processed": processed,
                    "remaining_in_queue": len(queue)
                }
                processing_results["processed_count"] += processed
            
            processing_results["processing_time"] = time.time() - start_time
            
        finally:
            self.processing_active = False
        
        return processing_results
    
    async def _process_request(self, request_entry: Dict[str, Any]) -> None:
        """Process individual request"""
        # Simulate processing time based on priority
        priority = PriorityLevel(request_entry["priority"])
        
        if priority == PriorityLevel.CRITICAL:
            await asyncio.sleep(0.01)  # 10ms for critical
        elif priority == PriorityLevel.HIGH:
            await asyncio.sleep(0.02)  # 20ms for high
        else:
            await asyncio.sleep(0.05)  # 50ms for normal/low
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        total_queued = sum(len(queue) for queue in self.request_queues.values())
        
        return {
            "total_queued": total_queued,
            "by_priority": {
                priority.value: {
                    "current_length": len(queue),
                    "limit": self.queue_limits[priority],
                    "utilization_percent": (len(queue) / self.queue_limits[priority]) * 100,
                    "processing_rate": self.processing_rates[priority],
                    "statistics": self.queue_stats[priority].copy()
                }
                for priority, queue in self.request_queues.items()
            },
            "processing_active": self.processing_active
        }
    
    async def clear_expired_requests(self, max_age_seconds: int = 300) -> int:
        """Clear expired requests from queues"""
        cleared_count = 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        
        for priority, queue in self.request_queues.items():
            initial_length = len(queue)
            
            # Filter out expired requests
            filtered_queue = deque()
            for request_entry in queue:
                if request_entry["queued_at"] > cutoff_time:
                    filtered_queue.append(request_entry)
                else:
                    cleared_count += 1
                    self.queue_stats[priority]["total_dropped"] += 1
            
            self.request_queues[priority] = filtered_queue
        
        return cleared_count


class ExamTrafficSurgeHandler:
    """Main traffic surge handling system for Turkish exams"""
    
    def __init__(self):
        self.traffic_predictor = TrafficPredictor()
        self.queue_manager = QueueManager()
        
        # Current traffic state
        self.current_metrics = TrafficMetrics()
        self.surge_active = False
        self.current_surge_responses: List[SurgeResponse] = []
        
        # Response configurations
        self.surge_responses: Dict[str, SurgeResponse] = {}
        
        # Monitoring and alerting
        self.monitoring_active = False
        self.alert_callbacks: List[Callable] = []
        
        # Performance history
        self.performance_history: deque = deque(maxlen=1000)
        
        # Turkish exam specific
        self.exam_mode_active = False
        self.priority_exam_types = {ExamEvent.YKS_REGISTRATION, ExamEvent.RESULTS_ANNOUNCEMENT}
        
        self._initialize_default_responses()
    
    def _initialize_default_responses(self) -> None:
        """Initialize default surge response configurations"""
        
        # Moderate surge response
        moderate_response = SurgeResponse(
            response_id="moderate_surge",
            trigger_conditions={
                "requests_per_second": 1000,
                "concurrent_users": 10000,
                "error_rate_percent": 3.0
            },
            actions=[
                SurgeAction.SCALE_UP,
                SurgeAction.ENABLE_CACHING,
                SurgeAction.QUEUE_MANAGEMENT
            ],
            scaling_multiplier=1.5,
            response_delay_seconds=30
        )
        
        # High surge response
        high_response = SurgeResponse(
            response_id="high_surge",
            trigger_conditions={
                "requests_per_second": 2000,
                "concurrent_users": 20000,
                "error_rate_percent": 5.0
            },
            actions=[
                SurgeAction.SCALE_UP,
                SurgeAction.ENABLE_CACHING,
                SurgeAction.RATE_LIMITING,
                SurgeAction.QUEUE_MANAGEMENT,
                SurgeAction.RESOURCE_PRIORITIZATION
            ],
            scaling_multiplier=2.5,
            rate_limit_factor=0.7,
            response_delay_seconds=15
        )
        
        # Critical surge response (exam events)
        critical_response = SurgeResponse(
            response_id="critical_surge",
            trigger_conditions={
                "requests_per_second": 5000,
                "concurrent_users": 50000,
                "error_rate_percent": 10.0
            },
            actions=[
                SurgeAction.SCALE_UP,
                SurgeAction.ENABLE_CACHING,
                SurgeAction.RATE_LIMITING,
                SurgeAction.QUEUE_MANAGEMENT,
                SurgeAction.RESOURCE_PRIORITIZATION,
                SurgeAction.FAILOVER_ACTIVATION,
                SurgeAction.DATABASE_OPTIMIZATION
            ],
            scaling_multiplier=5.0,
            rate_limit_factor=0.5,
            response_delay_seconds=5,
            exam_request_priority_boost=True,
            regional_load_balancing=True
        )
        
        self.surge_responses = {
            "moderate": moderate_response,
            "high": high_response,
            "critical": critical_response
        }
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize traffic surge handling system"""
        try:
            config = config or {}
            
            # Load exam schedules
            if "exam_schedules" in config:
                for schedule_data in config["exam_schedules"]:
                    schedule = ExamSchedule(**schedule_data)
                    self.traffic_predictor.add_exam_schedule(schedule)
            
            # Configure custom surge responses
            if "surge_responses" in config:
                for response_data in config["surge_responses"]:
                    response = SurgeResponse(**response_data)
                    self.surge_responses[response.response_id] = response
            
            # Start monitoring
            await self.start_monitoring()
            
            # Initialize queue processing
            asyncio.create_task(self._queue_processing_loop())
            
            logger.info("Exam traffic surge handling system initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize surge handler: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start traffic monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            asyncio.create_task(self._monitoring_loop())
            logger.info("Traffic monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop traffic monitoring"""
        self.monitoring_active = False
        logger.info("Traffic monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main traffic monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect current metrics
                await self._collect_traffic_metrics()
                
                # Check for surge conditions
                await self._evaluate_surge_conditions()
                
                # Process predictive scaling
                await self._handle_predictive_scaling()
                
                # Record performance history
                self.performance_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metrics": self.current_metrics.to_dict(),
                    "surge_active": self.surge_active,
                    "active_responses": len(self.current_surge_responses)
                })
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)
    
    async def _collect_traffic_metrics(self) -> None:
        """Collect current traffic metrics"""
        # Simulate metric collection - in real implementation, integrate with monitoring systems
        current_time = datetime.now(timezone.utc)
        
        # Base metrics with some variation
        base_rps = 500 + (hash(str(current_time.second)) % 200)
        base_users = 5000 + (hash(str(current_time.minute)) % 2000)
        
        # Apply exam schedule multipliers
        total_multiplier = 1.0
        for schedule in self.traffic_predictor.exam_schedules.values():
            multiplier = schedule.calculate_expected_load(current_time)
            total_multiplier = max(total_multiplier, multiplier)
        
        # Update current metrics
        self.current_metrics = TrafficMetrics(
            timestamp=current_time,
            requests_per_second=base_rps * total_multiplier,
            concurrent_users=int(base_users * total_multiplier),
            active_connections=int(base_users * total_multiplier * 0.8),
            queue_length=sum(len(q) for q in self.queue_manager.request_queues.values()),
            average_response_time=0.5 + (total_multiplier - 1.0) * 0.3,
            error_rate_percent=max(0, (total_multiplier - 2.0) * 2.0),
            cpu_usage_percent=30 + (total_multiplier - 1.0) * 15,
            memory_usage_percent=40 + (total_multiplier - 1.0) * 10,
            bandwidth_mbps=100 * total_multiplier,
            exam_requests_per_second=base_rps * total_multiplier * 0.3 if total_multiplier > 1.5 else 0,
            regional_distribution={
                "istanbul": int(base_users * 0.25),
                "ankara": int(base_users * 0.15),
                "izmir": int(base_users * 0.10),
                "other": int(base_users * 0.50)
            }
        )
    
    async def _evaluate_surge_conditions(self) -> None:
        """Evaluate if surge response should be triggered"""
        
        # Check each surge response configuration
        for response_id, response_config in self.surge_responses.items():
            if response_config.should_trigger(self.current_metrics):
                
                # Check if this response is already active
                active_response_ids = [r.response_id for r in self.current_surge_responses]
                if response_id not in active_response_ids:
                    
                    await self._activate_surge_response(response_config)
        
        # Check if surge conditions have subsided
        if self.surge_active:
            await self._check_surge_deactivation()
    
    async def _activate_surge_response(self, response: SurgeResponse) -> None:
        """Activate surge response"""
        try:
            logger.warning(f"Activating surge response: {response.response_id}")
            
            # Add to active responses
            self.current_surge_responses.append(response)
            self.surge_active = True
            
            # Execute response actions
            for action in response.actions:
                await self._execute_surge_action(action, response)
            
            # Notify alert callbacks
            alert_data = {
                "event": "surge_response_activated",
                "response_id": response.response_id,
                "metrics": self.current_metrics.to_dict(),
                "actions": [action.value for action in response.actions]
            }
            
            await self._send_alerts(alert_data)
            
        except Exception as e:
            logger.error(f"Failed to activate surge response: {e}")
    
    async def _execute_surge_action(self, action: SurgeAction, response: SurgeResponse) -> None:
        """Execute specific surge response action"""
        try:
            intensity = response.calculate_action_intensity(self.current_metrics)
            
            if action == SurgeAction.SCALE_UP:
                await self._scale_up_resources(response.scaling_multiplier * intensity)
                
            elif action == SurgeAction.ENABLE_CACHING:
                await self._enable_aggressive_caching(response.cache_ttl_multiplier)
                
            elif action == SurgeAction.RATE_LIMITING:
                await self._enable_rate_limiting(response.rate_limit_factor)
                
            elif action == SurgeAction.QUEUE_MANAGEMENT:
                await self._optimize_queue_management(response.priority_queue_enabled)
                
            elif action == SurgeAction.RESOURCE_PRIORITIZATION:
                await self._prioritize_exam_resources()
                
            elif action == SurgeAction.FAILOVER_ACTIVATION:
                await self._activate_failover_systems()
                
            elif action == SurgeAction.DATABASE_OPTIMIZATION:
                await self._optimize_database_for_surge()
            
            logger.info(f"Executed surge action: {action.value} with intensity {intensity:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to execute surge action {action.value}: {e}")
    
    async def _scale_up_resources(self, multiplier: float) -> None:
        """Scale up system resources"""
        # This would integrate with auto-scaling systems
        target_capacity = int(10 * multiplier)  # Assuming base capacity of 10
        logger.info(f"Scaling up to {target_capacity} instances (multiplier: {multiplier:.2f})")
    
    async def _enable_aggressive_caching(self, ttl_multiplier: float) -> None:
        """Enable aggressive caching strategies"""
        # This would integrate with caching systems
        new_ttl = int(3600 * ttl_multiplier)  # Default 1 hour
        logger.info(f"Enabling aggressive caching with TTL: {new_ttl}s")
    
    async def _enable_rate_limiting(self, rate_factor: float) -> None:
        """Enable rate limiting"""
        # This would integrate with rate limiting systems
        requests_per_minute = int(1000 * rate_factor)
        logger.info(f"Enabling rate limiting: {requests_per_minute} req/min per client")
    
    async def _optimize_queue_management(self, priority_enabled: bool) -> None:
        """Optimize queue management"""
        if priority_enabled:
            # Adjust processing rates for surge conditions
            surge_boost = 1.5
            for priority in self.queue_manager.processing_rates:
                self.queue_manager.processing_rates[priority] *= surge_boost
            
            logger.info("Optimized queue processing rates for surge")
    
    async def _prioritize_exam_resources(self) -> None:
        """Prioritize resources for exam-related requests"""
        # This would adjust load balancer weights and resource allocation
        logger.info("Prioritizing resources for exam-related requests")
    
    async def _activate_failover_systems(self) -> None:
        """Activate failover systems"""
        # This would activate backup systems and redundant infrastructure
        logger.info("Activating failover systems")
    
    async def _optimize_database_for_surge(self) -> None:
        """Optimize database settings for surge conditions"""
        # This would adjust database connection pools, query timeouts, etc.
        logger.info("Optimizing database for surge conditions")
    
    async def _check_surge_deactivation(self) -> None:
        """Check if surge responses should be deactivated"""
        active_responses_to_remove = []
        
        for response in self.current_surge_responses:
            # Check if conditions have subsided
            if not response.should_trigger(self.current_metrics):
                active_responses_to_remove.append(response)
        
        # Deactivate responses that are no longer needed
        for response in active_responses_to_remove:
            await self._deactivate_surge_response(response)
        
        # Update surge state
        if not self.current_surge_responses:
            self.surge_active = False
    
    async def _deactivate_surge_response(self, response: SurgeResponse) -> None:
        """Deactivate surge response"""
        try:
            logger.info(f"Deactivating surge response: {response.response_id}")
            
            # Remove from active responses
            self.current_surge_responses.remove(response)
            
            # Restore normal settings (simplified)
            await self._restore_normal_settings()
            
            # Notify alert callbacks
            alert_data = {
                "event": "surge_response_deactivated",
                "response_id": response.response_id,
                "metrics": self.current_metrics.to_dict()
            }
            
            await self._send_alerts(alert_data)
            
        except Exception as e:
            logger.error(f"Failed to deactivate surge response: {e}")
    
    async def _restore_normal_settings(self) -> None:
        """Restore normal operational settings"""
        # Restore normal queue processing rates
        self.queue_manager.processing_rates = {
            PriorityLevel.CRITICAL: 100,
            PriorityLevel.HIGH: 80,
            PriorityLevel.NORMAL: 50,
            PriorityLevel.LOW: 20,
            PriorityLevel.DEFERRED: 5
        }
        
        logger.info("Restored normal operational settings")
    
    async def _handle_predictive_scaling(self) -> None:
        """Handle predictive scaling based on upcoming exams"""
        predictions = self.traffic_predictor.predict_traffic_surge(hours_ahead=2)
        
        for prediction in predictions:
            hours_until = prediction.get("hours_until_surge", 0)
            expected_intensity = prediction.get("expected_intensity", 0)
            
            # Pre-scale if major surge is expected within 30 minutes
            if hours_until <= 0.5 and expected_intensity >= 5.0:
                await self._pre_scale_for_exam(prediction)
    
    async def _pre_scale_for_exam(self, prediction: Dict[str, Any]) -> None:
        """Pre-scale resources for predicted exam surge"""
        logger.info(f"Pre-scaling for predicted surge: {prediction.get('exam_name', 'Unknown')}")
        
        expected_multiplier = prediction.get("expected_intensity", 3.0)
        await self._scale_up_resources(expected_multiplier * 0.8)  # Scale to 80% of expected need
    
    async def _queue_processing_loop(self) -> None:
        """Background queue processing loop"""
        while True:
            try:
                await self.queue_manager.process_queues()
                
                # Clear expired requests every minute
                if int(time.time()) % 60 == 0:
                    await self.queue_manager.clear_expired_requests()
                
                await asyncio.sleep(1)  # Process every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing loop error: {e}")
                await asyncio.sleep(5)
    
    async def _send_alerts(self, alert_data: Dict[str, Any]) -> None:
        """Send alerts to registered callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    async def handle_request(
        self,
        request_data: Dict[str, Any],
        priority: PriorityLevel = PriorityLevel.NORMAL,
        exam_related: bool = False
    ) -> Dict[str, Any]:
        """Handle incoming request during surge conditions"""
        
        if self.surge_active:
            # Queue request during surge
            queue_result = await self.queue_manager.enqueue_request(
                request_data, priority, exam_related
            )
            
            if queue_result["queued"]:
                return {
                    "status": "queued",
                    "request_id": queue_result["request_id"],
                    "estimated_wait": queue_result["estimated_wait_seconds"],
                    "surge_active": True
                }
            else:
                return {
                    "status": "rejected",
                    "reason": queue_result["reason"],
                    "surge_active": True
                }
        
        else:
            # Process immediately during normal conditions
            return {
                "status": "processed",
                "processing_time": 0.1,
                "surge_active": False
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        # Get traffic predictions
        predictions = self.traffic_predictor.predict_traffic_surge(24)
        upcoming_predictions = [p for p in predictions if p.get("hours_until_surge", 0) <= 2]
        
        return {
            "surge_status": {
                "active": self.surge_active,
                "active_responses": [r.response_id for r in self.current_surge_responses],
                "total_responses_configured": len(self.surge_responses)
            },
            "current_metrics": self.current_metrics.to_dict(),
            "queue_status": self.queue_manager.get_queue_status(),
            "predictions": {
                "total_predictions_24h": len(predictions),
                "upcoming_surges_2h": len(upcoming_predictions),
                "next_prediction": upcoming_predictions[0] if upcoming_predictions else None
            },
            "performance": {
                "monitoring_active": self.monitoring_active,
                "exam_mode_active": self.exam_mode_active,
                "history_data_points": len(self.performance_history)
            },
            "exam_schedules": {
                "total_scheduled": len(self.traffic_predictor.exam_schedules),
                "approaching_24h": len([
                    s for s in self.traffic_predictor.exam_schedules.values()
                    if s.is_approaching(24)
                ]),
                "active_now": len([
                    s for s in self.traffic_predictor.exam_schedules.values()
                    if s.is_active
                ])
            }
        }
    
    async def enable_exam_mode(self) -> None:
        """Enable exam mode optimizations"""
        self.exam_mode_active = True
        
        # Boost processing rates for exam-related requests
        for priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            self.queue_manager.processing_rates[priority] *= 1.5
        
        logger.info("Exam traffic surge handler exam mode enabled")
    
    async def disable_exam_mode(self) -> None:
        """Disable exam mode optimizations"""
        self.exam_mode_active = False
        
        # Restore normal processing rates
        self.queue_manager.processing_rates = {
            PriorityLevel.CRITICAL: 100,
            PriorityLevel.HIGH: 80,
            PriorityLevel.NORMAL: 50,
            PriorityLevel.LOW: 20,
            PriorityLevel.DEFERRED: 5
        }
        
        logger.info("Exam traffic surge handler exam mode disabled")


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Exam Traffic Surge Handling System")
    print("=" * 50)
    
    async def test_traffic_surge_handler():
        """Test traffic surge handling system"""
        
        # Create surge handler
        surge_handler = ExamTrafficSurgeHandler()
        
        # Test configuration
        config = {
            "exam_schedules": [
                {
                    "exam_id": "yks_2024",
                    "exam_type": ExamEvent.YKS_REGISTRATION.value,
                    "exam_name": "YKS 2024 Kayıt",
                    "scheduled_datetime": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                    "expected_concurrent_users": 100000,
                    "expected_duration_hours": 6,
                    "traffic_pattern": TrafficPattern.SUDDEN_SPIKE.value
                }
            ]
        }
        
        # Initialize system
        await surge_handler.initialize(config)
        
        print("Testing traffic surge predictions...")
        
        # Get traffic predictions
        predictions = surge_handler.traffic_predictor.predict_traffic_surge(24)
        print(f"Found {len(predictions)} traffic surge predictions")
        
        for prediction in predictions:
            print(f"  - {prediction.get('exam_name', 'Pattern-based')}: "
                  f"{prediction['expected_intensity']:.1f}x intensity in "
                  f"{prediction['hours_until_surge']:.1f} hours")
        
        # Test request handling during normal conditions
        print("\nTesting request handling...")
        
        normal_request = {
            "type": "exam_query",
            "user_id": "student_123",
            "data": {"exam_type": "TYT", "subject": "matematik"}
        }
        
        result = await surge_handler.handle_request(
            normal_request, 
            PriorityLevel.NORMAL, 
            exam_related=True
        )
        print(f"Normal request result: {result}")
        
        # Simulate traffic surge by updating metrics
        print("\nSimulating traffic surge...")
        
        # Manually trigger high traffic metrics
        surge_handler.current_metrics = TrafficMetrics(
            requests_per_second=2500,
            concurrent_users=25000,
            error_rate_percent=8.0,
            average_response_time=3.5,
            cpu_usage_percent=85
        )
        
        # Allow surge evaluation
        await surge_handler._evaluate_surge_conditions()
        await asyncio.sleep(1)
        
        # Test request handling during surge
        surge_request = {
            "type": "exam_result_query",
            "user_id": "student_456", 
            "data": {"exam_type": "YKS", "query": "placement"}
        }
        
        surge_result = await surge_handler.handle_request(
            surge_request,
            PriorityLevel.HIGH,
            exam_related=True
        )
        print(f"Surge request result: {surge_result}")
        
        # Test queue processing
        print("\nTesting queue processing...")
        
        # Add multiple requests to queue
        for i in range(10):
            await surge_handler.queue_manager.enqueue_request(
                {"request_id": i, "data": f"test_request_{i}"},
                PriorityLevel.NORMAL,
                exam_related=(i % 2 == 0)
            )
        
        # Process queues
        processing_result = await surge_handler.queue_manager.process_queues()
        print(f"Queue processing result: {processing_result['processed_count']} requests processed")
        
        # Test exam mode
        print("\nTesting exam mode...")
        await surge_handler.enable_exam_mode()
        
        # Get system status
        system_status = surge_handler.get_system_status()
        
        print(f"\nSystem Status Summary:")
        print(f"Surge active: {system_status['surge_status']['active']}")
        print(f"Active responses: {system_status['surge_status']['active_responses']}")
        print(f"Current RPS: {system_status['current_metrics']['requests']['requests_per_second']}")
        print(f"Concurrent users: {system_status['current_metrics']['requests']['concurrent_users']}")
        print(f"Queue length: {system_status['queue_status']['total_queued']}")
        print(f"Exam mode: {system_status['performance']['exam_mode_active']}")
        
        print(f"\nQueue Status by Priority:")
        for priority, queue_info in system_status['queue_status']['by_priority'].items():
            print(f"  {priority}: {queue_info['current_length']}/{queue_info['limit']} "
                  f"({queue_info['utilization_percent']:.1f}%)")
        
        print(f"\nPredictions:")
        pred_info = system_status['predictions']
        print(f"  24h predictions: {pred_info['total_predictions_24h']}")
        print(f"  Upcoming (2h): {pred_info['upcoming_surges_2h']}")
        
        if pred_info['next_prediction']:
            next_pred = pred_info['next_prediction']
            print(f"  Next: {next_pred.get('exam_name', 'Unknown')} "
                  f"({next_pred.get('expected_intensity', 0):.1f}x intensity)")
        
        print(f"\nExam Schedules:")
        exam_info = system_status['exam_schedules']
        print(f"  Total scheduled: {exam_info['total_scheduled']}")
        print(f"  Approaching (24h): {exam_info['approaching_24h']}")
        print(f"  Active now: {exam_info['active_now']}")
        
        # Test traffic analysis
        print("\nTesting traffic trend analysis...")
        
        # Add some mock traffic history
        for i in range(100):
            surge_handler.traffic_predictor.traffic_history.append({
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=i*5)).isoformat(),
                "requests_per_second": 500 + (i * 10) + (hash(str(i)) % 200),
                "concurrent_users": 5000 + (i * 50)
            })
        
        trend_analysis = surge_handler.traffic_predictor.analyze_traffic_trends()
        
        if "traffic_trends" in trend_analysis:
            trends = trend_analysis["traffic_trends"]
            print(f"RPS trend: {trends['requests_per_second']['trend']} "
                  f"(current: {trends['requests_per_second']['current']:.0f}, "
                  f"peak: {trends['requests_per_second']['peak']:.0f})")
            print(f"Users trend: {trends['concurrent_users']['trend']} "
                  f"(current: {trends['concurrent_users']['current']}, "
                  f"peak: {trends['concurrent_users']['peak']})")
        
        # Cleanup
        await surge_handler.stop_monitoring()
        await surge_handler.disable_exam_mode()
        
        print("\nExam traffic surge handling system test completed!")
    
    # Run test
    asyncio.run(test_traffic_surge_handler())