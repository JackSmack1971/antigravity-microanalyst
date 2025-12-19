import pytest
from src.microanalyst.agents.swarm_supervisor import SwarmSupervisor
from src.microanalyst.agents.meta_optimizer import MetaPromptOptimizer

def test_onchain_specialist_execution():
    supervisor = SwarmSupervisor()
    result = supervisor.distribute_task({"timestamp": "test_time"})
    
    # Check if OnChain view exists and logic worked
    assert "onchain_view" in result
    assert "Distribution Risk High" in result['onchain_view']
    assert "OnChain" in result['supervisor_synthesis']

def test_onchain_tools_registered():
    supervisor = SwarmSupervisor()
    # Direct tool check
    assert supervisor.registry.get_tool("fetch_whale_alerts") is not None
    res = supervisor.registry.execute("fetch_whale_alerts")
    assert "WHALE ALERT" in res

def test_meta_prompt_optimization():
    optimizer = MetaPromptOptimizer()
    
    # Simulate repeated failures
    critiques = [
        "Error: RSI was overbought but price mooned. Bad sell.",
        "Error: Used RSI blindly in trend.",
        "Error: RSI divergence ignored."
    ]
    
    result = optimizer.analyze_critiques(critiques)
    
    assert result['status'] == "Optimization Proposal Generated"
    assert result['detected_pattern'] == "RSI_misinterpretation"
    assert "RSI overbought is NOT a sell signal" in result['proposal']

def test_meta_optimizer_no_data():
    optimizer = MetaPromptOptimizer()
    assert optimizer.analyze_critiques([])['status'] == "No critiques to analyze"
