
import asyncio
from playwright.async_api import async_playwright
import time

async def run_diagnostic():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        target_url = "https://www.coingecko.com/en/coins/bitcoin"
        
        # Test 1: networkidle (Standard strategy used in live_retrieval)
        print(f"\n[TEST 1] Navigating to {target_url} with 'networkidle'...")
        start = time.time()
        try:
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            print(f"SUCCESS: 'networkidle' reached in {time.time() - start:.2f}s")
        except Exception as e:
            print(f"FAILURE: 'networkidle' timed out after {time.time() - start:.2f}s: {e}")
            await page.screenshot(path="screenshots/diagnostic_gecko_timeout.png")
            print("Screenshot saved to screenshots/diagnostic_gecko_timeout.png")

        # Test 2: domcontentloaded (More lenient)
        print(f"\n[TEST 2] Navigating with 'domcontentloaded'...")
        start = time.time()
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            print(f"SUCCESS: 'domcontentloaded' reached in {time.time() - start:.2f}s")
        except Exception as e:
            print(f"FAILURE: 'domcontentloaded' failed: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
