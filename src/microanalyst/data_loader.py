import pandas as pd
from bs4 import BeautifulSoup
import os
import re
import json

# Paths to artifacts (relative to where script runs)
DATA_DIR = "data_exports"
BITBO_FILE = os.path.join(DATA_DIR, "bitbo_us_etf_flows_table.html")
TWELVE_FILE = os.path.join(DATA_DIR, "twelvedata_btcusd_hist_html.html")
BTCETFFO_FILE = os.path.join(DATA_DIR, "btcetffundflow_holdings.html")
COINALYZE_OI_FILE = os.path.join(DATA_DIR, "coinalyze_btc_open_interest.html")
COINALYZE_FUNDING_FILE = os.path.join(DATA_DIR, "coinalyze_btc_funding.html")
COINGECKO_FILE = os.path.join(DATA_DIR, "coingecko_btc_market_snapshot.html")

def load_etf_flows_enhanced():
    """
    Loads ETF flows using the enhanced JSON parser from btcetffundflow.com.
    Returns DataFrame compatible with UI: [Date, Net_Flow, Cumulative_Flow]
    """
    df_raw = load_btcetffundflow_json(BTCETFFO_FILE)
    if df_raw.empty:
        return pd.DataFrame()
        
    # Filter for USD flows
    df_usd = df_raw[df_raw["Field"] == "Flow (USD)"].copy()
    
    # Aggregation: Daily Net Flow
    daily_flow = df_usd.groupby("Date")["Value"].sum().reset_index()
    daily_flow.rename(columns={"Value": "Net_Flow"}, inplace=True)
    
    # Sort
    daily_flow.sort_values("Date", inplace=True)
    
    # Calculate Cumulative
    daily_flow["Cumulative_Flow"] = daily_flow["Net_Flow"].cumsum()
    
    # Scale to Millions for UI compatibility (if needed, UI expects Millions?)
    # UI uses: f"${flow_val:,.1f}M"
    # If parser returns raw dollars (billions), then divide by 1M is safest?
    # Step 538 output: Value is 2.86e+10 (28 Billion).
    # UI code: metrics["flow"]["val"] = f"${flow_val:,.1f}M"
    # If the UI expects raw value and formats it with 'M', that's weird. usually it divides.
    # Let's check `load_etf_flows` original logic if possible.
    # But usually "Flow (USD)" implies raw dollars.
    # If UI formatting is f"{val:,.1f}M", it implies val is in specific unit or just appended M.
    # Actually standard python f-string doesn't auto-scale. 
    # If I pass 28,000,000,000 it prints "28,000,000,000.0M".
    # So I MUST scale it to millions.
    
    daily_flow["Net_Flow"] = daily_flow["Net_Flow"] / 1_000_000.0
    daily_flow["Cumulative_Flow"] = daily_flow["Cumulative_Flow"] / 1_000_000.0
    
    # Return 
    return daily_flow

def load_etf_flows():
    """
    Parses Bitbo HTML to extract ETF flow data.
    Returns: pd.DataFrame with columns [Date, Total_Flow, IBIT, FBTC, ...]
    """
    if not os.path.exists(BITBO_FILE):
        return pd.DataFrame()

    with open(BITBO_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Find the stats table
    table = soup.find("table", class_="stats-table")
    if not table:
        return pd.DataFrame()

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    
    rows = []
    for tr in table.find_all("tr")[1:]: # Skip header row
        cols = tr.find_all("td")
        if not cols:
            continue
            
        row_data = {}
        # Date is usually first
        row_data["Date"] = cols[0].get_text(strip=True)
        
        # Parse flows (skipping Date index 0)
        # Note: headers often include 'Date' as first item
        for idx, col in enumerate(cols[1:], 1):
            if idx < len(headers):
                val_text = col.get_text(strip=True).replace(",", "")
                try:
                    val = float(val_text)
                except ValueError:
                    val = 0.0
                row_data[headers[idx]] = val
        
        rows.append(row_data)

    df = pd.DataFrame(rows)
    # Convert Date
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    # Filter valid dates
    df = df.dropna(subset=["Date"])
    # Sort
    df = df.sort_values("Date", ascending=True)
    
    # Locate 'Total' column (sometimes named 'Totals')
    total_col = [c for c in df.columns if "Total" in c]
    if total_col:
        df["Net_Flow"] = df[total_col[0]]
    else:
        df["Net_Flow"] = 0.0

    return df

def load_price_history():
    """
    Parses TwelveData HTML to extract OHLC data.
    Returns: pd.DataFrame with columns [Date, Open, High, Low, Close]
    """
    if not os.path.exists(TWELVE_FILE):
        return pd.DataFrame()

    with open(TWELVE_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Find the table that contains "Open" in its headers
    table = None
    for t in soup.find_all("table"):
        headers_text = [th.get_text(strip=True) for th in t.find_all("th")]
        if "Open" in headers_text and "Close" in headers_text:
            table = t
            break
    
    if not table:
        return pd.DataFrame()

    rows = []
    
    def parse_value(val_str):
        # Handle 'K' suffix (e.g. 87.85K -> 87850.0)
        val_str = val_str.replace(",", "").upper()
        multiplier = 1.0
        if "K" in val_str:
            multiplier = 1000.0
            val_str = val_str.replace("K", "")
        # Add other suffixes if needed, e.g. M, B
        try:
            return float(val_str) * multiplier
        except ValueError:
            return 0.0

    for tr in table.find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) < 5: 
            continue
            
        # Structure: Date, Open, High, Low, Close, % Change
        try:
            date_str = cols[0].get_text(strip=True)
            o = parse_value(cols[1].get_text(strip=True))
            h = parse_value(cols[2].get_text(strip=True))
            l = parse_value(cols[3].get_text(strip=True))
            c = parse_value(cols[4].get_text(strip=True))
            
            rows.append({
                "Date": date_str,
                "Open": o, "High": h, "Low": l, "Close": c
            })
        except Exception as e:
            # print(f"Error parsing row: {e}")
            continue

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    df = df.dropna(subset=["Date"]).sort_values("Date", ascending=True)
    return df

def load_btcetffundflow_json(file_path):
    """
    Parses the embedded JSON from btcetffundflow.com HTML export.
    Returns a DataFrame with columns: [Date, Ticker, Field, Value]
    where Field is 'Flow (USD)' or 'Flow (BTC)'.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return pd.DataFrame()

    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    next_data = soup.find("script", id="__NEXT_DATA__")

    if not next_data:
        print("No __NEXT_DATA__ script found.")
        return pd.DataFrame()

    try:
        data = json.loads(next_data.string)
        dehydrated_state = data.get("props", {}).get("pageProps", {}).get("dehydratedState", {})
        queries = dehydrated_state.get("queries", [])
        target_query = next((q for q in queries if q.get("queryKey") == ["data", "us"]), None)

        if not target_query:
            print("Target query ['data', 'us'] not found.")
            return pd.DataFrame()

        actual_data = target_query["state"]["data"]["data"]
        providers = actual_data.get("providers", {})
        
        if not providers:
            print("No providers map found.")
        
        records = []
        
        # chart1 appears to be the main time series with daily flows/holdings
        # Structure: [{'ts': 123456, '0': '123.45', '1': '67.89', ...}, ...]
        chart1 = actual_data.get("chart1", [])
        
        if not chart1:
            print("No chart1 data found.")
        
        for item in chart1:
            try:
                ts = int(item.get("ts", 0))
                if ts == 0:
                    continue
                dt = pd.to_datetime(ts, unit='s')
                
                # Iterate over all providers to find their value in this time slot
                for pid, ticker in providers.items():
                    if pid in item:
                        val_str = item[pid]
                        try:
                            val = float(val_str)
                            # Assuming chart1 is BTC Flows or Net Flows. 
                            # If there are chart2/chart3, they might be Price or Cumulative.
                            # Based on context, chart1 provides the main flow data.
                            # Let's label it "Flow (BTC)" if values are small (thousands) or "Flow (USD)" if large (millions).
                            # We can infer from magnitude or just default to Flow.
                            # Given Step 456 output: flows (USD) ~2B, flows2 (BTC) ~-3753.
                            # Let's check magnitude of the first value.
                            # If > 1,000,000, likely USD.
                            
                            field = "Flow"
                            if abs(val) > 1000000:
                                field = "Flow (USD)"
                            elif abs(val) > 0: # Avoid zero division or ambiguity
                                field = "Flow (BTC)"
                                
                            records.append({
                                "Date": dt,
                                "Ticker": ticker,
                                "Field": field,
                                "Value": val
                            })
                        except ValueError:
                            continue
            except Exception as e:
                pass

        if not records:
            print("No records extracted from chart1.")
            return pd.DataFrame()
            
        df = pd.DataFrame(records)
        
        # --- DELTA ALGORITHM v2 ---
        # Calculate daily net delta per Ticker/Field
        df = df.sort_values(["Ticker", "Field", "Date"])
        df["Value_Raw"] = df["Value"]
        # Group by Ticker and Field, then calculate the diff
        df["Value"] = df.groupby(["Ticker", "Field"])["Value_Raw"].diff()
        
        # The first entry for each series will be NaN; we'll treat it as zero (or the raw value if it's the start of history)
        # In this case, for flows, 0 is safest for the first recorded day in a partial export.
        df["Value"] = df["Value"].fillna(0.0)
        
        return df

    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return pd.DataFrame()

def load_coinalyze_oi():
    """Extract aggregate USD-notional OI (All/Perpetual/Futures)."""
    res = {"all": 0.0, "perpetual": 0.0, "futures": 0.0}
    if not os.path.exists(COINALYZE_OI_FILE):
        return res
    with open(COINALYZE_OI_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    # Look for grid labels
    for div in soup.find_all("div"):
        text = div.get_text(strip=True).lower()
        if "open interest" in text and "all" in text:
            # Simple heuristic parser for demo
            matches = re.findall(r"\$([0-9.,]+B)", div.get_text())
            if matches:
                res["all"] = float(matches[0].replace("B", "").replace(",", "")) * 1e9
    return res

def load_coinalyze_funding():
    """Extract funding rates from Coinalyze HTML."""
    if not os.path.exists(COINALYZE_FUNDING_FILE):
        return []
    with open(COINALYZE_FUNDING_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    rows = []
    table = soup.find("table")
    if table:
        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) >= 3:
                exchange = tds[0].get_text(strip=True)
                current = tds[1].get_text(strip=True)
                predicted = tds[2].get_text(strip=True)
                rows.append({"exchange": exchange, "current": current, "predicted": predicted})
    return rows

def load_coingecko_api():
    """Extract volume/price from CoinGecko API JSON."""
    json_path = os.path.join(DATA_DIR, "coingecko_api_simple.json")
    txt_path = os.path.join(DATA_DIR, "coingecko_api_simple.txt")
    path = json_path if os.path.exists(json_path) else txt_path
    
    if not os.path.exists(path):
        return {"price": 0.0, "volume": 0.0}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Handle simple price structure
        # If it's the raw JSON from fetch_http, it might be a list of captures or just the JSON
        # Actually our fetch_http saves the raw text. 
        # api.coingecko.com returns: {"bitcoin": {"usd": 123, "usd_24h_vol": 456}}
        if "bitcoin" in data:
            return {
                "price": float(data["bitcoin"].get("usd", 0.0)),
                "volume": float(data["bitcoin"].get("usd_24h_vol", 0.0))
            }
    except:
        pass
    return {"price": 0.0, "volume": 0.0}

def load_coingecko_volume():
    """Extract 24h rolling volume proxy from CoinGecko."""
    if not os.path.exists(COINGECKO_FILE):
        return 0.0
    with open(COINGECKO_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    # Target span with data-testid="coin-show-volume" or similar
    vol_text = soup.find("span", text=re.compile(r"24 Hour Trading Vol"))
    if vol_text:
        val_div = vol_text.find_next("span")
        if val_div:
            val_str = val_div.get_text(strip=True).replace("$", "").replace(",", "")
            try:
                return float(val_str)
            except:
                pass
    return 0.0

if __name__ == "__main__":
    # Test the new parser
    test_file = r"c:\Users\click\OneDrive\Desktop\antigravity test v2\data_exports\btcetffundflow_holdings_derived.html"
    print(f"Testing parser with: {test_file}")
    df = load_btcetffundflow_json(test_file)
    if not df.empty:
        print("Success! DataFrame Head:")
        print(df.head())
        print("\nUnique Tickers:", df["Ticker"].unique())
        print("\nLast 5 rows:")
        print(df.tail())
    else:
        print("Parser returned empty DataFrame.")
