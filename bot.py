# bot.py
import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters
)
from telegram.ext.filters import MessageFilter

import handlers

# ---------- кастомный фильтр «reply на стикер» ----------
class ReplyToStickerFilter(MessageFilter):
    def filter(self, message) -> bool:            # message: telegram.Message
        return (
            message.reply_to_message
            and message.reply_to_message.sticker is not None
        )

# --------------------------- MAIN ---------------------------
async def main() -> None:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN not set")

    logging.basicConfig(level=logging.INFO)

    # --- Application ---
    app = Application.builder().token(bot_token).build()

    # узнаём своё имя (@ убираем)
    me = await app.bot.get_me()
    bot_username = me.username           # str, без '@'
    logging.info("Bot username: %s", bot_username)

    # --- фильтры ---
    private_sticker   = filters.ChatType.PRIVATE & filters.Sticker.ALL
    reply_to_sticker  = filters.REPLY & ReplyToStickerFilter()
    mention           = filters.Regex(fr"@{bot_username}\b")

    sticker_or_mention = private_sticker | reply_to_sticker | mention

    # --- хэндлеры ---
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(sticker_or_mention, handlers.handle_sticker))

    # --- запуск ---
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logging.info("Bot started. Waiting for updates...")
    await app.updater.idle()             # держим процесс живым

# -----------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
