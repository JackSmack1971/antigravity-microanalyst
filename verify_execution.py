from src.microanalyst.simulation.paper_exchange import PaperExchange
from src.microanalyst.simulation.execution_router import ExecutionRouter
from src.microanalyst.simulation.portfolio_manager import PortfolioManager
import json

def verify_execution_router():
    print("--- Starting Execution Router Verification ---")
    
    # 1. Setup
    exchange = PaperExchange(initial_balance=50000.0) # $50k account
    router = ExecutionRouter(exchange)
    user_id = "agent_verify_001"
    
    initial_bal = exchange.get_balance(user_id)
    print(f"Initial: {initial_bal}")
    
    # 2. Test Case 1: Strong BUY (High Confidence)
    # 10% base * 1.5 mult = 15% allocation
    # 15% of 50k = $7,500
    thesis_strong_buy = {
        "decision": "BUY",
        "confidence": 0.9,
        "reasoning": "Strong trend alignment."
    }
    
    price = 100000.0
    print("\n--- Executing Strong BUY Signal ---")
    order = router.execute_signal(user_id, thesis_strong_buy, price)
    
    assert order is not None
    assert order.side == "BUY"
    
    # Check sizing
    # Expected: 7500 / 100000 = 0.075 BTC
    expected_qty = (50000.0 * 0.15) / price
    print(f"Order Qty: {order.quantity}, Expected (~): {expected_qty}")
    assert abs(order.quantity - expected_qty) < 0.0001
    
    # Execute on Exchange
    exchange.process_fills(price)
    
    # 3. Test Case 2: Weak SELL (Low Confidence)
    # We now hold ~0.075 BTC.
    # Low confidence (<0.6) = 0.5 mult.
    # 10% base * 0.5 = 5% allocation.
    # Current Holdings = 0.075 BTC.
    # Sell 5% of holdings = 0.075 * 0.05 = 0.00375 BTC
    
    thesis_weak_sell = {
        "decision": "SELL",
        "confidence": 0.4,
        "reasoning": "Minor bearish divergence."
    }
    
    print("\n--- Executing Weak SELL Signal ---")
    order_sell = router.execute_signal(user_id, thesis_weak_sell, price)
    
    assert order_sell is not None
    assert order_sell.side == "SELL"
    
    expected_sell_qty = order.quantity * 0.05
    print(f"Sell Qty: {order_sell.quantity}, Expected: {expected_sell_qty}")
    assert abs(order_sell.quantity - expected_sell_qty) < 0.00001
    
    exchange.process_fills(price)
    
    print("\n✅ Execution Router Logic Verified.")

if __name__ == "__main__":
    verify_execution_router()
