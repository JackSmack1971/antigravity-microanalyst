"""Antigravity Swarm API server application.

This module configures and initializes the FastAPI application for the
Antigravity Cognitive Micro-Analyst Swarm. It sets up CORS middleware for
cross-origin requests and includes all API route handlers.

Usage:
    Run the server directly:
        $ python src/microanalyst/server/server.py
    
    Or via uvicorn with custom settings:
        $ uvicorn src.microanalyst.server.server:app --host 0.0.0.0 --port 8000 --reload

Configuration:
    - Title: Antigravity Swarm API
    - Version: 0.4.0
    - Default Port: 8000
    - CORS: Permissive (all origins allowed for development)

Note:
    The permissive CORS policy is configured for development environments.
    For production deployments, restrict `allow_origins` to specific domains.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.microanalyst.server.api_routes import router

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Antigravity Swarm API",
    description="Real-time interface for the Cognitive Micro-Analyst Swarm",
    version="0.4.0"
)

# CORS Configuration
# Note: Permissive settings for development. Restrict for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # WARNING: Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API route handlers
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Start server with hot-reload for development
    uvicorn.run("src.microanalyst.server.server:app", host="0.0.0.0", port=8000, reload=True)
