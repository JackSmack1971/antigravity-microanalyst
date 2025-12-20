import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.getcwd())

from src.microanalyst.intelligence.risk_manager import AdvancedRiskManager

@pytest.fixture
def risk_manager():
    return AdvancedRiskManager()

@pytest.fixture
def sample_price_data():
    # Create 100 days of data with known volatility
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100)
    # Generate returns: Mean 0, Std 2%
    returns = np.random.normal(0, 0.02, 100)
    price = 100 * (1 + returns).cumprod()
    
    df = pd.DataFrame({
        'close': price,
        'high': price * 1.01,
        'low': price * 0.99
    }, index=dates)
    return df

def test_calculate_var(risk_manager, sample_price_data):
    # 95% Confidence VaR
    # Since returns are normal(0, 0.02), 5th percentile should be approx -1.645 * 0.02 = -0.0329 (-3.29%)
    
    result = risk_manager.calculate_value_at_risk(
        sample_price_data, 
        portfolio_value=10000.0, 
        confidence=0.95
    )
    
    print(f"\nVaR Result: {result}")
    
    assert result['var_amount'] > 0
    assert 2.0 < result['var_pct'] < 5.0 # Expecting around 3.3% driven by random seed
    assert result['confidence_level'] == 0.95

def test_stress_test_scenarios(risk_manager, sample_price_data):
    portfolio = 100000.0
    results = risk_manager.stress_test_scenarios(portfolio, sample_price_data)
    
    # Check Flash Crash Scenario
    flash_crash = next(r for r in results if r['scenario'] == "Flash Crash")
    assert flash_crash['projected_loss'] == 30000.0 # 30% of 100k
    assert flash_crash['remaining_equity'] == 70000.0
    assert flash_crash['impact_severity'] == 'Critical'

def test_position_sizing_kelly_logic(risk_manager):
    account = 10000.0
    
    # CASE 1: High Confidence, Low Volatility -> High Size
    # Vol 20% (matches target), Conf 0.8 -> Scalar 1.0 * (0.3*2)=0.6 -> 60% alloc?
    # Max size clamp: 2% risk / 5% stop = 40% position limit.
    # So should return 4000 (40%)
    
    res1 = risk_manager.optimal_position_sizing(
        signal_confidence=0.8,
        volatility_annualized=0.20,
        account_size=account
    )
    
    assert res1['size_usd'] == 4000.0
    assert res1['pct_of_equity'] == 40.0
    
    # CASE 2: Low Confidence -> Zero Size
    res2 = risk_manager.optimal_position_sizing(
        signal_confidence=0.4,
        volatility_annualized=0.20, 
        account_size=account
    )
    
    assert res2['size_usd'] == 0.0
    
    # CASE 3: High Volatility -> Reduced Size
    # Vol 80%, Conf 0.8
    # Vol Scalar = 0.2/0.8 = 0.25
    # Conf Scalar = 0.6
    # Raw = 0.25 * 0.6 = 0.15 (15%)
    # Limit is 40%.
    # So 15% wins (1500)
    
    res3 = risk_manager.optimal_position_sizing(
        signal_confidence=0.8,
        volatility_annualized=0.80,
        account_size=account
    )
    
    assert res3['size_usd'] == 1500.0
