from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.api import sessions
from backend.ws import chat as chat_ws
from backend.storage.db import engine
from backend.storage.schema import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="CC-ChatIQ Core API", version="1.0.0", lifespan=lifespan)

app.include_router(sessions.router)
app.include_router(chat_ws.router)

@app.get("/api/v1/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

