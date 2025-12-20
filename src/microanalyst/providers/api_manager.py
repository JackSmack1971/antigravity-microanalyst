import hashlib
import time
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class IntelligentAPIManager:
    """
    Maximizes Free Tier API value through aggressive caching and change detection.
    """
    
    def __init__(self):
        self._cache = {} # In-memory cache for demo, normally would be Redis/SQLite
        self._rate_limit_usage = {}
        
    def _generate_key(self, endpoint: str, params: Dict) -> str:
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{endpoint}:{param_str}".encode()).hexdigest()

    def fetch_smart(self, 
                    fetch_func, 
                    endpoint: str, 
                    params: Dict, 
                    ttl: int = 300, 
                    priority: int = 1) -> Dict[str, Any]:
        """
        Args:
            fetch_func: Function that actually makes the API call.
            priority: 1 (High) - Always refresh if TTL expired.
                      4 (Low) - Hold cache as long as possible.
        """
        key = self._generate_key(endpoint, params)
        now = time.time()
        
        # 1. Check Cache
        if key in self._cache:
            data, timestamp, content_hash = self._cache[key]
            age = now - timestamp
            
            if age < ttl:
                return {"data": data, "source": "cache", "age": int(age)}
            
            # Low priority: Return stale cache if we've refreshed recently enough
            if priority >= 3 and age < (ttl * 3):
                return {"data": data, "source": "stale_priority_cache", "age": int(age)}

        # 2. Execute Fetch
        try:
            logger.info(f"API Fresh Fetch: {endpoint}")
            fresh_data = fetch_func(**params)
            
            # 3. Change Detection (Save logic cycles)
            new_hash = hashlib.md5(str(fresh_data).encode()).hexdigest()
            
            if key in self._cache:
                _, _, old_hash = self._cache[key]
                if new_hash == old_hash:
                    # Data hasn't changed! Extend TTL without returning as 'Fresh'
                    self._cache[key] = (fresh_data, now, new_hash)
                    return {"data": fresh_data, "source": "cache_ext_unchanged", "age": 0}

            # 4. Update Cache
            self._cache[key] = (fresh_data, now, new_hash)
            return {"data": fresh_data, "source": "api_fresh", "age": 0}
            
        except Exception as e:
            logger.error(f"API Fetch failed: {e}")
            if key in self._cache:
                return {"data": self._cache[key][0], "source": "error_fallback", "error": str(e)}
            raise e
