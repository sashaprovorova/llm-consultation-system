import asyncio
from aiogram import Bot
from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterClient

async def _process_llm_request(tg_chat_id: int, prompt: str) -> None:
    bot = Bot(token=settings.telegram_bot_token)
    client = OpenRouterClient()

    try:
        # вызываем llm во внешнем сервисе
        answer = await client.chat(prompt)
    except RuntimeError as error:
        answer = f"Ошибка при обращении к LLM: {error}"

    # отправляем ответ обратно пользователю в telegram
    await bot.send_message(chat_id=tg_chat_id, text=answer)
    await bot.session.close()

@celery_app.task(name="llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> None:
    # celery задача синхронная, поэтому async код запускаем через asyncio
    asyncio.run(_process_llm_request(tg_chat_id, prompt))