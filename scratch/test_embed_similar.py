import asyncio
import uuid
from backend.utils.embedder import generate_embedding
from backend.storage.db import async_session_factory
from backend.repositories.knowledge import KnowledgeRepository

async def test():
    print("1. Testing generate_embedding...")
    try:
        query_vector = await asyncio.wait_for(generate_embedding("Hi, what are the specs of T001?"), timeout=5.0)
        print(f"Embedding generated successfully! Length: {len(query_vector)}")
    except asyncio.TimeoutError:
        print("generate_embedding HUNG!")
        return
    except Exception as e:
        print(f"generate_embedding failed with exception: {e}")
        return

    print("2. Testing search_similar...")
    async with async_session_factory() as session:
        repo = KnowledgeRepository(session)
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        try:
            chunks = await asyncio.wait_for(repo.search_similar(query_vector, tenant_id, top_k=5), timeout=5.0)
            print(f"search_similar returned {len(chunks)} chunks.")
        except asyncio.TimeoutError:
            print("search_similar HUNG!")
        except Exception as e:
            print(f"search_similar failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(test())
