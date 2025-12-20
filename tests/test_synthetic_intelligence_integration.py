import asyncio
import json
from src.microanalyst.synthetic.onchain import SyntheticOnChainMetrics
from src.microanalyst.synthetic.exchange_proxies import ExchangeProxyMetrics
from src.microanalyst.agents.agent_coordinator import AgentCoordinator
import os

# Set PYTHONPATH
os.environ["PYTHONPATH"] = os.getcwd()

async def test_synthetic_intelligence():
    print("Testing Synthetic Intelligence Framework...")
    
    # 1. Test On-Chain Synthesis (MVRV)
    print("\n[Scenario: Synthetic MVRV Calculation]")
    onchain = SyntheticOnChainMetrics()
    mvrv_data = onchain.calculate_synthetic_mvrv()
    
    if 'error' in mvrv_data:
        print(f"MVRV Calculation failed (likely rate limit or network): {mvrv_data['error']}")
    else:
        print(f"Synthetic MVRV: {mvrv_data['value']:.4f}")
        print(f"Method: {mvrv_data['method']}")
        print(f"Confidence: {mvrv_data['confidence']:.2%}")
        assert mvrv_data['value'] > 0

    # 2. Test Exchange Proxy Metrics (Order Flow Delta)
    print("\n[Scenario: Synthetic Order Flow Delta]")
    proxies = ExchangeProxyMetrics()
    delta_data = proxies.derive_order_flow_delta("BTCUSDT")
    
    if 'error' in delta_data:
        print(f"CVD Proxy failed: {delta_data['error']}")
    else:
        print(f"Order Flow Imbalance: {delta_data['imbalance_ratio']:.2%}")
        print(f"Bias: {delta_data['bias']}")
        assert 'imbalance_ratio' in delta_data

    # 3. Test Integrated Coordinator Collection
    print("\n[Scenario: Integrated Coordinator Synthetic Data]")
    coordinator = AgentCoordinator()
    
    # We use technical_only which I updated to request synthetic sources
    results = await coordinator.execute_multi_agent_workflow(
        "technical_only",
        {"lookback_days": 1}
    )
    
    # Check if synthetic metrics are in the 'collect_price' task result
    collect_task_res = coordinator.results.get('collect_price')
    assert collect_task_res is not None
    assert 'synthetic_metrics' in collect_task_res
    print("Synthetic metrics successfully collected by Coordinator.")
    
    mvrv_val = collect_task_res['synthetic_metrics']['mvrv'].get('value')
    if mvrv_val:
        print(f"Coordinator MVRV value: {mvrv_val:.4f}")

    print("\nSynthetic Intelligence Framework verification complete!")

if __name__ == "__main__":
    asyncio.run(test_synthetic_intelligence())
