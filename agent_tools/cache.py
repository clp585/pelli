"""
Cache module for session memory and performance optimization.
Contains TTLCache class for session management and lighting calculation caching.
"""
import hashlib
import json
import os
import threading
import time
from typing import Dict, Optional, Tuple, Any
from functools import lru_cache
from datetime import datetime, timedelta
from collections import OrderedDict

from .config import logger, SESSION_TTL, SESSION_MAX_SIZE, SESSION_CLEANUP_INTERVAL


class TTLCache:
    """
    Time-To-Live cache with automatic cleanup.
    Prevents memory leaks by expiring entries after TTL.
    """
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
    
    def set(self, key: str, value: Any):
        """Set a value with TTL."""
        with self._lock:
            self._maybe_cleanup()
            self._cache[key] = {
                "value": value,
                "timestamp": time.time()
            }
            # Enforce max size (remove oldest if needed)
            if len(self._cache) > self.max_size:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
                del self._cache[oldest_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value if it exists and hasn't expired."""
        with self._lock:
            self._maybe_cleanup()
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            age = time.time() - entry["timestamp"]
            
            if age > self.ttl_seconds:
                # Expired
                del self._cache[key]
                return None
            
            return entry["value"]
    
    def _maybe_cleanup(self):
        """Periodic cleanup of expired entries."""
        now = time.time()
        if now - self._last_cleanup < SESSION_CLEANUP_INTERVAL:
            return
        
        self._last_cleanup = now
        expired_keys = [
            key for key, entry in self._cache.items()
            if now - entry["timestamp"] > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            self._maybe_cleanup()
            return len(self._cache)
    
    def clear(self):
        """Clear all entries."""
        with self._lock:
            self._cache.clear()


# Global session memory instance
SESSION_MEMORY = TTLCache(ttl_seconds=SESSION_TTL, max_size=SESSION_MAX_SIZE)


def get_session_stats() -> Dict[str, int]:
    """Get statistics about session memory."""
    return {
        "size": SESSION_MEMORY.size(),
        "max_size": SESSION_MEMORY.max_size,
        "ttl_seconds": SESSION_MEMORY.ttl_seconds
    }


# Cache storage
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "cache")
LIGHTING_CACHE_PATH = os.path.join(CACHE_DIR, "lighting_cache.json")
CACHE_TTL_HOURS = 24  # Cache expires after 24 hours


def _ensure_cache_dir():
    """Ensure cache directory exists."""
    os.makedirs(CACHE_DIR, exist_ok=True)


def _create_cache_key(params: Dict[str, any]) -> str:
    """Create a cache key from parameters."""
    # Create deterministic key from relevant parameters
    key_params = {
        "lighting_mode": params.get("lighting_mode"),
        "style_name": params.get("style_name"),
        "location": params.get("location"),
        "weather": params.get("weather"),
        "season": params.get("season"),
        "color_temp": params.get("color_temp"),
        "contrast": params.get("contrast"),
        "strength": params.get("strength"),
        "god_rays_strength": params.get("god_rays_strength", 0),
        "facade_gradient_strength": params.get("facade_gradient_strength", 0),
        "bloom_strength": params.get("bloom_strength", 0),
        "interior_lighting": params.get("interior_lighting", False),
    }
    
    # Create hash from sorted parameters
    key_str = json.dumps(key_params, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_lighting_spec(cache_key: str, spec_data: Dict[str, any]):
    """Cache lighting specification data."""
    try:
        _ensure_cache_dir()
        
        # Load existing cache
        cache = {}
        if os.path.exists(LIGHTING_CACHE_PATH):
            with open(LIGHTING_CACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        
        # Add new entry with timestamp
        cache[cache_key] = {
            "data": spec_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Clean old entries (older than TTL)
        cutoff_time = datetime.now() - timedelta(hours=CACHE_TTL_HOURS)
        cache = {
            k: v for k, v in cache.items()
            if datetime.fromisoformat(v["timestamp"]) > cutoff_time
        }
        
        # Save cache
        with open(LIGHTING_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Cached lighting spec: {cache_key[:8]}...")
    except Exception as e:
        logger.warning(f"Error caching lighting spec: {e}")


def get_cached_lighting_spec(cache_key: str) -> Optional[Dict[str, any]]:
    """Get cached lighting specification if available and not expired."""
    try:
        if not os.path.exists(LIGHTING_CACHE_PATH):
            return None
        
        with open(LIGHTING_CACHE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        if cache_key not in cache:
            return None
        
        entry = cache[cache_key]
        timestamp = datetime.fromisoformat(entry["timestamp"])
        
        # Check if expired
        if datetime.now() - timestamp > timedelta(hours=CACHE_TTL_HOURS):
            # Remove expired entry
            del cache[cache_key]
            with open(LIGHTING_CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            return None
        
        logger.debug(f"Cache hit: {cache_key[:8]}...")
        return entry["data"]
    except Exception as e:
        logger.warning(f"Error reading cached lighting spec: {e}")
        return None


@lru_cache(maxsize=100)
def cached_solar_calculation(location: str, lighting_mode: str, season: str) -> Tuple[float, float, float]:
    """
    Cached solar position calculation.
    Returns: (elevation, azimuth, color_temp)
    """
    from .solar import calculate_solar_position
    solar_pos = calculate_solar_position(location, lighting_mode, season)
    return (solar_pos.elevation, solar_pos.azimuth, solar_pos.color_temp_k)


def get_reusable_lighting_spec(
    current_params: Dict[str, any],
    previous_params: Dict[str, any]
) -> Optional[Dict[str, any]]:
    """
    Check if lighting spec can be reused when only style changes.
    
    Args:
        current_params: Current lighting parameters
        previous_params: Previous lighting parameters
        
    Returns:
        Reusable spec data if available, None otherwise
    """
    # Check if only style changed (other params same)
    comparable_params = [
        "lighting_mode", "location", "weather", "season",
        "color_temp", "contrast", "strength", "god_rays_strength",
        "facade_gradient_strength", "bloom_strength", "interior_lighting"
    ]
    
    params_match = all(
        current_params.get(p) == previous_params.get(p)
        for p in comparable_params
    )
    
    if params_match and current_params.get("style_name") != previous_params.get("style_name"):
        # Only style changed - can reuse most of the spec
        cache_key = _create_cache_key(previous_params)
        cached_spec = get_cached_lighting_spec(cache_key)
        if cached_spec:
            logger.debug("Reusing lighting spec (only style changed)")
            return cached_spec
    
    return None
