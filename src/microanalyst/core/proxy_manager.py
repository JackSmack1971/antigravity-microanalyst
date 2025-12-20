import os
import random
import logging
from typing import Optional, List
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Manages a list of proxies (HTTP/HTTPS) for rotation.
    Supports loading from environment variables or a fallback free list.
    """
    def __init__(self, use_free_proxies: bool = True):
        self.proxies: List[str] = []
        self.banned_proxies: set = set()
        self.use_free_proxies = use_free_proxies
        self._load_proxies()

    def _load_proxies(self):
        """Loads proxies from ENV or fallback."""
        env_proxies = os.getenv("PROXY_LIST")
        if env_proxies:
            self.proxies = [p.strip() for p in env_proxies.split(",") if p.strip()]
            logger.info(f"Loaded {len(self.proxies)} proxies from environment.")
        
        if not self.proxies and self.use_free_proxies:
            logger.info("No environment proxies found. Loading free tier fallback (unreliable).")
            # Fallback list - verified free proxies (placeholder for now)
            # In a real scenario, this would scrape SSLProxies.org or similar
            self.proxies = [
                # "http://1.2.3.4:8080", # Example
            ]
            
    def get_proxy(self) -> Optional[str]:
        """Returns a random valid proxy from the pool."""
        available = [p for p in self.proxies if p not in self.banned_proxies]
        if not available:
            if self.proxies:
                logger.warning("All proxies are currently banned/exhausted. Recycling banned list.")
                self.banned_proxies.clear()
                available = self.proxies
            else:
                return None # Direct connection
        
        return random.choice(available)

    def report_failure(self, proxy: str):
        """Report a proxy as failed/banned."""
        if proxy and proxy not in self.banned_proxies:
            logger.warning(f"Marking proxy as failed: {proxy}")
            self.banned_proxies.add(proxy)

    def report_success(self, proxy: str):
        """Report a proxy as working (optional logic for scoring)."""
        pass

# Global Singleton
proxy_manager = ProxyManager()
