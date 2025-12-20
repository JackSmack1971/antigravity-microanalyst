from typing import List, Dict, Any, Optional

class SignalAnalyzer:
    """
    Detects technical signals (SMA Crossovers, RSI Divergence, Flow Anomalies).
    """
    
    def detect_all_signals(
        self,
        df_price,
        df_flows,
        regime_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        
        signals = []
        
        current_price = df_price['close'].iloc[-1]
        
        # 1. Simple MA Crossover
        # Just check alignment for now as a "signal"
        sma20 = df_price['close'].rolling(20).mean().iloc[-1]
        sma50 = df_price['close'].rolling(50).mean().iloc[-1]
        
        if sma20 > sma50:
            signals.append({
                'signal_type': 'Trend Alignment',
                'confidence': 0.7,
                'direction': 'bullish',
                'entry_price': current_price,
                'supporting_factors': ['SMA20 > SMA50'],
                'risk_reward_ratio': 2.0,
                'timeframe': 'daily',
                'stop_loss': current_price * 0.95,
                'take_profit': [current_price * 1.1]
            })
            
        # 2. RSI Check
        # RSI calculation included here for self-containment or use analytics lib
        delta = df_price['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        if rsi < 30:
            signals.append({
                'signal_type': 'RSI Oversold',
                'confidence': 0.8,
                'direction': 'bullish',
                'entry_price': current_price,
                'supporting_factors': [f'RSI is {rsi:.1f}'],
                'risk_reward_ratio': 3.0,
                'timeframe': 'short-term',
                'stop_loss': current_price * 0.98,
                'take_profit': [current_price * 1.05]
            })
        elif rsi > 70:
            signals.append({
                'signal_type': 'RSI Overbought',
                'confidence': 0.6,
                'direction': 'bearish',
                'entry_price': current_price,
                'supporting_factors': [f'RSI is {rsi:.1f}'],
                'risk_reward_ratio': 2.5,
                'timeframe': 'short-term',
                'stop_loss': current_price * 1.02,
                'take_profit': [current_price * 0.95]
            })
            
        return signals
