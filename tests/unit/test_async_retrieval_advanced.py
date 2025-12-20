import unittest
import sys
import os
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.core.async_retrieval import (
    AsyncRetrievalEngine,
    CircuitBreaker
)

class TestAsyncRetrievalAdvanced(unittest.TestCase):
    """Advanced tests for AsyncRetrievalEngine dealing with Context Managers and Edge Cases."""

    def setUp(self):
        # Patch config loading manually to ensure it applies
        self.config_patcher = patch('src.microanalyst.core.async_retrieval.AsyncRetrievalEngine._load_config')
        self.dirs_patcher = patch('src.microanalyst.core.async_retrieval.AsyncRetrievalEngine._ensure_dirs')
        
        self.mock_load = self.config_patcher.start()
        self.mock_ensure = self.dirs_patcher.start()
        
        self.mock_load.return_value = {} 
        
        self.addCleanup(self.config_patcher.stop)
        self.addCleanup(self.dirs_patcher.stop)
        
        self.retrieval = AsyncRetrievalEngine()

    def _run_async(self, coroutine):
        return asyncio.run(coroutine)

    @patch('src.microanalyst.core.async_retrieval.async_playwright')
    def test_playwright_context_flow(self, MockPlaywright):
        """Test the fetch_browser method with mocked browser context."""
        
        # Setup Mock Browser and Context
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.content.return_value = "<html><body>Target Content</body></html>"
        mock_page.goto.return_value = None
        
        # Helper to run async method
        async def run_fetch():
            adapter = {
                "id": "test_adapter",
                "url": "http://test.com",
                "browser": {"actions": []},
                "retrieval_mode": "browser"
            }
            return await self.retrieval.fetch_browser(adapter, mock_browser)
            
        result = self._run_async(run_fetch())
        
        # Verify
        self.assertEqual(result['status'], "success")
        
        # Verify calls
        mock_browser.new_context.assert_called_once()
        mock_page.goto.assert_called_with("http://test.com", wait_until="networkidle", timeout=60000)
        mock_context.close.assert_called_once()

    @patch('src.microanalyst.core.async_retrieval.async_playwright')
    def test_fetch_browser_failure_handling(self, MockPlaywright):
        """Test handling of browser errors."""
        mock_browser = AsyncMock()
        mock_browser.new_context.side_effect = Exception("Browser Crash")
        
        async def run():
            adapter = {"id": "fail_browser", "url": "http://fail.com", "retrieval_mode": "browser"}
            return await self.retrieval.fetch_browser(adapter, mock_browser)
            
        result = self._run_async(run())
        self.assertEqual(result['status'], "failure")
        
    def test_circuit_breaker_trip(self):
        """Test circuit breaker state transition from CLOSED to OPEN."""
        # 1. Fail 5 times
        for _ in range(5):
            self.retrieval.circuit_breaker.record_failure("test.com")
            
        # 2. Check State
        # Assuming defaults: threshold=3
        self.assertTrue(self.retrieval.circuit_breaker.is_open("test.com"))

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery logic."""
        # Trip it
        self.retrieval.circuit_breaker.record_failure("test.com")
        self.retrieval.circuit_breaker.failures["test.com"] = 5
        
        # Simulate time passing (modify last_failure directly)
        import datetime
        past = datetime.datetime.now() - datetime.timedelta(minutes=10)
        self.retrieval.circuit_breaker.last_failure["test.com"] = past
        
        # Should be allowed (OPEN -> check calls record_success -> CLOSED)
        # Wait, implementation says: if time passed, record_success and return False (not open)
        is_open = self.retrieval.circuit_breaker.is_open("test.com")
        self.assertFalse(is_open)
        
        # Verify failure count reset
        self.assertNotIn("test.com", self.retrieval.circuit_breaker.failures)

    @patch('src.microanalyst.core.async_retrieval.AsyncRetrievalEngine._fetch_http_attempt')
    @patch('src.microanalyst.core.proxy_manager.proxy_manager.get_proxy')
    def test_fetch_with_proxy_rotation(self, mock_get_proxy, mock_fetch_attempt):
        """Test delegation to _fetch_http_attempt."""
        mock_get_proxy.return_value = "http://proxy:8080"
        mock_fetch_attempt.return_value = "Success"
        
        async def run():
            adapter = {"id": "test_http", "url": "http://test.com", "retrieval_mode": "http"}
            return await self.retrieval.fetch_http(adapter)
            
        result = self._run_async(run())
        
        self.assertEqual(result['status'], "success")
        mock_fetch_attempt.assert_called()

if __name__ == '__main__':
    unittest.main()
