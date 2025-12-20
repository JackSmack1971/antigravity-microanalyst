# run_ultimate_research.py
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from src.microanalyst.agents.workflow_engine import WorkflowEngine, ResearchWorkflows

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ultimate_research")

async def run_all():
    print("\n🚀 INITIALIZING ULTIMATE RESEARCH FRAMEWORK")
    
    engine = WorkflowEngine()
    research_wf = ResearchWorkflows(engine)
    
    workflows_to_run = [
        "comprehensive_report",
        "correlation_analysis",
        "risk_assessment"
    ]
    
    results = {}
    
    for wf_id in workflows_to_run:
        print(f"\n📡 Executing Workflow: {wf_id}...")
        try:
            result = await engine.execute(wf_id, {"lookback_days": 90})
            results[wf_id] = result
            print(f"✅ {wf_id} completed successfully.")
        except Exception as e:
            print(f"❌ {wf_id} failed: {e}")
    
    # Generate Grand Report
    report_path = Path("ultimate_market_intel.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🌌 Ultimate Market Intelligence Report\n")
        f.write(f"**Generated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 1. Comprehensive Report Summary
        comp = results.get("comprehensive_report", {})
        outputs = comp.get("outputs", {})
        exec_summary = outputs.get("generate_executive_summary", "Summary generation failed")
        
        f.write(f"{exec_summary}\n\n")
        
        # 2. Risk Assessment
        risk = results.get("risk_assessment", {})
        risk_outputs = risk.get("outputs", {}).get("synthesize_risk_assessment", {})
        f.write("## ⚠️ Risk Assessment\n")
        f.write(f"- **Risk Level:** {risk_outputs.get('risk_level', 'Unknown')}\n")
        f.write(f"- **Positioning Recommendation:** {risk_outputs.get('position_recommendation', 'N/A')}\n\n")
        
        # 3. Correlation Analysis
        corr = results.get("correlation_analysis", {})
        corr_outputs = corr.get("outputs", {}).get("synthesize_correlations", {})
        f.write("## 🔄 Correlation Matrix\n")
        f.write(f"- **Price-Flow Correlation:** {corr_outputs.get('price_flow_corr', 'N/A')}\n")
        f.write(f"- **Interpretation:** {corr_outputs.get('interpretation', 'N/A')}\n\n")
        
        # 4. Full JSON logs
        f.write("## 📂 Raw Execution Data\n")
        f.write("<details>\n<summary>Click to expand raw workflow results</summary>\n\n")
        f.write("```json\n")
        f.write(json.dumps(results, indent=2, default=str))
        f.write("\n```\n</details>\n")

    print(f"\n✨ ULTIMATE REPORT GENERATED: {report_path.absolute()}")

if __name__ == "__main__":
    asyncio.run(run_all())
