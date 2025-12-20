import json
from datetime import datetime
from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer, MarketContext
from src.microanalyst.agents.reasoning_adapter import AgentReasoningAdapter

def test_reasoning_adapter():
    print("Testing AgentReasoningAdapter...")
    
    # Mock MarketContext
    context = MarketContext(
        timestamp=datetime.now(),
        regime={
            'current_regime': 'bull',
            'regime_confidence': 0.85,
            'regime_duration_days': 12
        },
        signals=[
            {'signal_type': 'MA_CROSS', 'confidence': 0.9, 'direction': 'bullish'}
        ],
        risks={
            'overall_risk_score': 0.3,
            'max_drawdown': 5.2,
            'volatility_annualized': 45.0,
            'primary_risks': [{'risk': 'low_liquidity', 'severity': 'medium'}]
        },
        opportunities=[],
        key_levels={
            'current_price': 85000.0,
            'nearest_support': 82000.0,
            'nearest_resistance': 88000.0
        },
        sentiment_indicators={
            'price_momentum': {'trend': 'bullish'},
            'flow_sentiment': {'direction': 'bullish', 'net_flow_7d': 1200000000.0}
        },
        historical_comparison={},
        confidence_score=0.88,
        metadata={'divergence_score': 0.1}
    )
    
    synthesizer = ContextSynthesizer()
    report = synthesizer.generate_report(context, output_format="reasoning")
    
    data = json.loads(report)
    print(f"Report Summary: {data['summary']}")
    
    # Verify Reasoning Nodes
    nodes = data['reasoning_graph']
    print(f"Number of Reasoning Nodes: {len(nodes)}")
    for node in nodes:
        print(f"- Claim: {node['claim']} (Confidence: {node['confidence']})")
        assert 'claim' in node
        assert 'evidence' in node
        assert 'reasoning_chain' in node

    # Verify Decision Tree
    tree = data['decision_tree']
    print(f"Decision Tree Root Question: {tree['root']['question']}")
    assert tree['root']['active_branch'] == 'bull'
    
    # Verify Uncertainties
    uncertainties = data['uncertainty_quantification']
    print(f"Uncertainties: {uncertainties}")
    assert 'regime_stability' in uncertainties
    
    print("AgentReasoningAdapter test passed!")

if __name__ == "__main__":
    test_reasoning_adapter()
