import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from openai_client import ask_chatgpt

logger = logging.getLogger(__name__)

MENU_KB = ReplyKeyboardMarkup([['Присоединиться', 'Узнать результат']], resize_keyboard=True)


async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Получаем файл и URL/bytes из стикера
    sticker = update.message.sticker
    file = await context.bot.get_file(sticker.file_id)
    img_bytes = await file.download_as_bytearray()

    # 2. Сохраняем полученные байты в user_data
    photos = context.user_data.setdefault("pending_photos", [])
    photos.append(img_bytes)

    await update.message.reply_text("Стикер получен. Обработка...")
    result = await ask_chatgpt(img_bytes)
    await update.message.reply_text(result)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Главное меню бота
    await update.message.reply_text(
        "👋 Отправьте стикер"
    )