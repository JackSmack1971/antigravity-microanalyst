import asyncio
import pytest
from src.microanalyst.agents.agent_coordinator import AgentCoordinator, AgentRole
import os

# Set PYTHONPATH
os.environ["PYTHONPATH"] = os.getcwd()

@pytest.mark.asyncio
async def test_multi_agent_workflow_integration():
    """Verify that a comprehensive workflow aggregates results from all stages."""
    coordinator = AgentCoordinator()
    objective = "comprehensive_analysis"
    params = {"lookback_days": 60}
    
    result = await coordinator.execute_multi_agent_workflow(objective, params)
    
    assert result['objective'] == objective
    assert 'final_result' in result
    assert result['final_result'] is not None
    
    # Verify that coordinator stored results for intermediate steps
    # Note: agent_coordinator stores results in self.results keyed by task_id
    assert "collect_data" in coordinator.results
    assert "analyze_technical" in coordinator.results
    assert "analyze_sentiment" in coordinator.results
    assert "analyze_risk" in coordinator.results
    assert "synthesize" in coordinator.results
    assert "decide" in coordinator.results
    
    # Verify content of some results
    tech_res = coordinator.results["analyze_technical"]
    assert "technical_signals" in tech_res
    assert len(tech_res["technical_signals"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])
