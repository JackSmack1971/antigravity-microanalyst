import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.microanalyst.core.async_retrieval import (
    AsyncRetrievalEngine,
    CircuitBreaker
)

class TestAsyncRetrievalEngine(unittest.TestCase):
    """Comprehensive tests for AsyncRetrievalEngine."""
    
    def setUp(self):
        # Mock Config Loading inside init
        with patch('src.microanalyst.core.async_retrieval.AsyncRetrievalEngine._load_config') as mock_conf:
             mock_conf.return_value = {"adapters": []}
             self.engine = AsyncRetrievalEngine()
             
        # Mock dependencies
        self.engine.semaphore = asyncio.Semaphore(5)
        self.engine.circuit_breaker = CircuitBreaker()
        self.engine.data_dir = MagicMock()
        
    def _run_async(self, coroutine):
        return asyncio.run(coroutine)

    # ========== HAPPY PATH TESTS ==========

    @patch('aiohttp.ClientSession')
    def test_fetch_http_happy_path(self, MockSession):
        """Test successful HTTP fetch."""
        
        # Mock Response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text.return_value = "<html>Success</html>"
        
        # Mock Context Manager
        mock_session_instance = MockSession.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.get.return_value.__aenter__.return_value = mock_resp
        
        adapter = {"id": "test_src", "url": "http://example.com"}
        
        # Execute
        result = self._run_async(self.engine.fetch_http(adapter))
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["id"], "test_src")

    def test_circuit_breaker_happy_path(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=2)
        
        # 1st Fail
        cb.record_failure("src1")
        self.assertFalse(cb.is_open("src1"))
        
        # 2nd Fail
        cb.record_failure("src1")
        self.assertTrue(cb.is_open("src1")) # NOW OPEN
        
        # Reset
        cb.record_success("src1")
        self.assertFalse(cb.is_open("src1"))

    # ========== EDGE CASE TESTS ==========

    def test_fetch_http_skipped_circuit_open(self):
        """Test request is skipped if circuit is open."""
        self.engine.circuit_breaker.is_open = Mock(return_value=True)
        
        adapter = {"id": "broken_src", "url": "http://bad.com"}
        
        result = self._run_async(self.engine.fetch_http(adapter))
        
        self.assertIn("skipped", result["status"])

    # ========== ERROR SCENARIO TESTS ==========

    @patch('aiohttp.ClientSession')
    def test_fetch_http_error_retry(self, MockSession):
        """Test HTTP fetch retries on failure (Tenacity integration)."""
        # Note: Testing Tenacity decorators is tricky with simple mocks
        # We verify that it eventually raises exception
        
        # Setup mock to always raise
        mock_session_instance = MockSession.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.get.side_effect = Exception("Conn Error")
        
        adapter = {"id": "fail_src", "url": "http://fail.com"}
        
        # Since tenacity is involved, we might need to await longer or mocking sleep
        # For unit test speed, we might want to bypass tenacity or catch exception
        
        with self.assertRaises(Exception):
             self._run_async(self.engine.fetch_http(adapter))
             
        # Mock should have been called multiple times (if we let tenacity run)
        # But `fetch_http` swallows exception and re-raises
        # Actually in code: `except Exception as e: logger.error... raise e`
        
if __name__ == '__main__':
    unittest.main()
