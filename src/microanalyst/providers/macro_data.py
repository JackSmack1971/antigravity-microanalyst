import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class MacroDataProvider:
    """
    Fetches and normalizes macroeconomic data (DXY, SPY, Gold)
    using yfinance for correlation analysis.
    """
    
    def __init__(self, cache_dir: str = "workflow_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Tickers map
        self.tickers = {
            'dxy': 'DX-Y.NYB',  # US Dollar Index
            'spy': 'SPY',       # S&P 500 ETF
            'gold': 'GC=F'      # Gold Futures
        }

    def fetch_macro_series(self, lookback_days: int = 60) -> Dict[str, pd.Series]:
        """
        Fetch normalized close price series for all macro assets.
        Returns a dict of pandas Series with DatetimeIndex.
        """
        results = {}
        
        for name, ticker in self.tickers.items():
            try:
                # 1. Check Cache
                cache_file = self.cache_dir / f"macro_{name}.parquet"
                if self._is_cache_valid(cache_file):
                    series = pd.read_parquet(cache_file)[name]
                    results[name] = series
                    logger.info(f"Loaded {name} from cache.")
                    continue
                
                # 2. Fetch Live
                logger.info(f"Fetching {name} ({ticker}) from yfinance...")
                data = yf.download(
                    ticker, 
                    period=f"{lookback_days}d",
                    interval="1d",
                    progress=False
                )
                
                if data.empty:
                    logger.warning(f"No data found for {ticker}")
                    results[name] = pd.Series(dtype=float)
                    continue
                    
                # 3. Process
                # Ensure we get 'Close' - yfinance structures can vary by version
                if 'Close' in data.columns:
                    if isinstance(data.columns, pd.MultiIndex):
                        # Handle multi-index (Price, Ticker)
                        series = data['Close'][ticker] if ticker in data['Close'].columns else data['Close'].iloc[:, 0]
                    else:
                        series = data['Close']
                else:
                     series = data.iloc[:, 0] # Fallback
                
                series.name = name
                series.index = pd.to_datetime(series.index).tz_localize(None) # Remove timezone for easy merge
                
                # 4. Cache
                df_to_save = series.to_frame()
                df_to_save.to_parquet(cache_file)
                results[name] = series
                
            except Exception as e:
                logger.error(f"Failed to fetch {name}: {e}")
                results[name] = pd.Series(dtype=float)

        return results

    def _is_cache_valid(self, cache_path: Path, max_age_hours: int = 12) -> bool:
        if not cache_path.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds() / 3600
        return age < max_age_hours

    def get_latest_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get latest values and 24h change for reporting"""
        series_dict = self.fetch_macro_series(lookback_days=5)
        metrics = {}
        
        for name, series in series_dict.items():
            if series.empty:
                continue
                
            current = series.iloc[-1]
            prev = series.iloc[-2] if len(series) > 1 else current
            
            change_pct = ((current - prev) / prev) * 100
            
            metrics[name] = {
                'price': float(current),
                'change_24h': float(change_pct),
                'trend': 'bullish' if change_pct > 0 else 'bearish'
            }
            
        return metrics
