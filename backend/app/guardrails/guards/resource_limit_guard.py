"""Resource limit guard - prevents resource exhaustion."""
import logging
import os
from typing import Any

from .base_guard import BaseGuard
from ..models import GuardResult, GuardStatus

logger = logging.getLogger(__name__)

# Try to import psutil, provide fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, resource monitoring will be limited")


class ResourceLimitGuard(BaseGuard):
    """Monitors and enforces resource limits to prevent exhaustion.

    Configuration:
        memory_limit_mb: Maximum memory usage in MB (default: 1024)
        cpu_limit_percent: Maximum CPU usage percentage (default: 80)
        disk_min_free_mb: Minimum free disk space in MB (default: 100)
        check_interval_iterations: Check resources every N iterations (default: 10)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Resource Limit guard.

        Args:
            config: Configuration with resource limits
        """
        super().__init__(config)
        self.memory_limit_mb: int = config.get("memory_limit_mb", 1024)
        self.cpu_limit_percent: float = config.get("cpu_limit_percent", 80.0)
        self.disk_min_free_mb: int = config.get("disk_min_free_mb", 100)
        self.check_interval: int = config.get("check_interval_iterations", 10)
        self.warning_threshold: float = config.get("warning_threshold", 0.8)

        self._last_cpu_check: float = 0.0
        self._iterations_since_check: int = 0
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check resource usage against limits.

        Args:
            context: Execution context

        Returns:
            GuardResult with STOP if limits exceeded, WARNING if approaching, OK otherwise
        """
        self._increment_check_count()
        self._iterations_since_check += 1

        # Only check resources every N iterations for performance
        if self._iterations_since_check < self.check_interval:
            return self._create_result(
                status=GuardStatus.OK,
                message="Resource check skipped (interval)",
                details={"iterations_until_check": self.check_interval - self._iterations_since_check},
                should_stop=False
            )

        self._iterations_since_check = 0

        if not PSUTIL_AVAILABLE:
            return self._create_result(
                status=GuardStatus.WARNING,
                message="Resource monitoring unavailable (psutil not installed)",
                details={"psutil_available": False},
                should_stop=False
            )

        # Get current resource usage
        memory_info = self._get_memory_usage()
        cpu_usage = self._get_cpu_usage()
        disk_info = self._get_disk_usage()

        details = {
            "memory_used_mb": memory_info["used_mb"],
            "memory_limit_mb": self.memory_limit_mb,
            "memory_percent": memory_info["percent"],
            "cpu_percent": cpu_usage,
            "cpu_limit_percent": self.cpu_limit_percent,
            "disk_free_mb": disk_info["free_mb"],
            "disk_min_free_mb": self.disk_min_free_mb,
        }

        # Check memory limit
        if memory_info["used_mb"] > self.memory_limit_mb:
            result = self._create_result(
                status=GuardStatus.STOP,
                message=f"Memory limit exceeded: {memory_info['used_mb']:.0f}MB/{self.memory_limit_mb}MB",
                details=details,
                should_stop=True
            )
            logger.error(f"Memory limit exceeded: {memory_info['used_mb']}MB > {self.memory_limit_mb}MB")
            self._log_check(result)
            return result

        # Check CPU limit
        if cpu_usage > self.cpu_limit_percent:
            result = self._create_result(
                status=GuardStatus.WARNING,
                message=f"CPU usage high: {cpu_usage:.1f}%/{self.cpu_limit_percent}%",
                details=details,
                should_stop=False  # Warning only for CPU
            )
            logger.warning(f"High CPU usage: {cpu_usage:.1f}%")
            self._log_check(result)
            return result

        # Check disk space
        if disk_info["free_mb"] < self.disk_min_free_mb:
            result = self._create_result(
                status=GuardStatus.STOP,
                message=f"Disk space low: {disk_info['free_mb']:.0f}MB (min: {self.disk_min_free_mb}MB)",
                details=details,
                should_stop=True
            )
            logger.error(f"Disk space low: {disk_info['free_mb']}MB")
            self._log_check(result)
            return result

        # Check warning thresholds
        warnings = []
        memory_warning_limit = self.memory_limit_mb * self.warning_threshold
        if memory_info["used_mb"] >= memory_warning_limit:
            warnings.append(f"memory at {memory_info['percent']:.0f}%")

        cpu_warning_limit = self.cpu_limit_percent * self.warning_threshold
        if cpu_usage >= cpu_warning_limit:
            warnings.append(f"CPU at {cpu_usage:.0f}%")

        if warnings:
            result = self._create_result(
                status=GuardStatus.WARNING,
                message=f"Resource warning: {', '.join(warnings)}",
                details=details,
                should_stop=False
            )
            self._log_check(result)
            return result

        # Normal operation
        result = self._create_result(
            status=GuardStatus.OK,
            message=f"Resources OK - Memory: {memory_info['percent']:.0f}%, CPU: {cpu_usage:.0f}%",
            details=details,
            should_stop=False
        )
        return result

    def reset(self) -> None:
        """Reset resource monitor for new execution."""
        self._iterations_since_check = 0
        self._last_cpu_check = 0.0
        self._check_count = 0
        logger.debug(
            f"Resource limit guard reset (memory: {self.memory_limit_mb}MB, "
            f"CPU: {self.cpu_limit_percent}%)"
        )

    def _get_memory_usage(self) -> dict[str, float]:
        """Get current memory usage.

        Returns:
            Dictionary with memory stats
        """
        if not self._process:
            return {"used_mb": 0, "percent": 0}

        try:
            mem_info = self._process.memory_info()
            used_mb = mem_info.rss / (1024 * 1024)
            total = psutil.virtual_memory().total / (1024 * 1024)
            return {
                "used_mb": used_mb,
                "percent": (used_mb / self.memory_limit_mb) * 100 if self.memory_limit_mb > 0 else 0,
                "total_mb": total,
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"used_mb": 0, "percent": 0}

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage.

        Returns:
            CPU usage percentage
        """
        if not self._process:
            return 0.0

        try:
            return self._process.cpu_percent(interval=0.1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return 0.0

    def _get_disk_usage(self) -> dict[str, float]:
        """Get current disk usage.

        Returns:
            Dictionary with disk stats
        """
        try:
            disk = psutil.disk_usage(os.getcwd())
            return {
                "total_mb": disk.total / (1024 * 1024),
                "used_mb": disk.used / (1024 * 1024),
                "free_mb": disk.free / (1024 * 1024),
                "percent": disk.percent,
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {"total_mb": 0, "used_mb": 0, "free_mb": float("inf"), "percent": 0}

    def get_resource_report(self) -> dict[str, Any]:
        """Generate a resource usage report.

        Returns:
            Dictionary with resource statistics
        """
        return {
            "memory": self._get_memory_usage(),
            "cpu_percent": self._get_cpu_usage(),
            "disk": self._get_disk_usage(),
            "limits": {
                "memory_limit_mb": self.memory_limit_mb,
                "cpu_limit_percent": self.cpu_limit_percent,
                "disk_min_free_mb": self.disk_min_free_mb,
            },
        }
