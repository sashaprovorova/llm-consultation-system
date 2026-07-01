from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.core.config import settings

# строка подключения к sqlite через async драйвер
database_url = f"sqlite+aiosqlite:///{settings.sqlite_path}"

engine = create_async_engine(database_url, echo=False)

# фабрика асинхронных сессий для работы с бд
AsyncSessionLocal = async_sessionmaker( bind=engine, expire_on_commit=False)