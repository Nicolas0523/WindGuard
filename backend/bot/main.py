import asyncio
from bot_instance import bot, dp

async def main() -> None:
    await dp.start_polling(
    bot,
    polling_timeout=30
)

if __name__ == "__main__":
    asyncio.run(main())