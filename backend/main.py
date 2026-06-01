from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.api import sessions, knowledge, webhooks, queue
from backend.ws import chat as chat_ws, agent as agent_ws
from backend.storage.db import engine
from backend.storage.schema import Base

from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Warning: Database initialization or pgvector extension setup failed: {e}")
    yield
    await engine.dispose()

app = FastAPI(title="CC-ChatIQ Core API", version="1.0.0", lifespan=lifespan)

app.include_router(sessions.router)
app.include_router(knowledge.router)
app.include_router(webhooks.router)
app.include_router(queue.router)
app.include_router(chat_ws.router)
app.include_router(agent_ws.router)

@app.get("/api/v1/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

