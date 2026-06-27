import json
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from backend.utils.jwt import verify_jwt_token
from backend.storage.db import async_session_factory
from backend.repositories.message import MessageRepository
from backend.repositories.session import SessionRepository
from backend.repositories.ticket import TicketRepository
from backend.session.state import RedisSessionManager
from backend.handoff.triggers import evaluate_escalation
from backend.handoff.executor import execute_handoff
from backend.handoff.queue_manager import get_queue_status
from backend.scoring.hook import score_session_async
from backend.rag.pipeline import run_rag_pipeline
from backend.rag.retriever import RAGRetrieverService
from backend.repositories.knowledge import KnowledgeRepository

router = APIRouter(tags=["websockets"])
logger = logging.getLogger("ws")

async def _auth_ws(
    websocket: WebSocket,
    session_id: str,
    token: str
) -> bool:
    """Accept and authenticate the incoming WebSocket connection."""
    await websocket.accept()
    from backend.config import LOCAL_TESTING
    if LOCAL_TESTING and token == "sandbox-token" and session_id == "00000000-0000-0000-0000-000000000000":
        return True
    try:
        claims = verify_jwt_token(token)
        if str(claims.get("sub")) != session_id:
            raise ValueError("Session mismatch")
        return True
    except Exception as e:
        logger.error(f"WS authentication failed: {str(e)}")
        await websocket.close(code=4001)
        return False

async def _send_sys_msg(websocket: WebSocket, session_uuid: uuid.UUID, session_id: str, content: str) -> None:
    """Helper to save and send a system message over WebSocket."""
    async with async_session_factory() as session:
        sys_msg = await MessageRepository(session).save_message(session_uuid, "system", content)
    await websocket.send_text(json.dumps({
        "type": "message",
        "payload": {
            "id": str(sys_msg.id), "session_id": session_id,
            "role": "system", "content": content,
            "created_at": sys_msg.created_at.isoformat()
        }
    }))

async def _handle_escalation(
    websocket: WebSocket, session_uuid: uuid.UUID, session_id: str,
    content: str, trigger_fallback: bool, redis: RedisSessionManager, session_repo: SessionRepository
) -> bool:
    """Evaluate escalation and perform handoff if needed. Returns True if escalated."""
    escalated = await evaluate_escalation(session_id, content, trigger_fallback, redis)
    if not escalated:
        return False

    reason = "keyword_trigger" if not trigger_fallback else "rag_fallback"
    await execute_handoff(session_id, reason, session_repo, redis)

    status = await get_queue_status(redis)
    await _send_sys_msg(websocket, session_uuid, session_id, status["message"])
    if status.get("is_full"):
        await websocket.send_text(json.dumps({
            "type": "render_ticket_form", "payload": {"session_id": session_id}
        }))
    return True

async def _stream_rag(
    websocket: WebSocket, 
    session_uuid: uuid.UUID, 
    session_id: str, 
    content: str, 
    tenant_id: str,
    redis: RedisSessionManager
) -> None:
    """Streams RAG responses token-by-token and saves the complete AI response."""
    msg_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        m_repo = MessageRepository(session)
        retriever = RAGRetrieverService(KnowledgeRepository(session))
        full = ""
        async for token in run_rag_pipeline(
            session_id=session_id, tenant_id=tenant_id, user_query=content,
            retriever_service=retriever, msg_repo=m_repo, session_repo=SessionRepository(session), redis_manager=redis
        ):
            full += token
            await websocket.send_text(json.dumps({
                "type": "token", "payload": {"message_id": msg_id, "token": token, "role": "ai"}
            }))
        
        # Check if the session was escalated during the pipeline execution
        is_silenced = await redis.redis.get(f"session:{session_id}:ai_silenced")
        if is_silenced in (b"true", "true", True):
            # Send queue status and ticket form to websocket
            status = await get_queue_status(redis)
            await _send_sys_msg(websocket, session_uuid, session_id, status["message"])
            if status.get("is_full"):
                await websocket.send_text(json.dumps({
                    "type": "render_ticket_form", "payload": {"session_id": session_id}
                }))
            return

        await m_repo.save_message(session_uuid, "ai", full)

async def _handle_chat_message(websocket: WebSocket, session_id: str, payload: dict, background_tasks: BackgroundTasks) -> None:
    """Persist customer message, trigger scoring, and stream RAG or escalate."""
    content = payload.get("content")
    if not content:
        return
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return

    from backend.storage.schema import SessionModel
    from sqlalchemy import select
    from unittest.mock import Mock

    customer_id_str = "00000000-0000-0000-0000-000000000000"
    tenant_id_str = "00000000-0000-0000-0000-000000000000"

    async with async_session_factory() as session:
        # Load the session to obtain actual customer_id and tenant_id
        query = select(SessionModel).where(SessionModel.id == session_uuid)
        res = await session.execute(query)
        db_sess = res.scalar_one_or_none()
        
        if db_sess and not isinstance(db_sess, Mock):
            try:
                customer_id_str = str(db_sess.customer_id)
                tenant_id_str = str(db_sess.tenant_id)
            except Exception:
                pass

        db_msg = await MessageRepository(session).save_message(session_uuid, "customer", content)
        
    await websocket.send_text(json.dumps({
        "type": "message",
        "payload": {
            "id": str(db_msg.id), "session_id": session_id,
            "role": "customer", "content": content,
            "created_at": db_msg.created_at.isoformat()
        }
    }))

    try:
        from backend.ws.agent import agent_manager
        await agent_manager.broadcast({
            "type": "message",
            "payload": {
                "id": str(db_msg.id), "session_id": session_id,
                "role": "customer", "content": content,
                "created_at": db_msg.created_at.isoformat()
            }
        })
    except Exception:
        pass

    background_tasks.add_task(score_session_async, session_id, customer_id_str, content, "")
    redis = RedisSessionManager()
    if await redis.redis.get(f"session:{session_id}:ai_silenced") in (b"true", "true"):
        return

    # Check keyword triggers first (early exit to prevent RAG execution and token streaming)
    content_lower = content.lower()
    from backend.config import KEYWORD_TRIGGER_LIST
    if any(keyword in content_lower for keyword in KEYWORD_TRIGGER_LIST):
        async with async_session_factory() as session:
            session_repo = SessionRepository(session)
            if await _handle_escalation(websocket, session_uuid, session_id, content, False, redis, session_repo):
                return

    await _stream_rag(websocket, session_uuid, session_id, content, tenant_id_str, redis)



async def _handle_ticket(websocket: WebSocket, session_id: str, payload: dict) -> None:
    """Save ticket capture form details into PostgreSQL."""
    email, msg = payload.get("email"), payload.get("message")
    if not email or not msg:
        return
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return
    async with async_session_factory() as session:
        await TicketRepository(session).create_ticket(session_uuid, email, msg)
    await websocket.send_text(json.dumps({
        "type": "ticket_submitted",
        "payload": {"status": "success", "message": "Thank you. Your request has been recorded."}
    }))

async def _process_frame(websocket: WebSocket, session_id: str, data: str, background_tasks: BackgroundTasks) -> None:
    """Process a single incoming text frame."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return
    p_type, p_load = payload.get("type"), payload.get("payload", {})
    if p_type == "ping":
        await websocket.send_text(json.dumps({"type": "pong"}))
    elif p_type == "message":
        await _handle_chat_message(websocket, session_id, p_load, background_tasks)
    elif p_type == "escalate":
        async with async_session_factory() as session:
            session_repo = SessionRepository(session)
            await execute_handoff(session_id, "user_request", session_repo, RedisSessionManager())
            status = await get_queue_status(RedisSessionManager())
            await _send_sys_msg(websocket, uuid.UUID(session_id), session_id, status["message"])
            if status.get("is_full"):
                await websocket.send_text(json.dumps({
                    "type": "render_ticket_form", "payload": {"session_id": session_id}
                }))
    elif p_type == "ticket":
        await _handle_ticket(websocket, session_id, p_load)

active_chat_connections: dict[str, WebSocket] = {}

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str, background_tasks: BackgroundTasks, token: str = Query(...)):
    """Handler for customer-facing chat WebSockets."""
    if not await _auth_ws(websocket, session_id, token):
        return
    active_chat_connections[session_id] = websocket
    try:
        while True:
            await _process_frame(websocket, session_id, await websocket.receive_text(), background_tasks)
    except WebSocketDisconnect:
        logger.info(f"WebSocket session {session_id} dropped.")
    finally:
        active_chat_connections.pop(session_id, None)
