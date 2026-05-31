import asyncio
import uuid
import logging
from backend.tasks.worker import celery_app
from backend.utils.text import chunk_text
from backend.utils.embedder import generate_embedding
from backend.storage.db import async_session_factory
from backend.repositories.knowledge import KnowledgeRepository

logger = logging.getLogger("ingestion_task")

async def async_ingest_document(
    tenant_id_str: str, 
    title: str, 
    source_url: str, 
    text: str
) -> None:
    """Core asynchronous ingestion handler processing text chunks and vector embeddings."""
    try:
        tenant_uuid = uuid.UUID(tenant_id_str)
        # 1. Parse text into overlapping chunks (512 words, 64 overlap)
        chunks = chunk_text(text, chunk_size=512, overlap=64)
        
        async with async_session_factory() as session:
            repo = KnowledgeRepository(session)
            
            # 2. Iterate through segments, generate embeddings, and save
            for idx, chunk in enumerate(chunks):
                embedding = await generate_embedding(chunk)
                await repo.save_chunk(
                    tenant_id=tenant_uuid,
                    title=title,
                    content=chunk,
                    embedding=embedding,
                    index=idx,
                    source_url=source_url
                )
        logger.info(f"Successfully ingested {len(chunks)} chunks for document: {title}")
    except Exception as e:
        logger.exception(f"Background ingestion failed: {str(e)}")
        raise e

@celery_app.task
def ingest_document_task(
    tenant_id_str: str, 
    title: str, 
    source_url: str, 
    text: str
) -> None:
    """Synchronous Celery task wrapper calling the async handler in a dedicated thread."""
    import threading
    
    exception = []
    
    def worker():
        try:
            asyncio.run(async_ingest_document(tenant_id_str, title, source_url, text))
        except Exception as e:
            exception.append(e)
            
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    
    if exception:
        raise exception[0]
