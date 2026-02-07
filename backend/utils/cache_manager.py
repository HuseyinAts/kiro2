"""
Cache manager for quality check hooks.

Manages .ruff_cache, .mypy_cache for performance optimization.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    """A single cache entry."""

    file_hash: str
    result: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
    tool: str

    def is_expired(self, max_age: float = 3600.0) -> bool:
        """Check if cache entry is expired (default 1 hour)."""
        return (time.time() - self.timestamp) > max_age


class CacheManager:
    """
    Manages caching for quality check results.

    Uses file hashes to determine if cached results are valid.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_age: float = 3600.0
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files
            max_age: Maximum age of cache entries in seconds
        """
        self.cache_dir = cache_dir or Path(".quality_cache")
        self.max_age = max_age
        self._cache: Dict[str, CacheEntry] = {}
        self._ensure_cache_dir()
        self._load_cache()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if needed."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file(self) -> Path:
        """Get path to cache file."""
        return self.cache_dir / "quality_check_cache.json"

    def _load_cache(self) -> None:
        """Load cache from disk."""
        cache_file = self._get_cache_file()
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        self._cache[key] = CacheEntry(**entry_data)
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        cache_file = self._get_cache_file()
        try:
            data = {k: v.model_dump() for k, v in self._cache.items()}
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file contents."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def _get_cache_key(self, tool: str, file_path: str) -> str:
        """Generate cache key for tool + file combination."""
        return f"{tool}:{file_path}"

    def get(
        self,
        tool: str,
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result if valid.

        Args:
            tool: Tool name (ruff, mypy, etc.)
            file_path: Path to file

        Returns:
            Cached result or None if not cached/expired
        """
        key = self._get_cache_key(tool, file_path)
        entry = self._cache.get(key)

        if entry is None:
            return None

        if entry.is_expired(self.max_age):
            del self._cache[key]
            return None

        # Check if file has changed
        current_hash = self._compute_file_hash(file_path)
        if current_hash != entry.file_hash:
            del self._cache[key]
            return None

        return entry.result

    def set(
        self,
        tool: str,
        file_path: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Cache a result.

        Args:
            tool: Tool name
            file_path: Path to file
            result: Result to cache
        """
        key = self._get_cache_key(tool, file_path)
        file_hash = self._compute_file_hash(file_path)

        self._cache[key] = CacheEntry(
            file_hash=file_hash,
            result=result,
            tool=tool
        )
        self._save_cache()

    def invalidate(self, file_path: str) -> None:
        """
        Invalidate all cache entries for a file.

        Args:
            file_path: Path to file
        """
        keys_to_remove = [
            k for k in self._cache.keys()
            if k.endswith(f":{file_path}")
        ]
        for key in keys_to_remove:
            del self._cache[key]
        self._save_cache()

    def invalidate_tool(self, tool: str) -> None:
        """
        Invalidate all cache entries for a tool.

        Args:
            tool: Tool name
        """
        keys_to_remove = [
            k for k in self._cache.keys()
            if k.startswith(f"{tool}:")
        ]
        for key in keys_to_remove:
            del self._cache[key]
        self._save_cache()

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache = {}
        self._save_cache()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        expired = sum(
            1 for e in self._cache.values()
            if e.is_expired(self.max_age)
        )
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired,
            "valid_entries": len(self._cache) - expired,
            "cache_dir": str(self.cache_dir),
            "max_age_seconds": self.max_age
        }


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    cache_dir: Optional[Path] = None
) -> CacheManager:
    """
    Get or create cache manager singleton.

    Args:
        cache_dir: Cache directory (only used on first call)

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir)
    return _cache_manager
