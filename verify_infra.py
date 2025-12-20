import sqlite3
import pandas as pd
from pathlib import Path

def verify_infra():
    db_path = "microanalyst.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check Tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables found: {tables}")
    
    if "btc_price_intraday" in tables:
        print("SUCCESS: btc_price_intraday table exists.")
        
        # Check Schema
        cursor.execute("PRAGMA table_info(btc_price_intraday);")
        columns = [r[1] for r in cursor.fetchall()]
        print(f"Columns: {columns}")
        
        if "interval" in columns:
            print("SUCCESS: 'interval' column exists.")
            
            # Check Data
            cursor.execute("SELECT * FROM btc_price_intraday WHERE interval='1h' LIMIT 5")
            rows = cursor.fetchall()
            print(f"1H Data Rows: {len(rows)}")
            if rows:
                print(f"Sample: {rows[0]}")
            else:
                print("WARNING: No 1H data found.")
        else:
            print("FAILURE: 'interval' column missing.")
    else:
        print("FAILURE: btc_price_intraday table MISSING.")
        
    conn.close()

if __name__ == "__main__":
    verify_infra()
