from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class ConfluenceType(Enum):
    """Classification of confluence factors"""
    SUPPORT = "support"
    RESISTANCE = "resistance"
    PIVOT = "pivot"  # Can act as either
    MAGNET = "magnet"  # Attracts price (OI clusters)

class FactorType(Enum):
    """Individual technical factors"""
    HISTORICAL_SR = "historical_support_resistance"
    VOLUME_PROFILE = "volume_profile_node"
    FIBONACCI = "fibonacci_level"
    MOVING_AVERAGE = "moving_average"
    ROUND_NUMBER = "round_number"
    ETF_FLOW_PIVOT = "etf_flow_pivot"
    OPEN_INTEREST = "open_interest_cluster"
    PIVOT_POINT = "pivot_point"
    GAP_LEVEL = "gap_level"
    SWING_POINT = "swing_high_low"

@dataclass
class ConfluenceFactor:
    """
    Represents an individual technical or fundamental factor at a specific price.
    
    Attributes:
        price: The numerical price level where the factor is located.
        factor_type: The category of the factor (e.g., FIBONACCI, VOLUME_PROFILE).
        strength: Normalized value (0.0 to 1.0) indicating the factor's significance.
        direction: Whether the factor acts as SUPPORT, RESISTANCE, or a PIVOT.
        metadata: Arbitrary dictionary for additional context (e.g., touch count).
        detected_at: Timestamp of when the factor was identified.
    """
    price: float
    factor_type: FactorType
    strength: float  # 0-1 normalized strength
    direction: ConfluenceType
    metadata: Dict = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self):
        return f"{self.factor_type.value}@{self.price:.2f}({self.strength:.2f})"

@dataclass
class ConfluenceZone:
    """
    Represents a clustered region of multiple confluence factors.
    
    Zones are formed by grouping factors that are mathematically close to 
    each other, indicating a much higher probability of a market reaction.
    
    Attributes:
        price_level: The weighted center of the zone.
        confluence_score: Aggregate score based on factor strength and diversity.
        factors: List of individual factors contained within the zone.
        zone_type: Predominant direction (SUPPORT/RESISTANCE/PIVOT).
        strength: Human-readable strength label (e.g., "Critical", "Strong").
        price_range: (Lower, Upper) bounds of the zone.
        distance_to_current: Percentage distance from current market price.
        historical_tests: Number of times price has interacted with this zone.
        last_test_date: Most recent interaction timestamp.
        breach_probability: Estimated probability of price breaking through the zone.
    """
    price_level: float
    confluence_score: float
    factors: List[ConfluenceFactor]
    zone_type: ConfluenceType
    strength: str  # "weak", "moderate", "strong", "critical"
    price_range: Tuple[float, float]  # (lower, upper) bounds
    distance_to_current: float  # Percentage distance
    historical_tests: int  # How many times tested
    last_test_date: Optional[datetime]
    breach_probability: float  # 0-1 probability of breakthrough
    
    def factor_count(self) -> int:
        return len(self.factors)
    
    def factor_diversity(self) -> float:
        """Measure of factor type diversity (0-1)"""
        unique_types = len(set(f.factor_type for f in self.factors))
        return unique_types / len(FactorType)
    
    def to_dict(self) -> Dict:
        return {
            "price_level": round(self.price_level, 2),
            "confluence_score": round(self.confluence_score, 3),
            "factor_count": self.factor_count(),
            "factor_diversity": round(self.factor_diversity(), 3),
            "zone_type": self.zone_type.value,
            "strength": self.strength,
            "price_range": [round(self.price_range[0], 2), round(self.price_range[1], 2)],
            "distance_to_current_pct": round(self.distance_to_current, 2),
            "factors": [
                {
                    "type": f.factor_type.value,
                    "price": round(f.price, 2),
                    "strength": round(f.strength, 3),
                    "direction": f.direction.value,
                    "metadata": f.metadata
                } 
                for f in self.factors
            ],
            "historical_tests": self.historical_tests,
            "last_test_date": self.last_test_date.isoformat() if self.last_test_date else None,
            "breach_probability": round(self.breach_probability, 3)
        }
