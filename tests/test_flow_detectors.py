import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from microanalyst.intelligence.factors.flows import ETFFlowDetector
from microanalyst.intelligence.schemas import FactorType, ConfluenceType

@pytest.fixture
def mock_flow_data():
    """Generates mock ETF flow and price data."""
    dates = [datetime(2024, 1, i) for i in range(1, 11)]
    
    # Prices: 50k to 60k
    df_price = pd.DataFrame({
        'date': dates,
        'open': np.linspace(50000, 59000, 10),
        'high': np.linspace(51000, 60000, 10),
        'low': np.linspace(49000, 58000, 10),
        'close': np.linspace(50500, 59500, 10)
    })
    
    # Flows: One huge spike on Jan 5
    df_flows = pd.DataFrame({
        'date': dates,
        'flow_usd': [10, -5, 12, 8, 1500, 15, -10, 5, 20, 12] # Spike at index 4 (Jan 5)
    })
    
    return df_price, df_flows

def test_etf_flow_spike_detection(mock_flow_data):
    """Verify that significant flow spikes are detected and mapped to price."""
    df_price, df_flows = mock_flow_data
    detector = ETFFlowDetector()
    
    factors = detector.detect(df_price, df_flows=df_flows)
    
    # Expected spike on Jan 5: Price range [53000, 55000] approx
    # Jan 5 is index 4
    expected_price_low = df_price.iloc[4]['low']
    expected_price_high = df_price.iloc[4]['high']
    
    assert len(factors) > 0
    spike_factor = next((f for f in factors if f.metadata.get('flow_magnitude') == 1500), None)
    
    assert spike_factor is not None
    assert spike_factor.factor_type == FactorType.ETF_FLOW_PIVOT
    assert expected_price_low <= spike_factor.price <= expected_price_high
    assert spike_factor.strength > 0.8 # Should be a strong spike

def test_empty_flows_returns_nothing(mock_flow_data):
    """Verify graceful handling of empty flow data."""
    df_price, _ = mock_flow_data
    detector = ETFFlowDetector()
    
    factors = detector.detect(df_price, df_flows=pd.DataFrame())
    assert len(factors) == 0

def test_no_spikes_returns_nothing(mock_flow_data):
    """Verify that normal flows don't trigger pivots."""
    df_price, _ = mock_flow_data
    flat_flows = pd.DataFrame({
        'date': df_price['date'],
        'flow_usd': [10] * 10
    })
    
    detector = ETFFlowDetector()
    factors = detector.detect(df_price, df_flows=flat_flows)
    assert len(factors) == 0
