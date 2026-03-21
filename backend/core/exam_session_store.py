"""
Exam Session Store — Redis-backed session persistence

Hybrid approach:
- L1: In-memory dict (fast, reference-based)
- L2: Redis (survives restart, enables horizontal scaling)

On write: update both dict AND Redis
On read: check dict first, fallback to Redis
On startup: dict is empty, sessions lazily loaded from Redis
"""

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.osym_exam_engine import ExamSessionData

logger = logging.getLogger("exam_session_store")

# Redis key prefix
_REDIS_PREFIX = "exam_session:"
_REDIS_TTL = 3 * 60 * 60  # 3 hours (max exam duration is 165 min)


def _serialize_session(data: "ExamSessionData") -> str:
    """Serialize ExamSessionData to JSON string."""
    d = asdict(data)
    # Convert enums to values
    d["status"] = d["status"].value if hasattr(d["status"], "value") else d["status"]
    if d.get("exam_config"):
        cfg = d["exam_config"]
        cfg["exam_type"] = (
            cfg["exam_type"].value
            if hasattr(cfg["exam_type"], "value")
            else cfg["exam_type"]
        )
        if cfg.get("ayt_field_type"):
            cfg["ayt_field_type"] = (
                cfg["ayt_field_type"].value
                if hasattr(cfg["ayt_field_type"], "value")
                else cfg["ayt_field_type"]
            )
        if cfg.get("ydt_language"):
            cfg["ydt_language"] = (
                cfg["ydt_language"].value
                if hasattr(cfg["ydt_language"], "value")
                else cfg["ydt_language"]
            )
    # Convert datetimes to ISO strings
    for key in ("started_at", "completed_at", "last_auto_save"):
        if d.get(key) and isinstance(d[key], datetime):
            d[key] = d[key].isoformat()
    # Performance metrics — nested dataclass
    if d.get("performance_metrics"):
        # Already a dict from asdict()
        pass
    return json.dumps(d, ensure_ascii=False)


def _deserialize_session(json_str: str) -> "ExamSessionData":
    """Deserialize JSON string to ExamSessionData."""
    from core.osym_exam_engine import (
        AYTFieldType,
        ExamPerformanceMetrics,
        ExamSessionData,
        ExamStatus,
        OSYMExamConfig,
        YDTLanguage,
    )
    from models.database import ExamType

    d = json.loads(json_str)

    # Restore enums
    d["status"] = ExamStatus(d["status"])

    # Restore exam_config
    cfg = d.get("exam_config", {})
    cfg["exam_type"] = ExamType(cfg["exam_type"])
    if cfg.get("ayt_field_type"):
        cfg["ayt_field_type"] = AYTFieldType(cfg["ayt_field_type"])
    if cfg.get("ydt_language"):
        cfg["ydt_language"] = YDTLanguage(cfg["ydt_language"])
    d["exam_config"] = OSYMExamConfig(**cfg)

    # Restore datetimes
    for key in ("started_at", "completed_at", "last_auto_save"):
        if d.get(key) and isinstance(d[key], str):
            d[key] = datetime.fromisoformat(d[key])

    # Restore performance_metrics
    if d.get("performance_metrics"):
        d["performance_metrics"] = ExamPerformanceMetrics(**d["performance_metrics"])

    return ExamSessionData(**d)


async def _get_redis():
    """Get Redis connection. Returns None if unavailable."""
    try:
        import redis.asyncio as aioredis

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = aioredis.from_url(url, decode_responses=True)
        await r.ping()
        return r
    except Exception:
        return None


async def persist_session(session_data: "ExamSessionData") -> None:
    """Write session to Redis (L2). Fails silently."""
    try:
        r = await _get_redis()
        if r:
            key = f"{_REDIS_PREFIX}{session_data.session_id}"
            await r.set(key, _serialize_session(session_data), ex=_REDIS_TTL)
            await r.aclose()
    except Exception as e:
        logger.warning(f"Redis persist failed for {session_data.session_id}: {e}")


async def load_session(session_id: str) -> "ExamSessionData | None":
    """Load session from Redis (L2). Returns None if not found or error."""
    try:
        r = await _get_redis()
        if r:
            key = f"{_REDIS_PREFIX}{session_id}"
            data = await r.get(key)
            await r.aclose()
            if data:
                return _deserialize_session(data)
    except Exception as e:
        logger.warning(f"Redis load failed for {session_id}: {e}")
    return None


async def delete_session(session_id: str) -> None:
    """Delete session from Redis (L2). Fails silently."""
    try:
        r = await _get_redis()
        if r:
            key = f"{_REDIS_PREFIX}{session_id}"
            await r.delete(key)
            await r.aclose()
    except Exception as e:
        logger.warning(f"Redis delete failed for {session_id}: {e}")


async def get_student_sessions(student_id: str) -> list["ExamSessionData"]:
    """Get all sessions for a student from Redis. Returns empty list on error."""
    try:
        r = await _get_redis()
        if r:
            keys = []
            async for key in r.scan_iter(match=f"{_REDIS_PREFIX}*"):
                keys.append(key)
            sessions = []
            for key in keys:
                data = await r.get(key)
                if data:
                    session = _deserialize_session(data)
                    if session.student_id == student_id:
                        sessions.append(session)
            await r.aclose()
            return sessions
    except Exception as e:
        logger.warning(f"Redis student sessions failed for {student_id}: {e}")
    return []
