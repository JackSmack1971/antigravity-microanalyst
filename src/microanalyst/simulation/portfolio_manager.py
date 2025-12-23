from typing import Dict
from loguru import logger
from .paper_exchange import PaperExchange

class PortfolioManager:
    """
    Tracks and analyzes portfolio performance for simulated users.
    Connects `PaperExchange` to Persistence.
    """
    def __init__(self, exchange: PaperExchange):
        self.exchange = exchange

    def get_portfolio_summary(self, user_id: str, current_price: float) -> Dict:
        """
        Calculate Realized and Unrealized PnL.
        """
        bal = self.exchange.get_balance(user_id)
        cash = bal.get("USDT", 0.0)
        btc = bal.get("BTC", 0.0)
        
        # Calculate Total Equity
        btc_value = btc * current_price
        total_equity = cash + btc_value
        
        # Determine PnL (assuming starting balance was fixed at 10k for now)
        # In a real system, we'd query `persistence` for initial deposit.
        initial_balance = 10000.0 
        total_pnl = total_equity - initial_balance
        pnl_pct = (total_pnl / initial_balance) * 100
        
        return {
            "user_id": user_id,
            "total_equity": round(total_equity, 2),
            "available_cash": round(cash, 2),
            "btc_held": round(btc, 6),
            "btc_value": round(btc_value, 2),
            "pnl_abs": round(total_pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "current_price": current_price
        }

    def log_state_to_db(self, db_manager, user_id: str, current_price: float):
        """
        Persists the current paper portfolio state to the SQLite database.
        
        This method acts as a bridge between the local simulation state and
        the institutional-grade persistence layer, ensuring that trading
        history and equity curves are not lost on application reload.
        
        Args:
            db_manager: The DatabaseManager instance for SQLite interaction.
            user_id: The unique identifier for the user session.
            current_price: The latest market price for mark-to-market valuation.
        """
        summary = self.get_portfolio_summary(user_id, current_price)
        try:
            db_manager.log_paper_portfolio(user_id, summary)
            logger.info(f"[PortfolioManager] Snapshot persisted to DB for {user_id}")
        except Exception as e:
            logger.error(f"[PortfolioManager] Failed to persist snapshot: {e}")
            # Fallback to print
            print(f"[PortfolioManager] Snapshot logged (not persisted): {summary}")
