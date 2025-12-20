import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AdaptiveConfigManager:
    """
    Manages persistence and retrieval of 'healed' selectors.
    Serves as the memory layer for the Autonomous Adaptive Selector system.
    """
    
    def __init__(self, config_path: str = "config/adaptive_selectors.json"):
        # Resolve path relative to project root if needed
        # Assuming run from root, but let's be safe
        self.config_path = Path(config_path)
        self.selectors: Dict[str, str] = {}
        self._load_config()

    def _load_config(self):
        """Load selectors from disk"""
        if not self.config_path.exists():
            self.logger.info(f"No adaptive config found at {self.config_path}, initializing empty.")
            self._save_config()
            return

        try:
            with open(self.config_path, 'r') as f:
                self.selectors = json.load(f)
            logger.debug(f"Loaded {len(self.selectors)} adaptive selectors.")
        except Exception as e:
            logger.error(f"Failed to load adaptive selectors: {e}")
            self.selectors = {}

    def _save_config(self):
        """Persist selectors to disk"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.selectors, f, indent=2, sort_keys=True)
            logger.debug("Adaptive selectors saved.")
        except Exception as e:
            logger.error(f"Failed to save adaptive selectors: {e}")

    def get_selector(self, original_source_key: str, default_selector: str) -> str:
        """
        Get the active selector. Returns the healed version if available,
        otherwise returns the default.
        
        Args:
            original_source_key: unique identifier (e.g., 'binance.price.selector')
            default_selector: the hardcoded selector
        """
        return self.selectors.get(original_source_key, default_selector)

    def update_selector(self, source_key: str, new_selector: str):
        """
        Register a new healed selector.
        """
        self.selectors[source_key] = new_selector
        self._save_config()
        logger.info(f"Persisted adaptive selector for {source_key}: {new_selector}")

    def clear_selector(self, source_key: str):
        """Remove a healed selector (e.g. if it also fails)"""
        if source_key in self.selectors:
            del self.selectors[source_key]
            self._save_config()
