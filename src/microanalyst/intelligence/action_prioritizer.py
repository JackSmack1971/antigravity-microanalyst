from typing import Dict, Any, List

class ActionPrioritizer:
    """
    Ranks potential actions for the agent/user based on context.
    """
    
    def prioritize_actions(self, context) -> List[Dict[str, Any]]:
        actions = []
        
        regime = context.regime['current_regime']
        risk_level = context.risks.get('risk_level', 'medium')
        
        # 1. Protective Actions (High Priority)
        if risk_level in ['high', 'critical']:
             actions.append({
                'action': 'Tighten Stop Losses',
                'priority': 'critical',
                'rationale': 'High risk environment detect',
                'timing': 'Immediate'
            })
             actions.append({
                'action': 'Reduce Position Size',
                'priority': 'high',
                'rationale': 'Volatility mandates smaller sizing',
                'timing': 'Next rebalance'
            })
            
        # 2. Opportunistic Actions
        if regime == 'bull':
             actions.append({
                'action': 'Accumulate Spot',
                'priority': 'high',
                'rationale': 'Trend is bullish',
                'timing': 'On 4H dips'
            })
        elif regime == 'bear':
            actions.append({
                'action': 'Preserve Capital / Hedge',
                'priority': 'high',
                'rationale': 'Trend is bearish',
                'timing': 'Immediate'
            })
            
        # 3. Monitoring
        actions.append({
            'action': f"Monitor Support at ${context.key_levels.get('nearest_support', 0):,.0f}",
            'priority': 'medium',
            'rationale': 'Key structural level',
            'timing': 'Continuous'
        })
        
        return actions
