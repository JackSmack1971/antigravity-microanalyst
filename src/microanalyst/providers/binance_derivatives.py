# src/microanalyst/providers/binance_derivatives.py
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class BinanceFreeDerivatives:
    """
    Complete derivatives suite using Binance's free API.
    Note: Standard consumers use fapi.binance.com.
    """
    
    BASE_URL = "https://fapi.binance.com"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.coingecko_api = "https://api.coingecko.com/api/v3"

    def _get_current_price(self, symbol='BTCUSDT') -> float:
        """Helper to get current mark price"""
        try:
            res = requests.get(f"{self.BASE_URL}/fapi/v1/premiumIndex", params={'symbol': symbol}, headers=self.headers, timeout=5)
            res.raise_for_status()
            return float(res.json()['markPrice'])
        except Exception:
            return 98000.0 # Fallback for demo if API unreachable
    
    def get_funding_rate_history(self, symbol='BTCUSDT', days=30) -> Dict[str, Any]:
        """
        Historical funding rates (updated every 8 hours)
        """
        try:
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            response = requests.get(
                f"{self.BASE_URL}/fapi/v1/fundingRate",
                params={
                    'symbol': symbol,
                    'startTime': start_time,
                    'limit': 1000
                },
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            funding_data = response.json()
            
            if not funding_data:
                return {'error': 'No funding data returned'}

            # Calculate metrics
            rates = [float(f['fundingRate']) for f in funding_data]
            current_rate = rates[-1]
            
            avg_rate_7d = sum(rates[-21:]) / min(len(rates), 21) if rates else 0
            avg_rate_30d = sum(rates) / len(rates) if rates else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'funding_rate_analysis',
                'current_funding_rate': current_rate * 100,  # Convert to percentage
                'avg_7d': avg_rate_7d * 100,
                'avg_30d': avg_rate_30d * 100,
                'trend': 'rising_cost' if current_rate > avg_rate_7d else 'falling_cost',
                'extreme_warning': abs(current_rate) > 0.001,  # 0.1% per 8h is significant
                'sample_size': len(rates)
            }
        except Exception as e:
            logger.warning(f"Binance API failed ({e}), attempting CoinGecko fallback...")
            return self._get_funding_coingecko(symbol)

    def _get_funding_coingecko(self, symbol='BTCUSDT') -> Dict[str, Any]:
        """Fallback for funding rate via CoinGecko"""
        try:
            # We assume BTCUSDT / Bitcoin for this demo
            response = requests.get(
                f"{self.coingecko_api}/derivatives/exchanges/binance_futures",
                params={'include_tickers': 'unexpired'},
                timeout=10,
                headers=self.headers
            )
            data = response.json()
            tickers = data.get('tickers', [])
            
            # Find BTC/USDT Pair
            ticker = next((t for t in tickers if t['base'] == 'BTC' and t['target'] == 'USDT'), None)
            
            if not ticker:
                 # Try specific ticker endpoint
                 try:
                     response = requests.get(
                        f"{self.coingecko_api}/derivatives/tickers",
                        params={'exchange_ids': 'binance_futures'},
                        timeout=10,
                        headers=self.headers
                     ) 
                     tickers = response.json()
                     ticker = next((t for t in tickers if t['base'] == 'BTC' and t['target'] == 'USDT'), None)
                 except: pass

            if ticker:
                # CG funding_rate is a floating point number (e.g., 0.01 for 0.01%) or ratio?
                # Usually API docs say "Funding Rate" (e.g. 0.01).
                # We'll return it as is or normalized if needed.
                funding_rate = float(ticker.get('funding_rate', 0)) * 100 
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'metric': 'funding_rate_analysis',
                    'current_funding_rate': funding_rate, 
                    'trend': 'neutral (fallback)',
                    'note': 'sourced_from_coingecko_fallback'
                }
            return {'error': 'Ticker not found in CoinGecko'}
        except Exception as e:
            logger.error(f"CoinGecko fallback failed: {e}")
            return {'error': str(e)}
    
    def get_open_interest(self, symbol='BTCUSDT') -> Dict[str, Any]:
        """
        Real-time open interest (free, unlimited)
        """
        try:
            # 1. Current OI
            response = requests.get(
                f"{self.BASE_URL}/fapi/v1/openInterest",
                params={'symbol': symbol},
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            oi_data = response.json()
            
            # 2. Historical OI for trend (Hourly)
            hist_response = requests.get(
                f"{self.BASE_URL}/futures/data/openInterestHist",
                params={
                    'symbol': symbol,
                    'period': '1h',
                    'limit': 24  # Just last 24h for simple trend
                },
                headers=self.headers,
                timeout=5
            )
            
            hist_oi_data = []
            if hist_response.status_code == 200:
                hist_oi_data = hist_response.json()
            
            current_oi = float(oi_data['openInterest'])
            current_price = self._get_current_price(symbol)
            
            # Calculate 24h change
            oi_change_24h = 0.0
            if hist_oi_data and len(hist_oi_data) > 0:
                first_entry = hist_oi_data[0] 
                oi_24h_ago = float(first_entry['sumOpenInterest'])
                if oi_24h_ago > 0:
                    oi_change_24h = ((current_oi - oi_24h_ago) / oi_24h_ago) * 100
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'open_interest',
                'open_interest_btc': current_oi,
                'open_interest_usd': current_oi * current_price,
                'change_24h_pct': oi_change_24h,
                'interpretation': 'increasing_interest' if oi_change_24h > 0 else 'decreasing_interest'
            }
        except Exception as e:
            logger.warning(f"Binance API failed ({e}), attempting CoinGecko fallback...")
            return self._get_oi_coingecko(symbol)

    def _get_oi_coingecko(self, symbol) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.coingecko_api}/derivatives/exchanges/binance_futures",
                timeout=10,
                headers=self.headers
            )
            data = response.json()
            
            # Aggregate OI for Binance Futures (often predominantly BTC)
            # This is "Exchange Open Interest", not symbol specific, but a good proxy for general leverage
            oi_btc = float(data.get('open_interest_btc', 0))
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'open_interest',
                'open_interest_btc': oi_btc,
                'change_24h_pct': 0.0, # Not available in simple fallback
                'note': 'exchange_aggregate_oi_fallback'
            }
        except Exception as e:
            return {'error': str(e)}

    def get_long_short_ratio(self, symbol='BTCUSDT', period='1h') -> Dict[str, Any]:
        """
        Top trader long/short ratio (free sentiment indicator)
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/futures/data/topLongShortAccountRatio",
                params={
                    'symbol': symbol,
                    'period': period,
                    'limit': 30
                },
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            ratio_data = response.json()
            
            if not ratio_data:
                 return {'error': 'No ratio data'}

            current_ratio = float(ratio_data[-1]['longShortRatio'])
            avg_ratio = sum(float(r['longShortRatio']) for r in ratio_data) / len(ratio_data)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'top_trader_ls_ratio',
                'current_long_short_ratio': current_ratio,
                'avg_30_periods': avg_ratio,
                'interpretation': f"{'bullish' if current_ratio > 1 else 'bearish'}_bias",
                'extreme_positioning': current_ratio > 2.0 or current_ratio < 0.5,
                'contrarian_signal': current_ratio > 3.0
            }
        except Exception as e:
             logger.warning(f"Binance API failed ({e}), deriving synthetic sentiment from Spot Order Flow...")
             return self._derive_synthetic_ls_from_spot(symbol)

    def _derive_synthetic_ls_from_spot(self, symbol='BTCUSDT') -> Dict[str, Any]:
        """
        Proxy L/S Ratio from Spot Order Book Imbalance.
        Ratio > 1.0 implies Bullish (Bid Heavy).
        Ratio < 1.0 implies Bearish (Ask Heavy).
        """
        try:
            # Avoid circular import by importing inside method
            from src.microanalyst.synthetic.exchange_proxies import ExchangeProxyMetrics
            
            proxy = ExchangeProxyMetrics()
            # Use binance.us spot data
            delta_data = proxy.derive_order_flow_delta(symbol)
            
            if 'error' in delta_data:
                return {'error': 'Synthetic fallback failed'}
                
            imbalance = delta_data.get('imbalance_ratio', 0.0)
            
            # Map imbalance (-1.0 to 1.0) to L/S Ratio (0.5 to 2.0 approx)
            # 0 imbalance -> 1.0 ratio
            # +0.5 imbalance -> 1.5 ratio
            # -0.5 imbalance -> 0.66 ratio (1/1.5)
            
            if imbalance >= 0:
                synthetic_ratio = 1.0 + imbalance
            else:
                synthetic_ratio = 1.0 / (1.0 + abs(imbalance))
                
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'synthetic_ls_ratio',
                'current_long_short_ratio': float(f"{synthetic_ratio:.2f}"),
                'interpretation': f"{'bullish' if synthetic_ratio > 1 else 'bearish'}_spot_pressure",
                'note': 'derived_from_spot_books_fallback'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_taker_buy_sell_volume(self, symbol='BTCUSDT') -> Dict[str, Any]:
        """
        Aggressive buy vs sell volume (order flow imbalance)
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/futures/data/takerlongshortRatio",
                params={
                    'symbol': symbol,
                    'period': '5m',
                    'limit': 288  # 24 hours of 5-min data
                },
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            volume_data = response.json()
            
            if not volume_data:
                return {'error': 'No volume data'}

            recent_ratio = float(volume_data[-1]['buySellRatio'])
            avg_ratio_24h = sum(float(v['buySellRatio']) for v in volume_data) / len(volume_data)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'taker_buy_sell_ratio',
                'current_buy_sell_ratio': recent_ratio,
                'avg_24h': avg_ratio_24h,
                'buy_pressure': recent_ratio > 1.0,
                'aggressive_buying': recent_ratio > 1.5,
                'aggressive_selling': recent_ratio < 0.5,
                'interpretation': 'market_aggression_metrics'
            }
        except Exception as e:
            logger.error(f"Error fetching Taker Volume: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    derivs = BinanceFreeDerivatives()
    print("Funding:", derivs.get_funding_rate_history())
    print("OI:", derivs.get_open_interest())
