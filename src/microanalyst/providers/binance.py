import requests
import pandas as pd

def fetch_order_book(symbol="BTCUSDT", limit=100):
    """
    Fetches the order book for a symbol from Binance Public API.
    Returns a pandas DataFrame with columns ['price', 'quantity', 'side'].
    """
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        bids = pd.DataFrame(data['bids'], columns=['price', 'quantity'], dtype=float)
        bids['side'] = 'bid'
        
        asks = pd.DataFrame(data['asks'], columns=['price', 'quantity'], dtype=float)
        asks['side'] = 'ask'
        
        # Combine and sort
        order_book = pd.concat([bids, asks])
        order_book = order_book.sort_values(by='price', ascending=True)
        
        return order_book
        
    except Exception as e:
        print(f"Error fetching Binance order book: {e}")
        return pd.DataFrame(columns=['price', 'quantity', 'side'])
