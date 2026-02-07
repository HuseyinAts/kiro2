"""Resource monitoring utilities for guardrails."""
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Try to import psutil, provide fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, resource monitoring will be limited")


@dataclass
class ResourceSnapshot:
    """Snapshot of system resource usage."""
    timestamp: float
    memory_used_mb: float
    memory_percent: float
    cpu_percent: float
    disk_free_mb: float
    disk_percent: float
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0


@dataclass
class ResourceThresholds:
    """Resource limit thresholds."""
    memory_limit_mb: int = 1024
    memory_warning_percent: float = 80.0
    cpu_warning_percent: float = 80.0
    disk_min_free_mb: int = 100
    network_bandwidth_limit_mbps: float = 100.0


class ResourceMonitor:
    """Monitors system resource usage.

    Provides continuous monitoring of:
    - Memory usage (process and system)
    - CPU usage
    - Disk space
    - Network bandwidth

    Usage:
        monitor = ResourceMonitor()
        monitor.start()

        while running:
            snapshot = monitor.get_snapshot()
            if monitor.check_limits():
                # Take action

        history = monitor.get_history()
    """

    def __init__(
        self,
        thresholds: ResourceThresholds | None = None,
        sampling_interval: float = 1.0,
        history_size: int = 100
    ):
        """Initialize resource monitor.

        Args:
            thresholds: Resource limit thresholds
            sampling_interval: Seconds between samples
            history_size: Number of samples to keep in history
        """
        self.thresholds = thresholds or ResourceThresholds()
        self.sampling_interval = sampling_interval
        self.history_size = history_size

        self._history: list[ResourceSnapshot] = []
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None
        self._start_time: float | None = None
        self._last_network: tuple[int, int] | None = None

    def start(self) -> None:
        """Start monitoring (record start time)."""
        self._start_time = time.time()
        self._history = []
        self._last_network = self._get_network_counters()
        logger.info("Resource monitor started")

    def get_snapshot(self) -> ResourceSnapshot:
        """Get current resource usage snapshot.

        Returns:
            ResourceSnapshot with current usage
        """
        if not PSUTIL_AVAILABLE:
            return ResourceSnapshot(
                timestamp=time.time(),
                memory_used_mb=0,
                memory_percent=0,
                cpu_percent=0,
                disk_free_mb=float("inf"),
                disk_percent=0,
            )

        current_time = time.time()

        # Memory
        mem_info = self._process.memory_info() if self._process else None
        memory_used_mb = mem_info.rss / (1024 * 1024) if mem_info else 0
        vm = psutil.virtual_memory()
        memory_percent = (memory_used_mb / self.thresholds.memory_limit_mb) * 100

        # CPU
        cpu_percent = self._process.cpu_percent(interval=0.1) if self._process else 0

        # Disk
        disk = psutil.disk_usage(os.getcwd())
        disk_free_mb = disk.free / (1024 * 1024)

        # Network
        network = self._get_network_counters()
        bytes_sent = network[0] - (self._last_network[0] if self._last_network else 0)
        bytes_recv = network[1] - (self._last_network[1] if self._last_network else 0)
        self._last_network = network

        snapshot = ResourceSnapshot(
            timestamp=current_time,
            memory_used_mb=memory_used_mb,
            memory_percent=memory_percent,
            cpu_percent=cpu_percent,
            disk_free_mb=disk_free_mb,
            disk_percent=disk.percent,
            network_bytes_sent=bytes_sent,
            network_bytes_recv=bytes_recv,
        )

        # Add to history
        self._history.append(snapshot)
        if len(self._history) > self.history_size:
            self._history = self._history[-self.history_size:]

        return snapshot

    def check_limits(self) -> dict[str, Any]:
        """Check if any resource limits are exceeded.

        Returns:
            Dictionary with limit check results
        """
        snapshot = self.get_snapshot()

        exceeded = []
        warnings = []

        # Memory
        if snapshot.memory_used_mb > self.thresholds.memory_limit_mb:
            exceeded.append("memory")
        elif snapshot.memory_percent >= self.thresholds.memory_warning_percent:
            warnings.append("memory")

        # CPU
        if snapshot.cpu_percent >= self.thresholds.cpu_warning_percent:
            warnings.append("cpu")

        # Disk
        if snapshot.disk_free_mb < self.thresholds.disk_min_free_mb:
            exceeded.append("disk")

        return {
            "ok": len(exceeded) == 0,
            "exceeded": exceeded,
            "warnings": warnings,
            "snapshot": snapshot,
        }

    def get_history(self) -> list[ResourceSnapshot]:
        """Get resource usage history.

        Returns:
            List of resource snapshots
        """
        return self._history.copy()

    def get_average_usage(self) -> dict[str, float]:
        """Calculate average resource usage from history.

        Returns:
            Dictionary with average values
        """
        if not self._history:
            return {"memory_mb": 0, "cpu_percent": 0}

        return {
            "memory_mb": sum(s.memory_used_mb for s in self._history) / len(self._history),
            "cpu_percent": sum(s.cpu_percent for s in self._history) / len(self._history),
        }

    def get_peak_usage(self) -> dict[str, float]:
        """Get peak resource usage from history.

        Returns:
            Dictionary with peak values
        """
        if not self._history:
            return {"memory_mb": 0, "cpu_percent": 0}

        return {
            "memory_mb": max(s.memory_used_mb for s in self._history),
            "cpu_percent": max(s.cpu_percent for s in self._history),
        }

    def _get_network_counters(self) -> tuple[int, int]:
        """Get network I/O counters.

        Returns:
            Tuple of (bytes_sent, bytes_recv)
        """
        if not PSUTIL_AVAILABLE:
            return (0, 0)

        try:
            net = psutil.net_io_counters()
            return (net.bytes_sent, net.bytes_recv)
        except Exception:
            return (0, 0)

    def generate_report(self) -> dict[str, Any]:
        """Generate a comprehensive resource usage report.

        Returns:
            Dictionary with usage statistics
        """
        elapsed = time.time() - self._start_time if self._start_time else 0

        return {
            "monitoring_duration_seconds": round(elapsed, 2),
            "samples_collected": len(self._history),
            "current": self.get_snapshot().__dict__ if self._history else {},
            "average": self.get_average_usage(),
            "peak": self.get_peak_usage(),
            "limits": {
                "memory_limit_mb": self.thresholds.memory_limit_mb,
                "cpu_warning_percent": self.thresholds.cpu_warning_percent,
                "disk_min_free_mb": self.thresholds.disk_min_free_mb,
            },
        }
