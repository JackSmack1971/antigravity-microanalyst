from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.microanalyst.server.api_routes import router

app = FastAPI(
    title="Antigravity Swarm API",
    description="Real-time interface for the Cognitive Micro-Analyst Swarm",
    version="0.4.0"
)

# CORS - Allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.microanalyst.server.server:app", host="0.0.0.0", port=8000, reload=True)
