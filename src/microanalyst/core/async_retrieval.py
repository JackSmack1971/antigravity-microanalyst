import yaml
import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from playwright.async_api import async_playwright, Browser
from src.microanalyst.core.proxy_manager import proxy_manager

try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

# Configure Logging in class __init__ instead of top level to ensure paths are resolved correctly
logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    Simple Circuit Breaker to prevent hammering rate-limited APIs.
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures: Dict[str, int] = {}
        self.last_failure: Dict[str, datetime] = {}

    def record_failure(self, key: str):
        self.failures[key] = self.failures.get(key, 0) + 1
        self.last_failure[key] = datetime.now()
        logger.warning(f"Circuit Breaker: Recorded failure for {key}. Count: {self.failures[key]}")

    def record_success(self, key: str):
        if key in self.failures:
            del self.failures[key]
        if key in self.last_failure:
            del self.last_failure[key]

    def is_open(self, key: str) -> bool:
        if self.failures.get(key, 0) < self.failure_threshold:
            return False
        
        last_fail = self.last_failure.get(key)
        if last_fail and (datetime.now() - last_fail).total_seconds() > self.recovery_timeout:
            # Recovery period over, auto-reset
            logger.info(f"Circuit Breaker: Recovery timeout passed for {key}. Resetting.")
            self.record_success(key) 
            return False
            
        return True

class AsyncRetrievalEngine:
    def __init__(self, config_path="BTC Market Data Adapters Configuration.yml"):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.config_path = self.project_root / config_path
        self.data_dir = self.project_root / "data_exports"
        self.screenshot_dir = self.project_root / "screenshots"
        self.log_dir = self.project_root / "logs"
        self._ensure_dirs()
        self._setup_logging()
        self.config = self._load_config()
        self.semaphore = asyncio.Semaphore(5) # max concurrent adapters
        self.circuit_breaker = CircuitBreaker()

    def _setup_logging(self):
        """Configure logging with absolute paths."""
        log_file = self.log_dir / "async_retrieval.log"
        
        # Avoid duplicate handlers if re-initialized
        if not logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            logger.info(f"Logging initialized at {log_file}")

    def _ensure_dirs(self):
        for d in [self.data_dir, self.screenshot_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_http_attempt(self, session, url, headers, adapter_id):
        """Internal method to perform the request with tenacity retries and proxy rotation."""
        proxy = proxy_manager.get_proxy()
        if proxy:
            logger.info(f"Using proxy {proxy} for {adapter_id}")

        try:
            async with session.get(url, headers=headers, proxy=proxy, timeout=15) as response:
                if response.status == 429 or response.status == 403:
                    logger.warning(f"Rate limited/Forbidden ({response.status}): {adapter_id} with proxy {proxy}")
                    proxy_manager.report_failure(proxy)
                    raise Exception(f"Rate limited {response.status}")
                
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                return await response.text()
        except Exception:
            # Report failure on connection errors too
            proxy_manager.report_failure(proxy)
            raise

    async def fetch_http(self, adapter):
        adapter_id = adapter["id"]
        url = adapter["url"]
        
        # Check Circuit Breaker
        if self.circuit_breaker.is_open(adapter_id):
            logger.warning(f"Circuit Breaker OPEN for {adapter_id}. Skipping request.")
            return {"id": adapter_id, "status": "skipped_circuit_breaker"}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

        async with self.semaphore:
            logger.info(f"Fetching HTTP: {adapter_id}")
            async with aiohttp.ClientSession() as session:
                try:
                    content = await self._fetch_http_attempt(session, url, headers, adapter_id)
                    
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
                        
                    self.circuit_breaker.record_success(adapter_id)
                    return {"id": adapter_id, "status": "success"}

                except Exception as e:
                    logger.error(f"HTTP failed via tenacity for {adapter_id}: {e}")
                    self.circuit_breaker.record_failure(adapter_id)
                    raise e

    async def fetch_browser(self, adapter, browser: Browser):
        adapter_id = adapter["id"]
        url = adapter["url"]
        
        # Actions configuration
        actions = adapter.get("browser", {}).get("actions", [])
        capture_xhr_action = next((a for a in actions if a["type"] == "capture_xhr"), None)
        xhr_data = []

        async with self.semaphore:
            logger.info(f"Fetching Browser: {adapter_id}")
            
            # Proxy Setup
            proxy_url = proxy_manager.get_proxy()
            context_args = {
                "viewport": {'width': 1920, 'height': 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            if proxy_url:
                logger.info(f"Using browser proxy {proxy_url} for {adapter_id}")
                context_args["proxy"] = {"server": proxy_url}

            context = None
            try:
                # Create context with proxy if available
                context = await browser.new_context(**context_args)
                
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

                return {"id": adapter_id, "status": "success"}

            except Exception as e:
                logger.error(f"Browser failed for {adapter_id}: {e}")
                return {"id": adapter_id, "status": "failure"}
            finally:
                # Ensure context is always closed to free resources
                if context:
                    await context.close()

    async def execute_pipeline(self):
        adapters = self.config.get("adapters", [])
        
        tasks = []
        
        # HTTP Tasks
        for adapter in [a for a in adapters if a.get("retrieval_mode") == "http"]:
             tasks.append(self.fetch_http(adapter))
             
        # Browser Tasks with Shared Pool
        browser_adapters = [a for a in adapters if a.get("retrieval_mode") == "browser"]
        
        if browser_adapters:
            # We strictly manage the lifecycle here
            logger.info(f"Initializing Shared Browser Pool for {len(browser_adapters)} tasks...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                logger.info("Shared Browser launched.")
                
                try:
                    for adapter in browser_adapters:
                        tasks.append(self.fetch_browser(adapter, browser))
                    
                    # Execute all tasks concurrenty (HTTP + Browser)
                    # Note: HTTP tasks were added first
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                finally:
                    logger.info("Closing Shared Browser...")
                    await browser.close()
        else:
            # Only HTTP tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        stats = {"success": 0, "failure": 0, "skipped": 0}
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Task exception: {res}")
                stats["failure"] += 1
            elif isinstance(res, dict):
                status = res.get("status", "failure")
                if "skipped" in status:
                    stats["skipped"] += 1
                elif status == "success":
                    stats["success"] += 1
                else:
                    stats["failure"] += 1
                
        logger.info(f"Async Pipeline Complete: {stats}")
        
        # Write summary to log file
        with open(self.log_dir / "retrieval_log.txt", "a", encoding="utf-8") as f:
             f.write(f"[{datetime.now()}] Async Stats: {stats}\n")

        return stats

if __name__ == "__main__":
    engine = AsyncRetrievalEngine()
    asyncio.run(engine.execute_pipeline())
