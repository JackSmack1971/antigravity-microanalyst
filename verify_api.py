import asyncio
import httpx
import uvicorn
import threading
import time
import json
from pathlib import Path
from src.microanalyst.server.server import app

# Setup paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data_exports"
THESIS_FILE = DATA_DIR / "latest_thesis.json"

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

async def verify_endpoints():
    print("Waiting for server startup...")
    await asyncio.sleep(2) # Give uvicorn a moment
    
    async with httpx.AsyncClient() as client:
        # 1. Health
        print("Testing /health...")
        r = await client.get("http://127.0.0.1:8000/health")
        print(f"Status: {r.status_code}, Resp: {r.json()}")
        if r.status_code != 200:
            print("FAILURE: Health check failed")
            return

        # 2. Latest Thesis (Empty)
        print("Testing /api/v1/latest/thesis (Empty)...")
        if THESIS_FILE.exists():
            THESIS_FILE.unlink()
            
        r = await client.get("http://127.0.0.1:8000/api/v1/latest/thesis")
        print(f"Resp: {r.json()}")
        if r.json().get("thesis") is not None:
             print("FAILURE: Should contain None thesis")

        # 3. Latest Thesis (Populated)
        print("Testing /api/v1/latest/thesis (Populated)...")
        mock_thesis = {
            "regime": "Bullish",
            "decision": "BUY",
            "confidence": 0.95
        }
        DATA_DIR.mkdir(exist_ok=True)
        with open(THESIS_FILE, "w") as f:
            json.dump(mock_thesis, f)
            
        r = await client.get("http://127.0.0.1:8000/api/v1/latest/thesis")
        print(f"Resp: {r.json()}")
        if r.json().get("decision") == "BUY":
            print("SUCCESS: Retrieved thesis.")
        else:
            print("FAILURE: Data mismatch.")

def main():
    # Start server in thread
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    
    try:
        asyncio.run(verify_endpoints())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
