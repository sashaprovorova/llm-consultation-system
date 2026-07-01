from typing import Any
from jose import ExpiredSignatureError, JWTError, jwt
from app.core.config import settings

# проверяем jwt, который был выдан auth service
def decode_and_validate(token: str) -> dict[str, Any]:
    try:
        return jwt.decode( token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except ExpiredSignatureError as error:
        raise ValueError("Token expired") from error
    except JWTError as error:
        raise ValueError("Invalid token") from error