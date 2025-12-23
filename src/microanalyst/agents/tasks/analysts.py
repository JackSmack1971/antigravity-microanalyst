# src/microanalyst/agents/tasks/analysts.py

import logging
import pandas as pd
from typing import Dict, Any

from src.microanalyst.intelligence.confluence_calculator import ConfluenceCalculator
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
            calculator = ConfluenceCalculator()
            
            # Extract flows and OI from inputs if present
            df_flows = pd.DataFrame(inputs.get('raw_flows', []))
            df_oi = pd.DataFrame(inputs.get('raw_oi', []))
            
            signals = lib.detect_all_signals(df)
            zones = calculator.calculate_confluence_zones(df, df_flows=df_flows, df_oi=df_oi)
            
            # Key levels summarized for the agent
            key_levels = {
                'support': float(df['low'].min()),
                'resistance': float(df['high'].max()),
                'confluence_zones': [
                    {
                        'price': z.price_level,
                        'strength': z.strength,
                        'score': z.confluence_score,
                        'factors': [f.factor_type.value for f in z.factors]
                    } for z in zones[:3] # Top 3 zones
                ]
            }
            return {
                'technical_signals': signals, 
                'key_levels': key_levels,
                'confluence_full': [z.__dict__ for z in zones] # Passing full zones for UI
            }
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
        from src.microanalyst.core.persistence import DatabaseManager
        db = DatabaseManager()
        
        # 1. Get Price History (Ground Truth)
        df_price = db.get_price_history(limit=60, interval="1d")
        if df_price.empty and 'raw_price_history' in inputs:
            df_price = pd.DataFrame(inputs['raw_price_history'])
            
        if df_price.empty:
            return {"regime": "UNKNOWN", "confidence": 0.0, "reasoning": "Missing price history for correlation."}

        # 2. Get Macro Series from DB
        macro_series = {}
        for asset in ['dxy', 'spy', 'gold']:
            df_macro = db.get_macro_history(asset_id=asset, limit=60)
            if not df_macro.empty:
                # Use date as index for alignment
                df_macro = df_macro.copy()
                if 'date' in df_macro.columns:
                    df_macro.set_index('date', inplace=True)
                macro_series[asset] = df_macro['price']
        
        if not macro_series:
             logger.warning("No macro data in DB. Falling back to empty analysis.")
        
        correlation_analyzer = CorrelationAnalyzer()
        macro_agent = MacroSpecialistAgent()
        
        # Use close price series, indexed by date
        df_price.set_index('date', inplace=True)
        correlations = correlation_analyzer.analyze_correlations(df_price['close'], macro_series)
        macro_signal = macro_agent.run_task({'correlations': correlations})
        return macro_signal

    except Exception as e:
        logger.error(f"Macro analysis failed: {e}")
        return {"regime": "UNKNOWN", "confidence": 0.0, "error": str(e)}
