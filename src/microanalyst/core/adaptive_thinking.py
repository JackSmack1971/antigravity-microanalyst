from enum import Enum
from typing import Dict, Any

class ThinkingLevel(str, Enum):
    FAST = "FAST"         # Low volatility, heuristic-based
    BALANCED = "BALANCED" # Normal conditions
    DEEP = "DEEP"         # High volatility, requires Chain-of-Thought
    CRITICAL = "CRITICAL" # Extreme crisis, requires Tree-of-Thoughts (simulated)

class AdaptiveThinkingConfig:
    """
    Manages prompt injections and reasoning depth based on ThinkingLevel.
    """
    
    @staticmethod
    def get_config(level: ThinkingLevel) -> Dict[str, Any]:
        if level == ThinkingLevel.FAST:
            return {
                "system_prompt_suffix": " Be concise. Focus on immediate price action.",
                "reasoning_steps": 1,
                "require_counterargument": False,
                "token_budget": 150
            }
        elif level == ThinkingLevel.BALANCED:
            return {
                "system_prompt_suffix": " Provide standard analysis.",
                "reasoning_steps": 2,
                "require_counterargument": False,
                "token_budget": 300
            }
        elif level == ThinkingLevel.DEEP:
            return {
                "system_prompt_suffix": " THINK STEP BY STEP. Analyze 2nd order effects.",
                "reasoning_steps": 5,
                "require_counterargument": True,
                "token_budget": 800
            }
        elif level == ThinkingLevel.CRITICAL:
            return {
                "system_prompt_suffix": " CRITICAL MODE. CHALLENGE EVERY ASSUMPTION. Use Tree-of-Thoughts.",
                "reasoning_steps": 10,
                "require_counterargument": True,
                "token_budget": 2000
            }
        return {}

    @staticmethod
    def determine_level(volatility_score: float) -> ThinkingLevel:
        """
        Maps a 0-100 volatility score to a thinking level.
        """
        if volatility_score < 30:
            return ThinkingLevel.FAST
        elif volatility_score < 60:
            return ThinkingLevel.BALANCED
        elif volatility_score < 90:
            return ThinkingLevel.DEEP
        else:
            return ThinkingLevel.CRITICAL
