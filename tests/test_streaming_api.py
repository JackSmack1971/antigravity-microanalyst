import asyncio
import httpx
import json
import subprocess
import time
import os

async def test_market_updates():
    print("\n[Testing /stream/market_updates]")
    url = "http://localhost:8001/stream/market_updates"
    
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream("GET", url) as response:
                print(f"Connected. Status: {response.status_code}")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        print(f"Received market update: {data.get('timestamp')}")
                        assert 'regime' in data
                        # We only need one for success
                        break
        except Exception as e:
            print(f"Error in market stream: {e}")

async def test_workflow_execution():
    print("\n[Testing /stream/workflow_execution/price_action_deep_dive]")
    url = "http://localhost:8001/stream/workflow_execution/price_action_deep_dive"
    
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream("POST", url) as response:
                print(f"Connected. Status: {response.status_code}")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        print(f"Received workflow status: {data.get('status')}")
                        if data.get('status') in ['completed', 'failed']:
                            print(f"Workflow finished with status: {data.get('status')}")
                            break
        except Exception as e:
            print(f"Error in workflow stream: {e}")

async def run_all_tests():
    # Start server in background
    server_process = subprocess.Popen(
        ["python", "-m", "src.microanalyst.api.streaming_server"],
        cwd=os.getcwd(),
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )
    
    print("Waiting for server to start (12s)...")
    time.sleep(12)
    
    try:
        await test_market_updates()
        await test_workflow_execution()
    finally:
        print("Shutting down server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
