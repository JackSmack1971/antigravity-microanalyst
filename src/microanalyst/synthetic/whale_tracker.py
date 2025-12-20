# src/microanalyst/synthetic/whale_tracker.py
import requests
import logging
from typing import List, Dict, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class WhaleActivityTracker:
    """
    Monitor large wallet movements using free blockchain APIs.
    Focuses on unconfirmed transactions (Mempool) for finding 'intent' before confirmation.
    """
    
    def __init__(self):
        self.blockchain_api = "https://blockchain.info"
        self.whale_addresses = self._load_whale_list()
    
    def detect_whale_movements(self, threshold_btc=100) -> Dict[str, Any]:
        """
        Real-time whale transaction alerts from mempool.
        Args:
            threshold_btc: Minimum transaction size to trigger alert.
        """
        try:
            # Poll mempool for unconfirmed transactions
            # Note: blockchain.info returns a list of latest txs
            response = requests.get(
                f"{self.blockchain_api}/unconfirmed-transactions",
                params={'format': 'json'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            unconfirmed_txs = data.get('txs', [])
            whale_txs = []
            total_whale_vol = 0.0
            
            # Helper to estimate price for USD conversion (mock or quick fetch if needed)
            # For speed, we might pass it in, but here we'll use a rough static or fetch one-off if needed.
            # We'll just return BTC value for now to keep it fast.
            
            for tx in unconfirmed_txs:
                # Calculate total output value (satoshi -> BTC)
                # 'out' contains list of outputs
                outputs = tx.get('out', [])
                total_value_sats = sum(o.get('value', 0) for o in outputs)
                tx_value_btc = total_value_sats / 1e8
                
                if tx_value_btc >= threshold_btc:
                    # Check if involves known whale
                    # Inputs are links to prev outputs, cumbersome to resolve address without parsing script
                    # We check Outputs for known receiving whale addresses
                    involved_whale = None
                    involved_addr = []
                    
                    for o in outputs:
                        addr = o.get('addr')
                        if addr:
                            involved_addr.append(addr)
                            if addr in self.whale_addresses:
                                involved_whale = self.whale_addresses[addr]
                    
                    # Also checking inputs would require previous_out lookup (expensive)
                    # We focus on "Whale Receivers" (Inflow) or just "Large Transfers"
                    
                    whale_txs.append({
                        'hash': tx.get('hash'),
                        'value_btc': float(f"{tx_value_btc:.4f}"),
                        'timestamp': tx.get('time'),
                        'is_known_entity': bool(involved_whale),
                        'entity_name': involved_whale if involved_whale else 'Unknown Whale',
                        'interpretation': self._interpret_tx(tx_value_btc, involved_whale)
                    })
                    total_whale_vol += tx_value_btc

            # Sort by size
            whale_txs.sort(key=lambda x: x['value_btc'], reverse=True)

            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'whale_mempool_activity',
                'whale_transactions_count': len(whale_txs),
                'total_volume_btc': float(f"{total_whale_vol:.4f}"),
                'largest_tx_btc': whale_txs[0]['value_btc'] if whale_txs else 0,
                'transactions': whale_txs[:10], # Top 10
                'alert_level': self._determine_alert_level(total_whale_vol)
            }
            
        except Exception as e:
            logger.error(f"Error checking whale movements: {e}")
            return {'error': str(e)}
    
    def _interpret_tx(self, value, entity):
        if entity:
            if 'Binance' in entity or 'Coinbase' in entity:
                return f"Inflow to Exchange ({entity})"
            return f"Transfer to Known Entity ({entity})"
        
        if value > 1000: return "Mega Whale Movement (>1k BTC)"
        return "Large Transfer"

    def _determine_alert_level(self, volume):
        if volume > 5000: return 'CRITICAL (Massive Movement)'
        if volume > 1000: return 'HIGH'
        if volume > 100: return 'MODERATE'
        return 'LOW'

    def _load_whale_list(self) -> Dict[str, str]:
        """
        Known large addresses (Exchange Cold Wallets, Funds, etc.)
        Source: Bitinfocharts public data
        """
        return {
            "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo": "Binance-Cold",
            "39884E3j6KZj82QH491vrzEjjC7SUb5e4H": "Binance-Cold-2",
            "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ": "Binance-Cold-3",
            "3LyCf26x8X7V8T83Yc2m3Wc8z9Qcj8j6h8": "Binance-US-Cold",
            "1FzWLk9y1pGAa5k3r7e5y6y3e5y6y3e5y6": "Coinbase-Cold-Mock", # Placeholder pattern
            "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmmdrturjdq5nsq4uecf3": "Bitfinex-Cold",
            "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF": "MtGox-Trustee",
            "3D2oetdNuZUqQHPJmcMDDHYoqkyNVsFk9r": "Bitfinex-Cold-2"
        }
