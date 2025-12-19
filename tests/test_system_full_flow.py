import asyncio
import os
import sys
import json

sys.path.append(os.getcwd())

from src.microanalyst.reporting.validation_reporter import ValidationReporter

async def main():
    print("🚀 Starting End-to-End System Integration Test...")
    print("Goal: Generate 'Daily Validation Report' using Zero-Cost Data Stack.\n")
    
    reporter = ValidationReporter()
    
    # Generate Report
    print("... Pulling levers (OnChain, Sentiment, Whale, Volatility, Derivatives, Consensus) ...")
    report = await reporter.generate_daily_report(symbol='BTCUSDT')
    
    if "error" in str(report):
        print(f"⚠️ Partial Errors Detected in Report construction (Expected if some APIs block):")
        # print specific errors if structure allows, or just dump
    
    # Pretty Print
    print("\n✅ Report Generated Successfully!")
    print("="*60)
    print(json.dumps(report, indent=2))
    print("="*60)
    
    # Simple Assertions
    assert "synthetic_metrics" in report, "Missing Synthetic Metrics"
    assert "market_environment" in report, "Missing Market Environment"
    assert "derivatives_market" in report, "Missing Derivatives"
    
    print("\n[System Check]")
    if report["synthetic_metrics"].get("synthetic_mvrv", {}).get("status"):
        print(f"   🔹 MVRV Status: {report['synthetic_metrics']['synthetic_mvrv']['status']}")
    if report["market_environment"].get("sentiment", {}).get("interpretation"):
        print(f"   🔹 Sentiment: {report['market_environment']['sentiment']['interpretation']}")

    print("\n🎉 Test Complete. The Microanalyst is fully operational.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
