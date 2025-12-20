import pytest
import os
import json
from src.microanalyst.memory.episodic_memory import EpisodicMemory
from src.microanalyst.agents.reflexion import ReflexionEngine

TEST_MEMORY_FILE = "tests/test_memory.json"

@pytest.fixture
def memory():
    # Setup
    if os.path.exists(TEST_MEMORY_FILE):
        os.remove(TEST_MEMORY_FILE)
    mem = EpisodicMemory(storage_path=TEST_MEMORY_FILE)
    yield mem
    # Teardown
    if os.path.exists(TEST_MEMORY_FILE):
        os.remove(TEST_MEMORY_FILE)

def test_full_reflexion_cycle(memory):
    # 1. Store Decision (Mock from Swarm)
    context = {"symbol": "BTC", "ground_truth": {"regime": "bull_trending"}}
    decision_data = {"decision": "BUY", "reasoning": "Strong momentum"}
    
    bid = memory.store_decision(context, decision_data)
    assert bid is not None
    
    # 2. Update Outcome (Simulate 24h later - BAD TRADE)
    # Bought, but price dropped 5%
    memory.update_outcome(bid, actual_roi=-0.05)
    
    rec = memory.load_memory()[0]
    assert rec['outcome']['actual_roi'] == -0.05
    
    # 3. Run Reflexion Engine
    engine = ReflexionEngine(memory)
    critiques = engine.run_daily_reflection()
    
    assert len(critiques) == 1
    assert "CRITICAL FAILURE" in critiques[0]
    
    # 4. Verify Reflection stored
    rec_after = memory.load_memory()[0]
    assert rec_after['reflection'] is not None
    assert "Tighten ADX" in rec_after['reflection']

def test_reflexion_success_cycle(memory):
    # 1. Store Decision
    context = {"symbol": "BTC", "ground_truth": {"regime": "bull_trending"}}
    decision_data = {"decision": "BUY", "reasoning": "Standard trend"}
    bid = memory.store_decision(context, decision_data)
    
    # 2. Update Outcome (GOOD TRADE)
    memory.update_outcome(bid, actual_roi=0.10)
    
    # 3. Reflect
    engine = ReflexionEngine(memory)
    critiques = engine.run_daily_reflection()
    
    assert "SUCCESS" in critiques[0]
