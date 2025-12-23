
import asyncio
from microanalyst.core.persistence import DatabaseManager
from microanalyst.simulation.paper_exchange import PaperExchange
from microanalyst.simulation.portfolio_manager import PortfolioManager
import logging

logging.basicConfig(level=logging.INFO)

async def test_persistence():
    db = DatabaseManager("test_refactor.db")
    exchange = PaperExchange()
    pm = PortfolioManager(exchange)
    
    user_id = "test_user_001"
    current_price = 98000.0
    
    print(f"--- Step 1: Logging state ---")
    pm.log_state_to_db(db, user_id, current_price)
    
    print(f"--- Step 2: Verifying DB ---")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM paper_portfolio WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row:
            print(f"PASS: Found row in DB: {row}")
        else:
            print(f"FAIL: No row found in DB")
            exit(1)

if __name__ == "__main__":
    asyncio.run(test_persistence())
