import asyncio
import json
from src.microanalyst.mcp_server import call_tool
import os

# Set PYTHONPATH to project root for imports
os.environ["PYTHONPATH"] = os.getcwd()

async def test_mcp_tools():
    print("Testing MCP Reasoning Tools...")
    
    # 1. Test get_reasoning_graph
    print("\n[Tool: get_reasoning_graph]")
    results = await call_tool("get_reasoning_graph", {"lookback_days": 30})
    if results and len(results) > 0:
        content = results[0].text
        data = json.loads(content)
        print(f"Success! Found reasoning nodes: {len(data['reasoning_graph'])}")
        assert 'reasoning_graph' in data
        assert 'decision_tree' in data
    else:
        print("Failed to get reasoning graph.")

    # 2. Test query_decision_tree
    print("\n[Tool: query_decision_tree]")
    results = await call_tool("query_decision_tree", {"condition": "bullish momentum"})
    if results and len(results) > 0:
        content = results[0].text
        data = json.loads(content)
        print(f"Success! Root question: {data['root']['question']}")
        assert 'root' in data
    else:
        print("Failed to query decision tree.")

    # 3. Test validate_reasoning
    print("\n[Tool: validate_reasoning]")
    results = await call_tool("validate_reasoning", {"claim": "Market is in bull regime"})
    if results and len(results) > 0:
        content = results[0].text
        data = json.loads(content)
        print(f"Success! Found {len(data)} matching claims.")
        if len(data) > 0:
            print(f"Match 0 Claim: {data[0]['claim']}")
    else:
        print("Failed to validate reasoning.")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
