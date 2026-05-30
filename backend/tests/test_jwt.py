import time
import pytest
from jose import ExpiredSignatureError
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
