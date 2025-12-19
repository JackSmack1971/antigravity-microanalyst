import asyncio
import json
from src.microanalyst.providers.binance_derivatives import BinanceFreeDerivatives
from src.microanalyst.agents.agent_coordinator import AgentCoordinator
import os

# Set PYTHONPATH
os.environ["PYTHONPATH"] = os.getcwd()

async def test_binance_derivatives_integration():
    print("Testing Synthetic Exchange Derivatives (Binance Free Provider)...")
    
    # 1. Test Provider Directly
    print("\n[Scenario: Direct Provider Access]")
    provider = BinanceFreeDerivatives()
    
    # Funding
    print("Fetching Funding Rates...")
    funding = provider.get_funding_rate_history()
    if 'error' in funding:
        print(f"❌ Funding Error: {funding['error']}")
    else:
        print(f"✅ Current Funding: {funding.get('current_funding_rate'):.4f}%")
        print(f"   Trend: {funding.get('trend')}")
        
    # Open Interest
    print("Fetching Open Interest...")
    oi = provider.get_open_interest()
    if 'error' in oi:
        print(f"❌ OI Error: {oi['error']}")
    else:
        print(f"✅ Open Interest: {oi.get('open_interest_btc'):.2f} BTC")
        print(f"   Change 24h: {oi.get('change_24h_pct'):.2f}%")

    # Long/Short Ratio
    print("Fetching Long/Short Ratio...")
    ls = provider.get_long_short_ratio()
    if 'error' in ls:
        print(f"❌ L/S Ratio Error: {ls['error']}")
    else:
        print(f"✅ Current L/S Ratio: {ls.get('current_long_short_ratio')}")
        print(f"   Interpretation: {ls.get('interpretation')}")

    # 2. Test Integrated Coordinator
    print("\n[Scenario: Integrated Coordinator Derivatives Data]")
    coordinator = AgentCoordinator()
    
    # We use technical_only and manually add 'derivatives' source
    # (In real app, 'sources' input drives this)
    params = {
        "lookback_days": 1,
        "sources": ["price", "synthetic", "derivatives"] # Requesting derivatives
    }
    
    # We need to ensure the task actually passes these sources to data_collector
    # The existing technical_only scaffold might hardcode sources, let's check or mock
    # Actually, let's use a custom task definition or rely on updated logic if possible.
    # The updated logic in _delegate_to_module respects inputs.get('sources').
    # But technical_only preset in execute_multi_agent_workflow might override inputs.
    
    # Let's bypass execute_multi_agent_workflow's preset for a moment and define a custom one or just trust existing logic
    # Re-reading: The presets in execute_multi_agent_workflow MERGE with user inputs but might overwrite 'sources'.
    # Let's try running it and see if we get derivatives data. 
    # If not, I'll update the preset in next step. For now, testing the direct module logic via direct call is safer.
    
    from src.microanalyst.agents.agent_coordinator import AgentRole
    
    print("Simulating DATA_COLLECTOR task execution directly...")
    result = await coordinator._delegate_to_module(
        AgentRole.DATA_COLLECTOR,
        {'sources': ['derivatives']}
    )
    
    derivs_res = result.get('derivatives_data', {})
    
    metrics = ['funding_rates', 'open_interest', 'long_short_ratio']
    for m in metrics:
        status = "✅" if m in derivs_res and 'error' not in derivs_res[m] else "❌"
        # Extract a key value for display
        val = "N/A"
        if status == "✅":
            if m == 'funding_rates': val = f"{derivs_res[m].get('current_funding_rate'):.4f}%"
            elif m == 'open_interest': val = f"{derivs_res[m].get('open_interest_btc'):.2f} BTC"
            elif m == 'long_short_ratio': val = derivs_res[m].get('current_long_short_ratio')
            
        print(f"{status} {m}: {val}")

    print("\nSynthetic Derivatives verification complete!")

if __name__ == "__main__":
    asyncio.run(test_binance_derivatives_integration())
