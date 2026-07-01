import pytest
import respx
from httpx import Response
from app.core.config import settings
from app.services.openrouter_client import OpenRouterClient

# проверяем, что клиент правильно читает ответ openrouter
@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_returns_answer() -> None:
    route = respx.post( f"{settings.openrouter_base_url}/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Тестовый ответ LLM",
                        }
                    }
                ]
            },
        )
    )

    client = OpenRouterClient()
    answer = await client.chat("Привет")

    assert route.called
    assert answer == "Тестовый ответ LLM"


# проверяем, что ошибка openrouter превращается в понятную ошибку
@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_raises_on_error() -> None:
    respx.post( f"{settings.openrouter_base_url}/chat/completions").mock(return_value=Response(500, text="server error"))

    client = OpenRouterClient()

    with pytest.raises(RuntimeError):
        await client.chat("Привет")