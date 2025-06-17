import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from aggregation import aggregate_results
from menu_parser import parse_menu
from models import BotState, Poll

logger = logging.getLogger(__name__)
state = BotState()

MENU_KB = ReplyKeyboardMarkup([['Присоединиться', 'Узнать результат']], resize_keyboard=True)


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
    try:
        await query.edit_message_reply_markup(None)
    except BadRequest:

        pass
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
    # Главное меню бота
    await update.message.reply_text(
        "👋 Отправьте фото меню (можно несколько).\n"
        "Когда всё готово — нажмите «Готово».\n\n"
        "🗳 «Присоединиться» — вступить в голосование\n"
        "📊 «Узнать результат» — посмотреть итоги",
        reply_markup=MENU_KB
    )


async def join_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        chat = update.callback_query.message
    else:
        chat = update.message
        context.user_data["awaiting_join"] = True
        await chat.reply_text("Введите номер голосования")


async def handle_join_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем номер опроса текстом
    if not context.user_data.get("awaiting_join"):
        return

    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Неверный ввод. Пожалуйста, введите число.")
        return

    poll_id = int(text)
    context.user_data.pop("awaiting_join", None)
    # перенаправляем в старую логику join, эмулируя args
    context.args = [text]
    await join(update, context)


async def result_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # ищем последний опрос, в котором участвует пользователь
    poll_id = next(
        (pid for pid in sorted(state.polls.keys(), reverse=True)
         if user_id in state.polls[pid].participants),
        None
    )
    if not poll_id:
        await update.message.reply_text("Вы не участвуете ни в одном опросе.", reply_markup=MENU_KB)
        return
    poll = state.polls[poll_id]
    # 1) сортируем меню по сумме голосов (от большего к меньшему)
    sorted_items = sorted(
        poll.menu,
        key=lambda it: sum(poll.votes.get(it.id, {}).values()),
        reverse=True
    )
    # 2) нумеруем уже в порядке ранжирования
    lines = [f"Результаты опроса #{poll_id}:"] + [
        f"{idx + 1}. {item.name} — {sum(poll.votes.get(item.id, {}).values())}"
        for idx, item in enumerate(sorted_items)
    ]
    await update.message.reply_text("\n".join(lines), reply_markup=MENU_KB)
