from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime

@dataclass
class MarketContext:
    """Complete market context snapshot"""
    timestamp: datetime
    regime: Dict[str, Any]
    signals: List[Dict[str, Any]]
    risks: Dict[str, Any]
    opportunities: List[Dict[str, Any]]
    key_levels: Dict[str, Any]
    sentiment_indicators: Dict[str, Any]
    historical_comparison: Dict[str, Any]
    macro_correlations: List[Dict[str, Any]] = None # P2 Add
    confidence_score: float
    metadata: Dict[str, Any]
