import uuid
from typing import AsyncGenerator
from backend.rag.retriever import RAGRetrieverService
from backend.rag.prompt import assemble_system_prompt
from backend.ai.base import get_active_ai_provider
from backend.handoff.triggers import evaluate_escalation
from backend.handoff.executor import execute_handoff
from backend.repositories.message import MessageRepository
from backend.repositories.session import SessionRepository
from backend.session.state import RedisSessionManager

async def run_rag_pipeline(
    session_id: str,
    tenant_id: str,
    user_query: str,
    retriever_service: RAGRetrieverService,
    msg_repo: MessageRepository,
    session_repo: SessionRepository,
    redis_manager: RedisSessionManager
) -> AsyncGenerator[str, None]:
    """
    Coordinates context retrieval, prompt construction, fallback counter state auditing,
    and real-time token streaming.
    """
    # 1. Retrieve tenant-isolated context blocks and fallback signals
    context_str, citations, trigger_fallback = await retriever_service.retrieve_context(
        query_text=user_query,
        tenant_id=tenant_id
    )

    print(f"--- RAG PIPELINE DEBUG: query='{user_query}', tenant_id='{tenant_id}', context_len={len(context_str)}, trigger_fallback={trigger_fallback} ---")

    # 2. Evaluate escalation constraints via keyword checks and fallback metrics
    should_escalate = await evaluate_escalation(
        session_id=session_id,
        message_content=user_query,
        trigger_fallback=trigger_fallback,
        redis_manager=redis_manager
    )

    if should_escalate:
        # Determine the reason code to report to the agent panel roster layout
        reason = "rag_fallback" if trigger_fallback else "keyword_trigger"
        await execute_handoff(session_id, reason, session_repo, redis_manager)
        
        # Stream the formal fallback escalation announcement response to the client
        from backend.config import RAG_FALLBACK_PHRASE
        yield RAG_FALLBACK_PHRASE
        
        # Save system escalation message to database to maintain session history continuity
        await msg_repo.save_message(
            session_id=uuid.UUID(session_id),
            role="system",
            content=RAG_FALLBACK_PHRASE
        )
        return

    # 3. Compile history and assemble dynamic prompt context if within safe bounds
    history_list = await msg_repo.get_history(
        session_id=uuid.UUID(session_id), 
        tenant_id=uuid.UUID(tenant_id), 
        limit=10
    )
    history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in reversed(history_list)])

    system_prompt = assemble_system_prompt(
        company_name="CC-ChatIQ Partner",
        context_str=context_str,
        history_str=history_str
    )

    # 4. Stream token responses seamlessly out of the active dynamic AI Provider
    ai_provider = get_active_ai_provider()
    async for token in ai_provider.stream_response(system_prompt):
        yield token
