import json
import logging
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.utils.jwt import verify_jwt_token
from backend.session.state import RedisSessionManager

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
    p_type = payload.get("type")
    if p_type == "ping":
        await websocket.send_text(json.dumps({"type": "pong"}))
    elif p_type == "message":
        p_load = payload.get("payload", {})
        session_id = p_load.get("session_id")
        content = p_load.get("content")
        if session_id and content:
            import uuid
            from backend.storage.db import async_session_factory
            from backend.repositories.message import MessageRepository
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError:
                return
            
            async with async_session_factory() as session:
                db_msg = await MessageRepository(session).save_message(session_uuid, "agent", content)
            
            # Forward to active customer WebSocket if online
            from backend.ws.chat import active_chat_connections
            cust_ws = active_chat_connections.get(session_id)
            if cust_ws:
                try:
                    await cust_ws.send_text(json.dumps({
                        "type": "message",
                        "payload": {
                            "id": str(db_msg.id), "session_id": session_id,
                            "role": "agent", "content": content,
                            "created_at": db_msg.created_at.isoformat()
                        }
                    }))
                except Exception:
                    pass
            else:
                # Customer is offline: trigger push notification
                from backend.utils.push import send_expo_push_notification
                from backend.storage.schema import SessionModel, CustomerPushTokenModel
                from sqlalchemy import select
                import asyncio
                
                async def trigger_push():
                    async with async_session_factory() as db_session:
                        res_sess = await db_session.execute(select(SessionModel).where(SessionModel.id == session_uuid))
                        db_sess = res_sess.scalar_one_or_none()
                        if db_sess:
                            res_tokens = await db_session.execute(
                                select(CustomerPushTokenModel).where(CustomerPushTokenModel.customer_id == db_sess.customer_id)
                            )
                            for row in res_tokens.scalars().all():
                                await send_expo_push_notification(
                                    push_token=row.push_token,
                                    title="New Agent Message",
                                    body=content[:100],
                                    data={"session_id": session_id}
                                )
                asyncio.create_task(trigger_push())
            
            # Broadcast to all active agents so they sync
            await agent_manager.broadcast({
                "type": "message",
                "payload": {
                    "id": str(db_msg.id), "session_id": session_id,
                    "role": "agent", "content": content,
                    "created_at": db_msg.created_at.isoformat()
                }
            })

@router.websocket("/ws/agent/{agent_id}")
async def agent_websocket_endpoint(websocket: WebSocket, agent_id: str, token: str = Query(...)):
    """Authenticated gateway connection for human agent clients."""
    from backend.config import LOCAL_TESTING
    if LOCAL_TESTING and token == "sandbox-token" and agent_id == "00000000-0000-0000-0000-000000000000":
        pass
    else:
        try:
            claims = verify_jwt_token(token)
            if claims.get("sub") != agent_id:
                await websocket.close(code=4001)
                return
        except Exception:
            await websocket.close(code=4001)
            return
        
    await agent_manager.connect(websocket)
    redis = RedisSessionManager()
    await redis.redis.hset("agents:online", agent_id, str(time.time()))
    try:
        while True:
            await _process_agent_frame(websocket, await websocket.receive_text())
    except WebSocketDisconnect:
        agent_manager.disconnect(websocket)
        await redis.redis.hdel("agents:online", agent_id)
