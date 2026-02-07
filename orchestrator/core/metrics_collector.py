"""
KIRO2 Metrics Collector - Performans ve Kalite Metrikleri Toplama Sistemi

Orchestrator ve ajan performansını izlemek için merkezi metrik toplama.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metrik türleri"""
    COUNTER = "counter"  # Sayaç (monoton artan)
    GAUGE = "gauge"  # Anlık değer
    HISTOGRAM = "histogram"  # Dağılım
    TIMER = "timer"  # Süre ölçümü


class MetricCategory(Enum):
    """Metrik kategorileri"""
    TASK = "task"  # Görev metrikleri
    AGENT = "agent"  # Ajan metrikleri
    SYSTEM = "system"  # Sistem metrikleri
    QUALITY = "quality"  # Kalite metrikleri
    PERFORMANCE = "performance"  # Performans metrikleri
    LEARNING = "learning"  # Öğrenme metrikleri


@dataclass
class MetricPoint:
    """Tek bir metrik noktası"""
    name: str
    value: float
    timestamp: datetime
    labels: dict = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class MetricSummary:
    """Metrik özeti"""
    name: str
    count: int
    total: float
    min_value: float
    max_value: float
    avg_value: float
    std_dev: float
    p50: float
    p95: float
    p99: float
    last_value: float
    last_updated: datetime


class MetricsCollector:
    """
    Merkezi Metrik Toplama Sistemi
    
    Özellikler:
    - Çoklu metrik türü desteği
    - Label tabanlı filtreleme
    - Zaman serisi depolama
    - İstatistiksel özet hesaplama
    - Alert threshold kontrolü
    """
    
    def __init__(self, retention_hours: int = 24):
        self._metrics: dict[str, list[MetricPoint]] = defaultdict(list)
        self._counters: dict[str, float] = defaultdict(float)
        self._retention = timedelta(hours=retention_hours)
        self._alerts: list[dict] = []
        self._thresholds: dict[str, dict] = {}
        
        # Temel metrikleri kaydet
        self._register_default_metrics()
        logger.info(f"MetricsCollector initialized (retention: {retention_hours}h)")
    
    def _register_default_metrics(self):
        """Varsayılan metrik threshold'larını kaydet"""
        self._thresholds = {
            "task.duration_seconds": {"warning": 60, "critical": 300},
            "task.error_rate": {"warning": 0.05, "critical": 0.15},
            "agent.cpu_percent": {"warning": 80, "critical": 95},
            "agent.memory_mb": {"warning": 1024, "critical": 2048},
            "system.queue_depth": {"warning": 100, "critical": 500},
            "quality.match_rate": {"warning": 0.50, "critical": 0.30},  # Düşük = kötü
        }
    
    def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[dict] = None
    ) -> None:
        """
        Metrik kaydet
        
        Args:
            name: Metrik adı (örn: "task.duration_seconds")
            value: Metrik değeri
            metric_type: Metrik türü
            labels: Ek etiketler
        """
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metric_type=metric_type
        )
        
        self._metrics[name].append(point)
        
        # Counter için toplam güncelle
        if metric_type == MetricType.COUNTER:
            self._counters[name] += value
        
        # Threshold kontrolü
        self._check_threshold(name, value)
        
        # Eski verileri temizle
        self._cleanup_old_metrics(name)
    
    def increment(self, name: str, value: float = 1, labels: Optional[dict] = None) -> None:
        """Counter artır"""
        self.record(name, value, MetricType.COUNTER, labels)
    
    def gauge(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        """Gauge kaydet"""
        self.record(name, value, MetricType.GAUGE, labels)
    
    def timer(self, name: str, duration_seconds: float, labels: Optional[dict] = None) -> None:
        """Timer kaydet"""
        self.record(name, duration_seconds, MetricType.TIMER, labels)
    
    def histogram(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        """Histogram değeri kaydet"""
        self.record(name, value, MetricType.HISTOGRAM, labels)
    
    def time_context(self, name: str, labels: Optional[dict] = None):
        """
        Context manager ile süre ölçümü
        
        Kullanım:
            with metrics.time_context("task.duration"):
                do_work()
        """
        return TimerContext(self, name, labels)
    
    def get_summary(self, name: str, minutes: int = 60) -> Optional[MetricSummary]:
        """
        Metrik özeti al
        
        Args:
            name: Metrik adı
            minutes: Son kaç dakikanın verisi
        
        Returns:
            MetricSummary veya None
        """
        if name not in self._metrics:
            return None
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        values = [p.value for p in self._metrics[name] if p.timestamp > cutoff]
        
        if not values:
            return None
        
        sorted_values = sorted(values)
        count = len(values)
        
        return MetricSummary(
            name=name,
            count=count,
            total=sum(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            std_dev=statistics.stdev(values) if count > 1 else 0,
            p50=sorted_values[int(count * 0.50)],
            p95=sorted_values[int(count * 0.95)] if count >= 20 else sorted_values[-1],
            p99=sorted_values[int(count * 0.99)] if count >= 100 else sorted_values[-1],
            last_value=values[-1],
            last_updated=self._metrics[name][-1].timestamp
        )
    
    def get_counter(self, name: str) -> float:
        """Counter toplam değeri"""
        return self._counters.get(name, 0)
    
    def get_rate(self, name: str, minutes: int = 5) -> float:
        """
        Oran hesapla (değer/dakika)
        
        Args:
            name: Metrik adı
            minutes: Hesaplama periyodu
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        values = [p.value for p in self._metrics.get(name, []) if p.timestamp > cutoff]
        
        if not values:
            return 0.0
        
        return sum(values) / minutes
    
    def _check_threshold(self, name: str, value: float) -> None:
        """Threshold kontrolü ve alert oluşturma"""
        if name not in self._thresholds:
            return
        
        thresholds = self._thresholds[name]
        
        # Bazı metrikler için düşük değer kötü
        is_lower_bad = name in ["quality.match_rate"]
        
        if is_lower_bad:
            if value < thresholds.get("critical", 0):
                self._create_alert(name, value, "critical", "Value too low")
            elif value < thresholds.get("warning", 0):
                self._create_alert(name, value, "warning", "Value below threshold")
        else:
            if value > thresholds.get("critical", float("inf")):
                self._create_alert(name, value, "critical", "Value exceeded critical threshold")
            elif value > thresholds.get("warning", float("inf")):
                self._create_alert(name, value, "warning", "Value exceeded warning threshold")
    
    def _create_alert(self, name: str, value: float, severity: str, message: str) -> None:
        """Alert oluştur"""
        alert = {
            "metric": name,
            "value": value,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now()
        }
        self._alerts.append(alert)
        logger.warning(f"ALERT [{severity.upper()}] {name}: {value} - {message}")
    
    def get_alerts(self, since_minutes: int = 60) -> list[dict]:
        """Son alert'leri getir"""
        cutoff = datetime.now() - timedelta(minutes=since_minutes)
        return [a for a in self._alerts if a["timestamp"] > cutoff]
    
    def clear_alerts(self) -> None:
        """Alert'leri temizle"""
        self._alerts.clear()
    
    def _cleanup_old_metrics(self, name: str) -> None:
        """Eski metrikleri temizle"""
        cutoff = datetime.now() - self._retention
        self._metrics[name] = [p for p in self._metrics[name] if p.timestamp > cutoff]
    
    def get_dashboard_data(self) -> dict:
        """Dashboard için özet veri"""
        now = datetime.now()
        
        # Temel metrikler
        task_summary = self.get_summary("task.duration_seconds", 60)
        error_rate = self.get_rate("task.error_count", 5) / max(self.get_rate("task.completed_count", 5), 1)
        
        return {
            "timestamp": now.isoformat(),
            "tasks": {
                "completed_last_hour": int(self.get_counter("task.completed_count")),
                "failed_last_hour": int(self.get_counter("task.error_count")),
                "avg_duration_seconds": task_summary.avg_value if task_summary else 0,
                "p95_duration_seconds": task_summary.p95 if task_summary else 0,
            },
            "agents": {
                "active": int(self._counters.get("agent.active_count", 0)),
                "total_tasks_processed": int(self._counters.get("agent.tasks_processed", 0)),
            },
            "quality": {
                "match_rate": self._get_last_value("quality.match_rate", 0),
                "validation_pass_rate": self._get_last_value("quality.validation_pass_rate", 0),
            },
            "system": {
                "queue_depth": int(self._get_last_value("system.queue_depth", 0)),
                "memory_mb": self._get_last_value("system.memory_mb", 0),
            },
            "alerts": {
                "warning": len([a for a in self.get_alerts(60) if a["severity"] == "warning"]),
                "critical": len([a for a in self.get_alerts(60) if a["severity"] == "critical"]),
            }
        }
    
    def _get_last_value(self, name: str, default: float = 0) -> float:
        """Son metrik değerini al"""
        if name in self._metrics and self._metrics[name]:
            return self._metrics[name][-1].value
        return default
    
    # ============ ÖNCEDEN TANIMLI METRİK KAYIT METHODLARI ============
    
    def record_task_start(self, task_id: str, task_type: str) -> None:
        """Görev başlangıcı kaydet"""
        self.increment("task.started_count", labels={"type": task_type})
        self._task_start_times[task_id] = time.time()
    
    def record_task_complete(self, task_id: str, task_type: str, success: bool = True) -> None:
        """Görev tamamlanması kaydet"""
        if success:
            self.increment("task.completed_count", labels={"type": task_type})
        else:
            self.increment("task.error_count", labels={"type": task_type})
        
        # Süre hesapla
        if hasattr(self, "_task_start_times") and task_id in self._task_start_times:
            duration = time.time() - self._task_start_times[task_id]
            self.timer("task.duration_seconds", duration, labels={"type": task_type})
            del self._task_start_times[task_id]
    
    def record_agent_metric(self, agent_id: str, cpu_percent: float, memory_mb: float) -> None:
        """Ajan kaynak kullanımı kaydet"""
        self.gauge("agent.cpu_percent", cpu_percent, labels={"agent": agent_id})
        self.gauge("agent.memory_mb", memory_mb, labels={"agent": agent_id})
    
    def record_match_result(self, matched: bool, confidence: float = 0) -> None:
        """Eşleştirme sonucu kaydet"""
        self.increment("match.total_count")
        if matched:
            self.increment("match.success_count")
            self.histogram("match.confidence", confidence)
        else:
            self.increment("match.failed_count")
        
        # Match rate güncelle
        total = self.get_counter("match.total_count")
        success = self.get_counter("match.success_count")
        if total > 0:
            self.gauge("quality.match_rate", success / total)
    
    _task_start_times: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self._task_start_times = {}


class TimerContext:
    """Context manager ile süre ölçümü"""
    
    def __init__(self, collector: MetricsCollector, name: str, labels: Optional[dict] = None):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.collector.timer(self.name, duration, self.labels)
        return False


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Singleton MetricsCollector erişimi"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        _metrics_collector._task_start_times = {}
    return _metrics_collector


if __name__ == "__main__":
    # Test
    metrics = get_metrics_collector()
    
    # Bazı metrikler kaydet
    metrics.increment("task.completed_count")
    metrics.increment("task.completed_count")
    metrics.increment("task.error_count")
    
    metrics.timer("task.duration_seconds", 2.5)
    metrics.timer("task.duration_seconds", 3.2)
    metrics.timer("task.duration_seconds", 1.8)
    
    metrics.gauge("system.queue_depth", 45)
    metrics.gauge("quality.match_rate", 0.65)
    
    # Dashboard verisi
    dashboard = metrics.get_dashboard_data()
    print("Dashboard Data:")
    for key, value in dashboard.items():
        print(f"  {key}: {value}")
    
    # Summary
    summary = metrics.get_summary("task.duration_seconds")
    if summary:
        print(f"\nTask Duration Summary:")
        print(f"  Count: {summary.count}")
        print(f"  Avg: {summary.avg_value:.2f}s")
        print(f"  P95: {summary.p95:.2f}s")
