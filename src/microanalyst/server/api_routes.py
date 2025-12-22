from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Union
from src.microanalyst.server.schemas import HealthResponse, ThesisResponse


router = APIRouter()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data_exports"
LOG_FILE = PROJECT_ROOT / "logs" / "async_retrieval.log"
THESIS_FILE = DATA_DIR / "latest_thesis.json"

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "online", "service": "Antigravity Swarm API"}

@router.get("/api/v1/latest/thesis", response_model=Union[ThesisResponse, Dict[str, Any]])
async def get_latest_thesis():

    """Returns the most recent generated thesis."""
    if not THESIS_FILE.exists():
        return {"status": "waiting_for_swarm", "thesis": None}
    
    try:
        with open(THESIS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/v1/stream/logs")
async def message_stream(request: Request):
    """Streams log changes to the client using SSE."""
    
    async def event_generator():
        # Simple tail implementation
        if not LOG_FILE.exists():
            yield {"event": "log", "data": "Log file not found."}
            return

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            # Move to end
            f.seek(0, os.SEEK_END)
            
            while True:
                if await request.is_disconnected():
                    break
                    
                line = f.readline()
                if line:
                    yield {"event": "log", "data": line.strip()}
                else:
                    await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
