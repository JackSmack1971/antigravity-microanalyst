# src/microanalyst/core/adaptive_cache.py
import json
import logging
import time
from datetime import timedelta, datetime
from typing import Any, Callable, Optional, Dict
import threading

logger = logging.getLogger(__name__)

# Try importing redis, if not available use fallback immediately
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis library not found. Using in-memory fallback.")

class SimpleMemoryCache:
    """
    Thread-safe in-memory fallback cache.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def get(self, key):
        with self._lock:
            item = self._cache.get(key)
            if not item:
                return None
            
            # Check expiry
            if datetime.now() > item['expiry']:
                del self._cache[key]
                return None
            return item['value']
    
    def setex(self, key, ttl_seconds, value):
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expiry': datetime.now() + timedelta(seconds=ttl_seconds)
            }
            
    def delete(self, *keys):
        with self._lock:
            for k in keys:
                # Handle glob-like patterns only basically (prefix) or direct match
                # For simplicity in fallback, exact match or simple manual iteration
                # Realistically, this fallback is for simple key-value use.
                if k.endswith('*'):
                    prefix = k[:-1]
                    to_del = [x for x in self._cache if x.startswith(prefix)]
                    for d in to_del:
                        del self._cache[d]
                elif k in self._cache:
                    del self._cache[k]

class AdaptiveCacheManager:
    """
    Cache duration based on metric volatility.
    Prioritizes Redis, falls back to Memory.
    """
    
    def __init__(self, redis_url='redis://localhost:6379'):
        self.use_redis = False
        self.redis_client = None
        self.memory_cache = None
        
        if REDIS_AVAILABLE:
            try:
                # Test connection
                r = redis.from_url(redis_url, socket_connect_timeout=1)
                r.ping()
                self.redis_client = r
                self.use_redis = True
                logger.info("Connected to Redis Cache.")
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}). using in-memory fallback.")
                self.memory_cache = SimpleMemoryCache()
        else:
            self.memory_cache = SimpleMemoryCache()
            
        # Define cache durations by metric type
        self.cache_policies = {
            'static': 86400,      # 24h (Supply, Metadata)
            'slow': 43200,        # 12h (Funding Rates - updating every 8h)
            'moderate': 3600,     # 1h (On-chain, detailed analysis)
            'fast': 300,          # 5m (Price History, OI, simple stats)
            'realtime': 10        # 10s (Order book snapshots)
        }
    
    def get_or_fetch(self, key: str, fetch_func: Callable, policy: str = 'moderate') -> Any:
        """
        Cache wrapper.
        Args:
            key: Cache key
            fetch_func: Function to call if cache miss
            policy: 'static', 'slow', 'moderate', 'fast', 'realtime'
        """
        cached_data = self._get(key)
        
        if cached_data is not None:
            # Check if it looks like a valid cached object
            return cached_data

        # Cache Miss
        logger.debug(f"Cache miss for {key}, fetching...")
        try:
            data = fetch_func()
            if data:
                ttl = self.cache_policies.get(policy, 300)
                self._set(key, data, ttl)
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {key}: {e}")
            raise e
            
    def _get(self, key):
        try:
            val = None
            if self.use_redis:
                val = self.redis_client.get(key)
            else:
                val = self.memory_cache.get(key)
                
            if val:
                # Redis returns bytes/str, memory returns object
                if isinstance(val, (bytes, str)):
                    return json.loads(val)
                return val
        except Exception:
            return None
        return None

    def _set(self, key, value, ttl):
        try:
            # Serialize for Redis (or memory consistency)
            val_str = json.dumps(value)
            
            if self.use_redis:
                self.redis_client.setex(key, ttl, val_str)
            else:
                # Memory cache can store object or str. Storing valid json-compatible helps consistency
                # but storing raw dict is faster.
                # Let's verify standard behavior: Redis setex takes seconds
                self.memory_cache.setex(key, ttl, value) # Storing native object in memory is fine
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    def invalidate_on_event(self, event_type):
        """
        Invalidate cache when major events occur
        """
        keys_to_delete = []
        if event_type == 'funding_update':
            keys_to_delete = ['funding:*']
        elif event_type == 'volatility_spike':
            keys_to_delete = ['orderbook:*', 'price:*', 'oi:*']
            
        if keys_to_delete:
            logger.info(f"Invalidating cache for event: {event_type}")
            if self.use_redis:
                for k in keys_to_delete:
                    # Scan keys
                    for key in self.redis_client.scan_iter(k):
                        self.redis_client.delete(key)
            else:
                self.memory_cache.delete(*keys_to_delete)
