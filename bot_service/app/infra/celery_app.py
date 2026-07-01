from celery import Celery
from app.core.config import settings

# celery использует rabbitmq как брокер, а redis как backend результатов
celery_app = Celery( "bot_service", broker=settings.rabbitmq_url, backend=settings.redis_url)

# явно импортируем tasks, чтобы celery зарегистрировал llm_request
import app.tasks.llm_tasks  # noqa: E402, F401