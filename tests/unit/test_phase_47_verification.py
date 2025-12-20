import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.microanalyst.intelligence.feature_engineering import MLFeatureEngineer
from src.microanalyst.outputs.agent_ready import AgentDatasetBuilder
from src.microanalyst.intelligence.oracle_analyzer import OracleAnalyzer

# Mock structures for testing
MOCK_VISION = [{"price": 95000, "side": "Long", "intensity": "High"}]
MOCK_VOL = {"synthetic_iv_garch": 45.5, "realized_vol_30d": 40.0}

def test_unified_feature_engineer():
    """Verify that MLFeatureEngineer can handle vision and vol context."""
    engineer = MLFeatureEngineer()
    
    context = {
        'volatility': {'synthetic_iv_garch': 45.5},
        'vision': {'liq_distance': 0.05},
        'sentiment': {'composite_score': 0.5},
        'onchain': {'whale_score': 0.8}
    }
    
    flattened = engineer.flatten_context(context)
    
    assert flattened['iv_garch'] == 45.5
    assert flattened['vision_liq_dist'] == 0.05
    assert flattened['sent_composite'] == 0.5
    assert flattened['onchain_whale'] == 0.8

def test_unified_dataset_builder():
    """Verify that AgentDatasetBuilder correctly passes vision/vol into ML dataset."""
    builder = AgentDatasetBuilder()
    
    dates = pd.date_range(end=datetime.now(), periods=10, freq='4h')
    df_price = pd.DataFrame({
        'open': [100]*10, 'high': [105]*10, 'low': [95]*10, 'close': [102]*10, 'volume': [1000]*10
    }, index=dates)
    
    # We'll use a wrapper or mock the engineer inside if needed, 
    # but here we test the interface proposed in the plan.
    df_ml = builder.build_ml_dataset(
        df_price,
        sentiment_history={'composite_score': 0.5},
        onchain_history={'whale_score': 0.8},
        risk_history={'var_95': -0.02},
        vision_history={'liq_distance': 0.05},
        volatility_history={'synthetic_iv_garch': 45.5},
        is_inference=True
    )
    
    assert 'sent_composite' in df_ml.columns
    assert 'onchain_whale' in df_ml.columns
    assert 'iv_garch' in df_ml.columns
    assert 'vision_liq_dist' in df_ml.columns
    
    # Check broadcast (is_inference=True)
    assert df_ml['iv_garch'].iloc[0] == 45.5
    assert df_ml['vision_liq_dist'].iloc[0] == 0.05

@pytest.mark.asyncio
async def test_prediction_agent_logic():
    """Verify that a PredictionAgent correctly synthesizes Oracle output."""
    from src.microanalyst.agents.prediction_agent import PredictionAgent
    
    agent = PredictionAgent()
    
    dates = pd.date_range(end=datetime.now(), periods=100, freq='4h')
    df_price = pd.DataFrame({
        'open': np.random.randn(100) + 100,
        'high': np.random.randn(100) + 105,
        'low': np.random.randn(100) + 95,
        'close': np.random.randn(100) + 102,
        'volume': np.random.randint(100, 1000, 100)
    }, index=dates)
    
    context = {
        'df_price': df_price,
        'context_metadata': {'sentiment': {'composite_score': 0.5}}
    }
    
    prediction = agent.run_task(context)
    
    assert 'direction' in prediction
    assert 'confidence' in prediction
    assert 'price_target' in prediction
    assert prediction['horizon'] == "24h"
    assert "Oracle" in prediction['reasoning']
