import asyncio
import uuid
from backend.storage.db import async_session_factory
from backend.repositories.knowledge import KnowledgeRepository
from backend.utils.embedder import generate_embedding

async def main():
    print("=================== SEEDING MOBILE CUSTOMER CARE RAG DATA ===================")
    
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    
    documents = [
        {
            "title": "ChatIQ Mobile Return & Refund Policy",
            "content": "All ChatIQ Mobile phones purchased from our official store come with a 1-year limited warranty covering hardware defects. Screen damage and water exposure are not covered. We offer replacement or repair service for verified defects, but all sales are final—we do not offer refunds.",
            "source_url": "https://chatiq-mobile.com/policies/warranty"
        },
        {
            "title": "ChatIQ Phone 12 Pro Specifications",
            "content": "The ChatIQ Phone 12 Pro features a 6.7-inch OLED display, a triple camera system with a 48MP main sensor, 12GB of RAM, and the A18 Bionic chip. It is available in obsidian black, galactic silver, and sunset gold, starting at $999.",
            "source_url": "https://chatiq-mobile.com/specs/phone12pro"
        },
        {
            "title": "Troubleshooting Battery Drain",
            "content": "If you are experiencing fast battery drain on your ChatIQ mobile phone, go to Settings > Battery > Battery Health to check capacity. You can optimize life by turning off background app refresh, lowering screen brightness, and enabling low power mode.",
            "source_url": "https://chatiq-mobile.com/help/battery-drain"
        }
    ]
    
    async with async_session_factory() as session:
        repo = KnowledgeRepository(session)
        for i, doc in enumerate(documents):
            print(f"Generating embedding for chunk {i+1}: '{doc['title']}'...")
            embedding = await generate_embedding(doc['content'])
            
            print(f"Persisting chunk {i+1} to PostgreSQL...")
            await repo.save_chunk(
                tenant_id=tenant_id,
                title=doc['title'],
                content=doc['content'],
                embedding=embedding,
                index=i,
                source_url=doc['source_url']
            )
            
    print("=================== SEEDING COMPLETED SUCCESSFULY ===================")

if __name__ == "__main__":
    asyncio.run(main())
