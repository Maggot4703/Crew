import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from errors import ConfigError

"""
Manages caching of data to improve performance by reducing redundant computations or data fetching.

This module provides a simple file-based caching mechanism. It can store Python objects
by serializing them using pickle and retrieve them on subsequent requests if the cache
is still valid (not expired).
"""


class Cache:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl: Dict[str, datetime] = {}
        self.default_ttl = timedelta(minutes=30)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache.

        Checks if a cached item for the given key exists and has not expired.
        If valid, it deserializes and returns the item; otherwise, returns None.

        Args:
            key (str): The unique identifier for the cache item.

        Returns:
            any: The cached object if found and valid, otherwise None.
        """
        if key in self.cache and key in self.ttl:
            if datetime.now() < self.ttl[key]:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.ttl[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """
        Store an item in the cache.

        Serializes the value using pickle and saves it to a file named after the key.
        A timestamp is stored with the item to manage its time-to-live (TTL).

        Args:
            key (str): The unique identifier for the cache item.
            value (any): The Python object to cache.
            ttl (int): Time-to-live in seconds for the cache item. Defaults to 3600 (1 hour).
        """
        self.cache[key] = value
        self.ttl[key] = datetime.now() + (ttl or self.default_ttl)
        self._save_to_disk(key)

    def invalidate(self, key: str) -> None:
        """Remove item from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl:
            del self.ttl[key]
        self._remove_from_disk(key)

    def clear(self, key: str = None) -> None:
        """
        Clear cache items.

        If a key is provided, only that specific cache item is removed.
        If no key is provided, all items in the cache directory are removed.

        Args:
            key (str, optional): The specific cache item to remove. Defaults to None.
        """
        if key:
            self.invalidate(key)
        else:
            self.cache.clear()
            self.ttl.clear()
            for file in self.cache_dir.glob("*.cache"):
                file.unlink()

    def save(self) -> None:
        """Save all cache items to disk"""
        for key in self.cache.keys():
            self._save_to_disk(key)

    def load(self) -> None:
        """Load all cache items from disk"""
        self._load_from_disk()

    def _save_to_disk(self, key: str) -> None:
        """Persist cache item to disk"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            data = {"value": self.cache[key], "ttl": self.ttl[key].isoformat()}
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Failed to save cache to disk: {e}")

    def _remove_from_disk(self, key: str) -> None:
        """Remove cache item from disk"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logging.error(f"Failed to remove cache from disk: {e}")

    def _load_from_disk(self) -> None:
        """Load cache from disk on startup"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                key = cache_file.stem
                with open(cache_file) as f:
                    data = json.load(f)
                    ttl = datetime.fromisoformat(data["ttl"])
                    if datetime.now() < ttl:
                        self.cache[key] = data["value"]
                        self.ttl[key] = ttl
                    else:
                        cache_file.unlink()
        except Exception as e:
            logging.error(f"Failed to load cache from disk: {e}")
            raise ConfigError(f"Cache initialization failed: {e}")
