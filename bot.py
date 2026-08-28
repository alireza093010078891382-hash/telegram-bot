import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
import asyncio

# توکن ربات شما
TOKEN = "8989518912:AAEiTdDY2xJwtgapKRghHqwBefEWJNj1b9U"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(lambda message: message.text == "/start")
async def start_handler(message: Message):
    await message.answer("سلام! ربات شما با موفقیت روی ریلوی روشن شد. 🚀")

@dp.message()
async def echo_handler(message: Message):
    await message.answer(f"پیام شما دریافت شد: {message.text}")

async def main():
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())