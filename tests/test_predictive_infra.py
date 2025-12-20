import pytest
import pandas as pd
import numpy as np
from src.microanalyst.intelligence.transition_predictor import RegimeTransitionPredictor
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer

def test_regime_transition_logic():
    predictor = RegimeTransitionPredictor()
    
    # 1. Test Bull Trending prediction
    res = predictor.predict_next_regime("bull_trending")
    # Bull usually goes to Distribution (0.20) or stays Bull (0.60)
    # The 'most_likely_next' excludes itself, so Distribution (0.20) or HighVol (0.15)
    
    assert res['current_regime'] == "bull_trending"
    assert res['most_likely_next'] == "distribution"
    assert res['transition_probability'] > 0.0

def test_regime_fallback():
    predictor = RegimeTransitionPredictor()
    res = predictor.predict_next_regime("unknown_regime")
    assert res['prediction'] == "sideways_compression"
    assert res['confidence'] == 0.0

def test_correlation_analysis():
    analyzer = CorrelationAnalyzer()
    
    # Mock Price Series
    dates = pd.date_range("2024-01-01", periods=100)
    prices = pd.Series(np.linspace(100, 200, 100), index=dates) # Linear up trend
    
    res = analyzer.analyze_correlations(prices)
    
    assert "metric" in res
    assert res['value'] != 0.0
    # Since we mock DXY as Inverse + Noise, correlation should be negative
    assert res['value'] < 0.5 
    assert "status" in res

def test_empty_price_correlation():
    analyzer = CorrelationAnalyzer()
    res = analyzer.analyze_correlations(pd.Series())
    assert "error" in res
