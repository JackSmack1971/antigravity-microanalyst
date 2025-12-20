import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.getcwd())

from src.microanalyst.intelligence.prompt_engine import PromptEngine

@pytest.fixture
def mock_bull_dataset():
    """Creates a dataset that should trigger BULL_TREND detection."""
    # Price increasing significantly
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = np.linspace(50000, 80000, 100) # Strong uptrend
    df = pd.DataFrame({
        'open': prices, 'high': prices*1.01, 'low': prices*0.99, 'close': prices, 'volume': 1000
    }, index=dates)
    
    # Needs to be dict format as per AgentDatasetBuilder
    df.index = df.index.astype(str)
    return {
        'raw_price_history': df.to_dict(),
        'price': {'current': 80000},
        'risk': {'recommended_sizing_pct': 0.8},
        'sentiment': {'composite_score': 75}
    }

@pytest.fixture
def mock_bear_dataset():
    """Creates a dataset that should trigger BEAR_TREND detection."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = np.linspace(80000, 50000, 100) # Strong downtrend
    df = pd.DataFrame({
        'open': prices, 'high': prices*1.01, 'low': prices*0.99, 'close': prices, 'volume': 1000
    }, index=dates)
    
    df.index = df.index.astype(str)
    return {
        'raw_price_history': df.to_dict(),
        'price': {'current': 50000}
    }

def test_regime_detection_bull(mock_bull_dataset):
    engine = PromptEngine()
    regime = engine.detect_regime(mock_bull_dataset)
    assert regime == "bull_trending"

def test_regime_detection_bear(mock_bear_dataset):
    engine = PromptEngine()
    regime = engine.detect_regime(mock_bear_dataset)
    assert regime == "bear_trending"

def test_prompt_construction_structure(mock_bull_dataset):
    """Verifies that the prompt contains all key technique components."""
    engine = PromptEngine()
    prompt = engine.construct_synthesizer_prompt(mock_bull_dataset)
    
    # Check for Technique 7: Regime Awareness
    assert "MARKET REGIME DETECTED: [bull_trending]" in prompt
    assert "Prioritize momentum indicators" in prompt # Bull instruction
    
    # Check for Technique 4: Constraints
    assert "CRITICAL CONSTRAINTS" in prompt
    assert "Do NOT hallucinate" in prompt
    
    # Check for Technique 1: Adversarial Debate
    assert "ANALYSIS PROTOCOL: ADVERSARIAL DEBATE" in prompt
    assert "THE BULLISH ANALYST SAYS" in prompt
    assert "THE BEARISH ANALYST SAYS" in prompt

def test_regime_specific_constraints(mock_bear_dataset):
    """Verifies that Bear regime gets Bear-specific constraints."""
    engine = PromptEngine()
    prompt = engine.construct_synthesizer_prompt(mock_bear_dataset)
    
    # Should see Bearish prompt instructions
    assert "Prioritize capital preservation" in prompt
    assert "Max position size: 2%" in prompt # Bear constraint
