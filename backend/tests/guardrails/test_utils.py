"""Tests for guardrail utilities."""
import threading
import time

import pytest

from app.guardrails.utils import ResourceMonitor, LockTracker
from app.guardrails.utils.resource_monitor import ResourceThresholds


class TestResourceMonitor:
    """Tests for ResourceMonitor."""

    @pytest.fixture
    def monitor(self) -> ResourceMonitor:
        """Create ResourceMonitor with test config."""
        thresholds = ResourceThresholds(
            memory_limit_mb=2048,
            cpu_warning_percent=90.0,
            disk_min_free_mb=100,
        )
        return ResourceMonitor(thresholds=thresholds, sampling_interval=0.1)

    def test_initialization(self, monitor: ResourceMonitor) -> None:
        """Test monitor initializes correctly."""
        assert monitor.thresholds.memory_limit_mb == 2048
        assert monitor.thresholds.cpu_warning_percent == 90.0

    def test_start(self, monitor: ResourceMonitor) -> None:
        """Test start records start time."""
        monitor.start()
        assert monitor._start_time is not None
        assert len(monitor._history) == 0

    def test_get_snapshot(self, monitor: ResourceMonitor) -> None:
        """Test snapshot captures resource usage."""
        monitor.start()
        snapshot = monitor.get_snapshot()

        assert snapshot.timestamp > 0
        assert snapshot.memory_used_mb >= 0
        assert snapshot.cpu_percent >= 0
        assert snapshot.disk_free_mb > 0

    def test_history_tracking(self, monitor: ResourceMonitor) -> None:
        """Test history is maintained."""
        monitor.start()

        for _ in range(5):
            monitor.get_snapshot()
            time.sleep(0.05)

        assert len(monitor._history) == 5

    def test_history_size_limit(self) -> None:
        """Test history is limited to max size."""
        monitor = ResourceMonitor(history_size=10)
        monitor.start()

        for _ in range(20):
            monitor.get_snapshot()

        assert len(monitor._history) == 10

    def test_check_limits_ok(self, monitor: ResourceMonitor) -> None:
        """Test check_limits returns ok for normal usage."""
        monitor.start()
        result = monitor.check_limits()

        assert "ok" in result
        assert "exceeded" in result
        assert "warnings" in result

    def test_get_average_usage(self, monitor: ResourceMonitor) -> None:
        """Test average calculation."""
        monitor.start()

        for _ in range(5):
            monitor.get_snapshot()
            time.sleep(0.05)

        avg = monitor.get_average_usage()
        assert "memory_mb" in avg
        assert "cpu_percent" in avg

    def test_get_peak_usage(self, monitor: ResourceMonitor) -> None:
        """Test peak calculation."""
        monitor.start()

        for _ in range(5):
            monitor.get_snapshot()
            time.sleep(0.05)

        peak = monitor.get_peak_usage()
        assert "memory_mb" in peak
        assert "cpu_percent" in peak

    def test_generate_report(self, monitor: ResourceMonitor) -> None:
        """Test report generation."""
        monitor.start()

        for _ in range(3):
            monitor.get_snapshot()
            time.sleep(0.05)

        report = monitor.generate_report()

        assert "monitoring_duration_seconds" in report
        assert "samples_collected" in report
        assert "average" in report
        assert "peak" in report
        assert "limits" in report


class TestLockTracker:
    """Tests for LockTracker."""

    @pytest.fixture
    def tracker(self) -> LockTracker:
        """Create LockTracker."""
        return LockTracker()

    def test_acquire_lock(self, tracker: LockTracker) -> None:
        """Test lock acquisition tracking."""
        tracker.acquire("lock_1", "thread_1")

        status = tracker.get_lock_status("lock_1")
        assert status is not None
        assert status["held_by"] == "thread_1"
        assert status["acquisition_count"] == 1

    def test_release_lock(self, tracker: LockTracker) -> None:
        """Test lock release tracking."""
        tracker.acquire("lock_1", "thread_1")
        tracker.release("lock_1", "thread_1")

        status = tracker.get_lock_status("lock_1")
        assert status["held_by"] is None

    def test_wait_for_lock(self, tracker: LockTracker) -> None:
        """Test wait tracking."""
        tracker.acquire("lock_1", "thread_1")
        tracker.wait("lock_1", "thread_2")

        status = tracker.get_lock_status("lock_1")
        assert "thread_2" in status["waiting_threads"]

    def test_thread_locks_tracking(self, tracker: LockTracker) -> None:
        """Test thread lock ownership tracking."""
        tracker.acquire("lock_1", "thread_1")
        tracker.acquire("lock_2", "thread_1")

        locks = tracker.get_thread_locks("thread_1")
        assert "lock_1" in locks
        assert "lock_2" in locks

    def test_no_deadlock_simple(self, tracker: LockTracker) -> None:
        """Test no deadlock in simple case."""
        tracker.acquire("lock_1", "thread_1")
        tracker.acquire("lock_2", "thread_2")

        result = tracker.detect_deadlock()
        assert result is None

    def test_detect_simple_deadlock(self, tracker: LockTracker) -> None:
        """Test detection of simple deadlock."""
        # Thread 1 holds lock_1, waits for lock_2
        tracker.acquire("lock_1", "thread_1")
        tracker.wait("lock_2", "thread_1")

        # Thread 2 holds lock_2, waits for lock_1
        tracker.acquire("lock_2", "thread_2")
        tracker.wait("lock_1", "thread_2")

        result = tracker.detect_deadlock()
        assert result is not None
        assert result["detected"] is True
        assert "thread_1" in result["involved_threads"] or "thread_2" in result["involved_threads"]

    def test_event_history(self, tracker: LockTracker) -> None:
        """Test event history recording."""
        tracker.acquire("lock_1", "thread_1")
        tracker.wait("lock_2", "thread_1")
        tracker.release("lock_1", "thread_1")

        history = tracker.get_event_history()
        assert len(history) == 3

        event_types = [e["event_type"] for e in history]
        assert "acquired" in event_types
        assert "waiting" in event_types
        assert "released" in event_types

    def test_history_size_limit(self) -> None:
        """Test history size is limited."""
        tracker = LockTracker(history_size=5)

        for i in range(10):
            tracker.acquire(f"lock_{i}", "thread_1")

        history = tracker.get_event_history()
        assert len(history) == 5

    def test_clear(self, tracker: LockTracker) -> None:
        """Test clear removes all state."""
        tracker.acquire("lock_1", "thread_1")
        tracker.acquire("lock_2", "thread_2")

        tracker.clear()

        assert tracker.get_lock_status("lock_1") is None
        assert len(tracker.get_event_history()) == 0

    def test_generate_report(self, tracker: LockTracker) -> None:
        """Test report generation."""
        tracker.acquire("lock_1", "thread_1")
        tracker.wait("lock_2", "thread_1")

        report = tracker.generate_report()

        assert "total_locks_tracked" in report
        assert "currently_held" in report
        assert "threads_waiting" in report
        assert "deadlock_detected" in report

    def test_get_waiting_threads(self, tracker: LockTracker) -> None:
        """Test get_waiting_threads method."""
        tracker.acquire("lock_1", "thread_1")
        tracker.wait("lock_1", "thread_2")
        tracker.wait("lock_1", "thread_3")

        waiting = tracker.get_waiting_threads()
        assert "lock_1" in waiting
        assert len(waiting["lock_1"]) == 2


class TestLockTrackerThreadSafety:
    """Thread safety tests for LockTracker."""

    def test_concurrent_acquisitions(self) -> None:
        """Test concurrent lock acquisitions don't corrupt state."""
        tracker = LockTracker()
        errors = []

        def acquire_locks(thread_num: int) -> None:
            try:
                for i in range(100):
                    tracker.acquire(f"lock_{i}", f"thread_{thread_num}")
                    tracker.release(f"lock_{i}", f"thread_{thread_num}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=acquire_locks, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_deadlock_detection(self) -> None:
        """Test deadlock detection during concurrent operations."""
        tracker = LockTracker()
        detection_results = []

        def check_deadlock() -> None:
            for _ in range(50):
                result = tracker.detect_deadlock()
                detection_results.append(result)
                time.sleep(0.001)

        def modify_locks() -> None:
            for i in range(50):
                tracker.acquire(f"lock_{i % 10}", f"thread_{i % 3}")
                time.sleep(0.001)
                tracker.release(f"lock_{i % 10}", f"thread_{i % 3}")

        threads = [
            threading.Thread(target=check_deadlock),
            threading.Thread(target=modify_locks),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert len(detection_results) == 50
