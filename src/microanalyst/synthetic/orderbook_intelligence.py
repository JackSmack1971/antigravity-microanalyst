# src/microanalyst/synthetic/orderbook_intelligence.py
import asyncio
import websockets
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class OrderBookIntelligence:
    """
    Derive institutional-grade order book analytics from free data streams.
    Supports automatic fallback for geo-restricted environments.
    """
    
    # Global typically faster, US specific for compliance/access
    ENDPOINTS = [
        "wss://stream.binance.com:9443/ws",
        "wss://stream.binance.us:9443/ws"
    ]

    def __init__(self):
        self.orderbook = {'bids': [], 'asks': []}
        self.depth_snapshots: List[Dict] = []
        self._running = False
        self._current_endpoint_idx = 0

    async def stream_orderbook(self, symbol='btcusdt', duration_seconds=10):
        """
        Connect to Binance WebSocket and yield metrics.
        Args:
            symbol: Trading pair (e.g., 'btcusdt')
            duration_seconds: How long to stream for (0 = infinite)
        """
        self._running = True
        start_time = datetime.now()
        
        while self._running:
            url = f"{self.ENDPOINTS[self._current_endpoint_idx]}/{symbol}@depth20@100ms"
            logger.info(f"Connecting to OrderBook Stream: {url}")
            
            try:
                async with websockets.connect(url) as ws:
                    logger.info("WebSocket Connected.")
                    async for message in ws:
                        if duration_seconds > 0 and (datetime.now() - start_time).total_seconds() > duration_seconds:
                            self._running = False
                            return

                        data = json.loads(message)
                        self.orderbook = {
                            'bids': [(float(p), float(q)) for p, q in data['bids']],
                            'asks': [(float(p), float(q)) for p, q in data['asks']]
                        }
                        
                        metrics = self.calculate_depth_metrics()
                        
                        # Store snapshot for heatmap
                        self.depth_snapshots.append({
                            'timestamp': datetime.now(),
                            'metrics': self.orderbook # Store raw book for heatmap aggregation
                        })
                        # Limit memory
                        if len(self.depth_snapshots) > 600: # ~1 min of 100ms updates
                            self.depth_snapshots.pop(0)

                        yield metrics
                        
            except (websockets.exceptions.ConnectionClosed, Exception) as e:
                logger.error(f"WebSocket error on {self.ENDPOINTS[self._current_endpoint_idx]}: {e}")
                # Switch endpoint
                self._current_endpoint_idx = (self._current_endpoint_idx + 1) % len(self.ENDPOINTS)
                logger.warning(f"Switching to fallback endpoint: {self.ENDPOINTS[self._current_endpoint_idx]}")
                await asyncio.sleep(1) # Backoff
                if not self._running: break

    def calculate_depth_metrics(self) -> Dict[str, Any]:
        """
        Extract institutional signals from current order book state.
        """
        bids = self.orderbook['bids']
        asks = self.orderbook['asks']
        
        if not bids or not asks:
            return {'error': 'Orderbook empty'}

        # 1. Bid-Ask Imbalance (BAI) - Simple liquidity pressure
        # Top 5 levels usually define immediate direction
        bid_volume_top5 = sum(qty for _, qty in bids[:5])
        ask_volume_top5 = sum(qty for _, qty in asks[:5])
        total_vol = bid_volume_top5 + ask_volume_top5
        bai = (bid_volume_top5 - ask_volume_top5) / total_vol if total_vol > 0 else 0
        
        # 2. Depth Weighted Price (DWP) / VWAP of the book
        # Simulates where a large market order would actually fill
        def weighted_price(orders, depth_target=5.0): # depth in BTC terms
            cumulative_qty = 0.0
            weighted_sum = 0.0
            for price, qty in orders:
                needed = depth_target - cumulative_qty
                if needed <= 0: break
                
                fill_qty = min(qty, needed)
                weighted_sum += price * fill_qty
                cumulative_qty += fill_qty
            
            return weighted_sum / cumulative_qty if cumulative_qty > 0 else 0
        
        bid_dwp = weighted_price(bids)
        ask_dwp = weighted_price(asks)
        
        # 3. Order Book Gradient (Slope)
        # Steeper slope = stronger support/resistance (requires more volume to move price)
        bid_gradient = self._calculate_gradient(bids)
        ask_gradient = self._calculate_gradient(asks)
        
        # 4. Wall Detection
        # A wall is defined as a level with > 3x average liquidity
        all_sizes = [q for _, q in bids] + [q for _, q in asks]
        avg_size = np.mean(all_sizes) if all_sizes else 0
        
        bid_walls = [price for price, qty in bids if qty > 3 * avg_size]
        ask_walls = [price for price, qty in asks if qty > 3 * avg_size]
        
        # 5. Spread
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100
        
        return {
            'timestamp': datetime.now().isoformat(),
            'bid_ask_imbalance': float(bai),
            'interpretation': self._interpret_imbalance(bai),
            
            'depth_weighted_bid': float(bid_dwp),
            'depth_weighted_ask': float(ask_dwp),
            
            'bid_gradient': float(bid_gradient),
            'ask_gradient': float(ask_gradient),
            'support_strength': 'Strong' if abs(bid_gradient) > 0.5 else 'Weak',
            
            'walls': {
                'bid_walls_count': len(bid_walls),
                'ask_walls_count': len(ask_walls),
                'nearest_bid_wall': bid_walls[0] if bid_walls else None,
                'nearest_ask_wall': ask_walls[0] if ask_walls else None
            },
            
            'spread_pct': float(spread_pct),
            'market_liquidity': 'High' if spread_pct < 0.01 else 'Low'
        }
    
    def _calculate_gradient(self, orders):
        """
        Calculate slope of cumulative volume vs price.
        High gradient = Wall. Low gradient = Thin book.
        """
        if len(orders) < 5:
            return 0.0
        
        # Use top 10 levels
        subset = orders[:10]
        prices = np.array([p for p, _ in subset])
        vols = np.array([q for _, q in subset])
        
        # We want slope of Volume relative to % distance from mid
        # But for stability, simple price vs cum_vol slope
        # Normalize price to % from best
        best_price = orders[0][0]
        price_deltas = np.abs((prices - best_price) / best_price) * 100 # % distance
        cum_vols = np.cumsum(vols)
        
        # Slope: How much volume (Y) per % price change (X)
        # Higher slope = More volume needed to move price 1%
        if np.sum(price_deltas) == 0: return 0.0 # Vertical line (same prices)
        
        slope, _ = np.polyfit(price_deltas, cum_vols, 1)
        return slope

    def _interpret_imbalance(self, bai):
        if bai > 0.2: return 'Strong Bullish Pressure (Bid Heavy)'
        if bai > 0.05: return 'Mild Bullish Bias'
        if bai < -0.2: return 'Strong Bearish Pressure (Ask Heavy)'
        if bai < -0.05: return 'Mild Bearish Bias'
        return 'Balanced Book'

    def generate_liquidity_heatmap(self) -> Dict[str, Any]:
        """
        Aggregate stored snapshots to find persistent walls.
        """
        if not self.depth_snapshots:
            return {'error': 'No data for heatmap'}

        price_map = {}
        for snap in self.depth_snapshots:
            # Check bids
            for p, q in snap['metrics']['bids']:
                p_bucket = round(p, -1) # 10s buckets for BTC
                price_map[p_bucket] = price_map.get(p_bucket, 0) + q
            # Check asks
            for p, q in snap['metrics']['asks']:
                p_bucket = round(p, -1)
                price_map[p_bucket] = price_map.get(p_bucket, 0) + q
                
        # Top levels
        sorted_levels = sorted(price_map.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'metric': 'liquidity_heatmap',
            'top_liquidity_clusters': sorted_levels,
            'duration_seconds': len(self.depth_snapshots) * 0.1 # approx
        }

if __name__ == '__main__':
    # Simple test run
    async def run_test():
        obi = OrderBookIntelligence()
        print("Streaming for 5 seconds...")
        async for metric in obi.stream_orderbook(duration_seconds=5):
            print(f"Imbalance: {metric.get('bid_ask_imbalance'):.2f} | Support: {metric.get('support_strength')}")
        
        print("\nHeatmap:")
        print(obi.generate_liquidity_heatmap())

    asyncio.run(run_test())
