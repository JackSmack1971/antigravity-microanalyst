from typing import Dict, Any, List

class ConstraintEnforcer:
    """
    Technique 4: Explicit Constraint Enforcement.
    Injects non-negotiable hard limits into agent prompts based on the market regime.
    These act as 'Guardrails' that the LLM is instructed NEVER to violate.
    """
    
    REGIME_CONSTRAINTS = {
        "bull_trending": {
            "max_allocation": 0.80,
            "stop_loss_type": "trailing",
            "forbidden_actions": ["SHORTING_INTO_MOMENTUM"]
        },
        "bear_trending": {
            "max_allocation": 0.30,
            "stop_loss_type": "fixed_tight",
            "forbidden_actions": ["CATCHING_KNIVES", "FOMO_BUYING"]
        },
        "high_volatility": {
            "max_allocation": 0.50,
            "stop_loss_type": "volatility_based",
            "forbidden_actions": ["LEVERAGE_GT_2X"]
        },
        "sideways_compression": {
            "max_allocation": 0.40,
            "stop_loss_type": "range_bound",
            "forbidden_actions": ["BREAKOUT_ANTICIPATION_WITHOUT_CONFIRMATION"]
        },
        "distribution": {
            "max_allocation": 0.20,
            "stop_loss_type": "aggressive_profit_taking",
            "forbidden_actions": ["HOLDING_THROUGH_DIPS"]
        }
    }

    def get_constraints_block(self, regime: str) -> str:
        """
        Returns a formatted text block for system prompt injection.
        """
        defaults = {
            "max_allocation": 0.50, 
            "stop_loss_type": "standard", 
            "forbidden_actions": []
        }
        
        rules = self.REGIME_CONSTRAINTS.get(regime, defaults)
        
        block = f"""
        *** CRITICAL CONSTRAINTS (NON-NEGOTIABLE) ***
        1. MAXIMUM ALLOCATION: {rules['max_allocation']:.0%} of capital.
        2. STOP LOSS STRATEGY: {rules['stop_loss_type'].replace('_', ' ').upper()}.
        3. FORBIDDEN ACTIONS: {', '.join(rules['forbidden_actions'])}.
        
        FAILURE TO ADHERE TO THESE CONSTRAINTS WILL RESULT IN CRITICAL SYSTEM ERROR.
        ***********************************************
        """
        return block
