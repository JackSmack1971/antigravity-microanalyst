import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path if needed (though pytest usually handles this if run from root)
sys.path.append(os.getcwd())

from src.microanalyst.synthetic.sentiment import FreeSentimentAggregator

@pytest.fixture
def aggregator():
    return FreeSentimentAggregator()

def test_sentiment_aggregator_initialization(aggregator):
    assert aggregator.fng_api == "https://api.alternative.me/fng/"
    assert aggregator.reddit_rss == "https://www.reddit.com/r/Bitcoin/hot/.rss?limit=25"
    assert 'moon' in aggregator.bull_words
    assert 'crash' in aggregator.bear_words

@patch('requests.get')
def test_aggregate_sentiment_bullish(mock_get, aggregator):
    # Mock Fear & Greed (Greed)
    mock_fng_resp = MagicMock()
    mock_fng_resp.status_code = 200
    mock_fng_resp.json.return_value = {'data': [{'value': '80'}]} # Greed

    # Mock Reddit (Bullish)
    mock_reddit_resp = MagicMock()
    mock_reddit_resp.status_code = 200
    # Create simple RSS with bullish titles
    rss_content = """
    <rss version="2.0">
        <channel>
            <item><title>Bitcoin to the moon soon!</title></item>
            <item><title>Time to accumulate now</title></item>
            <item><title>Great support at this level</title></item>
        </channel>
    </rss>
    """
    mock_reddit_resp.content = rss_content.encode('utf-8')
    mock_reddit_resp.text = rss_content

    # Configure side_effect for multiple calls
    # 1. F&G, 2. Reddit
    mock_get.side_effect = [mock_fng_resp, mock_reddit_resp]

    result = aggregator.aggregate_sentiment()
    
    # Expected scores:
    # F&G: 80
    # Reddit: 3 items, 3 bullish -> 100 score
    # Trends: 50 (default)
    # Composite: (80 * 0.5) + (100 * 0.3) + (50 * 0.2) = 40 + 30 + 10 = 80
    
    assert result['composite_score'] == 80.0
    assert result['interpretation'] == 'Extreme Greed' # >= 80
    assert result['metric'] == 'composite_market_sentiment'

@patch('requests.get')
def test_aggregate_sentiment_bearish(mock_get, aggregator):
    # Mock Fear & Greed (Fear)
    mock_fng_resp = MagicMock()
    mock_fng_resp.status_code = 200
    mock_fng_resp.json.return_value = {'data': [{'value': '20'}]} # Fear

    # Mock Reddit (Bearish)
    mock_reddit_resp = MagicMock()
    mock_reddit_resp.status_code = 200
    rss_content = """
    <rss version="2.0">
        <channel>
            <item><title>Market crash incoming due to regulation</title></item>
            <item><title>Panic selling everywhere</title></item>
            <item><title>Price falling at resistance</title></item>
        </channel>
    </rss>
    """
    mock_reddit_resp.content = rss_content.encode('utf-8')
    mock_reddit_resp.text = rss_content

    mock_get.side_effect = [mock_fng_resp, mock_reddit_resp]

    result = aggregator.aggregate_sentiment()
    
    # Expected scores:
    # F&G: 20
    # Reddit: 3 items, 3 bearish -> 0 score (ratio 0.0) -> damped? 
    # Logic check:
    # bull_count=0, total=3. ratio=0. score=0.
    # dampener: if total < 3. Here total=3, no dampener.
    # Trends: 50
    # Composite: (20 * 0.5) + (0 * 0.3) + (50 * 0.2) = 10 + 0 + 10 = 20
    
    assert result['composite_score'] == 20.0
    assert result['interpretation'] == 'Fear' # >= 20, < 40 is Fear. Wait, <20 is Extreme Fear. 20 is Fear.

@patch('requests.get')
def test_api_failures_fallback(mock_get, aggregator):
    # Mock generic failure
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = Exception("API Down")
    
    mock_get.return_value = mock_resp
    
    result = aggregator.aggregate_sentiment()
    
    # Verification of failure handling
    # F&G fails -> defaults to 50
    # Reddit fails -> defaults to 50
    # Trends -> defaults to 50
    # Composite: 50
    
    assert result['composite_score'] == 50.0
    assert result['sources']['fear_greed_index'] == 50
    assert result['sources']['reddit_sentiment'] == 50.0
    assert result['interpretation'] == 'Neutral'

def test_contrarian_signals(aggregator):
    assert aggregator._check_contrarian(10) == 'BUY SIGNAL (Blood in streets)'
    assert aggregator._check_contrarian(90) == 'SELL SIGNAL (Euphoria)'
    assert aggregator._check_contrarian(50) == 'No Signal'
