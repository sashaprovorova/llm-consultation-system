from datetime import datetime, timedelta, timezone
import pytest
from jose import jwt
from app.core.config import settings
from app.core.jwt import decode_and_validate

# проверяем, что bot service принимает jwt от auth service
def test_decode_valid_token() -> None:
    payload = {
        "sub": "1",
        "role": "user",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    token = jwt.encode( payload, settings.jwt_secret, algorithm=settings.jwt_alg)

    decoded_payload = decode_and_validate(token)

    assert decoded_payload["sub"] == "1"
    assert decoded_payload["role"] == "user"


# проверяем, что bot service не принимает мусор вместо jwt
def test_decode_invalid_token() -> None:
    with pytest.raises(ValueError):
        decode_and_validate("not-a-real-token")