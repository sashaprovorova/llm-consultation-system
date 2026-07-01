import httpx
from app.core.config import settings

class OpenRouterClient:
    async def chat(self, prompt: str) -> str:
        # собираем url для chat completions
        url = f"{settings.openrouter_base_url}/chat/completions"

        # заголовки нужны для авторизации в openrouter
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        }

        # payload содержит модель и сообщение пользователя
        payload = {
            "model": settings.openrouter_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as error:
            raise RuntimeError("Failed to connect to OpenRouter") from error

        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenRouter error: {response.status_code} {response.text}"
            )

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("Invalid response from OpenRouter") from error