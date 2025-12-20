from typing import Dict, Any, List

class RiskAnalyzer:
    """
    Assesses market risks based on volatility, drawdown, and correlation.
    """
    
    def assess_risks(
        self,
        df_price,
        df_flows,
        regime: Dict[str, Any],
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        risks = {
            'risk_level': 'medium',
            'overall_risk_score': 0.5,
            'primary_risks': []
        }
        
        current_price = df_price['close'].iloc[-1]
        
        # 1. Volatility Risk
        volatility = df_price['close'].pct_change().std() * (365**0.5) * 100
        if volatility > 80:
            risks['primary_risks'].append({
                'type': 'Extreme Volatility',
                'severity': 'high',
                'description': f'Annualized volatility is excessive ({volatility:.1f}%)'
            })
            risks['overall_risk_score'] += 0.2
            
        # 2. Drawdown Risk (simplified: distance from 30d high)
        high_30d = df_price['high'].tail(30).max()
        drawdown = (current_price - high_30d) / high_30d
        if drawdown < -0.2:
            risks['primary_risks'].append({
                'type': 'Significant Drawdown',
                'severity': 'medium',
                'description': f'Price is {drawdown*100:.1f}% below 30-day high'
            })
            
        # 3. Regime Risk
        if regime['current_regime'] == 'volatile':
            risks['primary_risks'].append({
                'type': 'Regime Uncertainty',
                'severity': 'medium',
                'description': 'Market is in a high-volatility, undefined regime'
            })
            risks['overall_risk_score'] += 0.1
            
        # normalize score max 1.0
        risks['overall_risk_score'] = min(risk_score for risk_score in [risks['overall_risk_score']] if True)
        risks['overall_risk_score'] = min(risks['overall_risk_score'], 1.0)
        
        if risks['overall_risk_score'] > 0.7:
            risks['risk_level'] = 'high'
        elif risks['overall_risk_score'] < 0.3:
            risks['risk_level'] = 'low'
            
        return risks
