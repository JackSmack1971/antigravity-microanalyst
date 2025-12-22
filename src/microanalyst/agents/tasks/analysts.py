# src/microanalyst/agents/tasks/analysts.py

import logging
import pandas as pd
from typing import Dict, Any

from src.microanalyst.signals.library import SignalLibrary
from src.microanalyst.synthetic.sentiment import FreeSentimentAggregator
from src.microanalyst.intelligence.risk_manager import AdvancedRiskManager
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer
from src.microanalyst.agents.macro_agent import MacroSpecialistAgent

logger = logging.getLogger(__name__)

async def handle_technical_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for ANALYST_TECHNICAL role."""
    if 'raw_price_history' in inputs:
        df = pd.DataFrame(inputs['raw_price_history'])
        if not df.empty:
            lib = SignalLibrary()
            signals = lib.detect_all_signals(df)
            key_levels = {
                'support': float(df['low'].min()),
                'resistance': float(df['high'].max())
            }
            return {'technical_signals': signals, 'key_levels': key_levels}
    return {'technical_signals': [], 'error': 'No price history provided'}

async def handle_sentiment_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for ANALYST_SENTIMENT role."""
    sent_data = inputs.get('sentiment', {})
    if not sent_data:
        agg = FreeSentimentAggregator()
        sent_data = agg.aggregate_sentiment()
    return {
        'sentiment_indicators': sent_data,
        'analysis': f"Market is in {sent_data.get('interpretation', 'Unknown')} state."
    }

async def handle_risk_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for ANALYST_RISK role."""
    risk_metrics = inputs.get('risk', {})
    recommended_sizing = 0.0
    if 'raw_price_history' in inputs:
        df = pd.DataFrame(inputs['raw_price_history'])
        rm = AdvancedRiskManager()
        confidence = 0.6 
        vol = df['close'].pct_change().std() * (365**0.5)
        sizing_res = rm.optimal_position_sizing(confidence, vol, 100000)
        recommended_sizing = sizing_res.get('pct_of_equity', 0.0)
        if not risk_metrics:
             risk_metrics = rm.calculate_value_at_risk(df)
    return {
        'risk_assessment': risk_metrics,
        'recommended_sizing_pct': recommended_sizing
    }

async def handle_macro_analysis(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for ANALYST_MACRO role."""
    try:
        history = inputs.get('raw_price_history', {})
        df_price = pd.DataFrame(history)
        macro_series = inputs.get('macro_series', {})
        if not macro_series and not df_price.empty:
            macro_series['dxy'] = df_price['close'] * 0.001 
        
        correlation_analyzer = CorrelationAnalyzer()
        macro_agent = MacroSpecialistAgent()
        
        correlations = correlation_analyzer.analyze_correlations(df_price['close'], macro_series)
        macro_signal = macro_agent.run_task({'correlations': correlations})
        return macro_signal
    except Exception as e:
        logger.error(f"Macro analysis failed: {e}")
        return {"regime": "UNKNOWN", "confidence": 0.0, "error": str(e)}
