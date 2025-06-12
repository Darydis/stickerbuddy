import logging
from telegram import Update
from telegram.ext import ContextTypes

from .models import BotState
from .menu_parser import parse_menu
from .aggregation import aggregate_results

logger = logging.getLogger(__name__)
state = BotState()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Отправьте изображение меню для начала. После подтверждения участники смогут голосовать.\n'
        'Используйте /rate <id> <0-10> или /veto <id>. Команда /result <K> покажет результат.'
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    image_path = 'menu.jpg'
    await photo_file.download_to_drive(image_path)
    state.menu = parse_menu(image_path)
    state.votes = {}
    lines = [f"{p.id}. {p.name} ({p.price})" for p in state.menu]
    await update.message.reply_text('Меню распознано:\n' + '\n'.join(lines))


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text('Использование: /rate <id> <оценка 0-10>')
        return
    try:
        pid = int(context.args[0])
        score = int(context.args[1])
    except ValueError:
        await update.message.reply_text('Неверный формат.')
        return
    if score < 0 or score > 10:
        await update.message.reply_text('Оценка от 0 до 10.')
        return
    user_votes = state.votes.setdefault(pid, {})
    user_votes[update.effective_user.id] = score
    await update.message.reply_text('Оценка сохранена.')


async def veto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text('Использование: /veto <id>')
        return
    try:
        pid = int(context.args[0])
    except ValueError:
        await update.message.reply_text('Неверный формат.')
        return
    user_votes = state.votes.setdefault(pid, {})
    user_votes[update.effective_user.id] = 'veto'
    await update.message.reply_text('Вето учтено.')


async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text('Использование: /result <K>')
        return
    try:
        k = int(context.args[0])
    except ValueError:
        await update.message.reply_text('K должно быть числом.')
        return
    summary = aggregate_results(state, k)
    await update.message.reply_text(summary)
