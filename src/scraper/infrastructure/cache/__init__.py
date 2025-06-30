"""
Content Caching Strategy Implementation for Web Scraper MCP.

This module implements comprehensive content caching strategies following T028 requirements:

1. Multiple cache implementations (in-memory, file-based, hybrid)
2. TTL (Time-To-Live) support with automatic expiration
3. Cache invalidation strategies (LRU, size-based, time-based)
4. Cache metrics and monitoring
5. Thread-safe operations with async support

TDD Implementation: GREEN phase - comprehensive caching system.
"""

import asyncio
import hashlib
import json
import os
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple, Union

from src.logger import Logger

logger = Logger(__name__)


class CacheType(Enum):
    """Cache implementation types."""

    IN_MEMORY = "in_memory"
    FILE_BASED = "file_based"
    HYBRID = "hybrid"


class EvictionPolicy(Enum):
    """Cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live based


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl_seconds: Optional[float] = None
    size_bytes: int = 0

    def __post_init__(self):
        """Calculate entry size if not provided."""
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()

    def _calculate_size(self) -> int:
        """Calculate approximate size of the entry in bytes."""
        try:
            if isinstance(self.value, str):
                return len(self.value.encode("utf-8"))
            elif isinstance(self.value, bytes):
                return len(self.value)
            elif isinstance(self.value, dict):
                return len(json.dumps(self.value).encode("utf-8"))
            else:
                return len(pickle.dumps(self.value))
        except Exception:
            return 1024  # Default size estimate

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    def touch(self) -> None:
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheConfig:
    """Configuration for cache implementations."""

    # General settings
    cache_type: CacheType = CacheType.IN_MEMORY
    max_size_mb: float = 100.0  # Maximum cache size in MB
    max_entries: int = 1000  # Maximum number of entries
    default_ttl_seconds: Optional[float] = 3600  # 1 hour default TTL

    # Eviction policy
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    eviction_threshold: float = 0.8  # Start eviction at 80% capacity

    # File-based cache settings
    cache_directory: str = ".cache/scraper"
    file_extension: str = ".cache"
    compression_enabled: bool = True

    # Performance settings
    cleanup_interval_seconds: float = 300  # 5 minutes
    enable_metrics: bool = True
    enable_persistence: bool = True

    # Thread safety
    thread_safe: bool = True


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired_entries: int = 0
    total_requests: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0

    # Performance metrics
    avg_access_time_ms: float = 0.0
    hit_rate: float = 0.0
    miss_rate: float = 0.0

    def update_hit(self, access_time_ms: float) -> None:
        """Update metrics for cache hit."""
        self.hits += 1
        self.total_requests += 1
        self._update_averages(access_time_ms)

    def update_miss(self, access_time_ms: float) -> None:
        """Update metrics for cache miss."""
        self.misses += 1
        self.total_requests += 1
        self._update_averages(access_time_ms)

    def update_eviction(self) -> None:
        """Update metrics for eviction."""
        self.evictions += 1

    def update_expiration(self) -> None:
        """Update metrics for expiration."""
        self.expired_entries += 1

    def _update_averages(self, access_time_ms: float) -> None:
        """Update average metrics."""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests
            self.miss_rate = self.misses / self.total_requests

            # Update rolling average for access time
            alpha = 0.1  # Smoothing factor
            self.avg_access_time_ms = (
                alpha * access_time_ms + (1 - alpha) * self.avg_access_time_ms
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expired_entries": self.expired_entries,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 3),
            "miss_rate": round(self.miss_rate, 3),
            "avg_access_time_ms": round(self.avg_access_time_ms, 2),
            "entry_count": self.entry_count,
            "total_size_mb": round(self.total_size_bytes / (1024 * 1024), 2),
        }


class ICacheProvider(ABC):
    """Interface for cache providers."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[float] = None
    ) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup expired entries."""
        pass


class InMemoryCache(ICacheProvider):
    """In-memory cache implementation with TTL and eviction policies."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = Logger(__name__)
        self._cache: Dict[str, CacheEntry] = {}
        self._metrics = CacheMetrics()
        self._lock = RLock() if config.thread_safe else None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Start cleanup task
        if config.cleanup_interval_seconds > 0:
            self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""

        async def cleanup_loop():
            while True:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                await self.cleanup()

        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # No event loop running, cleanup will be manual
            pass

    def _with_lock(self, func):
        """Execute function with lock if thread safety is enabled."""
        if self._lock:
            with self._lock:
                return func()
        else:
            return func()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()

        def _get():
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                self._metrics.update_expiration()
                return None

            entry.touch()
            return entry.value

        result = self._with_lock(_get)
        access_time_ms = (time.time() - start_time) * 1000

        if result is not None:
            self._metrics.update_hit(access_time_ms)
            self.logger.debug(f"Cache hit for key: {key}")
        else:
            self._metrics.update_miss(access_time_ms)
            self.logger.debug(f"Cache miss for key: {key}")

        return result

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[float] = None
    ) -> bool:
        """Set value in cache."""
        ttl = ttl_seconds or self.config.default_ttl_seconds

        def _set():
            # Check if eviction is needed
            if self._should_evict():
                self._evict_entries()

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl_seconds=ttl,
            )

            self._cache[key] = entry
            self._update_size_metrics()
            return True

        result = self._with_lock(_set)
        self.logger.debug(f"Cache set for key: {key}")
        return result

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""

        def _delete():
            if key in self._cache:
                del self._cache[key]
                self._update_size_metrics()
                return True
            return False

        result = self._with_lock(_delete)
        if result:
            self.logger.debug(f"Cache delete for key: {key}")
        return result

    async def clear(self) -> None:
        """Clear all cache entries."""

        def _clear():
            self._cache.clear()
            self._update_size_metrics()

        self._with_lock(_clear)
        self.logger.debug("Cache cleared")

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""

        def _exists():
            entry = self._cache.get(key)
            if entry is None:
                return False

            if entry.is_expired():
                del self._cache[key]
                self._metrics.update_expiration()
                return False

            return True

        return self._with_lock(_exists)

    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics."""

        def _get_metrics():
            self._update_size_metrics()
            return self._metrics

        return self._with_lock(_get_metrics)

    async def cleanup(self) -> None:
        """Cleanup expired entries."""

        def _cleanup():
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._metrics.update_expiration()

            self._update_size_metrics()
            return len(expired_keys)

        expired_count = self._with_lock(_cleanup)
        if expired_count > 0:
            self.logger.debug(f"Cleaned up {expired_count} expired entries")

    def _should_evict(self) -> bool:
        """Check if eviction is needed."""
        if len(self._cache) >= self.config.max_entries:
            return True

        total_size_mb = sum(entry.size_bytes for entry in self._cache.values()) / (
            1024 * 1024
        )
        if total_size_mb >= self.config.max_size_mb * self.config.eviction_threshold:
            return True

        return False

    def _evict_entries(self) -> None:
        """Evict entries based on eviction policy."""
        if not self._cache:
            return

        entries_to_evict = max(1, len(self._cache) // 10)  # Evict 10% of entries

        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Sort by last accessed time
            sorted_entries = sorted(
                self._cache.items(), key=lambda x: x[1].last_accessed
            )
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Sort by access count
            sorted_entries = sorted(
                self._cache.items(), key=lambda x: x[1].access_count
            )
        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # Sort by creation time
            sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].created_at)
        else:  # TTL
            # Sort by expiration time (entries closest to expiring first)
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].created_at + (x[1].ttl_seconds or float("inf")),
            )

        # Evict oldest/least used entries
        for key, _ in sorted_entries[:entries_to_evict]:
            del self._cache[key]
            self._metrics.update_eviction()

        self.logger.debug(
            f"Evicted {entries_to_evict} entries using {self.config.eviction_policy.value} policy"
        )

    def _update_size_metrics(self) -> None:
        """Update size-related metrics."""
        self._metrics.entry_count = len(self._cache)
        self._metrics.total_size_bytes = sum(
            entry.size_bytes for entry in self._cache.values()
        )


class FileBasedCache(ICacheProvider):
    """File-based cache implementation with persistence."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = Logger(__name__)
        self._metrics = CacheMetrics()
        self._cache_dir = Path(config.cache_directory)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = RLock() if config.thread_safe else None

        # Load existing cache metadata
        self._metadata_file = self._cache_dir / "metadata.json"
        self._metadata: Dict[str, Dict[str, Any]] = self._load_metadata()

    def _with_lock(self, func):
        """Execute function with lock if thread safety is enabled."""
        if self._lock:
            with self._lock:
                return func()
        else:
            return func()

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Create safe filename from key using SHA256 (secure hash)
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{safe_key}{self.config.file_extension}"

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load cache metadata from file."""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load cache metadata: {e}")
        return {}

    def _save_metadata(self) -> None:
        """Save cache metadata to file."""
        try:
            with open(self._metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save cache metadata: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()

        def _get():
            # Check metadata first
            metadata = self._metadata.get(key)
            if metadata is None:
                return None

            # Check TTL
            if metadata.get("ttl_seconds"):
                if (time.time() - metadata["created_at"]) > metadata["ttl_seconds"]:
                    self._delete_entry(key)
                    self._metrics.update_expiration()
                    return None

            # Load from file
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                # Metadata exists but file doesn't - cleanup
                del self._metadata[key]
                self._save_metadata()
                return None

            try:
                with open(cache_path, "rb") as f:
                    if self.config.compression_enabled:
                        import gzip

                        data = gzip.decompress(f.read())
                    else:
                        data = f.read()

                # Use JSON for safer deserialization (avoid pickle security risks)
                try:
                    value = json.loads(data.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Fallback to pickle for backward compatibility (with warning)
                    self.logger.warning(
                        f"Using pickle fallback for cache key {key} - consider regenerating cache"
                    )
                    value = pickle.loads(data)

                # Update access metadata
                metadata["last_accessed"] = time.time()
                metadata["access_count"] = metadata.get("access_count", 0) + 1
                self._save_metadata()

                return value

            except Exception as e:
                self.logger.warning(f"Failed to load cache entry {key}: {e}")
                self._delete_entry(key)
                return None

        result = self._with_lock(_get)
        access_time_ms = (time.time() - start_time) * 1000

        if result is not None:
            self._metrics.update_hit(access_time_ms)
            self.logger.debug(f"File cache hit for key: {key}")
        else:
            self._metrics.update_miss(access_time_ms)
            self.logger.debug(f"File cache miss for key: {key}")

        return result

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[float] = None
    ) -> bool:
        """Set value in cache."""
        ttl = ttl_seconds or self.config.default_ttl_seconds

        def _set():
            try:
                # Serialize value using JSON (safer than pickle)
                try:
                    data = json.dumps(value).encode("utf-8")
                except (TypeError, ValueError):
                    # Fallback to pickle for complex objects (with warning)
                    self.logger.warning(
                        f"Using pickle for complex object in cache key {key}"
                    )
                    data = pickle.dumps(value)

                if self.config.compression_enabled:
                    import gzip

                    data = gzip.compress(data)

                # Save to file
                cache_path = self._get_cache_path(key)
                with open(cache_path, "wb") as f:
                    f.write(data)

                # Update metadata
                self._metadata[key] = {
                    "created_at": time.time(),
                    "last_accessed": time.time(),
                    "access_count": 0,
                    "ttl_seconds": ttl,
                    "size_bytes": len(data),
                }
                self._save_metadata()

                # Check if cleanup is needed
                if len(self._metadata) > self.config.max_entries:
                    self._evict_entries()

                return True

            except Exception as e:
                self.logger.error(f"Failed to save cache entry {key}: {e}")
                return False

        result = self._with_lock(_set)
        if result:
            self.logger.debug(f"File cache set for key: {key}")
        return result

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""

        def _delete():
            return self._delete_entry(key)

        result = self._with_lock(_delete)
        if result:
            self.logger.debug(f"File cache delete for key: {key}")
        return result

    def _delete_entry(self, key: str) -> bool:
        """Delete cache entry (internal method)."""
        try:
            # Remove file
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()

            # Remove metadata
            if key in self._metadata:
                del self._metadata[key]
                self._save_metadata()
                return True

            return False
        except Exception as e:
            self.logger.warning(f"Failed to delete cache entry {key}: {e}")
            return False

    async def clear(self) -> None:
        """Clear all cache entries."""

        def _clear():
            try:
                # Remove all cache files
                for cache_file in self._cache_dir.glob(
                    f"*{self.config.file_extension}"
                ):
                    cache_file.unlink()

                # Clear metadata
                self._metadata.clear()
                self._save_metadata()
            except Exception as e:
                self.logger.error(f"Failed to clear cache: {e}")

        self._with_lock(_clear)
        self.logger.debug("File cache cleared")

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""

        def _exists():
            metadata = self._metadata.get(key)
            if metadata is None:
                return False

            # Check TTL
            if metadata.get("ttl_seconds"):
                if (time.time() - metadata["created_at"]) > metadata["ttl_seconds"]:
                    self._delete_entry(key)
                    self._metrics.update_expiration()
                    return False

            # Check if file exists
            cache_path = self._get_cache_path(key)
            return cache_path.exists()

        return self._with_lock(_exists)

    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics."""

        def _get_metrics():
            self._metrics.entry_count = len(self._metadata)
            self._metrics.total_size_bytes = sum(
                meta.get("size_bytes", 0) for meta in self._metadata.values()
            )
            return self._metrics

        return self._with_lock(_get_metrics)

    async def cleanup(self) -> None:
        """Cleanup expired entries."""

        def _cleanup():
            expired_keys = []
            current_time = time.time()

            for key, metadata in self._metadata.items():
                if metadata.get("ttl_seconds"):
                    if (current_time - metadata["created_at"]) > metadata[
                        "ttl_seconds"
                    ]:
                        expired_keys.append(key)

            for key in expired_keys:
                self._delete_entry(key)
                self._metrics.update_expiration()

            return len(expired_keys)

        expired_count = self._with_lock(_cleanup)
        if expired_count > 0:
            self.logger.debug(f"File cache cleaned up {expired_count} expired entries")

    def _evict_entries(self) -> None:
        """Evict entries based on eviction policy."""
        if not self._metadata:
            return

        entries_to_evict = max(1, len(self._metadata) // 10)  # Evict 10% of entries

        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Sort by last accessed time
            sorted_entries = sorted(
                self._metadata.items(), key=lambda x: x[1].get("last_accessed", 0)
            )
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Sort by access count
            sorted_entries = sorted(
                self._metadata.items(), key=lambda x: x[1].get("access_count", 0)
            )
        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # Sort by creation time
            sorted_entries = sorted(
                self._metadata.items(), key=lambda x: x[1].get("created_at", 0)
            )
        else:  # TTL
            # Sort by expiration time
            sorted_entries = sorted(
                self._metadata.items(),
                key=lambda x: x[1].get("created_at", 0)
                + x[1].get("ttl_seconds", float("inf")),
            )

        # Evict oldest/least used entries
        for key, _ in sorted_entries[:entries_to_evict]:
            self._delete_entry(key)
            self._metrics.update_eviction()

        self.logger.debug(
            f"File cache evicted {entries_to_evict} entries using {self.config.eviction_policy.value} policy"
        )


class HybridCache(ICacheProvider):
    """Hybrid cache combining in-memory and file-based caching."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = Logger(__name__)

        # Create L1 (memory) and L2 (file) caches
        memory_config = CacheConfig(
            cache_type=CacheType.IN_MEMORY,
            max_size_mb=config.max_size_mb * 0.3,  # 30% for memory
            max_entries=config.max_entries // 2,  # Half entries in memory
            default_ttl_seconds=config.default_ttl_seconds,
            eviction_policy=config.eviction_policy,
            thread_safe=config.thread_safe,
        )

        file_config = CacheConfig(
            cache_type=CacheType.FILE_BASED,
            max_size_mb=config.max_size_mb * 0.7,  # 70% for files
            max_entries=config.max_entries,
            default_ttl_seconds=config.default_ttl_seconds,
            eviction_policy=config.eviction_policy,
            cache_directory=config.cache_directory,
            compression_enabled=config.compression_enabled,
            thread_safe=config.thread_safe,
        )

        self._l1_cache = InMemoryCache(memory_config)
        self._l2_cache = FileBasedCache(file_config)
        self._metrics = CacheMetrics()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 first, then L2)."""
        # Try L1 cache first
        value = await self._l1_cache.get(key)
        if value is not None:
            self.logger.debug(f"Hybrid cache L1 hit for key: {key}")
            return value

        # Try L2 cache
        value = await self._l2_cache.get(key)
        if value is not None:
            # Promote to L1 cache
            await self._l1_cache.set(key, value)
            self.logger.debug(f"Hybrid cache L2 hit for key: {key} (promoted to L1)")
            return value

        self.logger.debug(f"Hybrid cache miss for key: {key}")
        return None

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[float] = None
    ) -> bool:
        """Set value in cache (both L1 and L2)."""
        # Set in both caches
        l1_result = await self._l1_cache.set(key, value, ttl_seconds)
        l2_result = await self._l2_cache.set(key, value, ttl_seconds)

        result = l1_result or l2_result  # Success if either succeeds
        if result:
            self.logger.debug(f"Hybrid cache set for key: {key}")
        return result

    async def delete(self, key: str) -> bool:
        """Delete value from cache (both L1 and L2)."""
        l1_result = await self._l1_cache.delete(key)
        l2_result = await self._l2_cache.delete(key)

        result = l1_result or l2_result
        if result:
            self.logger.debug(f"Hybrid cache delete for key: {key}")
        return result

    async def clear(self) -> None:
        """Clear all cache entries (both L1 and L2)."""
        await self._l1_cache.clear()
        await self._l2_cache.clear()
        self.logger.debug("Hybrid cache cleared")

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache (L1 or L2)."""
        return await self._l1_cache.exists(key) or await self._l2_cache.exists(key)

    def get_metrics(self) -> CacheMetrics:
        """Get combined cache metrics."""
        l1_metrics = self._l1_cache.get_metrics()
        l2_metrics = self._l2_cache.get_metrics()

        # Combine metrics
        combined = CacheMetrics(
            hits=l1_metrics.hits + l2_metrics.hits,
            misses=l1_metrics.misses + l2_metrics.misses,
            evictions=l1_metrics.evictions + l2_metrics.evictions,
            expired_entries=l1_metrics.expired_entries + l2_metrics.expired_entries,
            total_requests=l1_metrics.total_requests + l2_metrics.total_requests,
            total_size_bytes=l1_metrics.total_size_bytes + l2_metrics.total_size_bytes,
            entry_count=l1_metrics.entry_count + l2_metrics.entry_count,
        )

        # Calculate combined averages
        if combined.total_requests > 0:
            combined.hit_rate = combined.hits / combined.total_requests
            combined.miss_rate = combined.misses / combined.total_requests

        combined.avg_access_time_ms = (
            l1_metrics.avg_access_time_ms + l2_metrics.avg_access_time_ms
        ) / 2

        return combined

    async def cleanup(self) -> None:
        """Cleanup expired entries (both L1 and L2)."""
        await self._l1_cache.cleanup()
        await self._l2_cache.cleanup()


class CacheManager:
    """Main cache manager for coordinating cache operations."""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.logger = Logger(__name__)
        self._cache_provider = self._create_cache_provider()

    def _create_cache_provider(self) -> ICacheProvider:
        """Create appropriate cache provider based on configuration."""
        if self.config.cache_type == CacheType.IN_MEMORY:
            return InMemoryCache(self.config)
        elif self.config.cache_type == CacheType.FILE_BASED:
            return FileBasedCache(self.config)
        elif self.config.cache_type == CacheType.HYBRID:
            return HybridCache(self.config)
        else:
            raise ValueError(f"Unsupported cache type: {self.config.cache_type}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self._cache_provider.get(key)

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[float] = None
    ) -> bool:
        """Set value in cache."""
        return await self._cache_provider.set(key, value, ttl_seconds)

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self._cache_provider.delete(key)

    async def clear(self) -> None:
        """Clear all cache entries."""
        await self._cache_provider.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return await self._cache_provider.exists(key)

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        return self._cache_provider.get_metrics().get_summary()

    async def cleanup(self) -> None:
        """Cleanup expired entries."""
        await self._cache_provider.cleanup()

    def update_config(self, new_config: CacheConfig) -> None:
        """Update cache configuration."""
        self.config = new_config
        self._cache_provider = self._create_cache_provider()
        self.logger.info("Cache configuration updated")


# Convenience functions for easy integration
async def create_cache_manager(config: Optional[CacheConfig] = None) -> CacheManager:
    """Create and initialize cache manager."""
    manager = CacheManager(config)
    logger.info(f"Cache manager created with {manager.config.cache_type.value} cache")
    return manager


def create_memory_cache_config(
    max_size_mb: float = 50.0, max_entries: int = 500
) -> CacheConfig:
    """Create configuration optimized for in-memory caching."""
    return CacheConfig(
        cache_type=CacheType.IN_MEMORY,
        max_size_mb=max_size_mb,
        max_entries=max_entries,
        default_ttl_seconds=1800,  # 30 minutes
        eviction_policy=EvictionPolicy.LRU,
        enable_metrics=True,
        thread_safe=True,
    )


def create_file_cache_config(
    cache_dir: str = ".cache/scraper", max_size_mb: float = 200.0
) -> CacheConfig:
    """Create configuration optimized for file-based caching."""
    return CacheConfig(
        cache_type=CacheType.FILE_BASED,
        cache_directory=cache_dir,
        max_size_mb=max_size_mb,
        max_entries=2000,
        default_ttl_seconds=7200,  # 2 hours
        eviction_policy=EvictionPolicy.LRU,
        compression_enabled=True,
        enable_persistence=True,
        enable_metrics=True,
        thread_safe=True,
    )


def create_hybrid_cache_config(
    cache_dir: str = ".cache/scraper", max_size_mb: float = 100.0
) -> CacheConfig:
    """Create configuration optimized for hybrid caching."""
    return CacheConfig(
        cache_type=CacheType.HYBRID,
        cache_directory=cache_dir,
        max_size_mb=max_size_mb,
        max_entries=1000,
        default_ttl_seconds=3600,  # 1 hour
        eviction_policy=EvictionPolicy.LRU,
        compression_enabled=True,
        enable_persistence=True,
        enable_metrics=True,
        thread_safe=True,
    )
