
from src.microanalyst.intelligence.regime_detector import MarketRegimeDetector
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import logging
from src.microanalyst.intelligence.constraint_enforcer import ConstraintEnforcer
from src.microanalyst.memory.episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)

class PromptEngine:
    """
    Constructs high-fidelity prompts for the Synthesizer Agent.
    Updated for Phase 54: Layered Context, Reflexion Injection, Constraint Enforcement.
    """
    
    def __init__(self, memory: EpisodicMemory = None):
        self.regime_detector = MarketRegimeDetector()
        self.constraint_enforcer = ConstraintEnforcer()
        self.memory = memory if memory else EpisodicMemory()

    def detect_regime(self, dataset: Dict[str, Any]) -> str:
        """
        Classifies market regime using the detector.
        """
        history = dataset.get('raw_price_history', {})
        if not history:
            return "sideways_compression"
            
        df = pd.DataFrame(history)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        result = self.regime_detector.classify(df)
        return result.get('regime', "sideways_compression")

    def construct_synthesizer_prompt(self, dataset: Dict[str, Any]) -> str:
        """
        Builds the master prompt for the Synthesizer using Phase 54 Cognitive Architecture.
        """
        regime_info = dataset.get('ground_truth', {})
        regime = regime_info.get('regime', 'unknown')
        
        # --- Technique 4: Constraint Enforcement ---
        constraints_block = self.constraint_enforcer.get_constraints_block(regime)
        
        # --- Technique 2: Reflexion Injection ---
        lessons_block = self._get_reflexion_context()
        
        # --- Technique 3: Layered Context ---
        immediate_context = self._build_immediate_layer(dataset)
        tactical_context = self._build_tactical_layer(dataset)
        strategic_context = self._build_strategic_layer(dataset)
        
        # Construct Prompt
        prompt = f"""
        SYSTEM ROLE:
        You are an elite Crypto Synthesizer Agent. You synthesize multi-sourced data into actionable trading decisions.
        
        {constraints_block}
        
        {lessons_block}
        
        MARKET REGIME DETECTED: {regime.upper()} (Confidence: {regime_info.get('regime_confidence', 0):.0%})
        
        --- LAYER 1: IMMEDIATE CONTEXT (24H) ---
        {immediate_context}
        
        --- LAYER 2: TACTICAL CONTEXT (7-Day) ---
        {tactical_context}
        
        --- LAYER 3: STRATEGIC CONTEXT (Macro/Thesis) ---
        {strategic_context}
        
        ADVERSARIAL DEBATE REQUIRED:
        Current Regime Analysis Instructions: {regime_info.get('instructions', {}).get('synthesizer', 'Standard analysis.')}
        
        TASK:
        Synthesize the above layers into a coherent BUY/SELL/HOLD decision.
        """
        
        return prompt

    def _get_reflexion_context(self) -> str:
        """Fetch recent critiques from memory."""
        try:
            mems = self.memory.load_memory()
            # Filter for recent critiques
            recent = [m['reflection'] for m in mems if m.get('reflection')]
            
            if not recent:
                return ""
                
            block = "*** LESSONS LEARNED (DO NOT REPEAT PAST MISTAKES) ***\n"
            for i, r in enumerate(recent[-3:]): # Last 3
                 block += f"- {r}\n"
            block += "*****************************************************"
            return block
        except Exception:
            return ""

    def _build_immediate_layer(self, data: Dict[str, Any]) -> str:
        return f"""
        Price: {data.get('price', {}).get('current')}
        Volume: {data.get('price', {}).get('volume')}
        Order Flow: {data.get('derived_metrics', {}).get('whale_score', 'N/A')}
        """
        
    def _build_tactical_layer(self, data: Dict[str, Any]) -> str:
        # 7d trends, technicals (in real app, would fetch rolling windows)
        return f"""
        Technical Core: RSI, MACD trends...
        Sentiment: {data.get('sentiment', {}).get('value', 'Neutral')}
        
        24H ORACLE PREDICTION:
        Direction: {data.get('oracle_prediction', {}).get('direction', 'NEUTRAL')}
        Confidence: {data.get('oracle_prediction', {}).get('confidence', 0):.0%}
        Expected Target: {data.get('oracle_prediction', {}).get('price_target', 'N/A')}
        """

    def _build_strategic_layer(self, data: Dict[str, Any]) -> str:
        return f"""
        Macro Predictions: {data.get('intelligence', {}).get('predictions', {})}
        Correlations: {data.get('macro', {})}
        """

