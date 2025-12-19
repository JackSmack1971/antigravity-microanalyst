import asyncio
import json
from src.microanalyst.synthetic.onchain import SyntheticOnChainMetrics
from src.microanalyst.synthetic.exchange_proxies import ExchangeProxyMetrics
from src.microanalyst.agents.agent_coordinator import AgentCoordinator
import os

# Set PYTHONPATH
os.environ["PYTHONPATH"] = os.getcwd()

async def test_expanded_synthetic_intelligence():
    print("Testing Expanded Synthetic Intelligence Framework...")
    
    # 1. Test On-Chain Synthesis (MVRV, Netflow, SOPR)
    print("\n[Scenario: Advanced On-Chain Metrics]")
    onchain = SyntheticOnChainMetrics()
    
    # MVRV
    mvrv_data = onchain.calculate_synthetic_mvrv()
    if 'error' in mvrv_data:
        print(f"MVRV failed: {mvrv_data['error']}")
    else:
        print(f"Synthetic MVRV: {mvrv_data.get('value', 'N/A')} (Method: {mvrv_data.get('method')})")

    # Netflow
    netflow_data = onchain.calculate_synthetic_exchange_netflow()
    if 'error' in netflow_data:
        print(f"Netflow failed: {netflow_data['error']}")
    else:
        print(f"Synthetic Netflow 24h: {netflow_data.get('value', 'N/A')} BTC")
        print(f"Sample Size: {netflow_data.get('sample_size')} addresses")

    # SOPR
    sopr_data = onchain.calculate_synthetic_sopr()
    if 'error' in sopr_data:
        print(f"SOPR failed: {sopr_data['error']}")
    else:
        print(f"Synthetic SOPR: {sopr_data.get('value', 'N/A')}")
        print(f"Sample Size: {sopr_data.get('sample_size')} UTXOs")

    # 2. Test Integrated Coordinator Collection (Full Suite)
    print("\n[Scenario: Integrated Coordinator Full Suite]")
    coordinator = AgentCoordinator()
    
    # We use technical_only which triggers synthetic collection
    results = await coordinator.execute_multi_agent_workflow(
        "technical_only",
        {"lookback_days": 1}
    )
    
    synthetic = coordinator.results.get('collect_price', {}).get('synthetic_metrics', {})
    
    print("\n[Coordinator Result Checklist]")
    metrics = ['mvrv', 'order_flow_delta', 'exchange_netflow', 'sopr']
    for m in metrics:
        status = "✅" if m in synthetic and 'error' not in synthetic[m] else "❌"
        val = synthetic.get(m, {}).get('value', 'N/A')
        print(f"{status} {m}: {val}")

    print("\nExpanded Synthetic Intelligence Framework verification complete!")

if __name__ == "__main__":
    asyncio.run(test_expanded_synthetic_intelligence())
