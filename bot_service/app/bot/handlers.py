from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Сначала отправь JWT токен командой /token <токен>."
    )

@router.message(Command("token"))
async def token_handler(message: Message) -> None:
    parts = message.text.split(maxsplit=1) if message.text else []

    if len(parts) < 2:
        await message.answer("Отправь токен в формате: /token <jwt>")
        return

    token = parts[1].strip()

    try:
        # проверяем, что токен подписан auth service и ещё не истёк
        payload = decode_and_validate(token)
    except ValueError:
        await message.answer("Токен неверный или истёк. Получи новый токен в Auth Service.")
        return

    user_id = payload.get("sub")

    if user_id is None:
        await message.answer("В токене нет user_id.")
        return

    redis = get_redis()
    key = f"token:{message.from_user.id}"

    # сохраняем jwt в redis и привязываем его к telegram user_id
    await redis.set(key, token)

    await message.answer("Токен принят и сохранён.")


@router.message()
async def text_handler(message: Message) -> None:
    redis = get_redis()
    key = f"token:{message.from_user.id}"
    token = await redis.get(key)

    if token is None:
        await message.answer(
            "Нет токена. Сначала авторизуйся через Auth Service и отправь /token <jwt>."
        )
        return

    try:
        # перед llm запросом ещё раз проверяем jwt
        decode_and_validate(token)
    except ValueError:
        await message.answer("Токен неверный или истёк. Получи новый токен.")
        return

    if message.text is None:
        await message.answer("Отправь текстовый вопрос.")
        return

    # долгий llm запрос отправляем в celery, чтобы не блокировать бота
    llm_request.delay(message.chat.id, message.text)
    await message.answer("Запрос принят. Ответ придёт чуть позже.")