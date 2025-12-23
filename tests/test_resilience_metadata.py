import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.microanalyst.agents.agent_coordinator import AgentCoordinator
from src.microanalyst.agents.debate_swarm import run_adversarial_debate

@pytest.mark.asyncio
async def test_coordinator_simulation_mode_propagation():
    """Verify that coordinator flags simulation_mode when data collection fails."""
    coordinator = AgentCoordinator()
    
    # Mock handle_data_collection to return a fallback
    mock_fallback_result = {
        "raw_price_history": {},
        "fallback_active": True,
        "fallback_reason": "Mocked API Failure",
        "meta": {"source": "simulation"}
    }
    
    with patch("src.microanalyst.agents.tasks.data_collection.handle_data_collection", 
               return_value=asyncio.Future()):
        # We need to set the value of the future
        with patch("src.microanalyst.agents.registry.registry.get_handler", 
                   return_value=lambda x: asyncio.sleep(0, result=mock_fallback_result)):
            
            # This is complex to mock registry directly, so let's mock handle_data_collection 
            # and ensure coordinator's _execute_agent_task returns it.
            
            async def mock_handler(inputs):
                return mock_fallback_result
            
            with patch.dict("src.microanalyst.agents.registry.registry._handlers", {
                "DATA_COLLECTOR": mock_handler
            }):
                result = await coordinator.execute_multi_agent_workflow(
                    "comprehensive_analysis", 
                    {"lookback_days": 1}
                )
                
                assert result['simulation_mode'] is True
                assert result['component_metadata']['collect_data']['simulated'] is True
                assert result['component_metadata']['collect_data']['reason'] == "Mocked API Failure"

@pytest.mark.asyncio
async def test_debate_swarm_simulation_mode_aggregation():
    """Verify that run_adversarial_debate aggregates simulation_mode from nodes."""
    # Mock context with simulation_mode active
    context = {
        "ground_truth": {"regime": "Stable"},
        "market_data": {"price": 100},
        "simulation_mode": True # Already flagged by collector
    }
    
    # Even if agents are live, if collector was simulated, final thesis should be simulated.
    # However, let's also test if a node triggers it.
    
    with patch("src.microanalyst.agents.debate_swarm.get_openrouter_llm", return_value=None):
        # When LLM is None, agents return fallback_active: True
        result = run_adversarial_debate(context)
        assert result['simulation_mode'] is True
