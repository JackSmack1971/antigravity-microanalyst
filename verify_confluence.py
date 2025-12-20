from src.microanalyst.intelligence.confluence import ConfluenceUtils
from src.microanalyst.core.persistence import DatabaseManager
import pandas as pd
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)

def test_confluence():
    print("Testing ConfluenceUtils...")
    
    # 1. Test with existing DB data
    utils = ConfluenceUtils()
    result = utils.check_fractal_alignment()
    print("\n--- Live DB Result ---")
    print(result)
    
    # 2. Test with Mock Data injection (to ensure logic works even if DB is empty)
    # We will subclass/mock the db_manager for this test
    print("\n--- Mock Data Test ---")
    
    class MockDB:
        def get_price_history(self, limit=50, interval="1d"):
            # Create a localized bullish trend
            data = {
                "close": [100 + i for i in range(limit)]
            }
            return pd.DataFrame(data)

    mock_utils = ConfluenceUtils(db_manager=MockDB())
    mock_result = mock_utils.check_fractal_alignment()
    print(mock_result)
    
    if mock_result["aligned"] and mock_result["type"] == "Bullish Fractal":
        print("SUCCESS: Mock Bullish Fractal detected.")
    else:
        print("FAILURE: Mock detection failed.")

if __name__ == "__main__":
    test_confluence()
