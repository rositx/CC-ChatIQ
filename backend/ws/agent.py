import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.utils.jwt import verify_jwt_token

router = APIRouter(tags=["websockets"])
logger = logging.getLogger("ws")

class AgentConnectionManager:
    """Manages active human agent dashboard WebSocket connections."""
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for conn in list(self.active_connections):
            try:
                await conn.send_text(payload)
            except Exception:
                self.active_connections.discard(conn)

agent_manager = AgentConnectionManager()

async def _process_agent_frame(websocket: WebSocket, data: str) -> None:
    """Processes a single incoming frame from an active agent dashboard."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return
    if payload.get("type") == "ping":
        await websocket.send_text(json.dumps({"type": "pong"}))

@router.websocket("/ws/agent/{agent_id}")
async def agent_websocket_endpoint(websocket: WebSocket, agent_id: str, token: str = Query(...)):
    """Authenticated gateway connection for human agent clients."""
    try:
        claims = verify_jwt_token(token)
        if claims.get("sub") != agent_id:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return
        
    await agent_manager.connect(websocket)
    try:
        while True:
            await _process_agent_frame(websocket, await websocket.receive_text())
    except WebSocketDisconnect:
        agent_manager.disconnect(websocket)
