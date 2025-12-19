import pytest
import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.append(os.getcwd())

from src.microanalyst.agents.agent_coordinator import AgentCoordinator, AgentRole

@pytest.mark.asyncio
async def test_agent_coordinator_full_flow():
    """
    Test the full multi-agent workflow with the newly integrated data pipelines.
    """
    coordinator = AgentCoordinator()
    
    # Execute the workflow
    # Using 'comprehensive_analysis' triggers the full chain: 
    # Collector -> Validator -> All Analysts -> Synthesizer -> Decision Maker
    result = await coordinator.execute_multi_agent_workflow(
        objective="comprehensive_analysis",
        parameters={"lookback_days": 30, "sources": ["risk", "sentiment"]}
    )
    
    # 1. Verify Workflow Completion
    assert "final_result" in result
    assert "decision" in result['final_result']
    assert len(result['tasks_executed']) > 0
    
    # 2. Inspect Intermediate Results (from coordinator.results)
    results = coordinator.results
    
    # Data Collector Output
    collector_res = results['collect_data']
    assert "price" in collector_res, "Collector should produce 'price' key from AgentDatasetBuilder"
    assert "risk" in collector_res, "Collector should produce 'risk' key"
    assert "sentiment" in collector_res, "Collector should produce 'sentiment' key"
    assert "raw_price_history" in collector_res, "Collector should pass raw history"
    
    # Technical Analyst Output
    tech_res = results['analyze_technical']
    assert "technical_signals" in tech_res
    # Since we use random data, we might or might not have signals, but key should exist
    assert isinstance(tech_res['technical_signals'], list)
    
    # Risk Analyst Output
    risk_res = results['analyze_risk']
    assert "risk_assessment" in risk_res
    assert "recommended_sizing_pct" in risk_res
    # Check that real calc happened
    assert isinstance(risk_res['recommended_sizing_pct'], float)
    
    # Synthesizer Output
    synth_res = results['synthesize']
    assert "market_context" in synth_res
    context = synth_res['market_context']
    assert "bias" in context
    assert context['bias'] in ["BULLISH", "BEARISH", "NEUTRAL"]
    
    print("\nWorkflow Execution Summary:")
    print(json.dumps(result['final_result'], indent=2))
