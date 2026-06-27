import asyncio
from uuid import UUID
from backend.storage.db import async_session_factory
from backend.repositories.knowledge import KnowledgeRepository
from backend.rag.retriever import RAGRetrieverService
from backend.rag.prompt import assemble_system_prompt
from backend.ai.base import get_active_ai_provider

async def main():
    print("--- TESTING RAG RETRIEVAL AND LLM STREAMING ---")
    tenant_id = "00000000-0000-0000-0000-000000000000"
    query = "how can I optimize battery drain on my phone"
    
    async with async_session_factory() as session:
        repo = KnowledgeRepository(session)
        retriever = RAGRetrieverService(repo)
        
        print(f"Retrieving context for query: '{query}'...")
        context_str, citations, trigger_fallback = await retriever.retrieve_context(query, tenant_id)
        
        print(f"Context length: {len(context_str)}")
        print(f"Citations: {citations}")
        print(f"Trigger fallback: {trigger_fallback}")
        print(f"Context content:\n{context_str}\n")
        
        history_str = f"customer: {query}"
        system_prompt = assemble_system_prompt(
            company_name="CC-ChatIQ Partner",
            context_str=context_str,
            history_str=history_str
        )
        
        print(f"--- Constructed System Prompt ---\n{system_prompt}\n---------------------------------")
        
        print("Streaming response from active AI provider:")
        ai_provider = get_active_ai_provider()
        async for token in ai_provider.stream_response(system_prompt):
            print(token, end="", flush=True)
        print("\n--- STREAMING END ---")

if __name__ == "__main__":
    asyncio.run(main())
