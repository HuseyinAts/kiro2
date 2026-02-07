"""Shared data schemas for the learning system.

Central location for Lesson, SemanticInsight, SkillPointer, InjectedContext,
and Skill dataclasses. All orchestration modules import from here to avoid
schema drift between memory_injector, feedback_collector, skill_library,
and lesson_consolidator.

Confidence levels: LOW < MEDIUM < HIGH < VERIFIED
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIDENCE_SCORES: dict[str, float] = {
    "LOW": 0.2,
    "MEDIUM": 0.5,
    "HIGH": 0.8,
    "VERIFIED": 1.0,
}

CONFIDENCE_ORDER: list[str] = ["LOW", "MEDIUM", "HIGH", "VERIFIED"]

MAX_LESSONS = 10
MAX_TOKEN_BUDGET = 2000
MIN_CONFIDENCE = "MEDIUM"

# Allowed safety permissions for skills (FM-5 allowlist)
ALLOWED_PERMISSIONS: frozenset[str] = frozenset({
    "read_repo",
    "run_tests",
    "write_file",
    "run_lint",
    "run_typecheck",
    "read_db",
    "write_db",
    "http_request",
})


# ---------------------------------------------------------------------------
# Episodic Memory (Katman 3)
# ---------------------------------------------------------------------------


@dataclass
class Lesson:
    """Episodic memory lesson."""

    id: str
    agent_id: str
    task_type: str
    timestamp: str  # ISO 8601
    outcome: str  # "success" | "failure"
    signals: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    hypothesis: str = ""
    fix: str = ""
    result: str = ""
    applicability: dict[str, Any] = field(default_factory=dict)
    confidence: str = "LOW"
    safety_review: str = "pass"
    scope: list[str] = field(default_factory=list)
    expiry: str = ""
    owner: str = ""
    access_count: int = 0
    last_accessed: str = ""
    beta_alpha: int = 1  # Bayesian M4
    beta_beta: int = 1  # Bayesian M4

    @property
    def bayesian_mean(self) -> float:
        """Beta distribution posterior mean."""
        return self.beta_alpha / (self.beta_alpha + self.beta_beta)


# ---------------------------------------------------------------------------
# Semantic Memory (Katman 4)
# ---------------------------------------------------------------------------


@dataclass
class SemanticInsight:
    """Semantic memory insight."""

    key: str
    statement: str
    derived_from: list[str] = field(default_factory=list)
    conflict_keys: list[str] = field(default_factory=list)
    supersedes: list[str] = field(default_factory=list)
    last_verified: str = ""
    confidence: str = "LOW"
    domain: str = ""
    task_type: str = ""
    source_agent_id: str = ""
    insight_type: str = "heuristic"  # "fact" | "heuristic"
    created_by: str = ""
    created_at: str = ""


# ---------------------------------------------------------------------------
# Procedural Memory (Katman 5)
# ---------------------------------------------------------------------------


@dataclass
class SkillPointer:
    """Lightweight skill reference for injection."""

    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    confidence: str = "LOW"
    success_rate: float = 0.0


@dataclass
class Skill:
    """Full skill definition - Agent Skills Standard."""

    id: str = ""
    name: str = ""
    description: str = ""
    entrypoint: str = ""  # script path or instructions
    prerequisites: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    safety_permissions: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    version: str = "1.0.0"  # semver
    agent_id: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: str = "LOW"
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Skill:
        """Deserialize from dict."""
        valid_fields = cls.__dataclass_fields__
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# Working Memory (Katman 2)
# ---------------------------------------------------------------------------


@dataclass
class InjectedContext:
    """WM-State output - BDI state separation (P7)."""

    beliefs: list[str] = field(default_factory=list)
    desires: list[str] = field(default_factory=list)
    intentions: list[str] = field(default_factory=list)
    lessons: list[Lesson] = field(default_factory=list)
    anti_patterns: list[Lesson] = field(default_factory=list)
    skills: list[SkillPointer] = field(default_factory=list)
    facts: list[SemanticInsight] = field(default_factory=list)
    token_count: int = 0


# ---------------------------------------------------------------------------
# File locking utility
# ---------------------------------------------------------------------------


import contextlib
import os
import sys


@contextlib.contextmanager
def file_lock(path: str | os.PathLike[str]):
    """Cross-platform advisory file lock.

    Uses msvcrt on Windows, fcntl on POSIX.
    Yields an open file handle in 'r+' or 'w' mode (caller decides).
    """
    lock_path = str(path) + ".lock"
    lock_fd = None
    try:
        lock_fd = open(lock_path, "w", encoding="utf-8")
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except (OSError, IOError):
        # Could not acquire lock — proceed without it (best effort)
        yield
    finally:
        if lock_fd is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    try:
                        msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError:
                        pass
                else:
                    import fcntl
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                lock_fd.close()
                try:
                    os.remove(lock_path)
                except OSError:
                    pass
