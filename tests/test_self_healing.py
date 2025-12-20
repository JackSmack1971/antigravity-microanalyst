import asyncio
import json
from datetime import datetime
from pathlib import Path
from src.microanalyst.agents.self_healing import SelfHealingEngine, AllSourcesFailedError
import os

# Set PYTHONPATH to project root
os.environ["PYTHONPATH"] = os.getcwd()

# Mock operation that fails for specific source(s)
async def mock_load_data(source_id: str, fail_sources: list = None, transient=False, **kwargs):
    if fail_sources and source_id in fail_sources:
        if transient:
            # Only fail once
            fail_sources.remove(source_id)
            print(f"  [Mock] Transient failure for {source_id}")
        else:
            print(f"  [Mock] Persistent failure for {source_id}")
        raise ConnectionError(f"Simulated failure for {source_id}")
    
    print(f"  [Mock] Success for {source_id}")
    return {"price": 95000, "source": source_id}

async def test_self_healing():
    print("Testing Self-Healing Engine...")
    engine = SelfHealingEngine(cache_dir="tests/mock_cache")
    
    # Setup mock cache for degradation test
    cache_path = Path("tests/mock_cache/test_etf_flows_checkpoint.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump({"etf_flow": 500, "timestamp": "yesterday"}, f)

    # 1. Test Transient Failure (Retry)
    print("\n[Scenario: Transient Failure]")
    fail_list = ["twelvedata"]
    result = await engine.execute_with_recovery(
        mock_load_data, "price_data", "twelvedata", fail_sources=fail_list, transient=True
    )
    print(f"Result Status: {result['status']}, Attempts: {result.get('attempts')}")
    assert result["status"] == "success"
    assert result["attempts"] > 1

    # 2. Test Persistent Failure (Substitution)
    print("\n[Scenario: Persistent Primary Failure -> Substitute]")
    fail_list = ["twelvedata"] # Primary
    result = await engine.execute_with_recovery(
        mock_load_data, "price_data", "twelvedata", fail_sources=fail_list
    )
    print(f"Result Status: {result['status']}, Final Source: {result['source']}")
    assert result["status"] == "success_fallback"
    assert result["source"] == "coingecko_api"

    # 3. Test Circuit Breaker
    print("\n[Scenario: Circuit Breaker]")
    fail_list = ["bad_source", "bad_source", "bad_source"] # Force 3 failures
    try:
        for _ in range(3):
            await engine.execute_with_recovery(mock_load_data, "unknown", "bad_source", fail_sources=["bad_source"])
    except Exception:
        pass
    
    print(f"Circuit Open for bad_source: {engine._is_circuit_open('bad_source')}")
    assert engine._is_circuit_open("bad_source") is True

    # 4. Test Degradation (Cache Fallback)
    print("\n[Scenario: All Sources Failed -> Degrade]")
    # etf_flows strategy has degradation_acceptable=True
    fail_list = ["bitbo", "btcetffundflow", "primary"]
    result = await engine.execute_with_recovery(
        mock_load_data, "etf_flows", "primary", fail_sources=fail_list
    )
    print(f"Result Status: {result['status']}, Warning: {result.get('warning')}")
    assert result["status"] == "degraded"
    assert "stale data" in result["warning"]

    print("\nAll self-healing scenarios passed!")
    
    # Cleanup
    if cache_path.exists():
        cache_path.unlink()

if __name__ == "__main__":
    asyncio.run(test_self_healing())
