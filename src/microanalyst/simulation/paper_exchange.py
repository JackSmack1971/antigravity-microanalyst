from typing import Dict, List, Optional
from datetime import datetime
import uuid
from decimal import Decimal
from pydantic import BaseModel, Field

class Order(BaseModel):
    order_id: str
    user_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    order_type: str  # "MARKET" or "LIMIT"
    price: Optional[float] = None  # Limit price
    quantity: float
    status: str = "OPEN"  # OPEN, FILLED, CANCELED
    created_at: datetime
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None

class PaperExchange:
    """
    Simulates a Centralized Exchange (CEX) matching engine.
    Holds state in-memory (balances, orders).
    """
    def __init__(self, initial_balance: float = 10000.0, base_currency: str = "USDT"):
        self.base_currency = base_currency
        # Balances: {user_id: {"USDT": 10000, "BTC": 0}}
        self.balances: Dict[str, Dict[str, float]] = {}
        self.orders: List[Order] = []
        self._initial_balance = initial_balance

    def _init_user(self, user_id: str):
        if user_id not in self.balances:
            self.balances[user_id] = {
                self.base_currency: self._initial_balance,
                "BTC": 0.0
            }

    def get_balance(self, user_id: str) -> Dict[str, float]:
        self._init_user(user_id)
        return self.balances[user_id]

    def create_order(self, user_id: str, symbol: str, side: str, quantity: float, order_type: str = "MARKET", price: float = None) -> Order:
        """
        Place a new order on the paper exchange.
        """
        self._init_user(user_id)
        
        # Validation
        if order_type == "LIMIT" and price is None:
            raise ValueError("Limit orders must have a price")
        
        symbol_base = symbol.replace(self.base_currency, "") # e.g. BTC from BTCUSDT

        # Check funds (Simple Check, ignoring fees for now)
        bal = self.balances[user_id]
        if side == "BUY":
            cost = quantity * (price if price else 0) # For market we check at fill time usually, but here we can't.
            # For Simulation, we'll allow market buys if they have ANY cash, but realistically we need a price.
            # We will process validation at fill time for Market orders or assume current price if provided externally?
            # Better: This method creates the order, validation happens in matching engine or here if we have price context.
            pass 
        elif side == "SELL":
            if bal.get(symbol_base, 0) < quantity:
                raise ValueError(f"Insufficient {symbol_base} balance")

        order = Order(
            order_id=str(uuid.uuid4()),
            user_id=user_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=price,
            quantity=quantity,
            created_at=datetime.utcnow()
        )
        self.orders.append(order)
        print(f"[PaperExchange] Order Created: {side} {quantity} {symbol} @ {order_type} {price if price else 'MKT'}")
        return order

    def process_fills(self, current_price: float):
        """
        Match open orders against the current market price.
        Call this on every new candle/tick.
        """
        filled_count = 0
        for order in self.orders:
            if order.status != "OPEN":
                continue

            # Matching Logic
            should_fill = False
            fill_price = current_price

            if order.order_type == "MARKET":
                should_fill = True
                fill_price = current_price
            
            elif order.order_type == "LIMIT":
                if order.side == "BUY" and current_price <= order.price:
                    should_fill = True
                    fill_price = order.price # In reality, could be better, but limit guarantees this price
                elif order.side == "SELL" and current_price >= order.price:
                    should_fill = True
                    fill_price = order.price

            if should_fill:
                self._execute_fill(order, fill_price)
                filled_count += 1
        
        if filled_count > 0:
            print(f"[PaperExchange] Filled {filled_count} orders at ${current_price}")

    def _execute_fill(self, order: Order, price: float):
        user_id = order.user_id
        symbol_base = order.symbol.replace(self.base_currency, "")
        cost = order.quantity * price

        bal = self.balances[user_id]
        
        if order.side == "BUY":
            if bal[self.base_currency] >= cost:
                bal[self.base_currency] -= cost
                bal[symbol_base] += order.quantity
                order.status = "FILLED"
                order.filled_at = datetime.utcnow()
                order.filled_price = price
            else:
                print(f"[PaperExchange] Insufficient funds to fill BUY {order.order_id}")
                # Optional: Cancel order or keep trying? For sim, let's keep OPEN or CANCEL.
                # Let's keep OPEN for now.
        
        elif order.side == "SELL":
            if bal[symbol_base] >= order.quantity:
                bal[symbol_base] -= order.quantity
                bal[self.base_currency] += cost
                order.status = "FILLED"
                order.filled_at = datetime.utcnow()
                order.filled_price = price
            else:
                print(f"[PaperExchange] Insufficient asset to fill SELL {order.order_id}")
