from datetime import datetime, timedelta, timezone
from typing import Any
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

# bcrypt, чтобы не хранить реальные пароли в базе
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# превращаем пароль в хеш перед сохранением
def hash_password(password: str) -> str:
    return password_context.hash(password)

# проверяем введённый пароль против хеша из базы
def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)

# создаем jwt с id пользователя, ролью и временем жизни
def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode( payload, settings.jwt_secret, algorithm=settings.jwt_alg )

# проверяем подпись и срок действия jwt
def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode( token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except ExpiredSignatureError as error:
        raise TokenExpiredError() from error
    except JWTError as error:
        raise InvalidTokenError() from error