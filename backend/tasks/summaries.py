import asyncio
import uuid
import logging
from backend.tasks.worker import celery_app
from backend.storage.db import async_session_factory
from backend.repositories.session import SessionRepository
from backend.repositories.message import MessageRepository
from backend.ai.mock import MockAdapter

logger = logging.getLogger("summaries_task")

async def async_generate_summary(session_id_str: str) -> None:
    """Core asynchronous handler compiling message history, calling LLM, and saving summary."""
    try:
        session_uuid = uuid.UUID(session_id_str)
        async with async_session_factory() as session:
            repo = SessionRepository(session)
            msg_repo = MessageRepository(session)
            
            # 1. Fetch complete session message history
            messages = await msg_repo.get_history(session_uuid, None, limit=100)
            if not messages:
                logger.warning(f"No message history found for session {session_id_str}. Skipping summary.")
                return
                
            history_str = "\n".join([f"[{m.role}]: {m.content}" for m in messages])
            
            # 2. Query MockAdapter (or active AI provider) for a concise summary
            adapter = MockAdapter()
            prompt = f"Summarize the following support conversation in 1 or 2 sentences:\n{history_str}"
            
            summary_tokens = []
            async for token in adapter.send_message(
                session_id=session_id_str,
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a concise customer support summarizer."
            ):
                summary_tokens.append(token)
            summary = "".join(summary_tokens).strip()
            
            # 3. Truncate and persist summary back to the database record
            summary = summary[:500]
            await repo.update_summary(session_uuid, summary)
            logger.info(f"Successfully generated summary for session: {session_id_str}")
    except Exception as e:
        logger.exception(f"Background session summary generation failed: {str(e)}")
        raise e

@celery_app.task
def generate_summary_task(session_id_str: str) -> None:
    """Synchronous Celery task wrapper calling the async handler in a dedicated thread."""
    import threading
    exception = []
    
    def worker():
        try:
            asyncio.run(async_generate_summary(session_id_str))
        except Exception as e:
            exception.append(e)
            
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    
    if exception:
        raise exception[0]
