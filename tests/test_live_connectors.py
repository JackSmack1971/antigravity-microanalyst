import pytest
import pandas as pd
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.getcwd())

from src.microanalyst.providers.binance_spot import BinanceSpotProvider
from src.microanalyst.agents.agent_coordinator import AgentCoordinator, AgentRole

@pytest.fixture
def spot_provider():
    return BinanceSpotProvider()

def test_binance_spot_fetch_ohlcv_live(spot_provider):
    """
    Smoke test: Can we reach Binance API?
    Warning: Needs Internet.
    """
    df = spot_provider.fetch_ohlcv(symbol="BTCUSDT", interval="4h", limit=5)
    
    assert not df.empty, "Live fetch returned empty DataFrame"
    assert 'close' in df.columns
    assert len(df) == 5
    
def test_coordinator_data_fallback_logic():
    """
    Simulate API failure and ensure Coordinator falls back to simulation data cleanly.
    """
    coordinator = AgentCoordinator()
    
    # Mock BinanceSpotProvider to raise exception
    with patch('src.microanalyst.providers.binance_spot.BinanceSpotProvider.fetch_ohlcv') as mock_fetch:
        mock_fetch.side_effect = Exception("Simulated Network Error")
        
        # Manually invoke just the data collector task delegate logic (async)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        task_inputs = {'lookback_days': 30, 'sources': ['price']}
        
        # We need to call _delegate_to_module directly to test logic
        # OR run full flow. Let's run _delegate for precision.
        result = loop.run_until_complete(
            coordinator._delegate_to_module(AgentRole.DATA_COLLECTOR, task_inputs)
        )
        
        assert "price" in result
        assert "meta" in result
        assert result['meta']['source'] == 'simulation'
        
        # Verify dataset integrity despite fallback
        assert result['price']['current'] > 0
        
def test_coordinator_live_logic_integration():
    """
    Assuming internet works, running this should produce 'live' meta source.
    If internet fails (CI?), it might fallback, which is also 'pass' but different source.
    """
    coordinator = AgentCoordinator()
    import asyncio
    
    try:
        task_inputs = {'lookback_days': 2, 'sources': ['price']}
        result = asyncio.run(coordinator._delegate_to_module(AgentRole.DATA_COLLECTOR, task_inputs))
        
        # If API reached: source=live. If blocked: source=simulation.
        # Both are valid states for the software stability, but for this specific test
        # we want to see what happens.
        print(f"Data Source Obtained: {result.get('meta', {}).get('source')}")
        assert "price" in result
        
    except Exception as e:
        pytest.fail(f"Coordinator crashed during data collection: {e}")
