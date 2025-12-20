import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class AdvancedRiskManager:
    """
    Institutional-grade risk analytics:
    - Value at Risk (VaR)
    - Scenario Stress Testing
    - Dynamic Position Sizing (Kelly)
    """

    def calculate_value_at_risk(self, df_price: pd.DataFrame, portfolio_value: float = 100000.0, confidence: float = 0.95, days: int = 1) -> Dict[str, float]:
        """
        Calculate Historical Simulation VaR.
        
        Args:
            df_price: DataFrame with 'close' prices.
            portfolio_value: Current portfolio size in USD.
            confidence: Confidence level (e.g., 0.95 for 95%).
            days: Time horizon in days.
            
        Returns:
            Dict containing VaR amount and percentage.
        """
        if df_price.empty or len(df_price) < 30:
            logger.warning("Insufficient data for VaR calculation")
            return {"var_amount": 0.0, "var_pct": 0.0}

        try:
            # Calculate daily returns
            returns = df_price['close'].pct_change().dropna()
            
            # Historical Simulation: Find the percentile cutoff
            # For 95% confidence, we look at the 5th percentile of worst returns
            percentile = (1 - confidence) * 100
            cutoff_return = np.percentile(returns, percentile)
            
            # Scale for time horizon (Square root of time rule)
            scaled_return = cutoff_return * np.sqrt(days)
            
            var_amount = abs(portfolio_value * scaled_return)
            
            return {
                "var_amount": float(f"{var_amount:.2f}"),
                "var_pct": float(f"{abs(scaled_return)*100:.2f}"),
                "confidence_level": confidence,
                "horizon_days": days
            }
        except Exception as e:
            logger.error(f"VaR calc failed: {e}")
            return {"var_amount": 0.0, "var_pct": 0.0}

    def stress_test_scenarios(self, portfolio_value: float, df_price: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Simulate impact of extreme market events.
        """
        scenarios = [
            {
                "name": "Flash Crash",
                "description": "30% drop in 4 hours",
                "shock_pct": -0.30
            },
            {
                "name": "Regulatory FUD",
                "description": "15% drop over 24h",
                "shock_pct": -0.15
            },
            {
                "name": "Exchange Outage",
                "description": "Liquidity dry up, spreads widen (simulated as 5% slippage loss on total portfolio)",
                "shock_pct": -0.05
            }
        ]
        
        results = []
        for s in scenarios:
            loss = portfolio_value * s['shock_pct']
            remaining = portfolio_value + loss
            results.append({
                "scenario": s['name'],
                "projected_loss": float(f"{abs(loss):.2f}"),
                "remaining_equity": float(f"{remaining:.2f}"),
                "impact_severity": "Critical" if s['shock_pct'] <= -0.15 else "Moderate"
            })
            
        return results

    def optimal_position_sizing(self, signal_confidence: float, volatility_annualized: float, account_size: float, max_risk_pct: float = 0.02) -> Dict[str, Any]:
        """
        Calculate position size using a modified Kelly Criterion or Volatility Targeting.
        
        Args:
            signal_confidence: 0.0 to 1.0 (Probability of win proxy)
            volatility_annualized: Annualized volatility (e.g. 0.80 for 80%)
            account_size: Total equity
            max_risk_pct: Max account equity to risk per trade (Stop Loss risk)
            
        Returns:
            Recommended position size and leverage.
        """
        # Simplified Kelly: Size % = Confidence * Scale_Factor / Volatility
        # This is a heuristic: Higher confidence -> Size Up. Higher Vol -> Size Down.
        
        try:
            # Base sizing: Target 20% annualized volatility exposure
            target_vol = 0.20
            
            # Volatility Scalar
            if volatility_annualized > 0:
                vol_scalar = target_vol / volatility_annualized
            else:
                vol_scalar = 0.5 # Safe default
                
            # Confidence Scalar
            # If confidence < 0.5 (random guess), size should be 0
            if signal_confidence < 0.5:
                return {"size_usd": 0.0, "leverage": 0.0, "reason": "Low confidence"}
                
            conf_scalar = (signal_confidence - 0.5) * 2 # Map 0.5-1.0 to 0.0-1.0
            
            # Raw Allocation %
            raw_alloc_pct = vol_scalar * conf_scalar
            
            # Hard Limit: Cap at 50% of account (or max_risk logic)
            # Let's say we never want to risk more than max_risk_pct of equity on a Stop Loss.
            # Assuming a standard Stop Loss of 5%.
            # Position * 0.05 = Account * 0.02
            # Position = (Account * 0.02) / 0.05 = Account * 0.4
            
            assumed_stop_loss_dist = 0.05 # 5% move against
            max_position_size = (account_size * max_risk_pct) / assumed_stop_loss_dist
            
            # Proposed size
            proposed_size = account_size * raw_alloc_pct
            
            # Final Check
            final_size = min(proposed_size, max_position_size)
            final_size = max(final_size, 0.0)
            
            return {
                "size_usd": float(f"{final_size:.2f}"),
                "pct_of_equity": float(f"{(final_size/account_size)*100:.2f}"),
                "implied_leverage": float(f"{final_size/account_size:.2f}"),
                "details": f"Vol Scalar: {vol_scalar:.2f}, Conf Scalar: {conf_scalar:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Sizing calculation failed: {e}")
            return {"size_usd": 0.0, "error": str(e)}
