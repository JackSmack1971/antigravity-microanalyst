import requests
import pandas as pd
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BinanceSpotProvider:
    """
    Fetches Spot Market Data from Binance Public API (No Auth required).
    """
    BASE_URL = "https://api.binance.com"

    def fetch_ohlcv(self, symbol: str = "BTCUSDT", interval: str = "4h", limit: int = 100) -> pd.DataFrame:
        """
        Fetch OHLCV klines.
        Intervals: 1m, 5m, 1h, 4h, 1d
        Returns: DataFrame with Datetime Index and [open, high, low, close, volume] columns.
        """
        # Try Global URL first, then US
        urls = [f"{self.BASE_URL}/api/v3/klines", "https://api.binance.us/api/v3/klines"]
        
        for url in urls:
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
                ])
                
                # Convert types
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                    
                # Parse timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                logger.info(f"Successfully fetched OHLCV from {url}")
                return df[['open', 'high', 'low', 'close', 'volume']]
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 451:
                     logger.warning(f"Geoblocked by {url} (HTTP 451). Trying next endpoint...")
                     continue
                else:
                     logger.error(f"HTTP Error fetching OHLCV for {symbol} from {url}: {e}")
                     # If it's not a geo error, maybe don't break immediately? 
                     # But for now, let's allow trying the next mirror just in case.
                     continue
            except Exception as e:
                logger.error(f"Failed to fetch OHLCV for {symbol} from {url}: {e}")
                continue
        
        logger.error(f"All Binance endpoints failed for {symbol}")
        return pd.DataFrame()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    provider = BinanceSpotProvider()
    df = provider.fetch_ohlcv()
    print(df.head())
    print(df.tail())
