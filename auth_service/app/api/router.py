from fastapi import APIRouter
from app.api.routes_auth import router as auth_router

# общий роутер сервиса для новых групп эндпоинтов
router = APIRouter()
router.include_router(auth_router)