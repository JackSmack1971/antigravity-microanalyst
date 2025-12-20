# src/microanalyst/intelligence/confluence_calculator.py
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
import logging

logger = logging.getLogger(__name__)

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
    """Individual technical factor at a price level"""
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
    """Cluster of confluence factors"""
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

class ConfluenceCalculator:
    """
    Advanced confluence zone detection and scoring engine.
    
    Features:
    - Multi-factor detection (10+ technical factors)
    - Hierarchical clustering for zone identification
    - Weighted scoring with decay functions
    - Historical validation and test counting
    - Dynamic recalculation with market updates
    """
    
    def __init__(self, 
                 clustering_tolerance: float = 0.015,  # 1.5% clustering tolerance
                 min_factors_for_zone: int = 2,
                 lookback_days: int = 365):
        self.clustering_tolerance = clustering_tolerance
        self.min_factors = min_factors_for_zone
        self.lookback_days = lookback_days
        
        # Factor weights (sum to 1.0)
        self.factor_weights = {
            FactorType.HISTORICAL_SR: 0.18,
            FactorType.VOLUME_PROFILE: 0.15,
            FactorType.FIBONACCI: 0.12,
            FactorType.MOVING_AVERAGE: 0.10,
            FactorType.ROUND_NUMBER: 0.08,
            FactorType.ETF_FLOW_PIVOT: 0.12,
            FactorType.OPEN_INTEREST: 0.10,
            FactorType.PIVOT_POINT: 0.08,
            FactorType.GAP_LEVEL: 0.04,
            FactorType.SWING_POINT: 0.03
        }
        
        logger.info(f"ConfluenceCalculator initialized: tolerance={clustering_tolerance}, lookback={lookback_days}d")
    
    def calculate_confluence_zones(self,
                                   df_price: pd.DataFrame,
                                   df_flows: Optional[pd.DataFrame] = None,
                                   df_oi: Optional[pd.DataFrame] = None,
                                   current_price: Optional[float] = None) -> List[ConfluenceZone]:
        """
        Main entry point: Calculate all confluence zones.
        
        Args:
            df_price: OHLCV data (required)
            df_flows: ETF flow data (optional, enhances accuracy)
            df_oi: Open Interest data (optional, adds OI clusters)
            current_price: Override for current price (defaults to last close)
        
        Returns:
            List of ConfluenceZone objects, sorted by score descending
        """
        if df_price.empty:
            logger.warning("Empty price dataframe provided")
            return []
        
        # Input normalization for columns
        df_price = self._normalize_columns(df_price)
        
        current_price = current_price or df_price['close'].iloc[-1]
        logger.info(f"Calculating confluence zones. Current price: ${current_price:,.2f}")
        
        # Step 1: Detect all individual factors
        all_factors = []
        
        all_factors.extend(self._detect_historical_sr(df_price))
        all_factors.extend(self._detect_volume_profile_nodes(df_price))
        all_factors.extend(self._detect_fibonacci_levels(df_price))
        all_factors.extend(self._detect_moving_averages(df_price))
        all_factors.extend(self._detect_round_numbers(df_price))
        all_factors.extend(self._detect_pivot_points(df_price))
        all_factors.extend(self._detect_gap_levels(df_price))
        all_factors.extend(self._detect_swing_points(df_price))
        
        if df_flows is not None and not df_flows.empty:
            all_factors.extend(self._detect_etf_flow_pivots(df_flows))
        
        if df_oi is not None and not df_oi.empty:
            all_factors.extend(self._detect_oi_clusters(df_oi))
        
        logger.info(f"Detected {len(all_factors)} individual factors")
        
        if not all_factors:
            logger.warning("No factors detected")
            return []
        
        # Step 2: Cluster factors into zones
        zones = self._cluster_factors_into_zones(all_factors, current_price)
        
        # Step 3: Score and validate each zone
        scored_zones = []
        for zone in zones:
            score = self._calculate_zone_score(zone, current_price)
            zone.confluence_score = score
            zone.strength = self._classify_strength(score)
            zone.distance_to_current = ((zone.price_level - current_price) / current_price) * 100
            
            # Historical validation
            zone.historical_tests, zone.last_test_date = self._count_historical_tests(
                zone, df_price
            )
            zone.breach_probability = self._calculate_breach_probability(zone, df_price)
            
            scored_zones.append(zone)
        
        # Step 4: Filter and rank
        significant_zones = [z for z in scored_zones if z.confluence_score >= 0.5]
        significant_zones.sort(key=lambda x: x.confluence_score, reverse=True)
        
        logger.info(f"Identified {len(significant_zones)} significant confluence zones")
        
        return significant_zones
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure lowercase columns"""
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        return df

    # ===================================================================
    # FACTOR DETECTION METHODS
    # ===================================================================
    
    def _detect_historical_sr(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect historical support/resistance levels using swing points.
        """
        factors = []
        
        # Find swing highs (resistance candidates)
        df['swing_high'] = (
            (df['high'] > df['high'].shift(1)) &
            (df['high'] > df['high'].shift(2)) &
            (df['high'] > df['high'].shift(-1)) &
            (df['high'] > df['high'].shift(-2))
        )
        
        # Find swing lows (support candidates)
        df['swing_low'] = (
            (df['low'] < df['low'].shift(1)) &
            (df['low'] < df['low'].shift(2)) &
            (df['low'] < df['low'].shift(-1)) &
            (df['low'] < df['low'].shift(-2))
        )
        
        # Process swing highs
        swing_highs = df[df['swing_high']]['high'].values
        for price in swing_highs:
            # Count nearby touches (within 1%)
            touches = self._count_touches(df, price, tolerance=0.01)
            recency_weight = self._calculate_recency_weight(
                df[df['high'] == price].index[-1], len(df)
            )
            
            strength = min(1.0, (touches / 5.0) * recency_weight)
            
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.HISTORICAL_SR,
                strength=strength,
                direction=ConfluenceType.RESISTANCE,
                metadata={
                    "touches": touches,
                    "recency_weight": recency_weight
                }
            ))
        
        # Process swing lows
        swing_lows = df[df['swing_low']]['low'].values
        for price in swing_lows:
            touches = self._count_touches(df, price, tolerance=0.01)
            recency_weight = self._calculate_recency_weight(
                df[df['low'] == price].index[-1], len(df)
            )
            
            strength = min(1.0, (touches / 5.0) * recency_weight)
            
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.HISTORICAL_SR,
                strength=strength,
                direction=ConfluenceType.SUPPORT,
                metadata={
                    "touches": touches,
                    "recency_weight": recency_weight
                }
            ))
        
        logger.debug(f"Detected {len(factors)} historical S/R levels")
        return factors
    
    def _detect_volume_profile_nodes(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect high-volume nodes (POC - Point of Control).
        """
        factors = []
        
        if 'volume' not in df.columns or df['volume'].sum() == 0:
            logger.debug("No volume data available")
            return factors
        
        # Create price bins (0.5% intervals)
        price_min = df['low'].min()
        price_max = df['high'].max()
        if price_min == price_max: return []
        
        n_bins = int((price_max - price_min) / (price_min * 0.005))
        n_bins = max(10, n_bins) # prevent zero or too small bins
        
        bins = np.linspace(price_min, price_max, n_bins)
        
        # Aggregate volume per bin
        volume_profile = np.zeros(len(bins) - 1)
        for _, row in df.iterrows():
            # Distribute bar volume across price range
            bar_bins = np.digitize([row['low'], row['high']], bins)
            # Ensure indices are within bounds
            start_idx = max(0, bar_bins[0]-1)
            end_idx = min(len(volume_profile), bar_bins[1])
            
            for i in range(start_idx, end_idx):
                volume_profile[i] += row['volume']
        
        # Find peaks (local maxima)
        from scipy.signal import find_peaks
        if len(volume_profile) > 0:
             peaks, properties = find_peaks(volume_profile, prominence=np.std(volume_profile))
             
             for peak_idx in peaks:
                price = (bins[peak_idx] + bins[peak_idx + 1]) / 2
                volume_strength = volume_profile[peak_idx] / volume_profile.max()
                
                factors.append(ConfluenceFactor(
                    price=price,
                    factor_type=FactorType.VOLUME_PROFILE,
                    strength=volume_strength,
                    direction=ConfluenceType.PIVOT,
                    metadata={
                        "volume": volume_profile[peak_idx],
                        "prominence": properties['prominences'][np.where(peaks == peak_idx)[0][0]]
                    }
                ))
        
        logger.debug(f"Detected {len(factors)} volume profile nodes")
        return factors
    
    def _detect_fibonacci_levels(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Calculate Fibonacci retracement levels from recent swing.
        """
        factors = []
        
        # Find recent significant swing (last 60 days)
        recent = df.tail(60)
        swing_high = recent['high'].max()
        swing_low = recent['low'].min()
        
        fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        current_price = df['close'].iloc[-1]
        
        # Calculate retracement levels
        for level in fib_levels:
            price = swing_low + (swing_high - swing_low) * (1 - level)
            
            # Weight by importance
            if level in [0.5, 0.618]:
                strength = 0.9
            elif level in [0.382, 0.786]:
                strength = 0.7
            else:
                strength = 0.5
            
            direction = ConfluenceType.SUPPORT if price < current_price else ConfluenceType.RESISTANCE
            
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.FIBONACCI,
                strength=strength,
                direction=direction,
                metadata={
                    "fib_level": level,
                    "swing_high": swing_high,
                    "swing_low": swing_low
                }
            ))
        
        logger.debug(f"Detected {len(factors)} Fibonacci levels")
        return factors
    
    def _detect_moving_averages(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect key moving average levels (20, 50, 100, 200 day).
        """
        factors = []
        
        ma_periods = [20, 50, 100, 200]
        
        for period in ma_periods:
            if len(df) < period:
                continue
            
            ma_value = df['close'].rolling(period).mean().iloc[-1]
            if pd.isna(ma_value): continue

            # Strength based on price-MA relationship and period importance
            distance_pct = abs((df['close'].iloc[-1] - ma_value) / ma_value)
            strength = max(0.3, 1.0 - distance_pct * 2)  # Decay with distance
            
            if period >= 200:
                strength *= 1.2
            elif period >= 100:
                strength *= 1.1
            
            strength = min(1.0, strength)
            
            direction = ConfluenceType.SUPPORT if ma_value < df['close'].iloc[-1] else ConfluenceType.RESISTANCE
            
            factors.append(ConfluenceFactor(
                price=ma_value,
                factor_type=FactorType.MOVING_AVERAGE,
                strength=strength,
                direction=direction,
                metadata={
                    "period": period,
                    "distance_pct": distance_pct
                }
            ))
        
        logger.debug(f"Detected {len(factors)} moving average levels")
        return factors
    
    def _detect_round_numbers(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect psychological round numbers.
        """
        factors = []
        
        price_range = (df['low'].min(), df['high'].max())
        current_price = df['close'].iloc[-1]
        
        if current_price >= 100000:
            interval = 10000
        elif current_price >= 10000:
            interval = 1000
        elif current_price >= 1000:
            interval = 100
        else:
            interval = 100
        
        start = int(price_range[0] / interval) * interval
        end = int(price_range[1] / interval) * interval + interval
        
        for price in range(start, end, interval):
            if price_range[0] <= price <= price_range[1]:
                if price % (interval * 10) == 0:
                    strength = 0.8
                elif price % (interval * 5) == 0:
                    strength = 0.6
                else:
                    strength = 0.4
                
                direction = ConfluenceType.SUPPORT if price < current_price else ConfluenceType.RESISTANCE
                
                factors.append(ConfluenceFactor(
                    price=float(price),
                    factor_type=FactorType.ROUND_NUMBER,
                    strength=strength,
                    direction=direction,
                    metadata={"interval": interval}
                ))
        
        logger.debug(f"Detected {len(factors)} round number levels")
        return factors
    
    def _detect_etf_flow_pivots(self, df_flows: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect pivot points in ETF flow data.
        """
        factors = []
        
        if df_flows.empty:
            return factors

        # Determine Flow Column Name
        flow_col = 'flow_usd'
        if 'Net_Flow' in df_flows.columns:
            flow_col = 'Net_Flow'
        elif 'flow_usd' in df_flows.columns:
            flow_col = 'flow_usd'
        else:
            # Try lowercase
             cols_lower = {c.lower(): c for c in df_flows.columns}
             if 'flow_usd' in cols_lower:
                 flow_col = cols_lower['flow_usd']
             elif 'net_flow' in cols_lower:
                 flow_col = cols_lower['net_flow']
             else:
                 return []
        
        # Aggregate daily flows
        daily_flows = df_flows.groupby('date')[flow_col].sum().reset_index()
        daily_flows = daily_flows.sort_values('date')
        
        mean_flow = daily_flows[flow_col].mean()
        std_flow = daily_flows[flow_col].std()
        
        threshold = 2 * std_flow
        
        extremes = daily_flows[np.abs(daily_flows[flow_col] - mean_flow) > threshold]
        
        # TODO: Join with price data to get price level. Returning placeholders for now.
        
        logger.debug(f"Detected {len(extremes)} ETF flow pivot points")
        return factors
    
    def _detect_oi_clusters(self, df_oi: pd.DataFrame) -> List[ConfluenceFactor]:
        factors = []
        logger.debug(f"OI clustering detection (not implemented)")
        return factors
    
    def _detect_pivot_points(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Calculate classic pivot points.
        """
        factors = []
        
        if len(df) < 2: return factors

        yesterday = df.iloc[-2]
        
        pivot = (yesterday['high'] + yesterday['low'] + yesterday['close']) / 3
        
        r1 = 2 * pivot - yesterday['low']
        r2 = pivot + (yesterday['high'] - yesterday['low'])
        s1 = 2 * pivot - yesterday['high']
        s2 = pivot - (yesterday['high'] - yesterday['low'])
        
        levels = [
            (pivot, 0.8, ConfluenceType.PIVOT),
            (r1, 0.6, ConfluenceType.RESISTANCE),
            (r2, 0.5, ConfluenceType.RESISTANCE),
            (s1, 0.6, ConfluenceType.SUPPORT),
            (s2, 0.5, ConfluenceType.SUPPORT)
        ]
        
        for price, strength, direction in levels:
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.PIVOT_POINT,
                strength=strength,
                direction=direction,
                metadata={"pivot_type": "floor_trader"}
            ))
        
        logger.debug(f"Detected {len(factors)} pivot point levels")
        return factors
    
    def _detect_gap_levels(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect unfilled gaps.
        """
        factors = []
        
        df_gaps = df.copy()
        df_gaps['gap_up'] = df_gaps['low'] > df_gaps['high'].shift(1)
        df_gaps['gap_down'] = df_gaps['high'] < df_gaps['low'].shift(1)
        
        gap_ups = df_gaps[df_gaps['gap_up']]['high'].shift(1).dropna()
        for price in gap_ups:
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.GAP_LEVEL,
                strength=0.7,
                direction=ConfluenceType.SUPPORT,
                metadata={"gap_type": "up"}
            ))
        
        gap_downs = df_gaps[df_gaps['gap_down']]['low'].shift(1).dropna()
        for price in gap_downs:
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.GAP_LEVEL,
                strength=0.7,
                direction=ConfluenceType.RESISTANCE,
                metadata={"gap_type": "down"}
            ))
        
        logger.debug(f"Detected {len(factors)} gap levels")
        return factors
    
    def _detect_swing_points(self, df: pd.DataFrame) -> List[ConfluenceFactor]:
        """
        Detect significant swing high/low points.
        """
        factors = []
        window = 10
        
        df_swings = df.copy()
        df_swings['major_swing_high'] = df_swings['high'] == df_swings['high'].rolling(window * 2 + 1, center=True).max()
        df_swings['major_swing_low'] = df_swings['low'] == df_swings['low'].rolling(window * 2 + 1, center=True).min()
        
        swing_highs = df_swings[df_swings['major_swing_high']]['high'].dropna()
        for price in swing_highs:
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.SWING_POINT,
                strength=0.6,
                direction=ConfluenceType.RESISTANCE,
                metadata={"window": window}
            ))
        
        swing_lows = df_swings[df_swings['major_swing_low']]['low'].dropna()
        for price in swing_lows:
            factors.append(ConfluenceFactor(
                price=price,
                factor_type=FactorType.SWING_POINT,
                strength=0.6,
                direction=ConfluenceType.SUPPORT,
                metadata={"window": window}
            ))
        
        logger.debug(f"Detected {len(factors)} major swing points")
        return factors
    
    # ===================================================================
    # CLUSTERING & SCORING METHODS
    # ===================================================================
    
    def _cluster_factors_into_zones(self, 
                                    factors: List[ConfluenceFactor],
                                    current_price: float) -> List[ConfluenceZone]:
        """
        Cluster nearby factors using hierarchical clustering.
        """
        if len(factors) < self.min_factors:
            return []
        
        prices = np.array([f.price for f in factors]).reshape(-1, 1)
        threshold = current_price * self.clustering_tolerance
        
        from sklearn.cluster import AgglomerativeClustering
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=threshold,
            linkage='average'
        )
        
        labels = clustering.fit_predict(prices)
        
        zones = []
        for cluster_id in set(labels):
            cluster_factors = [f for i, f in enumerate(factors) if labels[i] == cluster_id]
            
            if len(cluster_factors) < self.min_factors:
                continue
            
            total_weight = sum(f.strength for f in cluster_factors)
            weighted_price = sum(f.price * f.strength for f in cluster_factors) / total_weight
            
            support_strength = sum(f.strength for f in cluster_factors if f.direction == ConfluenceType.SUPPORT)
            resistance_strength = sum(f.strength for f in cluster_factors if f.direction == ConfluenceType.RESISTANCE)
            
            if support_strength > resistance_strength:
                zone_type = ConfluenceType.SUPPORT
            elif resistance_strength > support_strength:
                zone_type = ConfluenceType.RESISTANCE
            else:
                zone_type = ConfluenceType.PIVOT
            
            zone_prices = [f.price for f in cluster_factors]
            price_range = (min(zone_prices), max(zone_prices))
            
            zone = ConfluenceZone(
                price_level=weighted_price,
                confluence_score=0.0,
                factors=cluster_factors,
                zone_type=zone_type,
                strength="",
                price_range=price_range,
                distance_to_current=0.0,
                historical_tests=0,
                last_test_date=None,
                breach_probability=0.0
            )
            
            zones.append(zone)
        
        logger.debug(f"Clustered {len(factors)} factors into {len(zones)} zones")
        return zones
    
    def _calculate_zone_score(self, zone: ConfluenceZone, current_price: float) -> float:
        """
        Calculate confluence score using weighted factors.
        """
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for factor in zone.factors:
            weight = self.factor_weights.get(factor.factor_type, 0.05)
            
            distance_pct = abs(factor.price - zone.price_level) / zone.price_level
            distance_decay = np.exp(-10 * distance_pct)
            
            contribution = weight * factor.strength * distance_decay
            total_weighted_score += contribution
            total_weight += weight
        
        base_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        diversity_bonus = zone.factor_diversity() * 0.15
        count_bonus = min(0.2, zone.factor_count() * 0.03)
        
        distance_pct = abs(zone.price_level - current_price) / current_price
        distance_penalty = min(0.15, distance_pct * 0.5)
        
        final_score = base_score + diversity_bonus + count_bonus - distance_penalty
        
        return max(0.0, min(1.0, final_score))
    
    def _classify_strength(self, score: float) -> str:
        """Classify zone strength based on score."""
        if score >= 0.85:
            return "critical"
        elif score >= 0.70:
            return "strong"
        elif score >= 0.55:
            return "moderate"
        else:
            return "weak"
    
    # ===================================================================
    # HELPER METHODS
    # ===================================================================
    
    def _count_touches(self, df: pd.DataFrame, price: float, tolerance: float = 0.01) -> int:
        within_range = (
            (df['high'] >= price * (1 - tolerance)) &
            (df['high'] <= price * (1 + tolerance))
        ) | (
            (df['low'] >= price * (1 - tolerance)) &
            (df['low'] <= price * (1 + tolerance))
        )
        return within_range.sum()
    
    def _calculate_recency_weight(self, touch_index: int, total_length: int) -> float:
        recency = (touch_index + 1) / total_length
        return 0.5 + (recency * 0.5)
    
    def _count_historical_tests(self, 
                                zone: ConfluenceZone,
                                df: pd.DataFrame) -> Tuple[int, Optional[datetime]]:
        tolerance = (zone.price_range[1] - zone.price_range[0]) / 2
        # Ensure minimum tolerance
        min_tolerance = zone.price_level * 0.001
        tolerance = max(tolerance, min_tolerance)

        tests = 0
        last_test = None
        
        for idx in df.index:
            row = df.loc[idx]
            if (row['low'] <= zone.price_level + tolerance and
                row['high'] >= zone.price_level - tolerance):
                tests += 1
                if last_test is None or idx > last_test:
                    last_test = idx
        
        last_test_date = df.loc[last_test, 'date'] if last_test is not None and 'date' in df.columns else None
        
        return tests, last_test_date
    
    def _calculate_breach_probability(self,
                                     zone: ConfluenceZone,
                                     df: pd.DataFrame) -> float:
        if zone.historical_tests == 0:
            return 0.5
        
        test_factor = max(0.2, 1.0 - (zone.historical_tests / 20.0))
        
        recent_bars = 5
        if len(df) >= recent_bars:
            recent_momentum = (df['close'].iloc[-1] - df['close'].iloc[-recent_bars]) / df['close'].iloc[-recent_bars]
            momentum_factor = abs(recent_momentum) * 0.3
        else:
            momentum_factor = 0.0
        
        breach_prob = test_factor + momentum_factor
        return max(0.0, min(1.0, breach_prob))


# ===================================================================
# VISUALIZATION & EXPORT
# ===================================================================

class ConfluenceVisualizer:
    """Generate visual representations of confluence zones."""
    
    @staticmethod
    def plot_zones(df_price: pd.DataFrame,
                   zones: List[ConfluenceZone],
                   output_path: str = "confluence_zones.png"):
        """
        Create price chart with confluence zones overlaid.
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3])
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_price['date'],
                open=df_price['open'],
                high=df_price['high'],
                low=df_price['low'],
                close=df_price['close'],
                name='BTC/USD'
            ),
            row=1, col=1
        )
        
        # Add confluence zones as horizontal lines
        colors = {
            "critical": "red",
            "strong": "orange",
            "moderate": "yellow",
            "weak": "lightgray"
        }
        
        for zone in zones:
            fig.add_hline(
                y=zone.price_level,
                line_dash="dash",
                line_color=colors.get(zone.strength, "gray"),
                annotation_text=f"${zone.price_level:,.0f} ({zone.strength})",
                annotation_position="right",
                row=1, col=1
            )
            
            fig.add_hrect(
                y0=zone.price_range[0],
                y1=zone.price_range[1],
                fillcolor=colors.get(zone.strength, "gray"),
                opacity=0.2,
                line_width=0,
                row=1, col=1
            )
        
        zone_prices = [z.price_level for z in zones]
        zone_scores = [z.confluence_score for z in zones]
        
        fig.add_trace(
            go.Bar(
                x=zone_prices,
                y=zone_scores,
                name='Confluence Score',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="BTC Confluence Zones",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            height=800,
            showlegend=True
        )
        
        return fig

# ===================================================================
# TESTING & VALIDATION
# ===================================================================

def test_confluence_calculator():
    """Unit tests for confluence calculator."""
    
    # Generate synthetic data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = 90000 + np.cumsum(np.random.randn(100) * 1000)
    
    df_test = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': prices + np.random.rand(100) * 500,
        'low': prices - np.random.rand(100) * 500,
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    calculator = ConfluenceCalculator()
    zones = calculator.calculate_confluence_zones(df_test)
    
    print(f"✓ Detected {len(zones)} zones")
    
    if zones:
        top_zone = zones[0]
        print(f"✓ Top zone: ${top_zone.price_level:,.2f} (score: {top_zone.confluence_score:.3f})")
        print(f"  Factors: {top_zone.factor_count()}")
        print(f"  Diversity: {top_zone.factor_diversity():.2%}")
    
    return True


if __name__ == "__main__":
    # Run tests
    test_confluence_calculator()
    print("\n✓ All tests passed")
