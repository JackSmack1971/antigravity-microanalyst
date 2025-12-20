import yaml
import json
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/async_retrieval.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AsyncRetrievalEngine:
    def __init__(self, config_path="BTC Market Data Adapters Configuration.yml"):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.config_path = self.project_root / config_path
        self.data_dir = self.project_root / "data_exports"
        self.screenshot_dir = self.project_root / "screenshots"
        self.log_dir = self.project_root / "logs"
        
        self._ensure_dirs()
        self.config = self._load_config()
        self.semaphore = asyncio.Semaphore(5) # max concurrent adapters

    def _ensure_dirs(self):
        for d in [self.data_dir, self.screenshot_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_http(self, adapter):
        adapter_id = adapter["id"]
        url = adapter["url"]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

        async with self.semaphore:
            logger.info(f"Fetching HTTP: {adapter_id}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 429:
                         logger.warning(f"Rate limited: {adapter_id}")
                         raise Exception("Rate limited")
                    
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    content = await response.text()
                    
                    # Logic for determining extension
                    fmt = adapter.get("expected_format", "").lower()
                    if "json" in fmt:
                        ext = "json"
                    elif "html" in fmt:
                        ext = "html"
                    else:
                        ext = "txt"
                        
                    file_path = self.data_dir / f"{adapter_id}.{ext}"
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                        
                    return {"id": adapter_id, "status": "success"}

    async def fetch_browser(self, adapter, playwright):
        adapter_id = adapter["id"]
        url = adapter["url"]
        
        # Actions configuration
        actions = adapter.get("browser", {}).get("actions", [])
        capture_xhr_action = next((a for a in actions if a["type"] == "capture_xhr"), None)
        xhr_data = []

        async with self.semaphore:
            logger.info(f"Fetching Browser: {adapter_id}")
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            if stealth_async:
                await stealth_async(page)

            # XHR Capture Setup
            if capture_xhr_action:
                xhr_filter = capture_xhr_action.get("filter", "json")
                async def handle_response(response):
                    try:
                        if response.request.method == "GET" and xhr_filter in response.headers.get("content-type", ""):
                            json_data = await response.json()
                            if json_data:
                                xhr_data.append({"url": response.url, "json": json_data})
                    except:
                        pass
                page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Scrolling
                for _ in range(5):
                    await page.mouse.wheel(0, 1000)
                    await asyncio.sleep(1)

                # Interactions
                for action in actions:
                    if action.get("type") == "set_timeframe":
                        val = action.get("value")
                        try:
                            # Using locator with first()
                            btn = page.locator(f"button:has-text('{val}'), div:has-text('{val}')").first
                            if await btn.count() > 0:
                                await btn.click(timeout=5000)
                                logger.info(f"Clicked {val} for {adapter_id}")
                                await asyncio.sleep(3)
                        except Exception as e:
                            logger.warning(f"Failed to click {val} for {adapter_id}: {e}")

                # Screenshots
                if adapter.get("artifacts", {}).get("screenshot_fullpage"):
                    await page.screenshot(path=str(self.screenshot_dir / f"{adapter_id}_full.png"), full_page=True)

                if adapter.get("artifacts", {}).get("screenshot_widgets"):
                    await page.screenshot(path=str(self.screenshot_dir / f"{adapter_id}_visible.png"))

                # Save Content
                content = await page.content()
                with open(self.data_dir / f"{adapter_id}.html", "w", encoding="utf-8") as f:
                    f.write(content)

                # Save XHR
                if adapter.get("artifacts", {}).get("xhr_bundle") and xhr_data:
                    with open(self.data_dir / f"{adapter_id}_xhr.json", "w", encoding="utf-8") as f:
                        json.dump(xhr_data, f, indent=2)

                await browser.close()
                return {"id": adapter_id, "status": "success"}

            except Exception as e:
                logger.error(f"Browser failed for {adapter_id}: {e}")
                await browser.close()
                return {"id": adapter_id, "status": "failure"}

    async def execute_pipeline(self):
        adapters = self.config.get("adapters", [])
        
        tasks = []
        
        # HTTP Tasks
        for adapter in [a for a in adapters if a.get("retrieval_mode") == "http"]:
             tasks.append(self.fetch_http(adapter))
             
        # Browser Tasks needs playwright instance context
        # We can mix them if we manage the context well. 
        # But typically we want one playwright instance for all browser tasks?
        # Actually, creating a new browser instance per task is safer for isolation but heavier.
        # Given we limit concurrency with semaphore, it's okay.
        
        # However, we must start playwright inside the async loop. 
        # We can wrap browser tasks.
        
        async def run_browser_task(adapter):
            async with async_playwright() as p:
                return await self.fetch_browser(adapter, p)

        for adapter in [a for a in adapters if a.get("retrieval_mode") == "browser"]:
            tasks.append(run_browser_task(adapter))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        stats = {"success": 0, "failure": 0}
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Task exception: {res}")
                stats["failure"] += 1
            elif isinstance(res, dict):
                status = res.get("status", "failure")
                stats[status] = stats.get(status, 0) + 1
                
        logger.info(f"Async Pipeline Complete: {stats}")
        
        # Write summary to log file
        with open(self.log_dir / "retrieval_log.txt", "a", encoding="utf-8") as f:
             f.write(f"[{datetime.now()}] Async Stats: {stats}\n")

        return stats

if __name__ == "__main__":
    engine = AsyncRetrievalEngine()
    asyncio.run(engine.execute_pipeline())
