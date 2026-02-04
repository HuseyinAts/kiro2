"""
Session Authentication Caching Module
Provides session-based authentication caching for KIRO2 platform
"""

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class SessionAuthCache:
    """Session authentication cache manager"""

    def __init__(self):
        """Initialize session auth cache"""
        self._cache: dict[str, dict[str, Any]] = {}
        self._expiry_times: dict[str, datetime] = {}
        self.default_ttl = timedelta(hours=2)  # 2 hour default TTL

    def set(
        self, session_id: str, auth_data: dict[str, Any], ttl: timedelta | None = None
    ):
        """Set authentication data for session"""
        self._cache[session_id] = auth_data
        expiry = datetime.now() + (ttl or self.default_ttl)
        self._expiry_times[session_id] = expiry

        logger.debug(
            f"Cached auth data for session: {session_id[:8]}... (expires: {expiry})"
        )

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Get authentication data for session"""
        if session_id not in self._cache:
            return None

        # Check expiry
        if session_id in self._expiry_times:
            if datetime.now() > self._expiry_times[session_id]:
                self.delete(session_id)
                return None

        return self._cache.get(session_id)

    def delete(self, session_id: str):
        """Delete authentication data for session"""
        if session_id in self._cache:
            del self._cache[session_id]
        if session_id in self._expiry_times:
            del self._expiry_times[session_id]

        logger.debug(f"Deleted auth data for session: {session_id[:8]}...")

    def clear_expired(self):
        """Clear all expired sessions"""
        now = datetime.now()
        expired_sessions = [
            session_id
            for session_id, expiry_time in self._expiry_times.items()
            if now > expiry_time
        ]

        for session_id in expired_sessions:
            self.delete(session_id)

        if expired_sessions:
            logger.info(f"Cleared {len(expired_sessions)} expired auth sessions")

    def clear_all(self):
        """Clear all cached sessions"""
        self._cache.clear()
        self._expiry_times.clear()
        logger.info("Cleared all cached auth sessions")

    def get_session_count(self) -> int:
        """Get count of active sessions"""
        self.clear_expired()  # Clean up first
        return len(self._cache)

    def get_session_ids(self) -> list:
        """Get list of active session IDs"""
        self.clear_expired()  # Clean up first
        return list(self._cache.keys())


# Global session auth cache instance
_global_session_auth_cache = SessionAuthCache()


def get_session_auth_cache() -> SessionAuthCache:
    """Get the global session auth cache instance"""
    return _global_session_auth_cache


def cache_user_session(
    session_id: str, user_data: dict[str, Any], ttl: timedelta | None = None
):
    """Convenience function to cache user session data"""
    cache = get_session_auth_cache()
    cache.set(session_id, user_data, ttl)


def get_cached_user_session(session_id: str) -> dict[str, Any] | None:
    """Convenience function to get cached user session data"""
    cache = get_session_auth_cache()
    return cache.get(session_id)


def invalidate_user_session(session_id: str):
    """Convenience function to invalidate user session"""
    cache = get_session_auth_cache()
    cache.delete(session_id)


def clear_expired_sessions():
    """Convenience function to clear expired sessions"""
    cache = get_session_auth_cache()
    cache.clear_expired()
