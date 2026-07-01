import asyncio
from app.bot.dispatcher import bot, dispatcher


# запускает telegram-бота в режиме polling
async def main() -> None:
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
