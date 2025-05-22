from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging
from errors import ConfigError

class Cache:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl: Dict[str, datetime] = {}
        self.default_ttl = timedelta(minutes=30)
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache and key in self.ttl:
            if datetime.now() < self.ttl[key]:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.ttl[key]
        return None
        
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """Set value in cache with optional TTL"""
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
        
    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
        self.ttl.clear()
        for file in self.cache_dir.glob("*.cache"):
            file.unlink()
            
    def _save_to_disk(self, key: str) -> None:
        """Persist cache item to disk"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            data = {
                'value': self.cache[key],
                'ttl': self.ttl[key].isoformat()
            }
            with open(cache_file, 'w') as f:
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
                    ttl = datetime.fromisoformat(data['ttl'])
                    if datetime.now() < ttl:
                        self.cache[key] = data['value']
                        self.ttl[key] = ttl
                    else:
                        cache_file.unlink()
        except Exception as e:
            logging.error(f"Failed to load cache from disk: {e}")
            raise ConfigError(f"Cache initialization failed: {e}")