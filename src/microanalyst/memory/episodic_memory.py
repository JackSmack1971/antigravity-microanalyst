import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

logger = logging.getLogger(__name__)

class EpisodicMemory:
    """
    Local JSON-based memory for storing agent decisions and outcomes.
    Acts as the 'Hippocampus' for the agent swarm, enabling reflection.
    """
    
    def __init__(self, storage_path: str = "memory/decisions.json"):
        self.storage_path = storage_path
        self._ensure_storage()
        
    def _ensure_storage(self):
        """Creates the memory file if it doesn't exist."""
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w') as f:
                json.dump([], f)
                
    def load_memory(self) -> List[Dict[str, Any]]:
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return []
            
    def store_decision(self, context: Dict[str, Any], decision_data: Dict[str, Any]) -> str:
        """
        Stores a decision made by the swarm.
        
        Args:
            context: The input data/regime (the 'state' of the world).
            decision_data: The output from the debate swarm (decision, reasoning, logic).
            
        Returns:
            decision_id: unique identifier
        """
        decision_id = str(uuid.uuid4())
        
        record = {
            "id": decision_id,
            "timestamp": datetime.now().isoformat(),
            "context": {
                "symbol": context.get('symbol', 'BTCUSDT'),
                "regime": context.get('ground_truth', {}).get('regime', 'unknown'),
                "price": context.get('price', {}).get('current', 0.0),
                "regime_confidence": context.get('ground_truth', {}).get('regime_confidence', 0.0)
            },
            "decision": decision_data,
            "outcome": None, # Will be filled later
            "reflection": None # Will be filled by ReflexionEngine
        }
        
        memories = self.load_memory()
        memories.append(record)
        
        with open(self.storage_path, 'w') as f:
            json.dump(memories, f, indent=2)
            
        return decision_id
        
    def update_outcome(self, decision_id: str, actual_roi: float) -> bool:
        """
        Updates a past decision with the actual market result.
        """
        memories = self.load_memory()
        updated = False
        
        for mem in memories:
            if mem['id'] == decision_id:
                mem['outcome'] = {
                    "actual_roi": actual_roi,
                    "timestamp_verified": datetime.now().isoformat()
                }
                updated = True
                break
                
        if updated:
            with open(self.storage_path, 'w') as f:
                json.dump(memories, f, indent=2)
                
        return updated
        
    def get_completed_decisions_without_reflection(self) -> List[Dict[str, Any]]:
        """Returns decisions that have known outcomes but no Critique yet."""
        memories = self.load_memory()
        return [
            m for m in memories 
            if m.get('outcome') is not None 
            and m.get('reflection') is None
        ]

    def add_reflection(self, decision_id: str, critique: str):
        """Stores the agent's self-critique."""
        memories = self.load_memory()
        updated = False
        
        for mem in memories:
            if mem['id'] == decision_id:
                mem['reflection'] = critique
                updated = True
                break
                
        if updated:
            with open(self.storage_path, 'w') as f:
                json.dump(memories, f, indent=2)
