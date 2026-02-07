"""Lock tracking utilities for deadlock detection."""
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LockInfo:
    """Information about a tracked lock."""
    lock_id: str
    held_by: str | None = None
    acquired_at: float | None = None
    waiting: list[str] = field(default_factory=list)
    acquisition_count: int = 0


@dataclass
class LockEvent:
    """Record of a lock event."""
    timestamp: float
    event_type: str  # "acquired", "released", "waiting"
    lock_id: str
    thread_id: str


class LockTracker:
    """Tracks lock acquisitions for deadlock detection.

    Maintains a dependency graph of locks and threads to detect
    potential deadlock conditions (circular waits).

    Usage:
        tracker = LockTracker()

        # Track lock events
        tracker.acquire("lock_1", "thread_1")
        tracker.wait("lock_2", "thread_1")

        # Check for deadlocks
        if tracker.detect_deadlock():
            handle_deadlock()

        tracker.release("lock_1", "thread_1")
    """

    def __init__(self, history_size: int = 1000):
        """Initialize lock tracker.

        Args:
            history_size: Maximum events to keep in history
        """
        self.history_size = history_size
        self._locks: dict[str, LockInfo] = {}
        self._thread_locks: dict[str, list[str]] = {}  # thread -> [lock_ids]
        self._events: list[LockEvent] = []
        self._lock = threading.RLock()

    def acquire(self, lock_id: str, thread_id: str | None = None) -> None:
        """Record lock acquisition.

        Args:
            lock_id: ID of the acquired lock
            thread_id: Thread that acquired the lock (default: current thread)
        """
        thread_id = thread_id or str(threading.current_thread().ident)

        with self._lock:
            # Create lock info if not exists
            if lock_id not in self._locks:
                self._locks[lock_id] = LockInfo(lock_id=lock_id)

            lock_info = self._locks[lock_id]
            lock_info.held_by = thread_id
            lock_info.acquired_at = time.time()
            lock_info.acquisition_count += 1
            lock_info.waiting = [w for w in lock_info.waiting if w != thread_id]

            # Track thread's locks
            if thread_id not in self._thread_locks:
                self._thread_locks[thread_id] = []
            self._thread_locks[thread_id].append(lock_id)

            # Log event
            self._add_event("acquired", lock_id, thread_id)

        logger.debug(f"Lock {lock_id} acquired by thread {thread_id}")

    def release(self, lock_id: str, thread_id: str | None = None) -> None:
        """Record lock release.

        Args:
            lock_id: ID of the released lock
            thread_id: Thread that released the lock (default: current thread)
        """
        thread_id = thread_id or str(threading.current_thread().ident)

        with self._lock:
            if lock_id in self._locks:
                lock_info = self._locks[lock_id]
                if lock_info.held_by == thread_id:
                    lock_info.held_by = None
                    lock_info.acquired_at = None

            if thread_id in self._thread_locks:
                if lock_id in self._thread_locks[thread_id]:
                    self._thread_locks[thread_id].remove(lock_id)

            self._add_event("released", lock_id, thread_id)

        logger.debug(f"Lock {lock_id} released by thread {thread_id}")

    def wait(self, lock_id: str, thread_id: str | None = None) -> None:
        """Record thread waiting for a lock.

        Args:
            lock_id: ID of the lock being waited for
            thread_id: Thread waiting for the lock (default: current thread)
        """
        thread_id = thread_id or str(threading.current_thread().ident)

        with self._lock:
            if lock_id not in self._locks:
                self._locks[lock_id] = LockInfo(lock_id=lock_id)

            lock_info = self._locks[lock_id]
            if thread_id not in lock_info.waiting:
                lock_info.waiting.append(thread_id)

            self._add_event("waiting", lock_id, thread_id)

        logger.debug(f"Thread {thread_id} waiting for lock {lock_id}")

    def detect_deadlock(self) -> dict[str, Any] | None:
        """Detect circular wait conditions (deadlock).

        Returns:
            Deadlock info if detected, None otherwise
        """
        with self._lock:
            # Build wait-for graph
            # Thread A waits for Thread B if A is waiting for a lock held by B
            wait_for: dict[str, set[str]] = {}

            for lock_id, lock_info in self._locks.items():
                if lock_info.held_by and lock_info.waiting:
                    for waiting_thread in lock_info.waiting:
                        if waiting_thread not in wait_for:
                            wait_for[waiting_thread] = set()
                        wait_for[waiting_thread].add(lock_info.held_by)

            # Detect cycle using DFS
            visited = set()
            rec_stack = set()

            def find_cycle(thread: str, path: list[str]) -> list[str] | None:
                visited.add(thread)
                rec_stack.add(thread)
                path.append(thread)

                for next_thread in wait_for.get(thread, set()):
                    if next_thread not in visited:
                        cycle = find_cycle(next_thread, path)
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
                    cycle = find_cycle(thread, [])
                    if cycle:
                        # Find involved locks
                        involved_locks = []
                        for lock_id, lock_info in self._locks.items():
                            if lock_info.held_by in cycle or any(w in cycle for w in lock_info.waiting):
                                involved_locks.append(lock_id)

                        return {
                            "detected": True,
                            "cycle": cycle,
                            "involved_threads": cycle,
                            "involved_locks": involved_locks,
                        }

            return None

    def get_lock_status(self, lock_id: str) -> dict[str, Any] | None:
        """Get status of a specific lock.

        Args:
            lock_id: ID of the lock

        Returns:
            Lock status or None if not found
        """
        with self._lock:
            if lock_id not in self._locks:
                return None

            lock_info = self._locks[lock_id]
            return {
                "lock_id": lock_info.lock_id,
                "held_by": lock_info.held_by,
                "acquired_at": lock_info.acquired_at,
                "waiting_count": len(lock_info.waiting),
                "waiting_threads": lock_info.waiting.copy(),
                "acquisition_count": lock_info.acquisition_count,
            }

    def get_thread_locks(self, thread_id: str | None = None) -> list[str]:
        """Get locks held by a thread.

        Args:
            thread_id: Thread ID (default: current thread)

        Returns:
            List of lock IDs held by the thread
        """
        thread_id = thread_id or str(threading.current_thread().ident)

        with self._lock:
            return self._thread_locks.get(thread_id, []).copy()

    def get_waiting_threads(self) -> dict[str, list[str]]:
        """Get all threads waiting for locks.

        Returns:
            Dictionary mapping lock_id to list of waiting thread IDs
        """
        with self._lock:
            return {
                lock_id: lock_info.waiting.copy()
                for lock_id, lock_info in self._locks.items()
                if lock_info.waiting
            }

    def get_event_history(self) -> list[dict[str, Any]]:
        """Get lock event history.

        Returns:
            List of event dictionaries
        """
        with self._lock:
            return [
                {
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "lock_id": e.lock_id,
                    "thread_id": e.thread_id,
                }
                for e in self._events
            ]

    def _add_event(self, event_type: str, lock_id: str, thread_id: str) -> None:
        """Add event to history (internal, must hold lock).

        Args:
            event_type: Type of event
            lock_id: Lock ID
            thread_id: Thread ID
        """
        event = LockEvent(
            timestamp=time.time(),
            event_type=event_type,
            lock_id=lock_id,
            thread_id=thread_id,
        )
        self._events.append(event)

        # Trim history
        if len(self._events) > self.history_size:
            self._events = self._events[-self.history_size:]

    def clear(self) -> None:
        """Clear all tracked locks and events."""
        with self._lock:
            self._locks.clear()
            self._thread_locks.clear()
            self._events.clear()
        logger.debug("Lock tracker cleared")

    def generate_report(self) -> dict[str, Any]:
        """Generate a lock tracking report.

        Returns:
            Dictionary with tracking statistics
        """
        with self._lock:
            held_count = sum(1 for l in self._locks.values() if l.held_by)
            waiting_count = sum(len(l.waiting) for l in self._locks.values())

            return {
                "total_locks_tracked": len(self._locks),
                "currently_held": held_count,
                "threads_waiting": waiting_count,
                "active_threads": len(self._thread_locks),
                "events_recorded": len(self._events),
                "deadlock_detected": self.detect_deadlock() is not None,
            }
