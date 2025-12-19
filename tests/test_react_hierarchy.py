import pytest
from src.microanalyst.agents.tool_registry import ToolRegistry
from src.microanalyst.agents.react_agent import ReActAgent
from src.microanalyst.agents.swarm_supervisor import SwarmSupervisor

def test_tool_registry():
    registry = ToolRegistry()
    registry.register("test_tool", lambda x: x * 2, "Doubles input")
    
    assert registry.get_tool("test_tool") is not None
    assert registry.execute("test_tool", x=5) == 10
    assert "Doubles input" in registry.list_tools()

def test_react_agent_loop():
    registry = ToolRegistry()
    registry.register("calculate_rsi", lambda period: 75, "RSI")
    
    agent = ReActAgent("TechnicalSpecialist", "Tech Expert", registry)
    result = agent.run_task("Check RSI", {})
    
    # Based on mock logic in ReActAgent._simulate_llm_thought
    assert "Bearish Divergence" in result

def test_swarm_hierarchy():
    supervisor = SwarmSupervisor()
    result = supervisor.distribute_task({"timestamp": "now"})
    
    assert "technical_view" in result
    assert "sentiment_view" in result
    assert "Bearish Divergence" in result['technical_view']
    assert "Sentiment Overheated" in result['sentiment_view']
