# src/microanalyst/synthetic/sentiment.py
import requests
import logging
from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FreeSentimentAggregator:
    """
    Multi-source sentiment aggregation using free tiers.
    Combines:
    1. Alternative.me Fear & Greed Index (Primary)
    2. Reddit r/Bitcoin Sentiment (RSS Scrape + Keyword Valence)
    3. Google Trends Proxy (Simulated or CoinGecko fallback)
    """
    
    def __init__(self):
        self.fng_api = "https://api.alternative.me/fng/"
        self.reddit_rss = "https://www.reddit.com/r/Bitcoin/hot/.rss?limit=25"
        self.headers = {'User-Agent': 'Microanalyst/1.0 (Educational Sentiment Bot)'}
        
        # Simple Valence Dictionary for Zero-Dependency Analysis
        self.bull_words = {
            'moon', 'pump', 'buy', 'long', 'bull', 'breakout', 'ath', 'soar', 
            'gain', 'profit', 'support', 'rally', 'accumulate', 'hodl', 'higher'
        }
        self.bear_words = {
            'crash', 'dump', 'sell', 'short', 'bear', 'drop', 'ban', 'fear', 
            'panic', 'loss', 'resistance', 'collapse', 'dead', 'rekt', 'lower'
        }

    def aggregate_sentiment(self) -> Dict[str, Any]:
        """
        Combine multiple free sentiment sources into a Composite Score (0-100).
        """
        try:
            # 1. Fear & Greed Index (0-100) - Weight: 50%
            fng_data = self._get_fear_greed()
            fng_score = float(fng_data.get('value', 50))
            
            # 2. Reddit Sentiment (0-100) - Weight: 30%
            reddit_score = self._get_reddit_sentiment()
            
            # 3. Google Trends / Social Volume (0-100) - Weight: 20%
            # Hard to get free reliable trends without auth. 
            # We'll use a placeholder or assume neutral if we can't fetch.
            trends_score = 50.0 
            
            # Composite Calculation
            composite_score = (fng_score * 0.5) + (reddit_score * 0.3) + (trends_score * 0.2)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': 'composite_market_sentiment',
                'composite_score': float(f"{composite_score:.2f}"),
                'sources': {
                    'fear_greed_index': fng_score,
                    'reddit_sentiment': reddit_score,
                    'google_trends_proxy': trends_score
                },
                'interpretation': self._interpret_score(composite_score),
                'contrarian_signal': self._check_contrarian(composite_score)
            }
            
        except Exception as e:
            logger.error(f"Error aggregating sentiment: {e}")
            return {'error': str(e)}

    def _get_fear_greed(self) -> Dict[str, Any]:
        try:
            r = requests.get(self.fng_api, params={'limit': 1}, timeout=5)
            r.raise_for_status()
            data = r.json()
            if data.get('data'):
                return data['data'][0]
        except Exception as e:
            logger.warning(f"F&G API failed: {e}")
        return {'value': 50}

    def _get_reddit_sentiment(self) -> float:
        """
        Scrape r/Bitcoin RSS and calculate sentiment from titles.
        Returns: 0 (Max Bearish) to 100 (Max Bullish). Neutral 50.
        """
        try:
            r = requests.get(self.reddit_rss, headers=self.headers, timeout=5)
            # Reddit often blocks non-browser agents, 429 Too Many Requests
            if r.status_code != 200:
                logger.warning(f"Reddit RSS failed ({r.status_code}), returning neutral.")
                return 50.0

            root = ET.fromstring(r.content)
            
            # Namespaces in RSS are annoying, usually simple tags like <title> inside <entry> (Atom) or <item> (RSS 2.0)
            # Reddit uses Atom usually.
            
            titles = []
            # Try finding 'entry' (Atom) or 'item' (RSS)
            # Check namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'} if 'Atom' in r.text else {}
            
            if ns:
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns)
                    if title is not None:
                        titles.append(title.text)
            else:
                # Fallback simplistic find (works for RSS 2.0 often)
                for item in root.findall('.//item'):
                    title = item.find('title')
                    if title is not None:
                        titles.append(title.text)
                        
            if not titles:
                return 50.0

            # Analyze basic sentiment
            bull_count = 0
            bear_count = 0
            
            for t in titles:
                text = t.lower()
                # Simple presence check
                if any(w in text for w in self.bull_words):
                    bull_count += 1
                if any(w in text for w in self.bear_words):
                    bear_count += 1
            
            total_matches = bull_count + bear_count
            if total_matches == 0:
                return 50.0
                
            # Ratio of bullishness
            bull_ratio = bull_count / total_matches
            
            # Convert to 0-100 scale
            # 0.5 ratio -> 50 score
            # 1.0 ratio -> 100 score
            score = bull_ratio * 100.0
            
            # Dampener: if mostly noise (low matches), pull towards 50
            if total_matches < 3:
                score = (score + 50) / 2
                
            return float(f"{score:.2f}")

        except Exception as e:
            logger.warning(f"Reddit sentiment analysis failed: {e}")
            return 50.0

    def _interpret_score(self, score):
        if score < 20: return 'Extreme Fear'
        if score < 40: return 'Fear'
        if score < 60: return 'Neutral'
        if score < 80: return 'Greed'
        return 'Extreme Greed'

    def _check_contrarian(self, score) -> str:
        if score < 15: return 'BUY SIGNAL (Blood in streets)'
        if score > 85: return 'SELL SIGNAL (Euphoria)'
        return 'No Signal'
