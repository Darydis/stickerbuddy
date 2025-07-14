import logging
from telegram import Update
from telegram.ext import ContextTypes
from openai_client import ask_chatgpt

logger = logging.getLogger(__name__)


async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message          # удобная краткая ссылка

    # ---------- ищем стикер в сообщении или в реплае ----------
    sticker = msg.sticker
    if sticker is None and msg.reply_to_message:
        sticker = msg.reply_to_message.sticker

    if sticker is None:                     # пришёл текст / фото / что-то ещё
        await msg.reply_text("Где стикер? 🙂")
        return

    logger.info("Chat type: %s  |  user %s sent a sticker",
                msg.chat.type, update.effective_user.id)
    logger.debug("Sticker file_id: %s", sticker.file_id)

    # ---------- скачиваем изображение ----------
    file = await context.bot.get_file(sticker.file_id)
    img_bytes = await file.download_as_bytearray()
    logger.info("Downloaded %d bytes", len(img_bytes))

    # ---------- сохраняем «в ожидании» (если нужно) ----------
    context.user_data.setdefault("pending_photos", []).append(img_bytes)

    await msg.reply_text("Стикер получен, думаю...")

    # ---------- отправляем на распознавание ----------
    try:
        result = await ask_chatgpt(img_bytes)
    except Exception as exc:
        logger.exception("ask_chatgpt failed: %s", exc)
        await msg.reply_text("Не смог распознать 🤷‍♀️")
        return

    await msg.reply_text(result)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User %s started the bot", update.effective_user.id)
    await update.message.reply_text("👋 Отправьте стикер или ответьте на стикер, упомянув меня.")
