import datetime
import uuid
from jose import jwt, JWTError
from backend.config import JWT_SECRET, JWT_ALGORITHM

def create_jwt_token(payload: dict, expires_in: int) -> str:
    """Generates a cryptographically signed, timezone-aware JWT token with absolute expiration."""
    data = payload.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)
    
    # Strictly cast UUID values to strings, preserving other types (like booleans, integers, etc.)
    processed_payload = {
        k: str(v) if isinstance(v, uuid.UUID) else v
        for k, v in data.items()
    }
    processed_payload.update({"exp": int(expire.timestamp())})
    
    return jwt.encode(processed_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Decodes and validates JWT claims; raises JWTError on expired, corrupt, or invalid token inputs."""
    if not token or not isinstance(token, str):
        raise JWTError("Invalid token format: token must be a non-empty string.")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise e
    except Exception as e:
        raise JWTError(f"JWT verification failed: {str(e)}") from e
