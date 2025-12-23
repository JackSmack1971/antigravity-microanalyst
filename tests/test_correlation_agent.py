# tests/test_correlation_agent.py
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.microanalyst.agents.tasks.analysts import handle_macro_analysis
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer

@pytest.fixture
def sample_price_history():
    dates = pd.date_range(start="2025-01-01", periods=40, freq='D')
    return pd.DataFrame({
        'date': dates,
        'close': [90000 + i*100 for i in range(40)]
    })

@pytest.fixture
def sample_macro_history():
    dates = pd.date_range(start="2025-01-01", periods=40, freq='D')
    return pd.DataFrame({
        'date': dates,
        'asset_id': ['dxy'] * 40,
        'price': [104 - i*0.1 for i in range(40)] # Negative correlation trend
    })

def test_correlation_math_logic():
    """Verifies the CorrelationAnalyzer correctly identifies decoupling."""
    analyzer = CorrelationAnalyzer()
    
    # Perfect negative correlation
    btc = pd.Series([10, 11, 12, 13, 14] * 10)
    dxy = pd.Series([20, 19, 18, 17, 16] * 10)
    
    # Needs at least 30 samples for the rolling code in the analyzer
    macro_dict = {'dxy': dxy}
    results = analyzer.analyze_correlations(btc, macro_dict)
    
    assert len(results) > 0
    dxy_result = next((r for r in results if 'DXY' in r['metric']), None)
    assert dxy_result is not None
    assert dxy_result['value'] < -0.9 # Should be close to -1.0
    assert dxy_result['status'] == "tightly_coupled"

@patch('src.microanalyst.core.persistence.DatabaseManager.get_price_history')
@patch('src.microanalyst.core.persistence.DatabaseManager.get_macro_history')
async def test_macro_agent_handler_real_data(mock_macro, mock_price, sample_price_history, sample_macro_history):
    """Verifies that handle_macro_analysis pulls from the database, not simulation."""
    mock_price.return_value = sample_price_history
    mock_macro.return_value = sample_macro_history
    
    inputs = {
        'symbol': 'BTCUSDT',
        'raw_price_history': sample_price_history.to_dict()
    }
    
    # Call the handler (which is async)
    result = await handle_macro_analysis(inputs)
    
    assert 'regime' in result
    assert result['regime'] != "UNKNOWN"
    assert 'reasoning' in result
    # It should cite real correlations, not the hardcoded logic
    assert "Macro Perspective" in result['reasoning']
    
    # Verify the mock was called (proving simulation was bypassed)
    mock_macro.assert_called()
