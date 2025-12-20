# src/microanalyst/synthetic/onchain.py
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class SyntheticOnChainMetrics:
    """
    Construct institutional-grade on-chain metrics from free sources
    """
    
    def __init__(self):
        self.blockchain_api = "https://blockchain.info"
        self.blockchair_api = "https://api.blockchair.com/bitcoin"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self._price_cache: Dict[str, float] = {} # date -> price mapping
    
    def calculate_synthetic_mvrv(self) -> Dict[str, Any]:
        """
        MVRV ≈ Market Cap / Realized Cap
        
        Free Derivation:
        - Market Cap = Current Price × Circulating Supply (CoinGecko free)
        - Realized Cap approximation = Average cost basis of all coins weighted by UTXO age
        - Proxy: Use UTXO age distribution as cost basis estimator
        """
        try:
            # 1. Get current market data (free from CoinGecko)
            logger.info("Fetching market cap from CoinGecko...")
            cg_response = requests.get(
                "https://api.coingecko.com/api/v3/coins/bitcoin",
                params={'localization': 'false', 'tickers': 'false', 'community_data': 'false', 'developer_data': 'false'},
                headers=self.headers,
                timeout=10
            )
            cg_response.raise_for_status()
            cg_data = cg_response.json()
            
            market_cap = cg_data['market_data']['market_cap']['usd']
            current_price = cg_data['market_data']['current_price']['usd']
            
            try:
                logger.info("Fetching UTXO data from Blockchair (with headers)...")
                bc_response = requests.get(
                    f"{self.blockchair_api}/outputs",
                    params={'q': 'is_spent(false)', 'limit': 100},
                    headers=self.headers,
                    timeout=10
                )
                bc_response.raise_for_status()
                bc_data = bc_response.json()
            except Exception as bc_err:
                logger.warning(f"Blockchair failed ({bc_err}), attempting Blockchain.info fallback...")
                return self._calculate_mvrv_via_blockchain_info(market_cap, current_price)
            
            # Weight coins by age and estimated cost basis
            total_realized_value = 0
            total_btc_value = 0
            
            # If no actual UTXO data returned or API Error
            if 'data' not in bc_data or not bc_data['data']:
                logger.warning("Empty UTXO data from Blockchair, using fallback estimation")
                return self._fallback_mvrv_estimate(market_cap, current_price)

            for utxo in bc_data['data']:
                # utxo['time'] is likely a string or timestamp depending on API version
                # Blockchair UTC time format: "2023-11-20 14:30:00"
                if isinstance(utxo['time'], str):
                    utxo_time = datetime.strptime(utxo['time'], "%Y-%m-%d %H:%M:%S")
                else:
                    utxo_time = datetime.fromtimestamp(utxo['time'])
                    
                age_days = (datetime.now() - utxo_time).days
                
                # Use historical price proxy (exponential decay assumption for cost basis)
                # realized_price = price_at_creation
                # Here we use a simpler model: cost_basis = current_price * decay_factor
                # A more accurate model would use a lookup table of monthly prices
                # For this synthetic version, we use age-based discounting
                estimated_cost_basis = current_price * (0.5 ** (age_days / 1460))  # Half value every 4 years (cycle length)
                
                # utxo['value'] is in Satoshis
                btc_amount = utxo['value'] / 100_000_000
                total_realized_value += btc_amount * estimated_cost_basis
                total_btc_value += btc_amount
            
            # 3. Calculate synthetic MVRV
            if total_btc_value == 0:
                 return self._fallback_mvrv_estimate(market_cap, current_price)
                 
            realized_price_estimate = total_realized_value / total_btc_value
            synthetic_mvrv = current_price / realized_price_estimate
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'synthetic_mvrv',
                'value': float(synthetic_mvrv),
                'market_cap': market_cap,
                'realized_price_estimate': float(realized_price_estimate),
                'confidence': self._calculate_mvrv_confidence(bc_data),
                'method': 'utxo_age_weighted_decay'
            }
            
        except Exception as e:
            logger.error(f"Error calculating synthetic MVRV: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }

    def _calculate_mvrv_via_blockchain_info(self, market_cap, current_price) -> Dict[str, Any]:
        """
        Blockchain.info gives raw block data which we can use to estimate realized value.
        For simplicity in this synthetic version, we'll use the 'total btc sent' 
        24h vs market cap as a velocity-based MVRV proxy.
        """
        try:
            # 1. Get 24h stats
            response = requests.get("https://api.blockchain.info/stats", timeout=5)
            response.raise_for_status()
            stats = response.json()
            
            # This is a different mathematical model: realized_cap ≈ coins_moved_weighted
            trade_vol_btc = stats['trade_volume_btc']
            estimated_velocity_mvrv = (current_price * trade_vol_btc) / (market_cap / 365) # Pure proxy
            
            # Normalize to standard MVRV ranges (1.0 - 3.5)
            normalized_val = max(1.1, min(3.8, estimated_velocity_mvrv / 100))
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'synthetic_mvrv',
                'value': float(normalized_val),
                'method': 'blockchain_info_velocity_proxy',
                'confidence': 0.45,
                'note': 'Using velocity proxy due to UTXO API restrictions'
            }
        except Exception as e:
            logger.error(f"Blockchain.info fallback failed: {e}")
            return self._fallback_mvrv_estimate(market_cap, current_price)
        """Simple fallback if full UTXO data is unavailable"""
        # Historical average MVRV for BTC is ~1.5 - 2.0
        # This is a safe 'placeholder' that signals failure but maintains structure
        return {
            'timestamp': datetime.now().isoformat(),
            'metric': 'synthetic_mvrv',
            'value': 1.85, 
            'note': 'fallback_estimate_used',
            'confidence': 0.1
        }

    def _calculate_mvrv_confidence(self, bc_data: Dict) -> float:
        """
        Confidence score based on UTXO sample size relative to context
        """
        try:
            sample_size = len(bc_data.get('data', []))
            # Blockchair often provides total count in context
            total_utxos = bc_data.get('context', {}).get('total_rows', 1)
            
            sample_ratio = sample_size / total_utxos
            
            # Exponential scoring for sample confidence
            # 100 UTXOs is tiny but better than nothing
            if sample_size >= 100:
                return 0.65
            elif sample_size > 0:
                return 0.35
            return 0.0
        except Exception:
            return 0.2
            
    def calculate_synthetic_exchange_netflow(self) -> Dict[str, Any]:
        """
        Exchange Netflow = Inflows - Outflows
        
        Free Derivation:
        - Track known exchange addresses (public lists available)
        - Monitor blockchain.com API for transactions
        - Calculate rolling 24h netflow
        """
        try:
            logger.info("Calculating synthetic exchange netflow...")
            # 1. Load exchange addresses (static list for top exchanges)
            exchange_addresses = self._load_exchange_addresses()
            
            # 2. Query blockchain.com for recent transactions (limited sample for demo)
            netflow_24h = 0
            count = 0
            
            # Sample only top 3 to avoid rate limits/lag in this demo
            for address in exchange_addresses[:3]:
                logger.info(f"Checking address {address[:8]}...")
                try:
                    txs_res = requests.get(
                        f"{self.blockchain_api}/rawaddr/{address}",
                        params={'limit': 10},
                        headers=self.headers,
                        timeout=10
                    )
                    txs_res.raise_for_status()
                    txs_data = txs_res.json()
                    
                    for tx in txs_data.get('txs', []):
                        # Calculate if inflow or outflow
                        inflow_val = sum(out['value'] for out in tx['out'] if out.get('addr') == address)
                        outflow_val = sum(inp['prev_out']['value'] for inp in tx['inputs'] if inp.get('prev_out', {}).get('addr') == address)
                        
                        netflow_24h += (inflow_val - outflow_val)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to fetch txs for {address}: {e}")
            
            # Convert satoshis to BTC
            netflow_btc = netflow_24h / 1e8
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'synthetic_exchange_netflow_24h',
                'value': float(netflow_btc),
                'interpretation': 'positive = accumulation, negative = distribution',
                'confidence': 0.75 if count > 0 else 0.0,
                'sample_size': count,
                'method': 'exchange_address_tracking'
            }
        except Exception as e:
            logger.error(f"Error calculating netflow: {e}")
            return {'error': str(e)}

    def calculate_synthetic_sopr(self) -> Dict[str, Any]:
        """
        SOPR = Average Selling Price / Average Buying Price
        
        Free Derivation:
        - Monitor spent UTXOs (blockchair)
        - Calculate profit ratio from creation price to spent price
        """
        try:
            logger.info("Calculating synthetic SOPR from spent UTXOs...")
            spent_utxos_res = requests.get(
                f"{self.blockchair_api}/outputs",
                params={'q': 'is_spent(true)', 'limit': 10}, # Small sample for efficiency
                headers=self.headers,
                timeout=10
            )
            spent_utxos_res.raise_for_status()
            spent_utxos = spent_utxos_res.json()
            
            total_profit_ratio = 0
            count = 0
            
            for utxo in spent_utxos.get('data', []):
                # We need historical prices. Blockchair uses block_id or time.
                # Let's use time if available.
                creation_time_str = utxo.get('time') # e.g. "2023-11-20 14:30:00"
                # If time not in data, we might need block_id lookup, but let's assume it is.
                
                if creation_time_str:
                    creation_dt = datetime.strptime(creation_time_str, "%Y-%m-%d %H:%M:%S")
                    creation_price = self._get_historical_price(creation_dt)
                    
                    # Spent time is contemporary (or use spending_time if provided)
                    spent_price = self._get_historical_price(datetime.now())
                    
                    if creation_price and spent_price:
                        profit_ratio = spent_price / creation_price
                        total_profit_ratio += profit_ratio
                        count += 1
            
            if count == 0:
                return self._fallback_sopr_estimate()

            sopr = total_profit_ratio / count if count > 0 else 1.0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'synthetic_sopr',
                'value': float(sopr),
                'interpretation': '>1 = profit-taking, <1 = loss realization',
                'confidence': 0.70 if count > 0 else 0.0,
                'sample_size': count,
                'method': 'spent_utxo_analysis'
            }
        except Exception as e:
            logger.error(f"Error calculating SOPR: {e}")
            return self._fallback_sopr_estimate()

    def _fallback_sopr_estimate(self) -> Dict[str, Any]:
        """Simple fallback for SOPR"""
        return {
            'timestamp': datetime.now().isoformat(),
            'metric': 'synthetic_sopr',
            'value': 1.02, # Neutral/Mild profit taking
            'note': 'fallback_estimate_used',
            'confidence': 0.1
        }

    def _get_historical_price(self, dt: datetime) -> Optional[float]:
        """
        Approximate price at given time using CoinGecko free historical API.
        Includes local caching to prevent redundancy.
        """
        date_str = dt.strftime('%d-%m-%Y')
        if date_str in self._price_cache:
            return self._price_cache[date_str]
        
        try:
            logger.info(f"Fetching historical price for {date_str}...")
            # CoinGecko free historical (no auth required)
            response = requests.get(
                f"https://api.coingecko.com/api/v3/coins/bitcoin/history",
                params={'date': date_str, 'localization': 'false'},
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            price = data.get('market_data', {}).get('current_price', {}).get('usd')
            if price:
                self._price_cache[date_str] = price
            return price
        except Exception as e:
            logger.warning(f"Failed to fetch historical price for {date_str}: {e}")
            return None

    def _load_exchange_addresses(self) -> List[str]:
        """
        Public exchange addresses from community sources
        """
        return [
            "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ",  # Bitfinex
            "3D2oetdNuZUqQHPJmcMDDHYoqkyNVsFk9r",  # Binance
            "16ftSEQ4ctQFDtVZiUBz2E2ktr8AqcEz3U",  # Binance 2
            "1LdRBaRefCnsuCtopadRbcAeEzpkuxSshX",  # Huobi
        ]

    def calculate_whale_concentration(self) -> Dict[str, Any]:
        """
        Estimate whale concentration from blockchair address list
        """
        try:
            logger.info("Fetching rich list sample from Blockchair...")
            bc_response = requests.get(
                f"{self.blockchair_api}/addresses",
                params={'limit': 50, 's': 'balance(desc)'},
                timeout=10
            )
            bc_response.raise_for_status()
            data = bc_response.json()
            
            top_50_balance = sum(addr['balance'] for addr in data['data']) / 100_000_000
            
            return {
                'metric': 'whale_concentration_top_50',
                'value': top_50_balance,
                'unit': 'BTC',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    onchain = SyntheticOnChainMetrics()
    print(onchain.calculate_synthetic_mvrv())
