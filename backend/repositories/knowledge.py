from typing import List, Optional, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.base import BaseKnowledgeRepository
from backend.storage.schema import KnowledgeChunkModel

class KnowledgeRepository(BaseKnowledgeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_chunk(
        self, 
        tenant_id: UUID, 
        title: str, 
        content: str, 
        embedding: List[float], 
        index: int, 
        source_url: Optional[str] = None
    ) -> Any:
        """Saves a single document chunk and its embedding to the database."""
        from backend.storage.schema import HAS_PGVECTOR
        import json
        
        db_embedding = embedding if HAS_PGVECTOR else json.dumps(embedding)
        chunk = KnowledgeChunkModel(
            tenant_id=tenant_id,
            document_title=title,
            content=content,
            embedding=db_embedding,
            chunk_index=index,
            source_url=source_url
        )
        self.session.add(chunk)
        await self.session.commit()
        return chunk

    async def search_similar(
        self, 
        query_vector: List[float], 
        tenant_id: UUID, 
        top_k: int = 5
    ) -> List[Any]:
        """Performs a tenant-isolated similarity search using cosine distance."""
        from backend.storage.schema import HAS_PGVECTOR
        import json
        import math
        
        try:
            if HAS_PGVECTOR:
                # Cosine distance between dynamic embedding and query_vector
                distance = KnowledgeChunkModel.embedding.cosine_distance(query_vector)
                stmt = (
                    select(KnowledgeChunkModel, (1.0 - distance).label("similarity_score"))
                    .where(KnowledgeChunkModel.tenant_id == tenant_id)
                    .order_by(distance)
                    .limit(top_k)
                )
                
                result = await self.session.execute(stmt)
                chunks = []
                for row in result:
                    chunk = row[0]
                    chunk.similarity_score = float(row[1])
                    chunks.append(chunk)
                    
                return chunks
            else:
                # Fallback: fetch chunks and compute cosine similarity in Python
                stmt = select(KnowledgeChunkModel).where(KnowledgeChunkModel.tenant_id == tenant_id)
                result = await self.session.execute(stmt)
                all_chunks = result.scalars().all()
                
                def cosine_similarity(v1, v2):
                    dot_product = sum(x * y for x, y in zip(v1, v2))
                    magnitude1 = math.sqrt(sum(x * x for x in v1))
                    magnitude2 = math.sqrt(sum(x * x for x in v2))
                    if not magnitude1 or not magnitude2:
                        return 0.0
                    return dot_product / (magnitude1 * magnitude2)
                
                scored_chunks = []
                for chunk in all_chunks:
                    try:
                        v2 = json.loads(chunk.embedding)
                        score = cosine_similarity(query_vector, v2)
                        chunk.similarity_score = score
                        scored_chunks.append((chunk, score))
                    except Exception:
                        continue
                        
                scored_chunks.sort(key=lambda item: item[1], reverse=True)
                return [item[0] for item in scored_chunks[:top_k]]
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Similarity search failed: %s", e)
            await self.session.rollback()
            return []
