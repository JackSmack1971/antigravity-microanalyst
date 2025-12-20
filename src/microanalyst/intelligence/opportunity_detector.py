from typing import Dict, Any, List

class OpportunityDetector:
    """
    Identifies high-probability setups based on regime and signal alignment.
    """
    
    def identify_opportunities(
        self,
        df_price,
        df_flows,
        regime: Dict[str, Any],
        signals: List[Dict[str, Any]],
        risks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        
        opportunities = []
        
        # 1. Trend Following
        if regime['current_regime'] == 'bull':
            opportunities.append({
                'type': 'Trend Continuation',
                'priority': 'high',
                'timeframe': 'swing',
                'description': 'Buy dips on short-term pullbacks in confirmed bull regime',
                'confidence': 0.8
            })
            
        # 2. Mean Reversion
        elif regime['current_regime'] == 'sideways':
             opportunities.append({
                'type': 'Range Trading',
                'priority': 'medium',
                'timeframe': 'intraday',
                'description': 'Trade range boundaries (Buy Support, Sell Resistance)',
                'confidence': 0.6
            })
            
        # 3. Signal-based
        for signal in signals:
            if signal['confidence'] > 0.75:
                opportunities.append({
                    'type': f"Signal: {signal['signal_type']}",
                    'priority': 'high',
                    'timeframe': signal.get('timeframe', 'short-term'),
                    'description': f"Execute {signal['direction']} trade based on {signal['signal_type']}",
                    'confidence': signal['confidence']
                })
                
        # Filter high risk if risk is critical
        if risks.get('risk_level') == 'critical':
            opportunities = [o for o in opportunities if o.get('confidence', 0) > 0.9]
            
        return opportunities
