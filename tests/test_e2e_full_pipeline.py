import asyncio
import pytest
from src.microanalyst.agents.agent_coordinator import AgentCoordinator
from src.microanalyst.agents.trace_system import trace_collector
from pathlib import Path
import os
import json

# Set PYTHONPATH
os.environ["PYTHONPATH"] = os.getcwd()

@pytest.mark.asyncio
async def test_full_agent_pipeline_e2e():
    """
    End-to-End Test:
    1. Orchestrate multi-agent analysis via Coordinator
    2. Implicitly triggers data acquisition simulation
    3. Generates internal reasoning events
    4. Persists execution trace
    5. Verifies trace integrity and narrative accessibility
    """
    print("\nStarting E2E Full Pipeline Test...")
    coordinator = AgentCoordinator()
    
    # Run a comprehensive workflow
    objective = "comprehensive_analysis"
    params = {"lookback_days": 14}
    
    # Step 1: Execute Workflow
    results = await coordinator.execute_multi_agent_workflow(objective, params)
    assert 'final_result' in results
    assert results['final_result'] is not None
    
    # Step 2: Verify Trace Generation
    # Coordinator generates a trace with a specific ID format
    # We can check for files in 'traces' dir generated just now
    trace_files = list(Path("traces").glob(f"trace_comprehensive_analysis_*.json"))
    assert len(trace_files) > 0
    
    latest_trace = sorted(trace_files, key=os.path.getmtime)[-1]
    with open(latest_trace) as f:
        trace_data = json.load(f)
        
    # Step 3: Verify Trace Content (Reasoning + Tool Calls)
    # We expect events for decomposition, start of each agent, and completion
    # 7 tasks * (start + complete) + decomposition = ~15 events
    assert len(trace_data['events']) >= 10
    
    # Verify presence of specific roles in trace
    roles_in_trace = set(e['agent_role'] for e in trace_data['events'])
    assert "data_collector" in roles_in_trace
    assert "analyst_technical" in roles_in_trace
    assert "decision_maker" in roles_in_trace
    
    # Step 4: Verify Explainability Report Generation
    trace_id = trace_data['trace_id']
    report = trace_collector.generate_explainability_report(trace_id)
    assert "# Agent Reasoning Explanation" in report
    assert objective in report
    assert "Decision Chain" in report
    
    print("E2E Pipeline Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_full_agent_pipeline_e2e())
