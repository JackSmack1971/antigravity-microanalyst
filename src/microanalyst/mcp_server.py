from mcp.server import Server
from mcp.types import TextContent, Tool
import asyncio
import json
import pandas as pd
from pathlib import Path
from src.microanalyst.reports.generator import ReportGenerator
# from src.microanalyst.validation.suite import DataQualitySuite # Removed unused/broken import
from src.microanalyst.cli import get_price as cli_get_price # Reuse CLI logic if possible or re-implement logic

# Initialize Server
server = Server("btc-microanalyst")

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data_clean"

async def get_price_data(days: int = 30):
    path = DATA_DIR / "btc_price_normalized.csv"
    if not path.exists():
        return "Error: Data file not found."
    
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').tail(days)
    return df.to_json(orient='records', date_format='iso')

async def get_etf_flows(days: int = 7):
    path = DATA_DIR / "etf_flows_normalized.csv"
    if not path.exists():
        return "Error: Data file not found."
        
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').tail(days) # Naive tail, assumes daily agg
    return df.to_json(orient='records', date_format='iso')

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_btc_price",
            description="Get Bitcoin OHLC price history",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to retrieve (default 30)"}
                }
            }
        ),
        Tool(
            name="get_etf_flows",
            description="Get Bitcoin ETF Flow data",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to retrieve (default 7)"}
                }
            }
        ),

        Tool(
            name="generate_market_report",
            description="Generate a daily market summary report",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Target date (YYYY-MM-DD), defaults to today"}
                }
            }
        ),
        Tool(
            name="get_market_context",
            description="Get deep context-aware market intelligence (Regime, Signals, Risks)",
            inputSchema={
                "type": "object",
                "properties": {
                    "lookback_days": {"type": "integer", "description": "Analysis window (default 30)"},
                    "report_type": {"type": "string", "description": "Report style (comprehensive, executive)"},
                    "agent_optimized": {"type": "boolean", "description": "Return minimal JSON for agents"}
                }
            }
        ),
        Tool(
            name="get_reasoning_graph",
            description="Get structured reasoning graph for agent consumption",
            inputSchema={
                "type": "object",
                "properties": {
                    "lookback_days": {"type": "integer", "default": 30},
                    "include_counterarguments": {"type": "boolean", "default": True},
                    "include_uncertainty": {"type": "boolean", "default": True}
                }
            }
        ),
        Tool(
            name="query_decision_tree",
            description="Query decision tree for specific market condition",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "Market condition query"},
                    "depth": {"type": "integer", "default": 3}
                },
                "required": ["condition"]
            }
        ),
        Tool(
            name="validate_reasoning",
            description="Self-validate reasoning against data sources",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "Claim to validate"},
                    "evidence_threshold": {"type": "number", "default": 0.7}
                },
                "required": ["claim"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_btc_price":
        days = arguments.get("days", 30)
        data = await get_price_data(days)
        return [TextContent(type="text", text=data)]
    
    elif name == "get_etf_flows":
        days = arguments.get("days", 7)
        data = await get_etf_flows(days)
        return [TextContent(type="text", text=data)]
        
    elif name == "generate_market_report":
        reporter = ReportGenerator()
        summary = reporter.generate_daily_market_summary()
        if "error" in summary:
             return [TextContent(type="text", text=f"Error: {summary['error']}")]
        report = reporter.generate_markdown_report(summary)
        return [TextContent(type="text", text=report)]
        
    elif name == "get_market_context":
        try:
            from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer
            synthesizer = ContextSynthesizer()
            
            lookback_days = arguments.get("lookback_days", 30)
            report_type = arguments.get("report_type", "comprehensive")
            agent_optimized = arguments.get("agent_optimized", True)
            
            context = synthesizer.synthesize_context(lookback_days=lookback_days)
            report_json = synthesizer.generate_report(
                context, 
                report_type=report_type, 
                output_format="json", 
                agent_optimized=agent_optimized
            )
            return [TextContent(type="text", text=report_json)]
        except Exception as e:
             return [TextContent(type="text", text=f"Error generating context: {str(e)}")]

    elif name == "get_reasoning_graph":
        try:
            from src.microanalyst.agents.reasoning_adapter import AgentReasoningAdapter
            from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer
            from dataclasses import asdict
            
            synthesizer = ContextSynthesizer()
            context = synthesizer.synthesize_context(
                lookback_days=arguments.get("lookback_days", 30)
            )
            
            adapter = AgentReasoningAdapter()
            structured_intel = adapter.adapt_context_to_reasoning(context)
            
            return [TextContent(
                type="text",
                text=json.dumps(asdict(structured_intel), default=str, indent=2)
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "query_decision_tree":
        try:
            from src.microanalyst.agents.reasoning_adapter import AgentReasoningAdapter
            from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer
            
            synthesizer = ContextSynthesizer()
            context = synthesizer.synthesize_context(lookback_days=30)
            adapter = AgentReasoningAdapter()
            structured_intel = adapter.adapt_context_to_reasoning(context)
            
            # Simple simulation: return the whole tree for now as it's small
            return [TextContent(
                type="text",
                text=json.dumps(structured_intel.decision_tree, default=str, indent=2)
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "validate_reasoning":
        try:
            from src.microanalyst.agents.reasoning_adapter import AgentReasoningAdapter
            from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer
            from dataclasses import asdict
            
            synthesizer = ContextSynthesizer()
            context = synthesizer.synthesize_context(lookback_days=30)
            adapter = AgentReasoningAdapter()
            intel = adapter.adapt_context_to_reasoning(context)
            
            claim = arguments.get("claim", "").lower()
            matches = [node for node in intel.reasoning_graph if claim in node.claim.lower()]
            
            return [TextContent(
                type="text",
                text=json.dumps([asdict(m) for m in matches], default=str, indent=2)
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return [TextContent(type="text", text=f"Tool {name} not found")]

async def main():
    # Run server via stdio
    async with server.run_stdio() as stream:
        await stream

if __name__ == "__main__":
    asyncio.run(main())
