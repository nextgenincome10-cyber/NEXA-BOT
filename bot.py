import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, WEBAPP_URL
from database import init_db, get_or_create_user


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_command(message: Message):
    user = message.from_user

    get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🚀 Open NEXA",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )

    keyboard.adjust(1)

    await message.answer(
        f"👋 Welcome to NEXA, {user.first_name}!\n\n"
        "Manage your mining dashboard, balance, "
        "tasks, referrals and account activity "
        "from the NEXA Mini App.\n\n"
        "Tap the button below to open NEXA.",
        reply_markup=keyboard.as_markup()
    )


async def main():
    print("NEXA Bot is starting...")

    init_db()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())