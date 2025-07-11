import os
import logging
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters
)
from telegram.ext.filters import MessageFilter

import handlers

class ReplyToStickerFilter(MessageFilter):
    def filter(self, message) -> bool:
        return (
            message.reply_to_message
            and message.reply_to_message.sticker is not None
        )

def main() -> None:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN not set")

    logging.basicConfig(level=logging.INFO)

    # --- Telegram application ---
    app = Application.builder().token(bot_token).build()

    # узнаём username динамически
    me = app.bot.get_me()
    BOT_USERNAME = me.username  # без @

    private_sticker   = filters.ChatType.PRIVATE & filters.Sticker.ALL
    reply_to_sticker = filters.REPLY & ReplyToStickerFilter()
    mention = filters.Regex(fr"@{BOT_USERNAME}\b")

    sticker_or_mention = private_sticker | reply_to_sticker | mention


    # хэндлеры
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(sticker_or_mention, handlers.handle_sticker))

    app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
