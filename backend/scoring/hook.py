import logging
import httpx
from backend.config import CALMIQ_WEBHOOK_URL, CALMIQ_WEBHOOK_SECRET

logger = logging.getLogger(__name__)

async def score_session_async(session_id: str, customer_id: str, message: str, history: str):
    """Asynchronously triggers the outbound CalmIQ webhook to evaluate frustration."""
    if not CALMIQ_WEBHOOK_URL:
        return

    payload = {
        "session_id": session_id,
        "customer_id": customer_id,
        "message": message,
        "history": history
    }
    
    headers = {
        "X-CalmIQ-Secret": CALMIQ_WEBHOOK_SECRET
    }

    async with httpx.AsyncClient() as client:
        try:
            # Parallel outbound scoring request does not delay primary chat widget replies
            response = await client.post(
                CALMIQ_WEBHOOK_URL,
                json=payload,
                headers=headers,
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("escalate"):
                    # Local direct escalation trigger on threshold breach
                    logger.info(f"CalmIQ webhook scored session {session_id} for urgent agent escalation")
        except Exception as e:
            # Resilient log and fallback: scoring failures do not block the active conversation
            logger.error(f"Outgoing CalmIQ scoring post request failed: {str(e)}")
