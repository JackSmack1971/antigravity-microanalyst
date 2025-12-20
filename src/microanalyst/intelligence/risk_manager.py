import numpy as np
import pandas as pd
import logging
from typing import Dict, Any
from src.microanalyst.core.persistence import DatabaseManager

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Quantifies downside risk using historical data.
    """
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager if db_manager else DatabaseManager()

    def calculate_volatility(self, prices: pd.Series, window: int = 30) -> float:
        """
        Calculates annualized volatility based on log returns.
        Assumes daily data inputs (default window 30 days).
        """
        if len(prices) < 2:
            return 0.0
        
        log_returns = np.log(prices / prices.shift(1))
        vol = log_returns.std() * np.sqrt(365) # Annualized
        return float(vol)

    def calculate_var(self, prices: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculates Historical Value at Risk (VaR).
        Returns the percentage drop expected with (confidence) probability.
        """
        if len(prices) < 30:
            return 0.0
            
        returns = prices.pct_change().dropna()
        var = np.percentile(returns, (1 - confidence) * 100)
        return float(abs(var)) # Return as positive percentage (risk magnitude)

    def get_risk_report(self, interval: str = "1d") -> Dict[str, Any]:
        """
        Generates a comprehensive risk report based on recent history.
        """
        try:
            df = self.db.get_price_history(limit=90, interval=interval)
            
            if df.empty:
                return {"error": "Insufficient Data", "score": 0}

            prices = df["close"]
            current_price = prices.iloc[-1]
            
            # Metrics
            volatility = self.calculate_volatility(prices)
            var_95 = self.calculate_var(prices, 0.95)
            var_99 = self.calculate_var(prices, 0.99)
            
            # Max Drawdown (Last 90 periods)
            rolling_max = prices.cummax()
            drawdown = (prices - rolling_max) / rolling_max
            max_drawdown = abs(drawdown.min())

            # Risk Score Calculation (0-100, where 100 is Extreme High Risk)
            # Heuristic: Base on Volatility and Drawdown proximity
            # If Vol > 80% or Drawdown > 20%, Risk is High.
            
            # Simple normalization for crypto
            risk_score = min(100, (volatility * 50) + (max_drawdown * 100))
            
            return {
                "current_price": current_price,
                "volatility_annualized": round(volatility, 4),
                "var_95_percent": round(var_95, 4),
                "var_99_percent": round(var_99, 4),
                "max_drawdown_90p": round(max_drawdown, 4),
                "risk_score": round(risk_score, 1),
                "interval": interval
            }
            
        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            return {"error": str(e), "score": 0}
