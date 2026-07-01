from redis.asyncio import Redis
from app.core.config import settings

# один общий redis клиент для хранения токенов пользователей telegram
redis_client = Redis.from_url( settings.redis_url,  decode_responses=True)

# отдаёт redis клиент в handlers и тесты
def get_redis() -> Redis:
    return redis_client