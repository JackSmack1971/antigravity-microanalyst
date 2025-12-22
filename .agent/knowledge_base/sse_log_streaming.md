# Pattern: real-time Log Streaming via SSE

## Context
Use this when you need live updates from a backend log file to a frontend dashboard or terminal without the complexity of WebSockets.

## Problem
Monitoring long-running backend processes usually requires polling the API or manually checking files. WebSockets are bidirectional but often overkill for a read-only stream.

## Solution
Use Server-Sent Events (SSE) with an async generator to "tail" a file in real-time.

### 1. Backend Implementation (FastAPI)
```python
from sse_starlette.sse import EventSourceResponse
import asyncio
import os

@router.get("/stream/logs")
async def message_stream(request: Request):
    async def event_generator():
        with open(LOG_FILE, "r") as f:
            f.seek(0, os.SEEK_END)  # Start from end of file
            while True:
                if await request.is_disconnected():
                    break
                line = f.readline()
                if line:
                    yield {"event": "log", "data": line.strip()}
                else:
                    await asyncio.sleep(0.5)
    return EventSourceResponse(event_generator())
```

### 2. Frontend Consumption (JavaScript)
```javascript
const eventSource = new EventSource('/api/v1/stream/logs');
eventSource.addEventListener('log', (event) => {
  console.log('New log:', event.data);
});
```

## Gotchas
- **File Descriptors**: Ensure the file is opened correctly and handles lack of content gracefully.
- **Client Disconnection**: Always check `request.is_disconnected()` to avoid lingering background loops.
- **Buffering**: SSE is HTTP-based; ensure no middleware or proxies (like Nginx) are buffering the response.
