
import pandas as pd
import numpy as np
import os
import sys

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from datetime import datetime
from src.microanalyst.data_loader import load_btcetffundflow_json, load_price_history, BTCETFFO_FILE, TWELVE_FILE

# Output Directory
DATA_CLEAN_DIR = os.path.join("data_clean")
if not os.path.exists(DATA_CLEAN_DIR):
    os.makedirs(DATA_CLEAN_DIR)


from src.microanalyst.metadata.lineage_tracker import LineageTracker

class DataNormalizer:
    def __init__(self):
        self.clean_dir = DATA_CLEAN_DIR
        self.lineage = LineageTracker()

    def run_pipeline(self):
        """
        Orchestrates the loading, cleaning, validating, and saving process.
        """
        print("Starting Normalization Pipeline...")
        
        # 1. ETF Flows
        print("Processing ETF Flows...")
        raw_flows = load_btcetffundflow_json(BTCETFFO_FILE)
        if not raw_flows.empty:
            norm_flows = self.normalize_etf_flows(raw_flows)
            if self.validate_schema(norm_flows, "etf_flows"):
                self.save_csv(norm_flows, "etf_flows_normalized.csv")
                
                # Metadata Recording
                self.lineage.record_transformation(
                    dataset_id='etf_flows_normalized',
                    source_datasets=['btcetffundflow_raw'],
                    transformation_module='normalization.py',
                    transformation_function='normalize_etf_flows',
                    metadata={'rows_processed': len(norm_flows), 'source': BTCETFFO_FILE}
                )
        else:
            print("WARNING: Raw ETF flows data is empty.")

        # 2. BTC Price
        print("Processing BTC Price...")
        # Note: load_price_history currently parses TwelveData HTML or similar. 
        # We assume it returns a DF with Date index or column.
        raw_price = load_price_history()
        if not raw_price.empty:
            norm_price = self.normalize_price_history(raw_price)
            if self.validate_schema(norm_price, "btc_price"):
                self.save_csv(norm_price, "btc_price_normalized.csv")
                
                # Metadata Recording
                self.lineage.record_transformation(
                    dataset_id='btc_price_normalized',
                    source_datasets=['twelvedata_raw'],
                    transformation_module='normalization.py',
                    transformation_function='normalize_price_history',
                    metadata={'rows_processed': len(norm_price), 'source': TWELVE_FILE}
                )
        else:
            print("WARNING: Raw BTC price data is empty.")

        # Cross Validation (Optional but good)
        if hasattr(self, 'cross_validate') and 'norm_flows' in locals() and 'norm_price' in locals():
             self.cross_validate(norm_flows, norm_price)

        print("Normalization Pipeline Complete.")

    def normalize_etf_flows(self, df):
        """
        Standardizes columns to [date, ticker, flow_usd, flow_btc, provider]
        Input DF from load_btcetffundflow_json has: [Date, Ticker, Field, Value]
        """
        # Pivot or reshape if needed. 
        # The raw format is long: Ticker | Field (Flow USD/BTC) | Value
        # We want a clean long format or specific columns?
        # Plan says: [date, ticker, flow_usd, flow_btc, provider]
        
        # 1. Pivot to get flow_usd and flow_btc as columns
        df_pivot = df.pivot_table(index=["Date", "Ticker"], columns="Field", values="Value").reset_index()
        
        # Rename columns to snake_case
        df_pivot.columns.name = None # Remove index name 'Field'
        mapping = {
            "Date": "date",
            "Ticker": "ticker",
            "Flow (USD)": "flow_usd",
            "Flow (BTC)": "flow_btc"
        }
        df_pivot.rename(columns=mapping, inplace=True)
        
        # Add provider column? Ticker is kind of the provider identifier here.
        # If we want a separate 'provider' id, we might need a map, but 'ticker' serves the purpose.
        
        # Ensure columns exist (fill NaN with 0 only if appropriate, or keep NaN)
        if "flow_usd" not in df_pivot.columns: df_pivot["flow_usd"] = np.nan
        if "flow_btc" not in df_pivot.columns: df_pivot["flow_btc"] = np.nan
        
        # Clean Datatypes
        df_pivot["date"] = pd.to_datetime(df_pivot["date"])
        df_pivot["flow_usd"] = df_pivot["flow_usd"].astype(float)
        df_pivot["flow_btc"] = df_pivot["flow_btc"].astype(float)
        
        # Deduplicate
        df_pivot.drop_duplicates(subset=["date", "ticker"], inplace=True)
        
        # Sort
        df_pivot.sort_values(["date", "ticker"], inplace=True)
        
        return df_pivot

    def normalize_price_history(self, df):
        """
        Standardizes columns to [date, open, high, low, close, volume]
        Assumed Input: [Date, Open, High, Low, Close] (Volume might be missing)
        """
        df = df.copy()
        
        # Ensure Date is column, not index
        if "Date" not in df.columns and isinstance(df.index, pd.DatetimeIndex):
            df.reset_index(inplace=True)
            df.rename(columns={"index": "Date"}, inplace=True)
            
        columns_map = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        }
        df.rename(columns=columns_map, inplace=True)
        
        # Lowercase all cols just in case
        df.columns = [c.lower() for c in df.columns]
        
        required_cols = ["date", "open", "high", "low", "close"]
        for c in required_cols:
            if c not in df.columns:
                print(f"Column {c} missing in price data")
                # Handle missing? or return empty?
        
        # Clean Types
        df["date"] = pd.to_datetime(df["date"])
        for c in ["open", "high", "low", "close"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
                
        # Deduplicate
        df.drop_duplicates(subset=["date"], inplace=True)
        df.sort_values("date", inplace=True)
        
        return df

    def validate_schema(self, df, schema_type):
        """
        Checks for missing columns, nulls in critical fields, and data types.
        """
        if df.empty:
            print(f"Validation Failed: {schema_type} DataFrame is empty.")
            return False
            
        if schema_type == "etf_flows":
            required = ["date", "ticker", "flow_usd"]
            if not all(col in df.columns for col in required):
                print(f"Validation Failed: Missing columns in {schema_type}. Got {df.columns}")
                return False
            
            # Null Check
            if df["date"].isnull().any():
                print("Validation Warning: Null dates found. Dropping.")
                df.dropna(subset=["date"], inplace=True)
                
            if df["ticker"].isnull().any():
                print("Validation Warning: Null tickers found.")
                
        elif schema_type == "btc_price":
            required = ["date", "close"]
            if not all(col in df.columns for col in required):
                print(f"Validation Failed: Missing columns in {schema_type}. Got {df.columns}")
                return False
                
            if df["date"].isnull().any():
                df.dropna(subset=["date"], inplace=True)

        # Future Date Check
        now = pd.Timestamp.now()
        future_rows = df[df["date"] > now + pd.Timedelta(days=1)]
        if not future_rows.empty:
            print(f"Validation Warning: {len(future_rows)} rows have future dates.")
            # Drop or keep? Plan says "flagged". We'll warn for now.
            
        return True

    def cross_validate(self, df_flows, df_price):
        """
        Inter-dataset validation.
        Checks if date ranges overlap reasonably.
        """
        print("Running Cross-Validation...")
        
        dates_flows = set(df_flows["date"].unique())
        dates_price = set(df_price["date"].unique())
        
        common_dates = dates_flows.intersection(dates_price)
        
        if not common_dates:
            print("Validation Warning: No overlapping dates between ETF Flows and BTC Price.")
            return False
            
        print(f"Cross-Validation Passed: {len(common_dates)} overlapping dates found.")
        
        # Check alignment of latest date
        latest_flow = max(dates_flows)
        latest_price = max(dates_price)
        
        diff = abs((latest_flow - latest_price).days)
        if diff > 1:
            print(f"Validation Warning: Latest dates diverge by {diff} days (Flows: {latest_flow.date()}, Price: {latest_price.date()})")
        else:
            print(f"Date Alignment: Good (Delta: {diff} days)")
            
        return True

    def save_csv(self, df, filename):
        path = os.path.join(self.clean_dir, filename)
        df.to_csv(path, index=False)
        print(f"Saved normalized data to {path} ({len(df)} rows)")

if __name__ == "__main__":
    normalizer = DataNormalizer()
    normalizer.run_pipeline()
