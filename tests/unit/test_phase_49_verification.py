import pytest
import pandas as pd
import numpy as np
from src.microanalyst.agents.macro_agent import MacroSpecialistAgent

def test_macro_agent_logic():
    """Verify that MacroSpecialistAgent generates appropriate reasoning from correlation data."""
    agent = MacroSpecialistAgent()
    
    # Mock context with DXY decoupling
    context = {
        "correlations": [
            {
                "metric": "BTC_DXY_Correlation_30d",
                "value": 0.3,
                "status": "decoupling_bullish",
                "interpretation": "BTC rising with DXY (Strength)."
            }
        ]
    }
    
    result = agent.run_task(context)
    
    assert "DECOUPLING_BULLISH" in result["regime"]
    assert "DXY" in result["reasoning"]
    assert result["confidence"] > 0.5

def test_macro_agent_missing_data():
    """Ensure agent handles missing data gracefully."""
    agent = MacroSpecialistAgent()
    result = agent.run_task({})
    
    assert result["regime"] == "UNKNOWN"
    assert result["confidence"] == 0.0
