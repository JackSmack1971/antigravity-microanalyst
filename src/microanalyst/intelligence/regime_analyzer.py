from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

class RegimeAnalyzer:
    """
    Detects market regime using multi-factor analysis:
    - Price momentum
    - Volatility
    - Market structure (HH/HL/LH/LL pattern)
    - Volume/flow pressure
    """
    
    def __init__(self):
        self.regime_states = [
            'bull', 'bear', 'accumulation', 'distribution', 'sideways', 'volatile'
        ]
    
    def detect_regime(
        self,
        df_price: pd.DataFrame,
        df_flows: pd.DataFrame = None,
        target_date: datetime = None
    ) -> Dict[str, Any]:
        """Detect current market regime"""
        
        # Feature extraction
        features = self._extract_features(df_price, df_flows)
        
        # Rule-based classification
        regime = self._classify_regime(features)
        confidence = self._calculate_regime_confidence(features, regime)
        
        # Duration calculation
        duration = self._calculate_regime_duration(df_price, regime)
        
        # Transition probability
        transitions = self._predict_transitions(features, regime)
        
        return {
            'current_regime': regime,
            'regime_confidence': confidence,
            'regime_duration_days': duration,
            'regime_characteristics': self._get_regime_characteristics(regime),
            'transition_probabilities': transitions,
            'features': features,
            'regime_history': self._get_regime_history(df_price, days=90)
        }
    
    def _extract_features(
        self,
        df_price: pd.DataFrame,
        df_flows: pd.DataFrame = None
    ) -> Dict[str, float]:
        """Extract regime classification features"""
        
        df = df_price.copy()
        
        # === Price Momentum ===
        returns_7d = df['close'].pct_change(7).iloc[-1]
        returns_30d = df['close'].pct_change(30).iloc[-1]
        
        # Moving averages
        sma_20 = df['close'].rolling(20).mean()
        sma_50 = df['close'].rolling(50).mean()
        price_vs_sma20 = (df['close'].iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1]
        price_vs_sma50 = (df['close'].iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1]
        
        # === Volatility ===
        volatility_20d = df['close'].pct_change().tail(20).std()
        atr_14 = self._calculate_atr(df, 14).iloc[-1]
        
        # === Market Structure ===
        # Simple heuristic for HH/LL
        recent_highs = df['high'].diff()
        recent_lows = df['low'].diff()
        
        higher_highs = (recent_highs > 0).tail(10).sum()
        lower_lows = (recent_lows < 0).tail(10).sum()
        
        # === Trend Strength ===
        try:
            adx = self._calculate_adx(df, 14).iloc[-1]
        except Exception:
            adx = 20.0 # Fallback
        
        # === Flow Pressure ===
        if df_flows is not None and not df_flows.empty:
            recent_flows = df_flows.tail(7)['flow_usd'].sum()
            flow_pressure = recent_flows / 1e9  # Normalize by $1B
        else:
            flow_pressure = 0
        
        return {
            'returns_7d': float(returns_7d),
            'returns_30d': float(returns_30d),
            'price_vs_sma20': float(price_vs_sma20),
            'price_vs_sma50': float(price_vs_sma50),
            'volatility_20d': float(volatility_20d),
            'atr_14': float(atr_14),
            'higher_highs_ratio': float(higher_highs / 10),
            'lower_lows_ratio': float(lower_lows / 10),
            'adx': float(adx),
            'flow_pressure': float(flow_pressure)
        }
    
    def _classify_regime(self, features: Dict[str, float]) -> str:
        """Rule-based regime classification"""
        
        momentum = features['returns_30d']
        volatility = features['volatility_20d']
        trend_strength = features['adx']
        structure = features['higher_highs_ratio'] - features['lower_lows_ratio']
        
        # Bull regime
        if (momentum > 0.05 and  # 5% positive momentum
            structure > 0.2 and  # More higher highs than lower lows
            features['price_vs_sma20'] > 0 and
            features['price_vs_sma50'] > 0):
            return 'bull'
        
        # Bear regime
        elif (momentum < -0.05 and
              structure < -0.2 and
              features['price_vs_sma20'] < 0 and
              features['price_vs_sma50'] < 0):
            return 'bear'
        
        # Volatile regime
        elif volatility > 0.04:  # 4% daily volatility
            return 'volatile'
        
        # Accumulation (bullish consolidation)
        elif (momentum > -0.02 and momentum < 0.02 and
              trend_strength < 25 and
              features['flow_pressure'] > 0.5):
            return 'accumulation'
        
        # Distribution (bearish consolidation)
        elif (momentum > -0.02 and momentum < 0.02 and
              trend_strength < 25 and
              features['flow_pressure'] < -0.5):
            return 'distribution'
        
        # Sideways (default)
        else:
            return 'sideways'
    
    def _calculate_regime_confidence(
        self,
        features: Dict[str, float],
        regime: str
    ) -> float:
        """Calculate confidence in regime classification"""
        
        # Check feature alignment with regime
        alignments = []
        
        if regime == 'bull':
            alignments = [
                features['returns_30d'] > 0.05,
                features['price_vs_sma20'] > 0.02,
                features['higher_highs_ratio'] > 0.6,
                features['adx'] > 25
            ]
        elif regime == 'bear':
            alignments = [
                features['returns_30d'] < -0.05,
                features['price_vs_sma20'] < -0.02,
                features['lower_lows_ratio'] > 0.6,
                features['adx'] > 25
            ]
        elif regime == 'volatile':
            alignments = [
                features['volatility_20d'] > 0.04,
                features['adx'] < 20
            ]
        else:  # sideways, accumulation, distribution
            alignments = [
                abs(features['returns_30d']) < 0.05,
                features['adx'] < 25
            ]
        
        # Confidence = proportion of aligned features
        if not alignments: return 0.5
        confidence = sum(alignments) / len(alignments)
        
        return float(confidence)
    
    def _calculate_regime_duration(
        self,
        df_price: pd.DataFrame,
        current_regime: str
    ) -> int:
        """Estimate how long current regime has persisted"""
        
        # Simplified: check when price crossed SMA50
        sma_50 = df_price['close'].rolling(50).mean()
        
        if current_regime in ['bull', 'accumulation']:
            # Count days since price crossed above SMA50
            above = df_price['close'] > sma_50
            duration = 0
            for i in range(len(above) - 1, -1, -1):
                if above.iloc[i]:
                    duration += 1
                else:
                    break
        elif current_regime in ['bear', 'distribution']:
            # Count days since price crossed below SMA50
            below = df_price['close'] < sma_50
            duration = 0
            for i in range(len(below) - 1, -1, -1):
                if below.iloc[i]:
                    duration += 1
                else:
                    break
        else:
            duration = 10  # Default for sideways/volatile
        
        return duration
    
    def _predict_transitions(
        self,
        features: Dict[str, float],
        current_regime: str
    ) -> Dict[str, float]:
        """Predict probability of transitioning to other regimes"""
        
        # Simplified transition probabilities based on momentum
        momentum = features['returns_30d']
        volatility = features['volatility_20d']
        
        transitions = {regime: 0.1 for regime in self.regime_states}
        transitions[current_regime] = 0.5  # Persistence probability
        
        if current_regime == 'bull':
            if momentum < 0:
                transitions['distribution'] = 0.2
                transitions['sideways'] = 0.15
            if volatility > 0.04:
                transitions['volatile'] = 0.2
        
        elif current_regime == 'bear':
            if momentum > 0:
                transitions['accumulation'] = 0.2
                transitions['sideways'] = 0.15
            if volatility > 0.04:
                transitions['volatile'] = 0.2
        
        # Normalize
        total = sum(transitions.values())
        transitions = {k: v/total for k, v in transitions.items()}
        
        return transitions
    
    def _get_regime_characteristics(self, regime: str) -> List[str]:
        """Get characteristics of regime"""
        characteristics = {
            'bull': [
                'Sustained uptrend',
                'Higher highs and higher lows',
                'Strong momentum',
                'Price above key moving averages'
            ],
            'bear': [
                'Sustained downtrend',
                'Lower highs and lower lows',
                'Weak momentum',
                'Price below key moving averages'
            ],
            'accumulation': [
                'Sideways consolidation',
                'Positive flow accumulation',
                'Building base for breakout',
                'Low volatility'
            ],
            'distribution': [
                'Sideways consolidation',
                'Negative flow distribution',
                'Building top for breakdown',
                'Low volatility'
            ],
            'sideways': [
                'Range-bound trading',
                'Lack of directional conviction',
                'Mean reversion tendencies',
                'Weak trend strength'
            ],
            'volatile': [
                'High volatility',
                'Rapid price swings',
                'Uncertain direction',
                'Heightened risk'
            ]
        }
        
        return characteristics.get(regime, [])
    
    def _get_regime_history(self, df_price: pd.DataFrame, days: int) -> List[Dict]:
        """Get historical regime classifications"""
        # Simplified: just return current for now
        last_date = df_price['date'].iloc[-1].strftime('%Y-%m-%d')
        return [
            {
                'date': last_date,
                'regime': 'current'
            }
        ]
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        # Make sure we have High, Low, Close
        # Input normalization should handle casing, but let's be safe
        high = df['high'] if 'high' in df.columns else df['High']
        low = df['low'] if 'low' in df.columns else df['Low']
        close = df['close'] if 'close' in df.columns else df['Close']
        
        close_prev = close.shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        return atr
    
    def _calculate_adx(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate ADX (simplified)"""
        high = df['high']
        low = df['low']
        
        # Directional movement
        up_move = high.diff()
        down_move = -low.diff()
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # ATR
        atr = self._calculate_atr(df, period)
        
        # Avoid division by zero
        atr = atr.replace(0, np.nan)
        
        # Directional indicators
        plus_di = 100 * (pd.Series(plus_dm).rolling(period).sum() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(period).sum() / atr)
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx
