from typing import List, Dict, Any, Tuple
import tiktoken
from backend.repositories.knowledge import KnowledgeRepository
from backend.utils.embedder import generate_embedding
from backend.config import RAG_TOP_K, RAG_MIN_SIMILARITY, RAG_MAX_CONTEXT_TOKENS

class RAGRetrieverService:
    def __init__(self, repo: KnowledgeRepository):
        self.repo = repo
        # Initialize cl100k_base tokenizer for accurate token ceiling checks
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        """Computes BPE token length of string."""
        return len(self.tokenizer.encode(text))

    async def retrieve_context(self, query_text: str, tenant_id: str) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Fetches similarity-bounded knowledge chunks, enforcing token bounds.
        Returns Tuple[context_string, citation_metadata_list, trigger_fallback_flag].
        """
        import uuid
        tenant_uuid = uuid.UUID(tenant_id)
        
        # 1. Generate query embedding representation
        query_vector = await generate_embedding(query_text)
        
        # 2. Search similarity in pgvector repository using top-k ceiling of 10
        top_k = min(int(RAG_TOP_K), 10)
        chunks = await self.repo.search_similar(query_vector, tenant_id=tenant_uuid, top_k=top_k)
        
        context_blocks = []
        citations = []
        current_token_count = 0
        
        # 3. Enforce similarity boundaries and token limits
        for chunk in chunks:
            if chunk.similarity_score < float(RAG_MIN_SIMILARITY):
                continue
                
            source_label = chunk.source_url if chunk.source_url else chunk.document_title
            formatted_block = f"[Source: {source_label}]\n{chunk.content}\n\n"
            block_tokens = self._count_tokens(formatted_block)
            
            if current_token_count + block_tokens > int(RAG_MAX_CONTEXT_TOKENS):
                break
                
            current_token_count += block_tokens
            context_blocks.append(formatted_block)
            citations.append({
                "document_title": chunk.document_title,
                "source_url": chunk.source_url,
                "chunk_index": chunk.chunk_index
            })

        # 4. Trigger fallback flag if no chunks matched similarity bounds
        trigger_fallback = len(context_blocks) == 0
        
        # Simple greetings or short conversational inputs shouldn't count as a RAG fallback
        clean_query = "".join(c for c in query_text.lower() if c.isalnum() or c.isspace()).strip()
        greetings = {"hi", "hello", "hey", "hola", "yo", "greetings", "good morning", "good afternoon", "good evening"}
        if clean_query in greetings or len(clean_query) <= 3:
            trigger_fallback = False

        full_context_str = "".join(context_blocks)
        
        return full_context_str, citations, trigger_fallback
