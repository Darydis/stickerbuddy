import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

import handlers


def main() -> None:
    load_dotenv()
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise RuntimeError('BOT_TOKEN not set')
    logging.basicConfig(level=logging.INFO)

    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler('start', handlers.start))
    app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    app.add_handler(CommandHandler('join', handlers.join))
    app.add_handler(CommandHandler('result', handlers.result))
    app.add_handler(CallbackQueryHandler(handlers.button))
    app.run_polling()


if __name__ == '__main__':
    main()
