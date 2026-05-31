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
        chunk = KnowledgeChunkModel(
            tenant_id=tenant_id,
            document_title=title,
            content=content,
            embedding=embedding,
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
