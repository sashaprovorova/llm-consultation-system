from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_auth_uc, get_current_user_id
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUseCase

# тут все маршруты начинаются с /auth
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post( "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register( data: RegisterRequest, auth_uc: AuthUseCase = Depends(get_auth_uc)) -> UserPublic:
    # роут не работает с бд напрямую, а передаёт данные в usecase
    return await auth_uc.register(email=data.email, password=data.password)

@router.post("/login", response_model=TokenResponse)
async def login( form: OAuth2PasswordRequestForm = Depends(), auth_uc: AuthUseCase = Depends(get_auth_uc)) -> TokenResponse:
    # username используется как email, чтобы работала oauth2-авторизация в swagger
    token = await auth_uc.login(email=form.username, password=form.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me( user_id: int = Depends(get_current_user_id),  auth_uc: AuthUseCase = Depends(get_auth_uc)) -> UserPublic:
    # user_id приходит из jwt, поэтому возвращаем текущего пользователя
    return await auth_uc.me(user_id)