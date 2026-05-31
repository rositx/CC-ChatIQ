import json
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.utils.jwt import verify_jwt_token
from backend.storage.db import async_session_factory
from backend.repositories.message import MessageRepository

router = APIRouter(tags=["websockets"])
logger = logging.getLogger("ws")

async def _authenticate_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str
) -> bool:
    """Accept and authenticate the incoming WebSocket connection."""
    await websocket.accept()
    try:
        claims = verify_jwt_token(token)
        if str(claims.get("sub")) != session_id:
            raise ValueError("Session mismatch")
        return True
    except Exception as e:
        logger.error(f"WS authentication failed: {str(e)}")
        await websocket.close(code=4001)
        return False


async def _handle_chat_message(
    websocket: WebSocket,
    session_id: str,
    msg_payload: dict
) -> None:
    """Persist the chat message and echo it back to the client."""
    if not isinstance(msg_payload, dict):
        return
    content = msg_payload.get("content")
    if not content:
        return

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        logger.error(f"Invalid session UUID: {session_id}")
        return

    async with async_session_factory() as session:
        repo = MessageRepository(session)
        db_msg = await repo.save_message(session_uuid, "customer", content)

    await websocket.send_text(json.dumps({
        "type": "message",
        "payload": {
            "id": str(db_msg.id),
            "session_id": session_id,
            "role": "customer",
            "content": content,
            "created_at": db_msg.created_at.isoformat()
        }
    }))


async def _process_chat_frame(
    websocket: WebSocket,
    session_id: str,
    data: str
) -> None:
    """Process a single incoming text frame from the WebSocket client."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        logger.warning("Received invalid JSON payload")
        return

    payload_type = payload.get("type")
    if payload_type == "ping":
        await websocket.send_text(json.dumps({"type": "pong"}))
    elif payload_type == "message":
        await _handle_chat_message(
            websocket,
            session_id,
            payload.get("payload", {})
        )


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...)
):
    """Handler for customer-facing chat WebSockets."""
    authenticated = await _authenticate_websocket(websocket, session_id, token)
    if not authenticated:
        return

    try:
        while True:
            data = await websocket.receive_text()
            await _process_chat_frame(websocket, session_id, data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket session {session_id} dropped.")

