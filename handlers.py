import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from aggregation import aggregate_results
from menu_parser import parse_menu
from models import BotState, Poll

logger = logging.getLogger(__name__)
state = BotState()


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Получаем файл и URL/bytes
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()

    photos = context.user_data.setdefault("pending_photos", [])
    photos.append(img_bytes)
    count = len(photos)

    await update.message.reply_text(
        f"Фото #{count} получено. Отправьте ещё или нажмите «Готово» ниже.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Готово", callback_data="done")]]
        ),
    )


async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    photos = context.user_data.pop("pending_photos", None)
    if not photos:
        await query.message.reply_text(
            "Нет загруженных фото. Сначала отправьте изображения меню."
        )
        return

    all_items = []
    for img in photos:
        try:
            items = await parse_menu(img)
            all_items.extend(items)
        except Exception as e:
            logger.exception("Ошибка при parse_menu:")
            await query.message.reply_text(f"Не удалось распознать одно фото: {e}")
            return

    # перенумеруем пункты
    for idx, item in enumerate(all_items, start=1):
        item.id = idx

    # создаём опрос
    poll_id = state.next_poll_id
    state.next_poll_id += 1
    poll = Poll(id=poll_id, menu=all_items)
    state.polls[poll_id] = poll

    # автоматически добавляем инициатора в участники и сразу начинаем голосование
    user_id = query.from_user.id
    poll.participants.add(user_id)
    context.user_data["poll_id"] = poll_id
    context.user_data["index"] = 0
    context.user_data["ratings"] = {}

    # показываем меню и первый вопрос
    lines = [f"{p.id}. {p.name}" for p in all_items]
    await query.message.reply_text(
        "Меню распознано, голосование началось.\n" +
        "\n".join(lines) +
        f"\n\nСоздано голосование номер #{poll_id}. Оцените пиццы от 1 до 5:"
    )
    await _send_next(update, context)


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /join <id>")
        return
    try:
        poll_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный id")
        return
    poll = state.polls.get(poll_id)
    if not poll:
        await update.message.reply_text("Голосование не найдено")
        return
    poll.participants.add(update.effective_chat.id)
    context.user_data["poll_id"] = poll_id
    context.user_data["index"] = 0
    context.user_data["ratings"] = {}
    await update.message.reply_text(
        f"Голосование {poll_id}. Оцените пиццы от 1 до 5"
    )
    await _send_next(update, context)


async def _send_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_id = context.user_data.get("poll_id")
    index = context.user_data.get("index", 0)
    poll = state.polls.get(poll_id)
    if not poll:
        return
    if index >= len(poll.menu):
        user_id = update.effective_user.id
        for pid, rating in context.user_data.get("ratings", {}).items():
            poll.votes.setdefault(pid, {})[user_id] = rating
        await update.effective_message.reply_text("Спасибо, ваш голос учтён")
        context.user_data.clear()
        return
    pizza = poll.menu[index]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(str(i), callback_data=f"rate:{i}") for i in range(1, 6)]
    ])
    await update.effective_message.reply_text(
        f"{pizza.id}. {pizza.name}", reply_markup=keyboard
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith("rate:"):
        return
    score = int(data.split(":", 1)[1])
    poll_id = context.user_data.get("poll_id")
    index = context.user_data.get("index", 0)
    poll = state.polls.get(poll_id)
    if not poll:
        await query.edit_message_reply_markup(None)
        return
    if index >= len(poll.menu):
        return
    pizza = poll.menu[index]
    context.user_data.setdefault("ratings", {})[pizza.id] = score
    context.user_data["index"] = index + 1
    await query.edit_message_reply_markup(None)
    await _send_next(update, context)


async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Использование: /result <id> <K>")
        return
    try:
        poll_id = int(context.args[0])
        k = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Неверные параметры")
        return
    poll = state.polls.get(poll_id)
    if not poll:
        await update.message.reply_text("Голосование не найдено")
        return
    summary = aggregate_results(poll, k)
    for chat_id in poll.participants:
        await context.bot.send_message(chat_id=chat_id, text=summary)
    if update.effective_chat.id not in poll.participants:
        await update.message.reply_text(summary)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправьте изображение меню для создания голосования. "
        "Вы можете отправить несколько снимков по очереди. "
        "Когда всё готово — нажмите кнопку «Готово»."
    )
