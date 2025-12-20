import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ChainWatcher:
    """
    Monitors Bitcoin On-Chain metrics via mempool.space API.
    Provides signals on Network Congestion (FOMO/Panic) and Fees.
    """
    BASE_URL = "https://mempool.space/api"

    def fetch_mempool_stats(self) -> Dict[str, Any]:
        """
        Fetches current mempool depth and recommended fees.
        """
        stats = {
            "mempool_vbytes": 0,
            "fastest_fee_sats": 0,
            "min_fee_sats": 0,
            "congestion_level": "Low"
        }
        
        try:
            # 1. Mempool backlog
            resp_pool = requests.get(f"{self.BASE_URL}/mempool", timeout=10)
            if resp_pool.status_code == 200:
                data = resp_pool.json()
                stats["mempool_vbytes"] = data.get("vsize", 0)
                stats["count"] = data.get("count", 0)
            
            # 2. Recommended Fees
            resp_fees = requests.get(f"{self.BASE_URL}/v1/fees/recommended", timeout=10)
            if resp_fees.status_code == 200:
                data = resp_fees.json()
                stats["fastest_fee_sats"] = data.get("fastestFee", 0)
                stats["min_fee_sats"] = data.get("minimumFee", 0)
            
            # Heuristic for Congestion
            # > 100 MB backlog is High
            # > 300 MB is Extreme
            vsize_mb = stats["mempool_vbytes"] / 1_000_000
            if vsize_mb > 300:
                stats["congestion_level"] = "Extreme"
            elif vsize_mb > 100:
                stats["congestion_level"] = "High"
            elif vsize_mb > 20:
                stats["congestion_level"] = "Medium"
                
            return stats

        except Exception as e:
            logger.error(f"ChainWatcher failed: {e}")
            return stats
