from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.api import sessions, knowledge, webhooks, queue, widget, analytics
from backend.ws import chat as chat_ws, agent as agent_ws
from backend.storage.db import engine
from backend.storage.schema import Base

from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Try to create vector extension
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    except Exception as ve:
        print(f"Warning: Database vector extension setup failed (this is normal if pgvector is not installed on the system): {ve}")

    # 2. Create tables one by one (gracefully handle table creation failures like pgvector table)
    for table in Base.metadata.sorted_tables:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: table.create(sync_conn, checkfirst=True))
        except Exception as te:
            print(f"Warning: Could not create table '{table.name}': {te}")

    # 3. Seed default sandbox session and default sandbox API key
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                INSERT INTO sessions (id, customer_id, tenant_id, status)
                VALUES (
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    'active'
                ) ON CONFLICT (id) DO NOTHING;
            """))
            await conn.execute(text("""
                INSERT INTO tenant_api_keys (id, tenant_id, api_key, domain_whitelist)
                VALUES (
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    '00000000-0000-0000-0000-000000000000'::uuid,
                    'sandbox-api-key',
                    NULL
                ) ON CONFLICT (id) DO NOTHING;
            """))
    except Exception as e:
        print(f"Warning: Database seeding failed: {e}")

    yield
    await engine.dispose()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CC-ChatIQ Core API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(knowledge.router)
app.include_router(webhooks.router)
app.include_router(queue.router)
app.include_router(widget.router)
app.include_router(analytics.router)
app.include_router(chat_ws.router)
app.include_router(agent_ws.router)

@app.get("/api/v1/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

