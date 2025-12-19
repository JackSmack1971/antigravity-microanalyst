import pytest
import pandas as pd
import numpy as np
import time
from src.microanalyst.intelligence.regime_detector import MarketRegimeDetector
from src.microanalyst.intelligence.derived_metrics import DerivedMetricsEngine
from src.microanalyst.providers.api_manager import IntelligentAPIManager

@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # Massive uptrend: 50k to 150k (3x)
    prices = np.linspace(50000, 150000, 100) 
    return pd.DataFrame({
        'open': prices, 'high': prices*1.01, 'low': prices*0.99, 'close': prices, 'volume': 1000
    }, index=dates)

    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = np.ones(100) * 50000
    # Low vol history (strict baseline)
    highs = prices * 1.01
    lows = prices * 0.99
    
    # Last 10 days spike volatility massively
    highs[-10:] = prices[-10:] * 1.3
    lows[-10:] = prices[-10:] * 0.7
    
    df = pd.DataFrame({
        'open': prices, 'high': highs, 'low': lows, 'close': prices, 'volume': 1000
    }, index=dates)
    return df

def test_regime_classification_bull(sample_ohlcv):
    detector = MarketRegimeDetector()
    result = detector.classify(sample_ohlcv)
    assert result['regime'] == "bull_trending"
    assert result['confidence'] >= 0.7

def test_regime_classification_high_vol(high_vol_ohlcv):
    detector = MarketRegimeDetector()
    result = detector.classify(high_vol_ohlcv)
    assert result['regime'] == "high_volatility"

def test_derived_funding_proxy():
    engine = DerivedMetricsEngine()
    # Mark > Spot (Bullish Funding)
    rate = engine.derive_funding_rate_proxy(50000, 50100)
    assert rate > 0
    assert rate > 5 # Significant annualized rate

def test_derived_whale_score():
    engine = DerivedMetricsEngine()
    # Increasing whale addresses
    history = [1000, 1005, 1010, 1015, 1020, 1025, 1030]
    result = engine.derive_whale_accumulation_score(history)
    assert result['status'] == "bullish"
    assert result['score'] > 0

def test_api_manager_caching():
    manager = IntelligentAPIManager()
    
    call_count = 0
    def mock_fetch(symbol):
        nonlocal call_count
        call_count += 1
        return {"price": 50000, "symbol": symbol}

    # First Call
    res1 = manager.fetch_smart(mock_fetch, "/price", {"symbol": "BTC"}, ttl=10)
    assert res1['source'] == "api_fresh"
    assert call_count == 1
    
    # Second Call (Cached)
    res2 = manager.fetch_smart(mock_fetch, "/price", {"symbol": "BTC"}, ttl=10)
    assert res2['source'] == "cache"
    assert call_count == 1

def test_api_manager_change_detection():
    manager = IntelligentAPIManager()
    
    data = {"status": "ok"}
    def mock_fetch():
        return data

    # First Call
    manager.fetch_smart(mock_fetch, "/status", {}, ttl=0) # Expired
    
    # Second Call (Same Data)
    res = manager.fetch_smart(mock_fetch, "/status", {}, ttl=0)
    assert res['source'] == "cache_ext_unchanged"
