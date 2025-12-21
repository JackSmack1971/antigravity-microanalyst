from src.microanalyst.core.persistence import DatabaseManager
import pandas as pd

def verify_db():
    db = DatabaseManager()
    with db._get_connection() as conn:
        print("\n--- Verifying Tables ---")
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
        print(tables)
        
        print("\n--- BTC Price Sample ---")
        try:
            price = pd.read_sql("SELECT * FROM btc_price_daily ORDER BY date DESC LIMIT 5;", conn)
            print(price)
        except Exception as e:
            print(f"Error reading price: {e}")
            
        print("\n--- ETF Flows Sample ---")
        try:
            flows = pd.read_sql("SELECT * FROM etf_flows_daily ORDER BY date DESC LIMIT 5;", conn)
            print(flows)
        except Exception as e:
            print(f"Error reading flows: {e}")

        print("\n--- Macro Data Sample ---")
        try:
            macro = pd.read_sql("SELECT * FROM macro_data_daily ORDER BY date DESC LIMIT 5;", conn)
            print(macro)
            if macro.empty:
                print("Note: macro_data_daily is currently empty.")
        except Exception as e:
            print(f"Error reading macro data: {e}")

if __name__ == "__main__":
    verify_db()
