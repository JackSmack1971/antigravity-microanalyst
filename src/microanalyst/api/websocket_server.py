from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any, Optional
import json
import asyncio
from datetime import datetime
from src.microanalyst.intelligence.context_synthesizer import ContextSynthesizer
from src.microanalyst.agents.workflow_engine import WorkflowEngine, ResearchWorkflows

app = FastAPI(title="BTC Microanalyst WebSocket API")

class AgentConnectionManager:
    """Manage WebSocket connections for multiple agents"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, agent_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.agent_subscriptions[agent_id] = set()
        print(f"Agent {agent_id} connected")
    
    def disconnect(self, agent_id: str):
        self.active_connections.pop(agent_id, None)
        self.agent_subscriptions.pop(agent_id, None)
        print(f"Agent {agent_id} disconnected")
    
    async def broadcast_to_subscribed(self, topic: str, message: Dict):
        """Broadcast message to all agents subscribed to topic"""
        for agent_id, topics in self.agent_subscriptions.items():
            if topic in topics:
                ws = self.active_connections.get(agent_id)
                if ws:
                    try:
                        await ws.send_json({
                            "type": "broadcast",
                            "topic": topic,
                            "data": message
                        })
                    except Exception as e:
                        print(f"Error broadcasting to {agent_id}: {e}")

manager = AgentConnectionManager()
synthesizer = ContextSynthesizer()
engine = WorkflowEngine()
ResearchWorkflows(engine)

async def handle_agent_query(query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve ad-hoc agent queries using intelligence layer"""
    try:
        if query_type == "market_context":
            context = synthesizer.synthesize_context(lookback_days=params.get("lookback_days", 30))
            report = synthesizer.generate_report(context, output_format="json", agent_optimized=True)
            return json.loads(report)
        elif query_type == "regime":
            context = synthesizer.synthesize_context(lookback_days=30)
            return context.regime
        elif query_type == "signals":
            context = synthesizer.synthesize_context(lookback_days=30)
            return {"signals": context.signals}
        else:
            return {"error": f"Unknown query type: {query_type}"}
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    await manager.connect(agent_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "subscribe":
                topics = data.get("topics", [])
                manager.agent_subscriptions[agent_id].update(topics)
                await websocket.send_json({
                    "type": "response",
                    "status": "subscribed",
                    "topics": list(manager.agent_subscriptions[agent_id])
                })
            
            elif command == "execute_workflow":
                workflow_id = data.get("workflow_id")
                parameters = data.get("parameters", {})
                
                # We use the new start_execution to avoid blocking the WS loop
                # but we want to monitor it and send a result back
                try:
                    execution_id = await engine.start_execution(workflow_id, parameters)
                    await websocket.send_json({
                        "type": "workflow_started",
                        "execution_id": execution_id
                    })
                    
                    # Periodic progress updates could be added here or via broadcast
                    # For now, we wait for completion in a task
                    async def monitor_and_return():
                        while True:
                            status = engine.get_execution_status(execution_id)
                            if status and status.get('status') in ['completed', 'failed']:
                                # If completed, we retrieve the full result if needed, 
                                # but status might have it
                                await websocket.send_json({
                                    "type": "workflow_result",
                                    "execution_id": execution_id,
                                    "status": status.get('status'),
                                    "data": status
                                })
                                break
                            await asyncio.sleep(1)
                    
                    asyncio.create_task(monitor_and_return())
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Workflow failed to start: {str(e)}"
                    })
            
            elif command == "query":
                query_type = data.get("query_type")
                response = await handle_agent_query(query_type, data.get("params", {}))
                await websocket.send_json({
                    "type": "query_response",
                    "data": response
                })
                
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown command: {command}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(agent_id)
    except Exception as e:
        print(f"WebSocket error for {agent_id}: {e}")
        manager.disconnect(agent_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
