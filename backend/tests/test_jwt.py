import time
import uuid
import pytest
from jose import ExpiredSignatureError, JWTError
from backend.utils.jwt import create_jwt_token, verify_jwt_token

def test_jwt_generation_and_verification():
    payload = {"sub": "user_id_123", "role": "customer", "tenant_id": "tenant_123"}
    token = create_jwt_token(payload, expires_in=10)
    decoded = verify_jwt_token(token)
    assert decoded["sub"] == "user_id_123"
    assert decoded["role"] == "customer"
    assert decoded["tenant_id"] == "tenant_123"

def test_jwt_expiration():
    payload = {"sub": "user_id_123", "role": "customer", "tenant_id": "tenant_123"}
    # Token expires in 1 second
    token = create_jwt_token(payload, expires_in=1)
    time.sleep(2)
    with pytest.raises(ExpiredSignatureError):
        verify_jwt_token(token)

def test_jwt_uuid_casting_and_type_preservation():
    test_uuid = uuid.uuid4()
    payload = {
        "sub": test_uuid,
        "is_admin": False,
        "count": 42
    }
    token = create_jwt_token(payload, expires_in=10)
    decoded = verify_jwt_token(token)
    
    # Assert UUID was cast to a string
    assert decoded["sub"] == str(test_uuid)
    # Assert boolean False was preserved and not cast to a string
    assert decoded["is_admin"] is False
    # Assert integer 42 was preserved and not cast to a string
    assert decoded["count"] == 42

def test_jwt_verify_robust_handling():
    # Test None token
    with pytest.raises(JWTError) as exc_info:
        verify_jwt_token(None)
    assert "Invalid token format" in str(exc_info.value)
    
    # Test empty token
    with pytest.raises(JWTError) as exc_info:
        verify_jwt_token("")
    assert "Invalid token format" in str(exc_info.value)
    
    # Test non-string token
    with pytest.raises(JWTError) as exc_info:
        verify_jwt_token(12345)
    assert "Invalid token format" in str(exc_info.value)

