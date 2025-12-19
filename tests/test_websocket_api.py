import asyncio
import json
import websockets
import subprocess
import time
import os

@pytest.mark.skip(reason="Requires running server")
async def test_websocket_agent():
    uri = "ws://localhost:8002/ws/agent/test_agent_007"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # 1. Test Subscribe
            print("\n[Command: subscribe]")
            subscribe_cmd = {
                "command": "subscribe",
                "topics": ["market_updates", "whale_alerts"]
            }
            await websocket.send(json.dumps(subscribe_cmd))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            assert data["status"] == "subscribed"
            
            # 2. Test Query
            print("\n[Command: query]")
            query_cmd = {
                "command": "query",
                "query_type": "regime",
                "params": {}
            }
            await websocket.send(json.dumps(query_cmd))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Query Response Regime: {data['data']['current_regime']}")
            assert "current_regime" in data["data"]
            
            # 3. Test Execute Workflow
            print("\n[Command: execute_workflow]")
            workflow_cmd = {
                "command": "execute_workflow",
                "workflow_id": "price_action_deep_dive",
                "parameters": {}
            }
            await websocket.send(json.dumps(workflow_cmd))
            
            # Expect workflow_started
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Started: {data}")
            assert data["type"] == "workflow_started"
            execution_id = data["execution_id"]
            
            # Wait for workflow_result
            print("Waiting for workflow result...")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Result Status: {data['status']}")
            assert data["type"] == "workflow_result"
            assert data["execution_id"] == execution_id
            
            print("\nWebSocket bidirectional test passed!")
            
    except Exception as e:
        print(f"WebSocket test failed: {e}")
        raise

async def run_integration_test():
    # Start server in background
    print("Starting WebSocket server...")
    server_process = subprocess.Popen(
        ["python", "-m", "src.microanalyst.api.websocket_server"],
        cwd=os.getcwd(),
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )
    
    print("Waiting for server to spin up (10s)...")
    await asyncio.sleep(10)
    
    try:
        await test_websocket_agent()
    finally:
        print("Shutting down WebSocket server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    # asyncio.run(run_integration_test())
    pass
