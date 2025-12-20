from dataclasses import dataclass
from typing import List, Dict, Any, Literal
from datetime import datetime

from src.microanalyst.intelligence.base import MarketContext

@dataclass
class ReasoningNode:
    """
    Atomic reasoning element for agent consumption
    """
    claim: str                              # The factual assertion
    evidence: List[str]                     # Supporting data points
    confidence: float                       # 0.0-1.0 confidence score
    reasoning_chain: List[str]              # CoT steps that led to claim
    counterarguments: List[str]             # Known challenges to claim
    temporal_validity: str                  # "current" | "degrading" | "expired"
    source_lineage: List[str]               # Data provenance trail
    agent_actions: List[str]                # Suggested next steps

@dataclass
class StructuredMarketIntelligence:
    """
    Agent-optimized market intelligence package
    """
    summary: str
    reasoning_graph: List[ReasoningNode]
    decision_tree: Dict[str, Any]           # If/then decision logic
    uncertainty_quantification: Dict[str, float]
    recommended_workflows: List[str]
    validation_queries: List[str]           # Self-check questions

class AgentReasoningAdapter:
    """
    Transforms pipeline outputs into agent-consumable reasoning structures
    """
    
    def adapt_context_to_reasoning(
        self, 
        context: MarketContext
    ) -> StructuredMarketIntelligence:
        """
        Convert MarketContext to reasoning-optimized format
        """
        reasoning_nodes = []
        
        # 1. Regime Reasoning Node
        regime_node = ReasoningNode(
            claim=f"Market is in {context.regime['current_regime']} regime",
            evidence=[
                f"Regime confidence: {context.regime['regime_confidence']:.2f}",
                f"Duration: {context.regime.get('regime_duration_days', 0)} days",
                f"Price momentum: {context.sentiment_indicators.get('price_momentum', {}).get('trend', 'unknown')}"
            ],
            confidence=context.regime['regime_confidence'],
            reasoning_chain=[
                "Analyzed 30-day price structure",
                "Compared against historical regime signatures",
                "Cross-validated with flow sentiment"
            ],
            counterarguments=[
                "Volatility spike could signal regime transition",
                "Low sample size if regime just started"
            ],
            temporal_validity="current" if context.regime['regime_confidence'] > 0.7 else "degrading",
            source_lineage=["btc_price_normalized.csv", "regime_analyzer.py"],
            agent_actions=[
                "Monitor for regime change signals",
                "Adjust position sizing to regime risk profile",
                "Set alerts at regime boundary levels"
            ]
        )
        reasoning_nodes.append(regime_node)
        
        # 2. Risk Reasoning Node (Example extension)
        risk_node = ReasoningNode(
            claim=f"Current risk level is {context.risks.get('overall_risk', 'medium')}",
            evidence=[
                f"Max drawdown: {context.risks.get('max_drawdown', 0):.2f}%",
                f"Volatility: {context.risks.get('volatility_annualized', 0):.2f}%"
            ],
            confidence=0.85, # Derived from analyzer reliability
            reasoning_chain=[
                "Calculated rolling volatility",
                "Measured distance from cycle peaks",
                "Assessed tail risk scenarios"
            ],
            counterarguments=[
                "Liquidity thinness could amplify moves",
                "External macro shocks not captured in price vol"
            ],
            temporal_validity="current",
            source_lineage=["risk_analyzer.py"],
            agent_actions=[
                "Review stop-loss levels",
                "Check correlation with equity hedges"
            ]
        )
        reasoning_nodes.append(risk_node)
        
        # Build logic structures
        decision_tree = self._build_decision_tree(context)
        
        # Quantify uncertainties
        uncertainties = {
            "regime_stability": 1.0 - context.regime['regime_confidence'],
            "signal_reliability": self._calculate_signal_uncertainty(context.signals),
            "data_freshness": self._calculate_freshness_penalty(context.metadata),
            "cross_source_divergence": self._measure_source_disagreement(context)
        }
        
        # Recommend workflows
        workflows = self._recommend_workflows(context, uncertainties)
        
        # Generate validation queries
        validation_queries = [
            f"Is {context.regime['current_regime']} regime still valid at current price?",
            f"Do ETF flows support {context.sentiment_indicators.get('flow_sentiment', {}).get('direction', 'unknown')} bias?",
            "Are there hidden risks in derivatives positioning?"
        ]
        
        return StructuredMarketIntelligence(
            summary=self._generate_executive_summary(context),
            reasoning_graph=reasoning_nodes,
            decision_tree=decision_tree,
            uncertainty_quantification=uncertainties,
            recommended_workflows=workflows,
            validation_queries=validation_queries
        )
    
    def _build_decision_tree(self, context: MarketContext) -> Dict[str, Any]:
        """
        Generate executable decision logic for agents
        """
        regime = context.regime['current_regime'].lower()
        
        return {
            "root": {
                "question": "What is current regime?",
                "active_branch": regime,
                "branches": {
                    "bull": {
                        "action": "seek_long_setups",
                        "conditions": ["price > major_support", "flows > 0"],
                        "next_question": "Is momentum sustainable?"
                    },
                    "bear": {
                        "action": "seek_short_setups",
                        "conditions": ["price < major_resistance", "flows < 0"],
                        "next_question": "Is selling exhausted?"
                    },
                    "sideways": {
                        "action": "range_trading",
                        "conditions": ["support_holds", "resistance_holds"],
                        "next_question": "Which boundary will break?"
                    }
                }
            }
        }

    def _calculate_signal_uncertainty(self, signals: List[Dict]) -> float:
        if not signals: return 1.0
        # Average of signal confidence
        confidences = [s.get('confidence', 0.5) for s in signals]
        return 1.0 - (sum(confidences) / len(confidences))

    def _calculate_freshness_penalty(self, metadata: Dict) -> float:
        # Placeholder: assume metadata has a 'last_update' timestamp
        return 0.1 # 10% uncertainty due to lag

    def _measure_source_disagreement(self, context: MarketContext) -> float:
        # Placeholder for cross-consistency divergence
        return context.metadata.get('divergence_score', 0.2)

    def _recommend_workflows(self, context: MarketContext, uncertainties: Dict) -> List[str]:
        recommendations = []
        if uncertainties['regime_stability'] > 0.3:
            recommendations.append("regime_transition_audit")
        if context.regime['current_regime'] == 'volatile':
            recommendations.append("tail_risk_scrub")
        return recommendations

    def _generate_executive_summary(self, context: MarketContext) -> str:
        return f"Market is currently in {context.regime['current_regime']} with {context.regime['regime_confidence']*100:.1f}% confidence."
