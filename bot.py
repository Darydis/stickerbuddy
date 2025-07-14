# bot.py
# python-telegram-bot ≥ 21  •  Python ≥ 3.11
import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters,
)
from telegram.ext.filters import MessageFilter

import handlers          # async-функции start() и handle_sticker()


# ---------- фильтр «reply на стикер» ----------
class ReplyToStickerFilter(MessageFilter):
    def filter(self, msg) -> bool:
        return msg.reply_to_message and msg.reply_to_message.sticker


# ---------- вспом. корутины ----------
async def get_bot_username(token: str) -> str:
    """Однократный вызов /getMe перед запуском бота."""
    bot = Bot(token)
    return (await bot.get_me()).username


async def drop_webhook(token: str) -> None:
    """Гарантированно сбрасываем старый веб-хук."""
    bot = Bot(token)
    await bot.delete_webhook(drop_pending_updates=True)


# ---------- точка входа ----------
def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN env var is not set")

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s"
    )

    # --- создаём и назначаем свой event-loop ----------------------
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # --- выполняем асинхронную подготовку ------------------------
    bot_username = loop.run_until_complete(get_bot_username(token))
    loop.run_until_complete(drop_webhook(token))
    logging.info("Bot username: %s", bot_username)

    # --- собираем Application ------------------------------------
    app = Application.builder().token(token).build()

    # фильтры
    private_sticker = filters.ChatType.PRIVATE & filters.Sticker.ALL
    reply_sticker   = filters.ChatType.GROUP & filters.REPLY & ReplyToStickerFilter()
    mention         = filters.ChatType.GROUP & filters.Regex(fr"@{bot_username}\b")
    sticker_or_ment = private_sticker | reply_sticker | mention

    # хэндлеры
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(sticker_or_ment, handlers.handle_sticker))

    # --- запуск (использует уже созданный loop) ------------------
    app.run_polling()


if __name__ == "__main__":
    main()
