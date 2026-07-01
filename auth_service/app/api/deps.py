from collections.abc import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import InvalidTokenError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.repositories.users import UsersRepository
from app.usecases.auth import AuthUseCase

# swagger получает токен через /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# открываем сессию бд на время одного запроса
async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session

# передаем текущую сессию в репозиторий пользователей
def get_users_repo(session: AsyncSession = Depends(get_db)) -> UsersRepository:
    return UsersRepository(session)

# собираем usecase авторизации из репозитория
def get_auth_uc( users_repository: UsersRepository = Depends(get_users_repo)) -> AuthUseCase:
    return AuthUseCase(users_repository)

# проверяем jwt и достаёт user_id из sub
def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    payload = decode_token(token)

    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as error:
        raise InvalidTokenError() from error