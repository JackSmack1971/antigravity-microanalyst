import pytest
from src.microanalyst.agents.reasoning_adapter import ReasoningNode, StructuredMarketIntelligence
from datetime import datetime

def test_reasoning_node_creation():
    """Verify that ReasoningNode can be initialized with correct types."""
    node = ReasoningNode(
        claim="Market is bullish",
        evidence=["Price up 10%", "Flows positive"],
        confidence=0.85,
        reasoning_chain=["Analyzed trend", "Validated flows"],
        counterarguments=["Low volume"],
        temporal_validity="current",
        source_lineage=["price_data.csv"],
        agent_actions=["Buy dips"]
    )
    assert node.claim == "Market is bullish"
    assert node.confidence == 0.85
    assert len(node.evidence) == 2
    assert "Low volume" in node.counterarguments

def test_structured_intelligence_structure():
    """Verify StructuredMarketIntelligence container integrity."""
    node = ReasoningNode(
        claim="Support holds",
        evidence=["95k bounce"],
        confidence=0.9,
        reasoning_chain=["S/R flip"],
        counterarguments=[],
        temporal_validity="short-term",
        source_lineage=[],
        agent_actions=[]
    )
    
    intel = StructuredMarketIntelligence(
        summary="Bullish outlook",
        reasoning_graph=[node],
        decision_tree={"if": "price > 100k", "then": "moon"},
        uncertainty_quantification={"low_vol": 0.3},
        recommended_workflows=["standard_audit"],
        validation_queries=["Is it moon?"]
    )
    
    assert len(intel.reasoning_graph) == 1
    assert intel.reasoning_graph[0].claim == "Support holds"
    assert intel.decision_tree["then"] == "moon"
    assert "low_vol" in intel.uncertainty_quantification

if __name__ == "__main__":
    pytest.main([__file__])
