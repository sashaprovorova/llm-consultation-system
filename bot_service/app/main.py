from fastapi import FastAPI
from app.core.config import settings

# создаём служебное fastapi-приложение для health check
app = FastAPI(title=settings.app_name)

@app.get("/health")
async def health() -> dict[str, str]:
    return { "status": "ok", "env": settings.env}