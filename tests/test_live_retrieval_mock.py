import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.microanalyst.core.async_retrieval import AsyncRetrievalEngine

class TestAsyncRetrievalMock:
    
    @pytest.fixture
    def mock_adapters(self):
        return [
            {
                "id": "mock_source_1",
                "url": "http://example.com/1",
                "retrieval_mode": "http",
                "role": "test",
                "expected_format": "html"
            }
        ]

    # Use AsyncMock for async methods
    @patch("src.microanalyst.core.async_retrieval.AsyncRetrievalEngine._load_config")
    @patch("aiohttp.ClientSession.get")
    def test_fetch_http_success(self, mock_get, mock_load_config, mock_adapters):
        # Setup Config Mock
        mock_load_config.return_value = {"adapters": mock_adapters}
        
        # Setup Response Mock
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text.return_value = "<html>Mock Data</html>"
        
        # Setup Context Manager Mock
        mock_get.return_value.__aenter__.return_value = mock_resp
        
        engine = AsyncRetrievalEngine()
        
        # Run Test
        async def run_test():
             res = await engine.fetch_http(mock_adapters[0])
             assert res["status"] == "success"
             assert res["id"] == "mock_source_1"
             
        asyncio.run(run_test())
