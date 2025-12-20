# src/microanalyst/synthetic/exchange_proxies.py
import requests
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ExchangeProxyMetrics:
    """
    Derive institutional-grade flow metrics from public exchange APIs (Free Tier)
    """
    
    def __init__(self):
        # Use Binance.us for US-based compliance
        self.binance_api = "https://api.binance.us/api/v3"
        self.kraken_api = "https://api.kraken.com/0/public"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def derive_order_flow_delta(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Derive synthetic Cumulative Volume Delta (CVD) proxy from order book imbalance.
        
        Logic: Large bid/ask imbalances in the mid-book are strong proxies for 
        taker buy/sell pressure which drives CVD.
        """
        try:
            logger.info(f"Fetching order book for {symbol} from Binance...")
            response = requests.get(
                f"{self.binance_api}/depth",
                params={'symbol': symbol, 'limit': 100},
                timeout=5
            )
            response.raise_for_status()
            depth = response.json()
            
            # bids: [ [price, quantity], ... ]
            bids = depth['bids']
            asks = depth['asks']
            
            # Calculate total depth within 1% of mid-price
            mid_price = (float(bids[0][0]) + float(asks[0][0])) / 2
            upper_bound = mid_price * 1.01
            lower_bound = mid_price * 0.99
            
            bid_volume_1pct = sum(float(q) for p, q in bids if float(p) >= lower_bound)
            ask_volume_1pct = sum(float(q) for p, q in asks if float(p) <= upper_bound)
            
            total_volume = bid_volume_1pct + ask_volume_1pct
            if total_volume == 0:
                imbalance = 0
            else:
                imbalance = (bid_volume_1pct - ask_volume_1pct) / total_volume
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'synthetic_order_flow_delta',
                'symbol': symbol,
                'bid_vol_1pct': bid_volume_1pct,
                'ask_vol_1pct': ask_volume_1pct,
                'imbalance_ratio': float(imbalance),
                'bias': 'bullish' if imbalance > 0.1 else 'bearish' if imbalance < -0.1 else 'neutral',
                'method': 'order_book_imbalance_proxy'
            }
            
        except Exception as e:
            logger.error(f"Error deriving order flow delta: {e}")
            return {'error': str(e)}

    def calculate_liquidity_density(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Calculate liquidity density (slippage resistance) from depth data.
        """
        try:
            logger.info(f"Calculating liquidity density for {symbol}...")
            # We already have Binance, let's use it
            response = requests.get(
                f"{self.binance_api}/depth",
                params={'symbol': symbol, 'limit': 100},
                timeout=5
            )
            response.raise_for_status()
            depth = response.json()
            
            mid_price = (float(depth['bids'][0][0]) + float(depth['asks'][0][0])) / 2
            
            # How much volume is needed to move price by 0.5%?
            threshold = 0.005 # 0.5%
            target_bid_price = mid_price * (1 - threshold)
            target_ask_price = mid_price * (1 + threshold)
            
            vol_to_move_bids = sum(float(q) for p, q in depth['bids'] if float(p) >= target_bid_price)
            vol_to_move_asks = sum(float(q) for p, q in depth['asks'] if float(p) <= target_ask_price)
            
            avg_vol_density = (vol_to_move_bids + vol_to_move_asks) / 2
            
            return {
                'symbol': symbol,
                'liquidity_density_score': float(avg_vol_density),
                'bid_liquidity_0.5pct': vol_to_move_bids,
                'ask_liquidity_0.5pct': vol_to_move_asks,
                'unit': 'BTC',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    proxies = ExchangeProxyMetrics()
    print(proxies.derive_order_flow_delta())
    print(proxies.calculate_liquidity_density())
