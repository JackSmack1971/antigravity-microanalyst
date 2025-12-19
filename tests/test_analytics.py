import pytest
import pandas as pd
import numpy as np
from src.microanalyst.analytics import calculate_rsi, calculate_cumulative_flows

def test_calculate_rsi_manual():
    # Create simple uptrend
    prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    df = pd.DataFrame({"Close": prices})
    
    # Period 2 for easy calc
    res = calculate_rsi(df, period=2)
    assert "RSI" in res.columns
    # Last RSI should be high (uptrend)
    assert res.iloc[-1]["RSI"] > 50

def test_calculate_rsi_empty():
    df = pd.DataFrame()
    res = calculate_rsi(df)
    assert res.empty

def test_calculate_cumulative_flows():
    df = pd.DataFrame({
        "Date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
        "Net_Flow": [100, 200]
    })
    res = calculate_cumulative_flows(df)
    assert "Cumulative_Flow" in res.columns
    assert res.iloc[1]["Cumulative_Flow"] == 300
