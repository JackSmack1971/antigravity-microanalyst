from typing import Dict, Any, Optional
from .paper_exchange import PaperExchange, Order

class ExecutionRouter:
    """
    Translates Intelligence Signals (Thesis) into Executable Orders.
    Reference: ADR-003 Agent-Ready Data.
    """
    def __init__(self, exchange: PaperExchange):
        self.exchange = exchange
        self.base_allocation_pct = 0.10  # 10% per trade base

    def execute_signal(self, user_id: str, thesis: Dict[str, Any], current_price: float) -> Optional[Order]:
        """
        Parses a Thesis dictionary and places orders if Actionable.
        Thesis expected format:
        {
            "decision": "BUY" | "SELL" | "HOLD",
            "confidence": 0.0-1.0,
            "allocation_pct": 0-100 (Optional override),
            "reasoning": "..."
        }
        """
        decision = thesis.get("decision", "HOLD").upper()
        confidence = thesis.get("confidence", 0.0)
        
        if decision == "HOLD":
            return None

        # Determine Sizing
        # Use thesis allocation if provided, else calc based on confidence
        if "allocation_pct" in thesis and thesis["allocation_pct"] is not None:
            allocation_pct = float(thesis["allocation_pct"]) / 100.0
        else:
            # Dynamic Sizing logic
            multiplier = 1.0
            if confidence > 0.8:
                multiplier = 1.5
            elif confidence < 0.6:
                multiplier = 0.5
            
            allocation_pct = self.base_allocation_pct * multiplier

        # Cap at 100% (sanity check)
        allocation_pct = min(allocation_pct, 1.0)
        
        balance = self.exchange.get_balance(user_id)
        
        order = None
        if decision == "BUY":
            cash_available = balance.get("USDT", 0.0)
            target_amount = cash_available * allocation_pct
            
            if target_amount < 10.0: # Minimum order size
                print(f"[ExecutionRouter] Trade ignored: Insufficient size ${target_amount:.2f}")
                return None
                
            qty = target_amount / current_price
            # Truncate to 6 decimals
            qty = round(qty, 6)
            
            print(f"[ExecutionRouter] SIGNAL: BUY {qty} BTC @ ${current_price} (Conf: {confidence}, Alloc: {allocation_pct:.0%})")
            order = self.exchange.create_order(user_id, "BTCUSDT", "BUY", qty, "MARKET")
            
        elif decision == "SELL":
            # For Sell, we usually sell entire position or a percentage of holdings
            # Simplified: Sell Allocation % of Holdings
            current_holdings = balance.get("BTC", 0.0)
            
            if current_holdings < 0.0001:
                print("[ExecutionRouter] Trade ignored: No position to sell.")
                return None
                
            qty = current_holdings * allocation_pct
            qty = round(qty, 6)
            
            print(f"[ExecutionRouter] SIGNAL: SELL {qty} BTC @ ${current_price} (Conf: {confidence}, Alloc: {allocation_pct:.0%})")
            order = self.exchange.create_order(user_id, "BTCUSDT", "SELL", qty, "MARKET")
            
        return order
