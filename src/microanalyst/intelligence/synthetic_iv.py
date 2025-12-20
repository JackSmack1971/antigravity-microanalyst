import pandas as pd
import numpy as np
from arch import arch_model
import logging

logger = logging.getLogger(__name__)

class SyntheticVolatilityEngine:
    """
    Calculates various volatility metrics, including GARCH(1,1) forecasts,
    to serve as a proxy for Implied Volatility (IV).
    """

    def calculate_metrics(self, price_df: pd.DataFrame) -> dict:
        """
        Input: DataFrame with 'date' and 'close' columns.
        Output: Dictionary with vol metrics.
        """
        if price_df.empty or len(price_df) < 30:
            logger.warning("Insufficient data for volatility calculation.")
            return {}

        df = price_df.sort_values("date").reset_index(drop=True)
        # Calculate Log Returns
        df['log_ret'] = np.log(df['close'] / df['close'].shift(1))
        df = df.dropna()

        metrics = {}

        # 1. Realized Volatility (30d) - Annualized
        # Std Dev of Returns * sqrt(365)
        realized_vol = df['log_ret'].tail(30).std() * np.sqrt(365) * 100
        metrics['realized_vol_30d'] = round(realized_vol, 2)

        # 2. GARCH(1,1) Volatility Forecast
        try:
            # Rescale returns to percentage for better numerical stability in optimization
            returns_pct = df['log_ret'] * 100
            
            # GARCH(1,1) model
            model = arch_model(returns_pct, vol='Garch', p=1, q=1, mean='Zero', dist='Normal')
            res = model.fit(disp='off', show_warning=False)
            
            # Forecast next 30 days variance
            forecast = res.forecast(horizon=30)
            
            # Get the variance forecast
            # variance over next 1 day
            next_day_var = forecast.variance.values[-1, 0]
            
            # Convert to Annualized Volatility
            # Vol = sqrt(variance) -- this is daily vol
            # Annualized = daily_vol * sqrt(365)
            # Since inputs were scaled by 100, the output is already in % terms roughly, 
            # but let's be precise: sqrt(var) is % daily change.
            garch_vol_daily = np.sqrt(next_day_var)
            garch_vol_annual = garch_vol_daily * np.sqrt(365)
            
            metrics['synthetic_iv_garch'] = round(garch_vol_annual, 2)
            
        except Exception as e:
            logger.error(f"GARCH calculation failed: {e}")
            metrics['synthetic_iv_garch'] = None

        return metrics
