from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader

from src.microanalyst.intelligence.regime_analyzer import RegimeAnalyzer
from src.microanalyst.intelligence.signal_analyzer import SignalAnalyzer
from src.microanalyst.intelligence.risk_analyzer import RiskAnalyzer
from src.microanalyst.intelligence.opportunity_detector import OpportunityDetector
from src.microanalyst.intelligence.narrative_generator import NarrativeGenerator
from src.microanalyst.intelligence.action_prioritizer import ActionPrioritizer
from src.microanalyst.agents.reasoning_adapter import AgentReasoningAdapter
from src.microanalyst.providers.macro_data import MacroDataProvider
from src.microanalyst.intelligence.correlation_analyzer import CorrelationAnalyzer
from src.microanalyst.signals.library import SignalLibrary
from src.microanalyst.intelligence.base import MarketContext

class ContextSynthesizer:
    """
    Generates context-aware market reports that adapt to:
    - Current market regime
    - Volatility levels
    - Signal strength
    - Risk environment
    - Historical precedent
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.project_root / "data_clean"
        self.template_dir = Path(__file__).parent / "templates"
        
        # Initialize analyzers
        self.regime_analyzer = RegimeAnalyzer()
        self.signal_analyzer = SignalAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        self.opportunity_detector = OpportunityDetector()
        self.narrative_generator = NarrativeGenerator()
        self.action_prioritizer = ActionPrioritizer()
        self.reasoning_adapter = AgentReasoningAdapter()
        
        # Macro Data
        self.macro_provider = MacroDataProvider()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.signal_lib = SignalLibrary() # Remediation: Use shared signal library
        
        # Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def synthesize_context(
        self, 
        lookback_days: int = 30,
        target_date: Optional[datetime] = None,
        is_simulation: bool = False # Remediation: Allow passing simulation flag
    ) -> MarketContext:
        """
        Generate complete market context with all intelligence layers
        """
        target_date = target_date or datetime.now()
        
        # Load data
        df_price = self._load_price_data(lookback_days)
        df_flows = self._load_flow_data(lookback_days)
        
        if df_price.empty:
            raise ValueError("No price data available")
        
        # === Intelligence Gathering ===
        
        # 1. Regime Analysis
        regime_info = self.regime_analyzer.detect_regime(
            df_price, 
            df_flows,
            target_date=target_date
        )
        
        # 2. Signal Detection
        signals = self.signal_analyzer.detect_all_signals(
            df_price,
            df_flows,
            regime_context=regime_info
        )
        
        # 3. Risk Assessment
        risks = self.risk_analyzer.assess_risks(
            df_price,
            df_flows,
            regime=regime_info,
            signals=signals
        )
        
        # 4. Opportunity Detection
        opportunities = self.opportunity_detector.identify_opportunities(
            df_price,
            df_flows,
            regime=regime_info,
            signals=signals,
            risks=risks
        )
        
        # 5. Key Levels (Remediation: Using decoupled SignalLibrary instead of placeholders)
        key_levels = self.signal_lib.find_support_resistance(df_price)
        key_levels['current_price'] = float(df_price['close'].iloc[-1])
        key_levels['psychological_levels'] = self._find_psychological_levels(key_levels['current_price'])
        
        # 6. Sentiment Indicators
        sentiment = self._calculate_sentiment_indicators(df_price, df_flows)
        
        # 7. Historical Comparison
        historical = self._compare_to_history(df_price, regime_info)
        
        # 8. Macro Correlations (P2 Integration)
        macro_data = self.macro_provider.fetch_macro_series(lookback_days)
        correlations = self.correlation_analyzer.analyze_correlations(df_price['close'], macro_data)
        
        # 9. Overall Confidence
        confidence = self._calculate_confidence_score(
            df_price, df_flows, regime_info, signals, risks
        )
        
        # Build context object
        context = MarketContext(
            timestamp=target_date,
            regime=regime_info,
            signals=signals,
            risks=risks,
            opportunities=opportunities,
            key_levels=key_levels,
            sentiment_indicators=sentiment,
            historical_comparison=historical,
            confidence_score=confidence,
            is_simulation=is_simulation, # Remediation: Set simulation flag
            macro_correlations=correlations, # Add to context
            metadata={
                'data_points': len(df_price),
                'lookback_days': lookback_days,
                'analysis_version': '3.0.0'
            }
        )
        
        return context
    
    def generate_report(
        self,
        context: MarketContext,
        report_type: str = "comprehensive",
        output_format: str = "markdown",
        agent_optimized: bool = True
    ) -> str:
        """
        Generate context-aware report in specified format
        """
        
        if output_format == "json":
            return self._generate_json_report(context, agent_optimized)
        elif output_format == "reasoning":
            return self._generate_reasoning_report(context)
        elif output_format == "structured_json":
            return self._generate_structured_json(context)
        elif output_format == "plain_text":
            return self._generate_plain_text(context, report_type)
        else:  # markdown (default)
            return self._generate_markdown_report(context, report_type, agent_optimized)
    
    def _generate_markdown_report(
        self,
        context: MarketContext,
        report_type: str,
        agent_optimized: bool
    ) -> str:
        """Generate markdown report with regime-aware template"""
        
        # Select template based on regime
        regime = context.regime['current_regime']
        template_map = {
            'bull': 'bull_regime.j2',
            'bear': 'bear_regime.j2',
            'accumulation': 'sideways_regime.j2',
            'distribution': 'sideways_regime.j2',
            'sideways': 'sideways_regime.j2',
            'volatile': 'volatile_regime.j2'
        }
        
        template_name = template_map.get(regime, 'executive_summary.j2')
        
        if report_type == "executive":
            template_name = "executive_summary.j2"
        
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception:
            # Fallback to simple if template missing
            print(f"Warning: Template {template_name} not found. Using backup.")
            return self._generate_simple_markdown(context)

        
        # Build context for template
        template_context = self._build_template_context(context, agent_optimized)
        
        # Render
        report = template.render(**template_context)
        
        return report
    
    def _build_template_context(
        self,
        context: MarketContext,
        agent_optimized: bool
    ) -> Dict[str, Any]:
        """Build context dictionary for Jinja template"""
        
        # remediation: Inject simulation status into narratives
        simulation_prefix = "⚠️ [SIMULATION MODE] " if context.is_simulation else ""
        
        # Generate narrative elements
        executive_summary = simulation_prefix + self.narrative_generator.generate_executive_summary(context)
        regime_narrative = self.narrative_generator.generate_regime_narrative(context)
        signal_narrative = self.narrative_generator.generate_signal_narrative(context)
        risk_narrative = self.narrative_generator.generate_risk_narrative(context)
        
        # Prioritize actions
        actions = self.action_prioritizer.prioritize_actions(context)
        
        # Format data for template
        return {
            # Core context
            'timestamp': context.timestamp.strftime('%Y-%m-%d %H:%M UTC'),
            'regime': context.regime,
            'signals': context.signals,
            'risks': context.risks,
            'opportunities': context.opportunities,
            'key_levels': context.key_levels,
            'sentiment': context.sentiment_indicators,
            'historical': context.historical_comparison,
            'confidence_score': context.confidence_score,
            
            # Narratives
            'executive_summary': executive_summary,
            'regime_narrative': regime_narrative,
            'signal_narrative': signal_narrative,
            'risk_narrative': risk_narrative,
            
            # Actions
            'prioritized_actions': actions,
            
            # Formatting hints
            'agent_optimized': agent_optimized,
            'show_details': not agent_optimized,
            
            # Helper functions
            'format_price': lambda x: f"${x:,.2f}" if x is not None else "N/A",
            'format_percent': lambda x: f"{x:.2f}%" if x is not None else "N/A",
            'format_large_number': lambda x: self._format_large_number(x),
            'confidence_badge': lambda x: self._confidence_badge(x),
            'severity_badge': lambda x: self._severity_badge(x)
        }
    
    def _generate_json_report(self, context: MarketContext, agent_optimized: bool) -> str:
        """Generate JSON report optimized for agent consumption"""
        import json
        
        if agent_optimized:
            # Minimal, high-signal JSON
            report = {
                'timestamp': context.timestamp.isoformat(),
                'regime': {
                    'current': context.regime['current_regime'],
                    'confidence': context.regime['regime_confidence'],
                    'duration_days': context.regime.get('regime_duration_days', 0)
                },
                'signals': [
                    {
                        'type': s['signal_type'],
                        'confidence': s['confidence'],
                        'entry': s.get('entry_price'),
                        'direction': s.get('direction', 'neutral')
                    }
                    for s in context.signals[:5]  # Top 5 only
                ],
                'risks': {
                    'overall_score': context.risks.get('overall_risk_score', 0),
                    'primary_risks': context.risks.get('primary_risks', [])[:3]
                },
                'opportunities': [
                    {
                        'type': o['type'],
                        'priority': o['priority'],
                        'timeframe': o.get('timeframe')
                    }
                    for o in context.opportunities[:3]
                ],
                'key_levels': {
                    'support': context.key_levels.get('nearest_support'),
                    'resistance': context.key_levels.get('nearest_resistance'),
                    'current_price': context.key_levels.get('current_price')
                },
                'sentiment_score': context.sentiment_indicators.get('composite_score', 0.5),
                'confidence': context.confidence_score
            }
        else:
            # Full context
            report = {
                'timestamp': context.timestamp.isoformat(),
                'regime': context.regime,
                'signals': context.signals,
                'risks': context.risks,
                'opportunities': context.opportunities,
                'key_levels': context.key_levels,
                'sentiment_indicators': context.sentiment_indicators,
                'historical_comparison': context.historical_comparison,
                'confidence_score': context.confidence_score,
                'metadata': context.metadata
            }
        
        return json.dumps(report, indent=2, default=str)

    def _generate_reasoning_report(self, context: MarketContext) -> str:
        """Generate reasoning-optimized report using the AgentReasoningAdapter"""
        import json
        from dataclasses import asdict
        
        reasoning_data = self.reasoning_adapter.adapt_context_to_reasoning(context)
        return json.dumps(asdict(reasoning_data), indent=2, default=str)
    
    def _generate_structured_json(self, context: MarketContext) -> str:
        """Generate highly structured JSON for agent reasoning"""
        import json
        
        structured = {
            'metadata': {
                'report_type': 'structured_context',
                'version': '3.0.0',
                'timestamp': context.timestamp.isoformat(),
                'confidence': context.confidence_score
            },
            'market_state': {
                'regime': {
                    'classification': context.regime['current_regime'],
                    'confidence': context.regime['regime_confidence'],
                    'characteristics': self._get_regime_characteristics(context.regime),
                    'expected_behavior': self._get_expected_behavior(context.regime)
                },
                'price_action': {
                    'current_price': context.key_levels.get('current_price'),
                    'trend': self._determine_trend(context),
                    'momentum': context.sentiment_indicators.get('momentum', 'neutral'),
                    'volatility': context.sentiment_indicators.get('volatility_classification', 'normal')
                }
            },
            'decision_factors': {
                'bullish_factors': self._extract_bullish_factors(context),
                'bearish_factors': self._extract_bearish_factors(context),
                'neutral_factors': self._extract_neutral_factors(context),
                'net_bias': self._calculate_net_bias(context)
            },
            'actionable_insights': {
                'high_confidence_setups': [s for s in context.signals if s['confidence'] > 0.8],
                'key_price_levels': {
                    'immediate_support': context.key_levels.get('nearest_support'),
                    'immediate_resistance': context.key_levels.get('nearest_resistance'),
                    'major_support': context.key_levels.get('major_support_zone'),
                    'major_resistance': context.key_levels.get('major_resistance_zone')
                },
                'risk_considerations': [
                    r for r in context.risks.get('primary_risks', [])
                    if r.get('severity') in ['high', 'critical']
                ],
                'opportunities': context.opportunities
            },
            'risk_management': {
                'overall_risk_level': context.risks.get('overall_risk_score', 0.5),
                'position_sizing_guidance': self._get_position_sizing(context),
                'stop_loss_placement': self._get_stop_loss_guidance(context),
                'time_horizon': self._recommend_time_horizon(context)
            },
            'execution_plan': {
                'prioritized_actions': self.action_prioritizer.prioritize_actions(context),
                'timing_considerations': self._get_timing_guidance(context),
                'monitoring_requirements': self._get_monitoring_requirements(context)
            }
        }
        
        return json.dumps(structured, indent=2, default=str)
    
    # === Helper Methods ===
    
    def _load_price_data(self, lookback_days: int) -> pd.DataFrame:
        """Load and prepare price data"""
        file_path = self.data_dir / "btc_price_normalized.csv"
        if not file_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Filter to lookback period
            cutoff = datetime.now() - timedelta(days=lookback_days)
            df = df[df['date'] >= cutoff]
            return df
        except Exception:
            return pd.DataFrame()
    
    def _load_flow_data(self, lookback_days: int) -> pd.DataFrame:
        """Load and prepare flow data"""
        file_path = self.data_dir / "etf_flows_normalized.csv"
        if not file_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            cutoff = datetime.now() - timedelta(days=lookback_days)
            df = df[df['date'] >= cutoff]
            return df
        except Exception:
            return pd.DataFrame()
    
    def _find_psychological_levels(self, price: float) -> List[float]:
        """Identifies round numbers near current price."""
        base = round(price, -4)  # Round to nearest 10k
        return [base - 10000, base, base + 10000]
    
    def _calculate_sentiment_indicators(
        self,
        df_price: pd.DataFrame,
        df_flows: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate sentiment indicators"""
        if df_price.empty: return {}
        
        # Price-based sentiment
        returns_7d = df_price['close'].pct_change(7).iloc[-1] * 100
        returns_30d = df_price['close'].pct_change(30).iloc[-1] * 100
        
        # Volatility
        volatility = df_price['close'].pct_change().tail(30).std() * np.sqrt(365) * 100
        
        # Flow-based sentiment
        if not df_flows.empty and 'flow_usd' in df_flows.columns:
            recent_flows = df_flows[df_flows['date'] >= df_flows['date'].max() - timedelta(days=7)]
            net_flow = recent_flows['flow_usd'].sum()
            flow_sentiment = 'bullish' if net_flow > 0 else 'bearish'
        else:
            net_flow = 0
            flow_sentiment = 'neutral'
        
        # Composite score (-1 to 1)
        # Handle nan
        returns_7d = 0 if pd.isna(returns_7d) else returns_7d
        
        price_component = np.tanh(returns_7d / 10)  # Normalize to -1,1
        flow_component = np.tanh(net_flow / 1e9)  # Normalize by $1B
        
        composite_score = (price_component * 0.6 + flow_component * 0.4)
        
        return {
            'composite_score': float(composite_score),
            'composite_label': self._score_to_label(composite_score),
            'price_momentum': {
                '7d_return': float(returns_7d),
                '30d_return': float(returns_30d) if not pd.isna(returns_30d) else 0.0,
                'trend': 'bullish' if returns_7d > 0 else 'bearish'
            },
            'volatility': {
                'annualized': float(volatility) if not pd.isna(volatility) else 0.0,
                'classification': self._classify_volatility(volatility)
            },
            'flow_sentiment': {
                'net_flow_7d': float(net_flow),
                'direction': flow_sentiment,
                'magnitude': self._classify_flow_magnitude(net_flow)
            }
        }
    
    def _compare_to_history(
        self,
        df_price: pd.DataFrame,
        regime_info: Dict
    ) -> Dict[str, Any]:
        """Compare current conditions to historical patterns"""
        if df_price.empty: return {}
        
        current_price = df_price['close'].iloc[-1]
        
        # Historical percentile
        percentile = (df_price['close'] < current_price).sum() / len(df_price) * 100
        
        # Distance from historical high/low
        hist_high = df_price['high'].max()
        hist_low = df_price['low'].min()
        
        distance_from_high = ((current_price - hist_high) / hist_high) * 100
        distance_from_low = ((current_price - hist_low) / hist_low) * 100
        
        return {
            'price_percentile': float(percentile),
            'distance_from_high_pct': float(distance_from_high),
            'distance_from_low_pct': float(distance_from_low),
            'historical_high': float(hist_high),
            'historical_low': float(hist_low),
            'interpretation': self._interpret_historical_position(percentile, distance_from_high)
        }
    
    def _calculate_confidence_score(
        self,
        df_price: pd.DataFrame,
        df_flows: pd.DataFrame,
        regime_info: Dict,
        signals: List[Dict],
        risks: Dict
    ) -> float:
        """Calculate overall confidence in analysis"""
        
        factors = []
        
        # Data freshness (0-1)
        latest_date = df_price['date'].max()
        hours_old = (datetime.now() - latest_date).total_seconds() / 3600
        freshness_score = max(0, 1 - (hours_old / 24))
        factors.append(('freshness', freshness_score, 0.2))
        
        # Data completeness (0-1)
        # Approximate
        completeness = 1.0 # assume valid if loaded
        factors.append(('completeness', completeness, 0.15))
        
        # Regime confidence
        regime_confidence = regime_info.get('regime_confidence', 0.5)
        factors.append(('regime', regime_confidence, 0.25))
        
        # Signal strength
        if signals:
            avg_signal_confidence = np.mean([s['confidence'] for s in signals])
        else:
            avg_signal_confidence = 0.5
        factors.append(('signals', avg_signal_confidence, 0.2))
        
        # Risk clarity (lower risk score = higher confidence)
        risk_score = risks.get('overall_risk_score', 0.5)
        risk_confidence = 1 - risk_score
        factors.append(('risk_clarity', risk_confidence, 0.2))
        
        # Weighted average
        confidence = sum(score * weight for _, score, weight in factors)
        
        return float(confidence)
    
    def _format_large_number(self, value: float) -> str:
        """Format large numbers with K/M/B suffix"""
        if value is None: return "N/A"
        if abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    
    def _confidence_badge(self, confidence: float) -> str:
        """Generate confidence badge"""
        if confidence >= 0.8:
            return "🟢 HIGH"
        elif confidence >= 0.6:
            return "🟡 MEDIUM"
        else:
            return "🔴 LOW"
    
    def _severity_badge(self, severity: str) -> str:
        """Generate severity badge"""
        badges = {
            'critical': '🔴 CRITICAL',
            'high': '🟠 HIGH',
            'medium': '🟡 MEDIUM',
            'low': '🟢 LOW',
            'info': '🔵 INFO'
        }
        return badges.get(severity.lower(), severity)
    
    def _score_to_label(self, score: float) -> str:
        """Convert composite score to label"""
        if score > 0.6:
            return "strongly_bullish"
        elif score > 0.2:
            return "bullish"
        elif score > -0.2:
            return "neutral"
        elif score > -0.6:
            return "bearish"
        else:
            return "strongly_bearish"
    
    def _classify_volatility(self, annualized_vol: float) -> str:
        """Classify volatility level"""
        if pd.isna(annualized_vol): return "unknown"
        if annualized_vol < 30:
            return "low"
        elif annualized_vol < 60:
            return "normal"
        elif annualized_vol < 100:
            return "high"
        else:
            return "extreme"
    
    def _classify_flow_magnitude(self, net_flow: float) -> str:
        """Classify flow magnitude"""
        abs_flow = abs(net_flow)
        if abs_flow < 100e6:
            return "minimal"
        elif abs_flow < 500e6:
            return "moderate"
        elif abs_flow < 1e9:
            return "significant"
        else:
            return "massive"
    
    def _interpret_historical_position(self, percentile: float, distance_from_high: float) -> str:
        """Interpret historical price position"""
        if percentile > 95 and distance_from_high > -5:
            return "Near all-time highs - overbought territory"
        elif percentile > 75:
            return "Upper historical range - elevated valuation"
        elif percentile > 25:
            return "Mid-range historical levels - neutral zone"
        elif percentile > 5:
            return "Lower historical range - potential value zone"
        else:
            return "Near historical lows - deep value or distress"
    
    def _find_flow_pivots(self, df: pd.DataFrame) -> List[float]:
        """Detect pivot points based on volume flow nodes."""
        return []
    
    def _find_flow_pivots(self, df: pd.DataFrame) -> List[float]:
        return []
    
    def _get_regime_characteristics(self, regime: Dict) -> List[str]:
        regime_map = {
            'bull': ['Sustained uptrend', 'Higher highs/lows', 'Strong momentum'],
            'bear': ['Sustained downtrend', 'Lower highs/lows', 'Weak momentum'],
            'sideways': ['Range-bound', 'Lack of directional conviction', 'Mean reversion']
        }
        return regime_map.get(regime['current_regime'], [])
    
    def _get_expected_behavior(self, regime: Dict) -> str:
        behavior_map = {
            'bull': "Expect trend continuation with pullbacks to support",
            'bear': "Expect trend continuation with bounces to resistance",
            'sideways': "Expect range-bound trading between support/resistance"
        }
        return behavior_map.get(regime['current_regime'], "Monitor for regime change")
    
    def _determine_trend(self, context: MarketContext) -> str:
        momentum = context.sentiment_indicators.get('price_momentum', {})
        return momentum.get('trend', 'neutral')
    
    def _extract_bullish_factors(self, context: MarketContext) -> List[str]:
        factors = []
        
        if context.regime['current_regime'] in ['bull', 'accumulation']:
            factors.append(f"Bullish regime: {context.regime['current_regime']}")
        
        momentum = context.sentiment_indicators.get('price_momentum', {})
        if momentum.get('7d_return', 0) > 0:
            factors.append(f"Positive 7-day momentum: {momentum.get('7d_return'):.1f}%")
        
        flow = context.sentiment_indicators.get('flow_sentiment', {})
        if flow.get('direction') == 'bullish':
            factors.append(f"Positive ETF flows: {self._format_large_number(flow.get('net_flow_7d', 0))}")
        
        return factors
    
    def _extract_bearish_factors(self, context: MarketContext) -> List[str]:
        factors = []
        
        if context.regime['current_regime'] in ['bear', 'distribution']:
            factors.append(f"Bearish regime: {context.regime['current_regime']}")
        
        momentum = context.sentiment_indicators.get('price_momentum', {})
        if momentum.get('7d_return', 0) < 0:
            factors.append(f"Negative 7-day momentum: {momentum.get('7d_return'):.1f}%")
        
        flow = context.sentiment_indicators.get('flow_sentiment', {})
        if flow.get('direction') == 'bearish':
            factors.append(f"Negative ETF flows: {self._format_large_number(flow.get('net_flow_7d', 0))}")
        
        return factors
    
    def _extract_neutral_factors(self, context: MarketContext) -> List[str]:
        factors = []
        
        vol = context.sentiment_indicators.get('volatility', {})
        if vol.get('classification') in ['normal', 'low']:
            factors.append("Normal volatility environment")
        
        return factors
    
    def _calculate_net_bias(self, context: MarketContext) -> str:
        bullish = len(self._extract_bullish_factors(context))
        bearish = len(self._extract_bearish_factors(context))
        
        if bullish > bearish + 1:
            return "bullish"
        elif bearish > bullish + 1:
            return "bearish"
        else:
            return "neutral"
    
    def _get_position_sizing(self, context: MarketContext) -> str:
        risk_score = context.risks.get('overall_risk_score', 0.5)
        
        if risk_score > 0.7:
            return "Reduce position sizes to 25-50% of normal"
        elif risk_score > 0.5:
            return "Moderate position sizes at 50-75% of normal"
        else:
            return "Normal position sizing appropriate"
    
    def _get_stop_loss_guidance(self, context: MarketContext) -> Dict:
        support = context.key_levels.get('nearest_support')
        current = context.key_levels.get('current_price')
        
        if support and current:
            distance = ((current - support) / current) * 100
            return {
                'recommended_level': support,
                'distance_pct': distance,
                'rationale': "Below nearest support level"
            }
        return {}
    
    def _recommend_time_horizon(self, context: MarketContext) -> str:
        regime = context.regime['current_regime']
        volatility = context.sentiment_indicators.get('volatility', {}).get('classification')
        
        if regime in ['bull', 'bear'] and volatility != 'extreme':
            return "swing_trading_3-10_days"
        elif volatility == 'extreme':
            return "intraday_scalping"
        else:
            return "position_trading_10-30_days"
    
    def _get_timing_guidance(self, context: MarketContext) -> List[str]:
        guidance = []
        
        regime = context.regime['current_regime']
        if regime == 'bull':
            guidance.append("Buy dips to support levels")
        elif regime == 'bear':
            guidance.append("Sell bounces to resistance levels")
        
        return guidance
    
    def _get_monitoring_requirements(self, context: MarketContext) -> List[str]:
        requirements = [
            f"Monitor {context.key_levels.get('nearest_support')} support level",
            f"Watch for regime change signals",
            "Track ETF flow direction"
        ]
        return requirements
    
    def _generate_simple_markdown(self, context: MarketContext) -> str:
        """Fallback markdown generation"""
        report = "# Market Report\n\n"
        if context.is_simulation:
            report += "⚠️ **SIMULATION MODE ACTIVE** - Data is synthetic/simulated.\n\n"
        report += f"Regime: {context.regime['current_regime']}\nPrice: {context.key_levels['current_price']}"
        return report
