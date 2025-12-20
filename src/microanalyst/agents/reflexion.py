import logging
from typing import List, Dict, Any
from src.microanalyst.memory.episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)

class ReflexionEngine:
    """
    Self-improvement loop.
    1. DailyReflector: Critiques individual decisions where outcome != prediction.
    2. MetaReflector: Identifies systemic patterns.
    """
    
    def __init__(self, memory: EpisodicMemory):
        self.memory = memory
        
    def run_daily_reflection(self):
        """Scans memory for completed trades and generates critiques."""
        candidates = self.memory.get_completed_decisions_without_reflection()
        critiques = []
        
        for decision in candidates:
            critique = self._generate_critique(decision)
            self.memory.add_reflection(decision['id'], critique)
            critiques.append(critique)
            
        return critiques
        
    def _generate_critique(self, record: Dict[str, Any]) -> str:
        """
        Simulates LLM self-critique. 
        In production, this would use PromptEngine + LLM.
        For Tier 2, we use deterministic logic to prove the loop.
        """
        
        signal = record['decision'].get('decision', 'HOLD')
        roi = record['outcome'].get('actual_roi', 0.0)
        regime = record['context'].get('regime', 'unknown')
        
        # logic: Did we lose money?
        wrong_direction = (signal == "BUY" and roi < -0.01) or (signal == "SELL" and roi > 0.01)
        
        if wrong_direction:
            critique = f"[CRITICAL FAILURE] Algorithm bought in {regime} but price dropped {roi:.2%}. "
            critique += "Hypothesis: MarketRegimeDetector failed to identify distribution phase. "
            critique += "Action: Tighten ADX threshold for trend confirmation."
        elif abs(roi) < 0.005 and signal != "HOLD":
            critique = "[NOISE] Trade was flat. Inefficient capital usage. "
            critique += "Consider raising volatility threshold."
        else:
            critique = "[SUCCESS] Signal validated by market structure."
            
        return critique
