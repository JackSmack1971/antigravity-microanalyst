import requests
import json

def check_fallbacks():
    print("Checking Derivatives Fallbacks...")
    
    # 1. CoinGecko Derivatives
    try:
        print("\n[CoinGecko]")
        # Get Binance Futures specific data from CG
        url = "https://api.coingecko.com/api/v3/derivatives/exchanges/binance_futures" 
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Access Success")
            print(f"Open Interest (BTC): {data.get('open_interest_btc', 'N/A')}")
            # CG often aggregates, let's see if we can get per-ticker
        else:
            print(f"❌ Failed: {res.status_code}")
            
        # Tickers to find BTC funding
        url2 = "https://api.coingecko.com/api/v3/derivatives/exchanges/binance_futures/tickers?coin_ids=bitcoin"
        res2 = requests.get(url2, timeout=10)
        if res2.status_code == 200:
            tickers = res2.json().get('tickers', [])
            if tickers:
                btc_perp = next((t for t in tickers if t['base'] == 'BTC' and t['target'] == 'USDT'), None)
                if btc_perp:
                    print(f"✅ Found BTC/USDT Perp")
                    print(f"Funding Rate: {btc_perp.get('funding_rate')}")
                    print(f"Open Interest (USD): {btc_perp.get('open_interest_usd')}")
                else:
                    print("❌ BTC/USDT Perp not found in ticker list")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 2. Kraken Futures
    try:
        print("\n[Kraken Futures]")
        url = "https://futures.kraken.com/derivatives/api/v3/tickers"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # Kraken structure: tickers list
            tickers = data.get('tickers', [])
            btc_perp = next((t for t in tickers if t['symbol'] == 'pi_xbtusd'), None)
            if btc_perp:
                 print(f"✅ Found pi_xbtusd (BTC Perp)")
                 print(f"Funding Rate: {btc_perp.get('fundingRate')}")
                 print(f"Open Interest: {btc_perp.get('openInterest')}")
            else:
                 print("❌ pi_xbtusd not found")
        else:
             print(f"❌ Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_fallbacks()
