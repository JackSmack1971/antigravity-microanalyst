import asyncio
import httpx
import uvicorn
import threading
import time
import json
from pathlib import Path
from src.microanalyst.server.server import app
from src.microanalyst.server.schemas import HealthResponse, ThesisResponse

# Setup paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data_exports"
THESIS_FILE = DATA_DIR / "latest_thesis.json"

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

async def verify_endpoints():
    print("Waiting for server startup...")
    await asyncio.sleep(2) # Give uvicorn a moment
    
    async with httpx.AsyncClient() as client:
        # 1. Health
        print("Testing /health...")
        r = await client.get("http://127.0.0.1:8001/health")
        print(f"Status: {r.status_code}, Resp: {r.json()}")
        if r.status_code != 200:
            print("FAILURE: Health check failed")
            return
        
        # Schema Validation
        try:
            HealthResponse(**r.json())
            print("SUCCESS: Health schema valid.")
        except Exception as e:
            print(f"FAILURE: Health schema mismatch: {e}")
            return

        # 2. Latest Thesis (Empty)
        print("Testing /api/v1/latest/thesis (Empty)...")
        if THESIS_FILE.exists():
            THESIS_FILE.unlink()
            
        r = await client.get("http://127.0.0.1:8001/api/v1/latest/thesis")
        print(f"Resp: {r.json()}")
        if r.json().get("thesis") is not None:
             print("FAILURE: Should contain None thesis")

        # 3. Latest Thesis (Populated)
        print("Testing /api/v1/latest/thesis (Populated)...")
        mock_thesis = {
            "decision": "BUY",
            "confidence": 0.85,
            "allocation_pct": 50.0,
            "reasoning": "BTC decoupling from DXY/SPY into a structural Safe Haven. | Mixed signals. | Macro Economist logic validated.",
            "bull_case": "[RETAIL]: Moon soon!",
            "bear_case": "[WHALE]: Wait for liquidity.",
            "macro_thesis": "[MACRO]: Structural shift.",
            "logs": ["Test log entry"]
        }
        DATA_DIR.mkdir(exist_ok=True)
        with open(THESIS_FILE, "w", encoding="utf-8") as f:
            json.dump(mock_thesis, f)
            
        r = await client.get("http://127.0.0.1:8001/api/v1/latest/thesis")
        data = r.json()
        print(f"Resp Status: {r.status_code}")
        
        # Schema Validation
        try:
            ThesisResponse(**data)
            print("SUCCESS: Thesis schema valid.")
        except Exception as e:
            print(f"CRITICAL BREAKING CHANGE: Thesis schema mismatch: {e}")
            return

        if data.get("decision") == "BUY":
            print("SUCCESS: Retrieved valid thesis.")
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

