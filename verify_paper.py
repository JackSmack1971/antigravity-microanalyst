from src.microanalyst.simulation.paper_exchange import PaperExchange
from src.microanalyst.simulation.portfolio_manager import PortfolioManager
import json

def verify_paper_trading():
    print("--- Starting Paper Trading Verification ---")
    
    # 1. Init Exchange
    exchange = PaperExchange(initial_balance=10000.0)
    user_id = "test_user_001"
    
    print(f"Initial Balance: {exchange.get_balance(user_id)}")
    
    # 2. Place Market Buy
    # Buy 0.1 BTC at current market price (simulated fill)
    print("\n--- Placing Market Buy ---")
    order = exchange.create_order(user_id, "BTCUSDT", "BUY", 0.1, "MARKET")
    
    # 3. Simulate Fill at $95,000
    market_price = 95000.0
    exchange.process_fills(current_price=market_price)
    
    print(f"Post-Buy Balance: {exchange.get_balance(user_id)}")
    
    # 4. Check Portfolio
    pm = PortfolioManager(exchange)
    summary = pm.get_portfolio_summary(user_id, market_price)
    print("\n[Portfolio Summary (After Buy)]")
    print(json.dumps(summary, indent=2))
    
    # Assertions
    assert summary["btc_held"] == 0.1, "BTC Balance incorrect"
    assert summary["available_cash"] == 10000.0 - (0.1 * 95000), "Cash Balance incorrect"
    
    # 5. Place Limit Sell (Take Profit)
    print("\n--- Placing Limit Sell at $96,000 ---")
    limit_order = exchange.create_order(user_id, "BTCUSDT", "SELL", 0.1, "LIMIT", price=96000.0)
    
    # 6. Simulate Price moving UP to $96,500
    market_price_high = 96500.0
    exchange.process_fills(current_price=market_price_high)
    
    # 7. Check Portfolio
    summary_final = pm.get_portfolio_summary(user_id, market_price_high)
    print("\n[Portfolio Summary (After Limit Sell)]")
    print(json.dumps(summary_final, indent=2))
    
    # Assertions
    # Note: Limit sell at 96000 fills at 96000 in our basic logic (or better, but let's stick to limit price for simplicity or modify exchange logic)
    # The exchange logic implementation:
    # elif order.side == "SELL" and current_price >= order.price: fill_price = order.price (Limit guarantees price)
    
    expected_cash = 10000.0 - (0.1 * 95000) + (0.1 * 96000)
    assert summary_final["available_cash"] == expected_cash, f"Cash incorrect. Got {summary_final['available_cash']}, expected {expected_cash}"
    assert summary_final["pnl_abs"] == 100.0, "PnL should be $100 profit"
    
    print("\n✅ Verification Successful: Paper Trading Engine matches expected behavior.")

if __name__ == "__main__":
    verify_paper_trading()
