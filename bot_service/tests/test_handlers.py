from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from fakeredis.aioredis import FakeRedis
from jose import jwt
from app.bot import handlers
from app.core.config import settings

class FakeMessage:
    def __init__(self, text: str | None, user_id: int = 123, chat_id: int = 456):
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.chat = SimpleNamespace(id=chat_id)
        self.answers: list[str] = []

    # сохраняем ответы бота, чтобы проверить их в тестах
    async def answer(self, text: str) -> None:
        self.answers.append(text)

def create_test_token() -> str:
    payload = {
        "sub": "1",
        "role": "user",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


# проверяем, что команда /token сохраняет валидный jwt в redis
@pytest.mark.asyncio
async def test_token_handler_saves_token(mocker) -> None:
    fake_redis = FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

    token = create_test_token()
    message = FakeMessage(text=f"/token {token}", user_id=123)
    await handlers.token_handler(message)

    saved_token = await fake_redis.get("token:123")
    assert saved_token == token
    assert message.answers == ["Токен принят и сохранён."]


# проверяем, что без токена обычный текст не отправляется в celery
@pytest.mark.asyncio
async def test_text_handler_without_token_refuses_access(mocker) -> None:
    fake_redis = FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    message = FakeMessage(text="Привет", user_id=123)
    await handlers.text_handler(message)

    delay_mock.assert_not_called()
    assert "Нет токена" in message.answers[0]


# проверяем, что с валидным токеном текст отправляется в celery
@pytest.mark.asyncio
async def test_text_handler_with_token_sends_task(mocker) -> None:
    fake_redis = FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    token = create_test_token()
    await fake_redis.set("token:123", token)

    message = FakeMessage(text="Объясни JWT", user_id=123, chat_id=456)
    await handlers.text_handler(message)

    delay_mock.assert_called_once_with(456, "Объясни JWT")
    assert message.answers == ["Запрос принят. Ответ придёт чуть позже."]