import httpx
import logging
import os

logger = logging.getLogger(__name__)

async def send_expo_push_notification(push_token: str, title: str, body: str, data: dict):
    """Asynchronously dispatches a push notification to Expo."""
    access_token = os.getenv("EXPO_ACCESS_TOKEN", "")
    
    payload = {
        "to": push_token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data
    }
    
    # Always log the simulated push notification payload
    logger.info(f"[SIMULATED PUSH] Sending notification to {push_token}: {title} - {body}")
    
    if not access_token or "mock" in access_token.lower() or "ExponentPushToken" not in push_token:
        # In sandbox/local test mode, return immediately
        return True

    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip, deflate",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://exp.host/--/api/v2/push/send",
                json=payload,
                headers=headers,
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to dispatch real push notification to Expo: {str(e)}")
            return False
