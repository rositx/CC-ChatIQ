import datetime
from jose import jwt, JWTError
from backend.config import JWT_SECRET, JWT_ALGORITHM

def create_jwt_token(payload: dict, expires_in: int) -> str:
    """Generates a cryptographically signed, timezone-aware JWT token with absolute expiration."""
    data = payload.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)
    
    stringified_payload = {k: str(v) for k, v in data.items()}
    stringified_payload.update({"exp": int(expire.timestamp())})
    
    return jwt.encode(stringified_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Decodes and validates JWT claims; raises JWTError on expired or corrupt strings."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise e
