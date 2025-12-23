# tests/test_macro_pipeline.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.microanalyst.providers.macro_data import MacroDataProvider
from src.microanalyst.core.persistence import DatabaseManager

@pytest.fixture
def db_manager():
    # Use a temporary test database
    db = DatabaseManager(db_name="test_macro.db")
    yield db
    # Cleanup after tests
    import os
    if os.path.exists(db.db_path):
        os.remove(db.db_path)

@pytest.fixture
def macro_provider():
    return MacroDataProvider(cache_dir="test_cache")

def test_macro_data_upsert_and_retrieval(db_manager):
    """Verifies that macro data can be persisted and retrieved correctly."""
    # Create sample macro data
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]
    df_macro = pd.DataFrame({
        'date': dates,
        'asset_id': ['dxy'] * 5,
        'price': [104.2, 104.5, 104.1, 103.8, 104.0],
        'change_pct': [0.1, 0.3, -0.4, -0.3, 0.2]
    })
    
    # 1. Upsert
    db_manager.upsert_macro_data(df_macro)
    
    # 2. Retrieve (Using the new method to be implemented)
    # Note: We'll assume the method signature is get_macro_history(asset_id, limit)
    try:
        df_history = db_manager.get_macro_history(asset_id='dxy', limit=10)
        assert not df_history.empty
        assert len(df_history) == 5
        assert 'price' in df_history.columns
        assert df_history.iloc[0]['asset_id'] == 'dxy'
    except AttributeError:
        pytest.fail("DatabaseManager.get_macro_history not implemented yet.")

def test_macro_provider_fetch_structure(macro_provider):
    """Verifies the output structure of the MacroDataProvider."""
    # We'll mock the yfinance download if needed, but for now check the logic
    # This might require internet if not mocked, but for TDD we define the expectation
    series_dict = macro_provider.fetch_macro_series(lookback_days=5)
    
    assert isinstance(series_dict, dict)
    for asset in ['dxy', 'spy']:
        assert asset in series_dict
        assert isinstance(series_dict[asset], pd.Series)
        # Dates should be localized to None (as per macro_data.py:70)
        if not series_dict[asset].empty:
            assert series_dict[asset].index.tz is None

def test_macro_metrics_generation(macro_provider):
    """Verifies the get_latest_metrics returns standardized dicts."""
    metrics = macro_provider.get_latest_metrics()
    
    assert isinstance(metrics, dict)
    if 'dxy' in metrics:
        assert 'price' in metrics['dxy']
        assert 'change_24h' in metrics['dxy']
        assert 'trend' in metrics['dxy']
        assert metrics['dxy']['trend'] in ['bullish', 'bearish']
