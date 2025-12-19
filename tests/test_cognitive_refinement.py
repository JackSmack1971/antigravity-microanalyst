import pytest
import os
import shutil
from src.microanalyst.memory.episodic_memory import EpisodicMemory
from src.microanalyst.intelligence.prompt_engine import PromptEngine

TEST_MEM_PATH = "tests/test_cognitive_mem.json"

@pytest.fixture
def clean_memory():
    if os.path.exists(TEST_MEM_PATH):
        os.remove(TEST_MEM_PATH)
    mem = EpisodicMemory(storage_path=TEST_MEM_PATH)
    yield mem
    if os.path.exists(TEST_MEM_PATH):
        os.remove(TEST_MEM_PATH)

def test_constraint_injection_high_vol():
    engine = PromptEngine()
    dataset = {
        "ground_truth": {"regime": "high_volatility"},
        "price": {"current": 50000}
    }
    
    prompt = engine.construct_synthesizer_prompt(dataset)
    
    # Check for Constraints (Tech 4)
    assert "CRITICAL CONSTRAINTS" in prompt
    assert "REDUCE SIZE by 50%" not in prompt # Old static string removed
    assert "50% of capital" in prompt # New ConstraintEnforcer output
    assert "LEVERAGE_GT_2X" in prompt # Forbidden action

def test_reflexion_injection(clean_memory):
    # 1. Store a lesson
    clean_memory.store_decision({"s": "t"}, {"d": "x"})
    # Manually hack reflection for testing (since we test reflexion engine elsewhere)
    recs = clean_memory.load_memory()
    clean_memory.add_reflection(recs[0]['id'], "LESSON: Don't chase pumps.")
    
    # 2. Generate prompt
    engine = PromptEngine(memory=clean_memory)
    dataset = {"ground_truth": {"regime": "bull_trending"}}
    
    prompt = engine.construct_synthesizer_prompt(dataset)
    
    # Check for Lessons (Tech 2)
    assert "LESSONS LEARNED" in prompt
    assert "Don't chase pumps" in prompt

def test_layered_context_structure():
    engine = PromptEngine()
    dataset = {
        "ground_truth": {"regime": "bull_trending"},
        "price": {"current": 100},
        "intelligence": {"predictions": "Up"},
        "macro": {"dummy": 1}
    }
    prompt = engine.construct_synthesizer_prompt(dataset)
    
    # Check for Layers (Tech 3)
    assert "LAYER 1: IMMEDIATE CONTEXT" in prompt
    assert "LAYER 2: TACTICAL CONTEXT" in prompt
    assert "LAYER 3: STRATEGIC CONTEXT" in prompt
