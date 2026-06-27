import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from backend.rag.pipeline import run_rag_pipeline
from backend.rag.retriever import RAGRetrieverService
from backend.session.state import RedisSessionManager
from backend import config
from backend.rag.prompt import assemble_system_prompt
from backend.ai.base import get_active_ai_provider

# Set active provider to Groq and use the provided API key
config.AI_PROVIDER = "groq"
config.AI_MODEL_GROQ = "llama-3.1-8b-instant"
import os
config.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

async def main():
    print("=================== CC-ChatIQ RAG TEST RUN ===================")
    
    # 1. Mock database similarity search to return the text document context
    mock_repo = AsyncMock()
    mock_chunk = MagicMock()
    mock_chunk.document_title = "Refund Policy"
    mock_chunk.source_url = None
    mock_chunk.content = "we dont have any refund policy only replacement available"
    mock_chunk.chunk_index = 0
    mock_chunk.similarity_score = 0.95
    
    mock_repo.search_similar.return_value = [mock_chunk]
    
    # Instantiate retriever service
    retriever_service = RAGRetrieverService(mock_repo)
    
    # Mock message and session repositories
    mock_msg_repo = AsyncMock()
    mock_msg_repo.get_history.return_value = []
    mock_session_repo = AsyncMock()
    
    # Mock Redis client and manager
    mock_redis = AsyncMock()
    mock_redis.incrby.return_value = 0
    redis_manager = RedisSessionManager(redis_client=mock_redis)
    
    session_id = str(uuid4())
    tenant_id = str(uuid4())
    
    # Customer query
    query = "i want a refund for this am not happy with the product"
    
    # -------------------------------------------------------------
    # Case 1: Standard Pipeline (Keyword Trigger check)
    # -------------------------------------------------------------
    print(f"\n[Customer Query]: '{query}'")
    print("\n--- Case 1: Standard Pipeline (Keyword 'refund' triggers human handoff) ---")
    print("Output:")
    async for token in run_rag_pipeline(
        session_id=session_id,
        tenant_id=tenant_id,
        user_query=query,
        retriever_service=retriever_service,
        msg_repo=mock_msg_repo,
        session_repo=mock_session_repo,
        redis_manager=redis_manager
    ):
        print(token, end="", flush=True)
    print("\n--------------------------------------------------------------")
    
    # -------------------------------------------------------------
    # Case 2: Forced Grounded RAG (Bypasses keyword trigger to show LLM RAG answering)
    # -------------------------------------------------------------
    print("\n--- Case 2: Grounded RAG (Bypassing triggers to show LLM RAG output) ---")
    print("Context Chunk: 'we dont have any refund policy only replacement available'")
    print("Output:")
    
    # Retrieve context manually
    context_str, citations, trigger_fallback = await retriever_service.retrieve_context(
        query_text=query,
        tenant_id=tenant_id
    )
    
    # Compile prompt
    system_prompt = assemble_system_prompt(
        company_name="CC-ChatIQ Partner",
        context_str=context_str,
        history_str=""
    )
    
    # Stream from Groq LLM
    ai_provider = get_active_ai_provider()
    async for token in ai_provider.stream_response(system_prompt):
        print(token, end="", flush=True)
    print("\n==============================================================")

if __name__ == "__main__":
    asyncio.run(main())
