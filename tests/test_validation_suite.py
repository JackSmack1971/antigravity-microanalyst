import pytest
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.getcwd())

from src.microanalyst.validation.suite import DataValidator, SchemaValidationException, DataFreshnessException

# Setup validator
# We rely on default config/validation_rules.yml existing
validator = DataValidator(config_path="config/validation_rules.yml")

def test_schema_validation():
    print("\n--- Testing Schema Validation ---")
    
    # Valid Price Data
    valid_df = pd.DataFrame({'open':[], 'high':[], 'low':[], 'close':[], 'volume':[]})
    assert validator.validate_schema(valid_df, "price_data") == True
    print("✅ Valid schema passed")
    
    # Invalid Price Data
    invalid_df = pd.DataFrame({'price': [], 'vol': []})
    try:
        validator.validate_schema(invalid_df, "price_data")
        print("❌ Invalid schema failed to raise exception")
        assert False
    except SchemaValidationException as e:
        print(f"✅ Caught expected schema error: {e}")

def test_freshness_validation():
    print("\n--- Testing Freshness Validation ---")
    
    # Valid timestamp (Now)
    now = datetime.now()
    assert validator.validate_freshness(now, "price_data") == True
    print("✅ Fresh data passed")
    
    # Stale timestamp (24h ago, limit is 6h for price)
    stale = now - timedelta(hours=24)
    try:
        validator.validate_freshness(stale, "price_data")
        print("❌ Stale data failed to raise exception")
        assert False
    except DataFreshnessException as e:
        print(f"✅ Caught expected freshness error: {e}")

def test_outlier_detection():
    print("\n--- Testing Outlier Detection ---")
    
    # Normal distribution
    data = np.random.normal(100, 5, 100)
    series = pd.Series(data)
    
    # Inject outlier (10 sigma)
    series.iloc[50] = 500 
    
    outliers = validator.detect_outliers(series, "price_data")
    assert outliers.iloc[50] == True
    assert outliers.sum() == 1
    print(f"✅ Detected {outliers.sum()} outliers correctly")

def test_full_dataset_validation():
    print("\n--- Testing Full Dataset Report ---")
    
    # Create Mixed Bag Data
    # - Valid Schema
    # - Stale Timestamp
    # - Outlier in Close
    
    
    dates = [datetime.now() - timedelta(hours=24)] * 100
    prices = [100.0] * 100
    prices[50] = 100000.0 # Outlier (Massive spike)
    
    df = pd.DataFrame({
        'open': prices,
        'high': prices,
        'low': prices,
        'close': prices,
        'volume': [1000] * 100,
        'timestamp': dates
    })
    
    report = validator.validate_dataset(df, "price_data", timestamp_col="timestamp")
    
    print("Validation Report:", report)
    
    assert report['status'] == 'stale'
    assert any("outliers" in w.lower() for w in report['warnings'])
    print("✅ Report captured Stale Status and Outlier Warnings")

if __name__ == "__main__":
    try:
        test_schema_validation()
        test_freshness_validation()
        test_outlier_detection()
        test_full_dataset_validation()
        print("\nALL VALIDATION TESTS PASSED ✅")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
