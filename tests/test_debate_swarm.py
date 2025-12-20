import pytest
from src.microanalyst.agents.debate_swarm import run_adversarial_debate, MarketSignal

@pytest.fixture
def mock_dataset():
    return {
        "ground_truth": {
            "regime": "bull_trending",
            "confidence": 0.9,
            "instructions": {"synthesizer": "Stay aggressive."}
        },
        "derived_metrics": {
            "funding_rate_annualized": 10.5,
            "whale_score": {"score": 0.8}
        },
        "price": {"current": 100000}
    }

@pytest.fixture
def high_vol_dataset():
    return {
        "ground_truth": {
            "regime": "high_volatility",
            "confidence": 0.9,
            "instructions": {"synthesizer": "De-risk."}
        },
        "derived_metrics": {},
        "price": {"current": 100000}
    }

def test_debate_swarm_bull_output(mock_dataset):
    result = run_adversarial_debate(mock_dataset)
    assert result['decision'] == "BUY"
    assert result['allocation_pct'] <= 70.0 # Hard cap
    assert "Bull Analyst" in str(result['logs'])
    assert "Risk Manager" in str(result['logs'])

def test_debate_swarm_high_vol_sizing(high_vol_dataset):
    result = run_adversarial_debate(high_vol_dataset)
    # Target allocation in code is 0.5 for non-HOLD. 
    # High vol cuts by 50% -> 0.25 (25%)
    assert result['allocation_pct'] == 25.0 
    assert "Risk Manager adjusted" in result['reasoning']

def test_debate_swarm_bear_regime():
    bear_dataset = {
        "ground_truth": {"regime": "bear_trending"},
        "market_data": {}
    }
    result = run_adversarial_debate(bear_dataset)
    assert result['decision'] == "SELL"
    assert result['allocation_pct'] == 50.0 # 0.5 * 100
