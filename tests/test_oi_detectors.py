import pytest
import pandas as pd
import numpy as np
from microanalyst.intelligence.factors.liquidity import OpenInterestDetector
from microanalyst.intelligence.schemas import FactorType, ConfluenceType

@pytest.fixture
def mock_oi_data():
    """Generates mock OI data with clear clusters."""
    # Prices from 80k to 90k
    prices = np.linspace(80000, 90000, 100)
    
    # OI clusters at 82k and 88k
    oi_values = np.ones_like(prices) * 1000
    oi_values[20] = 50000 # Cluster at ~82k
    oi_values[80] = 75000 # Cluster at ~88k
    
    df_oi = pd.DataFrame({
        'price': prices,
        'open_interest': oi_values
    })
    
    df_price = pd.DataFrame({
        'close': [85000] # Current price at 85k
    })
    
    return df_price, df_oi

def test_oi_cluster_detection(mock_oi_data):
    """Verify that OI peaks are identified as magnet/pivot factors."""
    df_price, df_oi = mock_oi_data
    detector = OpenInterestDetector()
    
    factors = detector.detect(df_price, df_oi=df_oi)
    
    assert len(factors) >= 2
    
    # Check for the 88k cluster
    cluster_88k = next((f for f in factors if 87500 <= f.price <= 88500), None)
    assert cluster_88k is not None
    assert cluster_88k.factor_type == FactorType.OPEN_INTEREST
    assert cluster_88k.strength > 0.7
    assert cluster_88k.direction == ConfluenceType.RESISTANCE # 88k > 85k

def test_missing_oi_columns_fails_gracefully(mock_oi_data):
    """Verify handling of malformed OI data."""
    df_price, _ = mock_oi_data
    bad_df = pd.DataFrame({'wrong_col': [1, 2, 3]})
    
    detector = OpenInterestDetector()
    factors = detector.detect(df_price, df_oi=bad_df)
    assert len(factors) == 0
