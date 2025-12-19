import pytest
import pandas as pd
import numpy as np
from src.microanalyst.normalization import DataNormalizer

class TestDataNormalizer:
    
    @pytest.fixture
    def normalizer(self):
        return DataNormalizer()

    def test_normalize_price_history_valid(self, normalizer):
        # Setup clean input with consistent casing
        raw_data = {
            "Date": ["2023-01-01", "2023-01-02"],
            "Open": [100, 101],
            "High": [105, 106],
            "Low": [95, 96],
            "Close": [102, 103],
            "Volume": [1000, 1100]
        }
        df = pd.DataFrame(raw_data)
        
        norm = normalizer.normalize_price_history(df)
        
        assert "date" in norm.columns
        assert "close" in norm.columns
        assert pd.api.types.is_datetime64_any_dtype(norm["date"])
        assert len(norm) == 2
        assert norm.iloc[0]["close"] == 102

    def test_normalize_price_history_handles_missing_cols(self, normalizer):
        # Case insensitive check + missing Volume
        raw_data = {
            "date": ["2023-01-01"],
            "open": [100],
            "HIGH": [105],
            "low": [95],
            "CLOSE": [102]
        }
        df = pd.DataFrame(raw_data)
        norm = normalizer.normalize_price_history(df)
        assert "volume" not in norm.columns # Should handle missing OK
        assert "high" in norm.columns
        assert norm.iloc[0]["high"] == 105

    def test_normalize_etf_flows(self, normalizer):
        # Raw format: Date | Ticker | Field | Value
        raw_data = {
            "Date": ["2023-01-01", "2023-01-01", "2023-01-02"],
            "Ticker": ["IBIT", "IBIT", "IBIT"],
            "Field": ["Flow (USD)", "Flow (BTC)", "Flow (USD)"],
            "Value": [1000.0, 0.1, 2000.0]
        }
        df = pd.DataFrame(raw_data)
        
        norm = normalizer.normalize_etf_flows(df)
        
        assert "flow_usd" in norm.columns
        assert "flow_btc" in norm.columns
        assert len(norm) == 2 # 2 days
        assert norm.iloc[0]["flow_usd"] == 1000.0

    def test_validate_schema_etf(self, normalizer):
        valid_df = pd.DataFrame({
            "date": [pd.Timestamp("2023-01-01")],
            "ticker": ["IBIT"],
            "flow_usd": [100.0] 
        })
        assert normalizer.validate_schema(valid_df, "etf_flows") == True
        
        invalid_df = pd.DataFrame({"ticker": ["IBIT"]})
        assert normalizer.validate_schema(invalid_df, "etf_flows") == False

    def test_validate_schema_price(self, normalizer):
        valid_df = pd.DataFrame({
            "date": [pd.Timestamp("2023-01-01")],
            "close": [100.0]
        })
        assert normalizer.validate_schema(valid_df, "btc_price") == True

    def test_cross_validate(self, normalizer):
        flows = pd.DataFrame({"date": [pd.Timestamp("2023-01-01")]})
        price = pd.DataFrame({"date": [pd.Timestamp("2023-01-01")]})
        assert normalizer.cross_validate(flows, price) == True
        
        price_bad = pd.DataFrame({"date": [pd.Timestamp("2024-01-01")]})
        assert normalizer.cross_validate(flows, price_bad) == False
