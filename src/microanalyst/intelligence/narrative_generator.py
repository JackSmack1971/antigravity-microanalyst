from typing import Dict, Any

class NarrativeGenerator:
    """
    Generates natural language narratives from structured intelligence data.
    """
    
    def generate_executive_summary(self, context) -> str:
        regime = context.regime['current_regime'].upper()
        confidence = context.confidence_score * 100
        
        narrative = f"The market is currently in a **{regime}** regime with {confidence:.0f}% confidence. "
        
        if context.sentiment_indicators.get('composite_label'):
             narrative += f"Sentiment is **{context.sentiment_indicators['composite_label'].replace('_', ' ')}**. "
             
        if context.risks.get('risk_level') == 'high':
            narrative += "Caution is advised due to elevated risk levels. "
            
        return narrative
        
    def generate_regime_narrative(self, context) -> str:
        regime = context.regime['current_regime']
        duration = context.regime.get('regime_duration_days', 0)
        
        return f"Market has been in {regime} state for approx. {duration} days. Characteristics suggest structure is {context.regime.get('regime_characteristics', ['undefined'])[0].lower()}."

    def generate_signal_narrative(self, context) -> str:
        count = len(context.signals)
        if count == 0:
            return "No significant technical signals detected at this time."
        
        top_signal = context.signals[0]
        return f"Detected {count} active signals. Primary signal is **{top_signal['signal_type']}** ({top_signal['direction']}) with {top_signal['confidence']*100:.0f}% confidence."

    def generate_risk_narrative(self, context) -> str:
        score = context.risks.get('overall_risk_score', 0) * 100
        level = context.risks.get('risk_level', 'unknown')
        return f"Risk environment is rated **{level.upper()}** (Score: {score:.0f}/100). Primary concerns include: {', '.join([r['type'] for r in context.risks.get('primary_risks', [])[:2]])}."
