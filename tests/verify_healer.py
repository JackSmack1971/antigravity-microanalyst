import asyncio
import logging
import json
from pathlib import Path
from src.microanalyst.agents.self_healing import SelfHealingEngine, AllSourcesFailedError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HealerVerification")

async def mock_failing_scraper(*args, **kwargs):
    """Simulates a scraper that fails to find an element but returns HTML"""
    # Simulate a scraper that grabs HTML but fails to parse the specific selector
    # In the real engine, the exception would be caught, and the Healer would be passed this HTML
    raise Exception("ElementNotFound: #price-display")

async def main():
    logger.info("Starting Healer Verification...")
    
    # 1. Setup
    engine = SelfHealingEngine()
    
    # Reset config for clean test
    config_path = Path("config/adaptive_selectors.json")
    if config_path.exists():
        with open(config_path, 'w') as f:
            json.dump({}, f)

    # 2. Define Context
    # We construct the HTML such that the logic in healer_agent.py finds the data-testid
    html_snapshot = """
    <html>
        <body>
            <div class="container">
                <h1>Bitcoin Price</h1>
                <!-- The old ID #price-display is gone -->
                <!-- The new element has a testid which our mock healer logic looks for -->
                <div data-testid='healed-element'>$98,500.00</div>
            </div>
        </body>
    </html>
    """
    
    # 3. Execution
    try:
        # We manually fail the operation to allow the engine to catch it.
        # However, SelfHealingEngine's execute_with_recovery expects the *function* to fail.
        # But for 'heal' strategy, we need to pass the HTML content to the healer.
        # In a real Playwright flow, we'd catch the error -> get page.content() -> pass to engine.
        # Here, we directly call _attempt_healing or mock the flow.
        
        # Let's test the internal _attempt_healing directly first for unit testing the logic
        logger.info("Testing internal _attempt_healing...")
        result = await engine._attempt_healing(
            source_id="verify.test.source",
            failed_selector="#price-display",
            target_description="Current Bitcoin Price",
            html_content=html_snapshot,
            screenshot_path=None
        )
        
        # 4. Assertions
        assert result['status'] == 'healed', f"Status mismatch: {result['status']}"
        assert result['new_selector'] == "[data-testid='healed-element']", f"Selector mismatch: {result['new_selector']}"
        assert result['confidence'] >= 0.9, "Confidence too low"
        
        logger.info("✅ Internal Healer Logic Verified.")
        
        # 5. Verify Persistence
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config.get("verify.test.source") == "[data-testid='healed-element']", "Persistence failed"
        logger.info("✅ Persistence Verified.")
        
    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
