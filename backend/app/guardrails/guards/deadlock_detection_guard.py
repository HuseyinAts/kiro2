"""Deadlock detection guard - prevents stuck processes."""
import asyncio
import logging
import threading
import time
from typing import Any

from .base_guard import BaseGuard
from ..models import GuardResult, GuardStatus

logger = logging.getLogger(__name__)


class LockNode:
    """Represents a lock in the dependency graph."""

    def __init__(self, lock_id: str):
        self.lock_id = lock_id
        self.held_by: str | None = None  # Thread/Task ID
        self.waiting: list[str] = []  # Thread/Task IDs waiting for this lock
        self.acquired_at: float | None = None


class DeadlockDetectionGuard(BaseGuard):
    """Detects deadlocks using lock dependency graph analysis.

    Configuration:
        deadlock_timeout: Seconds before considering a wait as potential deadlock (default: 30)
        check_interval: Seconds between deadlock checks (default: 5)
        enable_watchdog: Enable watchdog timer (default: True)
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize Deadlock Detection guard.

        Args:
            config: Configuration with deadlock settings
        """
        super().__init__(config)
        self.deadlock_timeout: float = config.get("deadlock_timeout", 30.0)
        self.check_interval: float = config.get("check_interval", 5.0)
        self.enable_watchdog: bool = config.get("enable_watchdog", True)

        # Lock dependency graph
        self._locks: dict[str, LockNode] = {}
        self._thread_locks: dict[str, list[str]] = {}  # thread_id -> [lock_ids]
        self._last_check_time: float = 0.0
        self._lock = threading.Lock()

        # Watchdog timer
        self._watchdog_task: asyncio.Task | None = None
        self._last_activity_time: float = time.time()

    async def check(self, context: dict[str, Any]) -> GuardResult:
        """Check for deadlock conditions.

        Args:
            context: Execution context containing:
                - lock_acquired: Lock ID that was acquired (optional)
                - lock_released: Lock ID that was released (optional)
                - lock_waiting: Lock ID being waited for (optional)
                - thread_id: Current thread/task ID (optional)

        Returns:
            GuardResult with STOP if deadlock detected, OK otherwise
        """
        self._increment_check_count()
        current_time = time.time()
        self._last_activity_time = current_time

        # Process lock events
        thread_id = context.get("thread_id", str(threading.current_thread().ident))

        if "lock_acquired" in context:
            self._record_lock_acquired(thread_id, context["lock_acquired"])

        if "lock_released" in context:
            self._record_lock_released(thread_id, context["lock_released"])

        if "lock_waiting" in context:
            self._record_lock_waiting(thread_id, context["lock_waiting"])

        # Check for deadlock periodically
        if current_time - self._last_check_time >= self.check_interval:
            self._last_check_time = current_time
            deadlock_info = self._detect_deadlock()

            if deadlock_info:
                result = self._create_result(
                    status=GuardStatus.STOP,
                    message=f"Deadlock detected involving locks: {', '.join(deadlock_info['involved_locks'])}",
                    details={
                        "involved_locks": deadlock_info["involved_locks"],
                        "involved_threads": deadlock_info["involved_threads"],
                        "cycle": deadlock_info["cycle"],
                    },
                    should_stop=True
                )
                logger.error(f"Deadlock detected: {deadlock_info}")
                self._log_check(result)
                return result

        # Check for long waits (potential deadlock)
        long_waits = self._check_long_waits()
        if long_waits:
            result = self._create_result(
                status=GuardStatus.WARNING,
                message=f"Potential deadlock: {len(long_waits)} locks held > {self.deadlock_timeout}s",
                details={
                    "long_waits": long_waits,
                    "threshold_seconds": self.deadlock_timeout,
                },
                should_stop=False
            )
            self._log_check(result)
            return result

        # Normal operation
        return self._create_result(
            status=GuardStatus.OK,
            message=f"No deadlock detected ({len(self._locks)} locks tracked)",
            details={
                "tracked_locks": len(self._locks),
                "active_threads": len(self._thread_locks),
            },
            should_stop=False
        )

    def reset(self) -> None:
        """Reset deadlock detector for new execution."""
        with self._lock:
            self._locks.clear()
            self._thread_locks.clear()
            self._last_check_time = 0.0
        self._check_count = 0
        logger.debug(f"Deadlock detection guard reset (timeout: {self.deadlock_timeout}s)")

    def _record_lock_acquired(self, thread_id: str, lock_id: str) -> None:
        """Record a lock acquisition.

        Args:
            thread_id: Thread/task that acquired the lock
            lock_id: ID of the acquired lock
        """
        with self._lock:
            if lock_id not in self._locks:
                self._locks[lock_id] = LockNode(lock_id)

            node = self._locks[lock_id]
            node.held_by = thread_id
            node.acquired_at = time.time()
            node.waiting = [w for w in node.waiting if w != thread_id]

            if thread_id not in self._thread_locks:
                self._thread_locks[thread_id] = []
            self._thread_locks[thread_id].append(lock_id)

            logger.debug(f"Lock {lock_id} acquired by {thread_id}")

    def _record_lock_released(self, thread_id: str, lock_id: str) -> None:
        """Record a lock release.

        Args:
            thread_id: Thread/task that released the lock
            lock_id: ID of the released lock
        """
        with self._lock:
            if lock_id in self._locks:
                node = self._locks[lock_id]
                if node.held_by == thread_id:
                    node.held_by = None
                    node.acquired_at = None

            if thread_id in self._thread_locks:
                if lock_id in self._thread_locks[thread_id]:
                    self._thread_locks[thread_id].remove(lock_id)

            logger.debug(f"Lock {lock_id} released by {thread_id}")

    def _record_lock_waiting(self, thread_id: str, lock_id: str) -> None:
        """Record a thread waiting for a lock.

        Args:
            thread_id: Thread/task waiting for the lock
            lock_id: ID of the lock being waited for
        """
        with self._lock:
            if lock_id not in self._locks:
                self._locks[lock_id] = LockNode(lock_id)

            node = self._locks[lock_id]
            if thread_id not in node.waiting:
                node.waiting.append(thread_id)

            logger.debug(f"Thread {thread_id} waiting for lock {lock_id}")

    def _detect_deadlock(self) -> dict[str, Any] | None:
        """Detect circular wait conditions (deadlock).

        Returns:
            Deadlock information if detected, None otherwise
        """
        with self._lock:
            # Build wait-for graph
            # Thread A waits for Thread B if A is waiting for a lock held by B
            wait_for: dict[str, set[str]] = {}

            for lock_id, node in self._locks.items():
                if node.held_by and node.waiting:
                    for waiting_thread in node.waiting:
                        if waiting_thread not in wait_for:
                            wait_for[waiting_thread] = set()
                        wait_for[waiting_thread].add(node.held_by)

            # Detect cycle using DFS
            visited = set()
            rec_stack = set()

            def has_cycle(thread: str, path: list[str]) -> list[str] | None:
                visited.add(thread)
                rec_stack.add(thread)
                path.append(thread)

                for next_thread in wait_for.get(thread, set()):
                    if next_thread not in visited:
                        cycle = has_cycle(next_thread, path)
                        if cycle:
                            return cycle
                    elif next_thread in rec_stack:
                        # Found cycle
                        cycle_start = path.index(next_thread)
                        return path[cycle_start:]

                path.pop()
                rec_stack.remove(thread)
                return None

            for thread in wait_for:
                if thread not in visited:
                    cycle = has_cycle(thread, [])
                    if cycle:
                        # Find involved locks
                        involved_locks = []
                        for lock_id, node in self._locks.items():
                            if node.held_by in cycle or any(w in cycle for w in node.waiting):
                                involved_locks.append(lock_id)

                        return {
                            "involved_threads": cycle,
                            "involved_locks": involved_locks,
                            "cycle": cycle,
                        }

            return None

    def _check_long_waits(self) -> list[dict[str, Any]]:
        """Check for locks held longer than timeout.

        Returns:
            List of long-wait information
        """
        current_time = time.time()
        long_waits = []

        with self._lock:
            for lock_id, node in self._locks.items():
                if node.acquired_at and node.held_by:
                    hold_time = current_time - node.acquired_at
                    if hold_time > self.deadlock_timeout:
                        long_waits.append({
                            "lock_id": lock_id,
                            "held_by": node.held_by,
                            "hold_time_seconds": round(hold_time, 2),
                            "waiting_count": len(node.waiting),
                        })

        return long_waits

    def get_lock_status(self) -> dict[str, Any]:
        """Get current lock status report.

        Returns:
            Dictionary with lock statistics
        """
        with self._lock:
            return {
                "total_locks": len(self._locks),
                "held_locks": sum(1 for n in self._locks.values() if n.held_by),
                "waiting_threads": sum(len(n.waiting) for n in self._locks.values()),
                "threads_with_locks": len(self._thread_locks),
            }

    async def start_watchdog(self) -> None:
        """Start the watchdog timer for activity monitoring."""
        if not self.enable_watchdog:
            return

        async def watchdog_loop():
            while True:
                await asyncio.sleep(self.deadlock_timeout / 2)
                elapsed = time.time() - self._last_activity_time
                if elapsed > self.deadlock_timeout:
                    logger.warning(f"Watchdog: No activity for {elapsed:.1f}s")

        self._watchdog_task = asyncio.create_task(watchdog_loop())

    async def stop_watchdog(self) -> None:
        """Stop the watchdog timer."""
        if self._watchdog_task:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
            self._watchdog_task = None
