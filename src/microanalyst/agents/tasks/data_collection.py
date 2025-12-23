# src/microanalyst/agents/tasks/data_collection.py

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any

from src.microanalyst.synthetic.onchain import SyntheticOnChainMetrics
from src.microanalyst.synthetic.exchange_proxies import ExchangeProxyMetrics
from src.microanalyst.providers.binance_derivatives import BinanceFreeDerivatives
from src.microanalyst.providers.binance_spot import BinanceSpotProvider
from src.microanalyst.synthetic.sentiment import FreeSentimentAggregator
from src.microanalyst.intelligence.risk_manager import RiskManager
from src.microanalyst.outputs.agent_ready import AgentDatasetBuilder

logger = logging.getLogger(__name__)

async def handle_data_collection(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for the DATA_COLLECTOR role.
    Fetches price, derivatives, and synthetic metrics.
    """
    logger.info("Executing DATA_COLLECTOR task...")
    
    # 1. Fetch Price Data (Try Live, Fallback to Simulation)
    df_price = pd.DataFrame()
    fallback_active = False
    fallback_reason = None
    
    try:
        # Attempt Live Fetch
        spot_provider = BinanceSpotProvider()
        lookback = inputs.get('lookback_days', 30)
        # Approx bars for 4h intervals: 30 days * 6 = 180 bars
        limit = min(lookback * 6, 1000)
        
        logger.info(f"Fetching Live OHLCV from Binance (limit={limit})...")
        df_price = spot_provider.fetch_ohlcv(symbol="BTCUSDT", interval="4h", limit=limit)
        
        if df_price.empty:
            raise ValueError("Empty dataframe returned from spot provider")
    
    except Exception as e:
        logger.warning(f"Live Data Fetch Failed ({e}). Falling back to Simulation.")
        fallback_active = True
        fallback_reason = str(e)
        
        # Fallback Simulation
        dates = pd.date_range(datetime.now().date() - pd.Timedelta(days=30), periods=200, freq='4h')
        np.random.seed(42)
        prices = 100000 * (1 + np.random.randn(200).cumsum() * 0.01)
        
        df_price = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(100, 1000, 200)
        }, index=dates)

    # 2. Derivatives Data (Try Live, Fallback to None/Sim)
    derivatives_data = {}
    if 'derivatives' in inputs.get('sources', []):
         try: 
             deriv_provider = BinanceFreeDerivatives()
             funding = deriv_provider.get_funding_rate_history()
             oi = deriv_provider.get_open_interest()
             
             derivatives_data = {
                 'funding_rates': funding,
                 'open_interest': oi
             }
         except Exception as e:
             logger.warning(f"Derivatives Fetch Failed: {e}")
             derivatives_data = {'error': 'live_fetch_failed'}

    # 3. Build Agent Dataset
    builder = AgentDatasetBuilder()
    
    sentiment_data = None
    if 'sentiment' in inputs.get('sources', []):
        agg = FreeSentimentAggregator()
        sentiment_data = agg.aggregate_sentiment()
        
    risk_data = None
    if 'risk' in inputs.get('sources', []):
         rm = RiskManager()
         try:
             risk_data = rm.calculate_value_at_risk(df_price)
         except Exception as e:
             logger.warning(f"Risk calculation failed: {e}")
             risk_data = {}

    # Synthetic Metrics (OnChain / Proxies)
    synthetic_metrics = {}
    if 'synthetic' in inputs.get('sources', []):
        try:
            onchain = SyntheticOnChainMetrics()
            mvrv = onchain.calculate_synthetic_mvrv()
            
            proxies = ExchangeProxyMetrics()
            flow_delta = proxies.derive_order_flow_delta("BTCUSDT")
            
            synthetic_metrics = {
                'mvrv': mvrv,
                'order_flow_delta': flow_delta
            }
        except Exception as e:
            logger.warning(f"Synthetic metrics fetch failed: {e}")

    dataset = builder.build_feature_dataset(
        df_price=df_price,
        sentiment_data=sentiment_data,
        risk_data=risk_data,
        derivatives_data=derivatives_data
    )
    dataset['synthetic_metrics'] = synthetic_metrics
    
    # Pass the raw DF as well for downstream analysts who need history
    df_price.index = df_price.index.astype(str)
    dataset['raw_price_history'] = df_price.to_dict()
    
    # Improved Metadata Signaling
    dataset['fallback_active'] = fallback_active
    dataset['fallback_reason'] = fallback_reason
    dataset['meta'] = {
        'source': 'live' if not fallback_active else 'simulation',
        'provider': 'BinanceSpot' if not fallback_active else 'SyntheticPriceEngine'
    }
    
    return dataset
