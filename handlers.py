import logging

from telegram import Update
from telegram.ext import ContextTypes

from openai_client import ask_chatgpt

logger = logging.getLogger(__name__)

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info("User %s sent a sticker", user_id)

    # 1. Получаем файл и URL/bytes из стикера
    sticker = update.message.sticker
    logger.debug("Sticker file_id: %s", sticker.file_id)
    file = await context.bot.get_file(sticker.file_id)
    img_bytes = await file.download_as_bytearray()
    logger.info("Downloaded sticker bytes (%d bytes)", len(img_bytes))

    # 2. Сохраняем полученные байты в user_data
    photos = context.user_data.setdefault("pending_photos", [])
    photos.append(img_bytes)
    logger.debug("pending_photos count: %d", len(photos))

    await update.message.reply_text("Стикер получен. Обработка...")
    logger.info("Sending image to ChatGPT for recognition")
    result = await ask_chatgpt(img_bytes)
    logger.info("ChatGPT response: %s", result)

    await update.message.reply_text(result)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info("User %s started the bot", user_id)
    await update.message.reply_text("👋 Отправьте стикер")
