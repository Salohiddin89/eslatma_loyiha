"""
Kun Tartibi — Telegram Bot
Foydalanish: python bot/main.py
"""
import asyncio
import logging
import os
import sys
import django
from pathlib import Path

# Django setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from django.conf import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    from accounts.models import User
    tid = message.from_user.id
    try:
        user = User.objects.get(telegram_id=tid)
        await message.answer(
            f"👋 Salom, <b>{user.first_name}</b>!\n\n"
            f"Men sizning <b>Kun Tartibi</b> botingizman.\n"
            f"Kunlik vazifalaringiz va eslatmalaringiz vaqtida xabar bo'lib keladi.\n\n"
            f"🌐 Sayt: /sayt",
            parse_mode='HTML'
        )
    except User.DoesNotExist:
        await message.answer(
            "👋 Salom!\n\n"
            "Siz hali ro'yxatdan o'tmagansiz yoki Telegram ID kiritmagansiz.\n"
            f"🆔 Sizning Telegram ID: <code>{tid}</code>\n\n"
            "Saytda ro'yxatdan o'tishda ushbu ID ni kiriting.",
            parse_mode='HTML'
        )


@dp.message(Command('id'))
async def id_handler(message: Message):
    await message.answer(
        f"🆔 Sizning Telegram ID: <code>{message.from_user.id}</code>",
        parse_mode='HTML'
    )


@dp.message(Command('sayt'))
async def sayt_handler(message: Message):
    await message.answer(
        "🌐 <b>Kun Tartibi</b> saytiga kirish uchun:\n"
        "http://localhost:8000/",
        parse_mode='HTML'
    )


async def main():
    from scheduler import start_scheduler
    scheduler = start_scheduler(bot)
    try:
        logger.info("Bot ishga tushdi...")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
