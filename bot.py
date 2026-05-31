import asyncio
import asyncio
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = "8972127511:AAEjvKfNUX5XiM72edNA1XnbkjummStkv14"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ASK_NAME, ASK_GOAL = range(2)

MORNING_PRACTICES = [
    "🌿 Прогулка без наушников помогает мозгу восстанавливаться от информационного шума. Попробуй сегодня — хотя бы 10 минут тишины на свежем воздухе.",
    "🌿 Начни день с одного стакана тёплой воды — до кофе. Это запускает пищеварение и помогает мягко войти в день.",
    "🌿 Перед тем как открыть телефон — сделай 3 глубоких вдоха. Просто три вдоха. Это уже практика.",
    "🌿 Запиши одно намерение на сегодня. Не список задач — одно намерение. Как ты хочешь себя чувствовать?",
    "🌿 Посмотри в окно 2 минуты. Без телефона, без мыслей о делах. Просто наблюдай.",
]

MORNING_QUOTES = [
    "✦ «Тишина — не отсутствие звука, а присутствие себя.»",
    "✦ «Медленно — не значит плохо. Медленно — значит внимательно.»",
    "✦ «Каждое утро — это шанс начать с чистого листа.»",
    "✦ «Забота о себе — это не эгоизм. Это необходимость.»",
    "✦ «Маленькие шаги каждый день приводят к большим переменам.»",
]

DAILY_INTELLIGENCE = [
    {"title": "Архитектура тишины", "body": "Минималистичные пространства снижают когнитивную нагрузку — мозг тратит меньше ресурсов на фильтрацию визуального шума. Это не эстетика, это физиология."},
    {"title": "Почему мы устаём от выбора", "body": "Каждый день мы принимаем тысячи решений. Усталость от выбора — реальный феномен. Упрощай рутину, чтобы сохранить энергию для важного."},
    {"title": "Сила маленьких ритуалов", "body": "Ритуалы создают предсказуемость, а предсказуемость снижает тревогу. Даже простая чашка чая в одно время каждый день — это якорь для нервной системы."},
    {"title": "Природа и восстановление", "body": "20 минут на природе снижают уровень кортизола на 21%. Не нужен лес — достаточно парка или даже вида на деревья из окна."},
    {"title": "Цифровой детокс", "body": "Первые 30 минут после пробуждения без телефона улучшают концентрацию в течение всего дня. Мозг успевает настроиться на собственный ритм."},
]

CULTURE_NOTES = [
    {"title": "Wabi-sabi", "body": "Японская эстетика несовершенства учит ценить простоту, незавершённость и быстротечность. Трещина в чашке — не изъян, а история."},
    {"title": "Hygge", "body": "Датская концепция уюта — это не о вещах, а об атмосфере. Свечи, тёплый плед, близкие люди и ощущение безопасности."},
    {"title": "Lagom", "body": "Шведский принцип «ровно столько, сколько нужно». Не слишком много, не слишком мало — идеальный баланс во всём."},
    {"title": "Niksen", "body": "Голландское искусство ничегонеделания. Просто сидеть, смотреть в окно, позволить мыслям блуждать — это не лень, это практика."},
    {"title": "Forest bathing", "body": "Японская практика shinrin-yoku — купание в лесной атмосфере. Не спорт, не медитация — просто медленная прогулка и присутствие в природе."},
]

SOFT_SUGGESTIONS = [
    "🌸 Попробуй 5 минут диафрагмального дыхания — вдох 4 секунды, задержка 4, выдох 6. Это снижает кортизол и помогает войти в вечер спокойно.",
    "🌸 Напиши одному человеку, которого давно не видела. Просто «привет, думала о тебе».",
    "🌸 Сделай что-то приятное для себя без причины — любимый чай, свеча, музыка которую любишь.",
    "🌸 Убери один лишний предмет со своего рабочего стола. Пространство влияет на мысли.",
    "🌸 Проведи следующий час без фоновых звуков — без подкастов, музыки, сериала. Просто тишина.",
]

EVENING_MEDITATIONS = [
    "🌙 Закрой глаза. Сделай три глубоких вдоха. Почувствуй как тело расслабляется с каждым выдохом. Этот день завершён — ты сделала всё что могла.",
    "🌙 Представь как всё напряжение дня растворяется с каждым выдохом. Твоё тело тяжелеет, мысли замедляются. Ты в безопасности.",
    "🌙 Вспомни один момент сегодня, когда тебе было хорошо. Удержи это ощущение. Пусть оно будет последним перед сном.",
]

def get_user_name(context):
    return context.user_data.get('name', 'друг')

def get_time_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"

def get_daily_item(items):
    day = datetime.now().timetuple().tm_yday
    return items[day % len(items)]

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("☀️  Morning Flow", callback_data="morning")],
        [InlineKeyboardButton("✦   Daily Intelligence", callback_data="daily")],
        [InlineKeyboardButton("📖  Culture Note", callback_data="culture")],
        [InlineKeyboardButton("🌸  Soft Suggestion", callback_data="soft")],
        [InlineKeyboardButton("🌙  Evening Reset", callback_data="evening")],
        [InlineKeyboardButton("⚙️  Настройки", callback_data="settings")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет, я Slow Glow ✦\n\n"
        "Твой интеллектуальный Telegram-бот, который помогает замедлиться, "
        "принимать осознанные решения и жить в гармонии с собой и миром.\n\n"
        "Как тебя зовут? 🌿"
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data['name'] = name
    await update.message.reply_text(
        f"Рада знакомству, {name} ✦\n\nЧто тебя привело сюда?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌅 Хочу лучше начинать день", callback_data="goal_morning")],
            [InlineKeyboardButton("✦ Ищу умный контент без шума", callback_data="goal_intel")],
            [InlineKeyboardButton("🌙 Хочу лучше завершать день", callback_data="goal_evening")],
            [InlineKeyboardButton("🌸 Просто хочу больше радости", callback_data="goal_soft")],
        ])
    )
    return ASK_GOAL

async def ask_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = get_user_name(context)
    await query.edit_message_text(
        f"Отлично, {name} 🌿\n\n"
        f"Каждый день буду присылать тебе что-то полезное и тёплое.\n\n"
        f"take it slow. let it glow. ✦"
    )
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"{get_time_greeting()}, {name} ✦\n\nВыбери с чего начнём:",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = get_user_name(context)
    text = f"{get_time_greeting()}, {name} ✦\n\nПусть этот день будет спокойным и наполненным смыслом."
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard())

async def morning_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    practice = get_daily_item(MORNING_PRACTICES)
    quote = get_daily_item(MORNING_QUOTES)
    await query.edit_message_text(
        f"☀️ *Morning Flow*\n\n*Практика дня*\n\n{practice}\n\n_{quote}_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✓ Попробую сегодня", callback_data="morning_done"),
             InlineKeyboardButton("→ Следующее", callback_data="morning_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def morning_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Отлично! 🌿")
    name = get_user_name(context)
    await query.edit_message_text(
        f"Замечательно, {name} 🌿\n\n_take it slow. let it glow. ✦_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩ В меню", callback_data="menu")]])
    )

async def morning_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('morning_idx', 0) + 1
    context.user_data['morning_idx'] = idx
    practice = MORNING_PRACTICES[idx % len(MORNING_PRACTICES)]
    quote = MORNING_QUOTES[idx % len(MORNING_QUOTES)]
    await query.edit_message_text(
        f"☀️ *Morning Flow*\n\n{practice}\n\n_{quote}_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✓ Попробую сегодня", callback_data="morning_done"),
             InlineKeyboardButton("→ Следующее", callback_data="morning_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def daily_intelligence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item = get_daily_item(DAILY_INTELLIGENCE)
    culture = get_daily_item(CULTURE_NOTES)
    await query.edit_message_text(
        f"✦ *Daily Intelligence*\n\n*{item['title']}*\n\n{item['body']}\n\n"
        f"━━━━━━━━━━\n\n📖 *Culture Note*\n\n*{culture['title']}*\n\n{culture['body']}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ Сохранить", callback_data="daily_save"),
             InlineKeyboardButton("→ Ещё", callback_data="daily_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def daily_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Сохранено ❤️")

async def daily_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('daily_idx', 0) + 1
    context.user_data['daily_idx'] = idx
    item = DAILY_INTELLIGENCE[idx % len(DAILY_INTELLIGENCE)]
    await query.edit_message_text(
        f"✦ *Daily Intelligence*\n\n*{item['title']}*\n\n{item['body']}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ Сохранить", callback_data="daily_save"),
             InlineKeyboardButton("→ Ещё", callback_data="daily_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def culture_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item = get_daily_item(CULTURE_NOTES)
    await query.edit_message_text(
        f"📖 *Culture Note*\n\n*{item['title']}*\n\n{item['body']}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ Сохранить", callback_data="culture_save"),
             InlineKeyboardButton("→ Ещё", callback_data="culture_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def culture_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Сохранено ❤️")

async def culture_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('culture_idx', 0) + 1
    context.user_data['culture_idx'] = idx
    item = CULTURE_NOTES[idx % len(CULTURE_NOTES)]
    await query.edit_message_text(
        f"📖 *Culture Note*\n\n*{item['title']}*\n\n{item['body']}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ Сохранить", callback_data="culture_save"),
             InlineKeyboardButton("→ Ещё", callback_data="culture_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def soft_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    suggestion = get_daily_item(SOFT_SUGGESTIONS)
    await query.edit_message_text(
        f"🌸 *Soft Suggestion*\n\n_Небольшая идея для тебя_\n\n{suggestion}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✓ Сделаю", callback_data="soft_done"),
             InlineKeyboardButton("↻ Другое", callback_data="soft_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def soft_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Здорово! 🌸")
    name = get_user_name(context)
    await query.edit_message_text(
        f"Ты замечательная, {name} 🌸\n\n_take it slow. let it glow. ✦_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩ В меню", callback_data="menu")]])
    )

async def soft_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('soft_idx', 0) + 1
    context.user_data['soft_idx'] = idx
    suggestion = SOFT_SUGGESTIONS[idx % len(SOFT_SUGGESTIONS)]
    await query.edit_message_text(
        f"🌸 *Soft Suggestion*\n\n{suggestion}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✓ Сделаю", callback_data="soft_done"),
             InlineKeyboardButton("↻ Другое", callback_data="soft_next")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def evening_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = get_user_name(context)
    await query.edit_message_text(
        f"🌙 *Evening Reset*\n\nКак прошёл твой день, {name}?\nВремя замедлиться и отпустить.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("😌 Спокойно", callback_data="eve_calm"),
             InlineKeyboardButton("😔 Устала", callback_data="eve_tired")],
            [InlineKeyboardButton("😤 Напряжённо", callback_data="eve_tense"),
             InlineKeyboardButton("🤍 Нейтрально", callback_data="eve_neutral")],
        ])
    )

async def evening_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    responses = {
        "eve_calm": "Как хорошо 😌\n\nСохрани это ощущение спокойствия — оно твоё.",
        "eve_tired": "Ты сегодня много сделала 🌿\n\nТвоя усталость — это след от усилий. Пора отдыхать.",
        "eve_tense": "Напряжение — это сигнал тела 🌙\n\nПозволь себе выдохнуть. Завтра будет легче.",
        "eve_neutral": "Нейтрально — это тоже хорошо 🤍\n\nНе каждый день должен быть ярким.",
    }
    text = responses.get(query.data, "Спасибо что поделилась 🌿")
    await query.edit_message_text(
        f"🌙 *Evening Reset*\n\n{text}\n\n*Три вещи, за которые ты благодарна сегодня* 🌿\n\nНапиши их в ответ — просто списком или мыслями вслух.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🕯️ Медитация сна", callback_data="eve_meditation")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def evening_meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = get_user_name(context)
    meditation = get_daily_item(EVENING_MEDITATIONS)
    await query.edit_message_text(
        f"🕯️ *Медитация сна*\n\n{meditation}\n\n_Спокойной ночи, {name} ✦_\n\n_take it slow. let it glow._",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩ В меню", callback_data="menu")]])
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = get_user_name(context)
    await query.edit_message_text(
        f"⚙️ *Настройки*\n\nИмя: {name}\n\nРассылки:\n☀️ Утро — 08:00\n✦ День — 12:00\n🌙 Вечер — 21:00",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Изменить имя", callback_data="change_name")],
            [InlineKeyboardButton("↩ В меню", callback_data="menu")],
        ])
    )

async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Как тебя теперь называть? 🌿")
    context.user_data['changing_name'] = True

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('changing_name'):
        name = update.message.text.strip()
        context.user_data['name'] = name
        context.user_data['changing_name'] = False
        await update.message.reply_text(
            f"Отлично, теперь буду называть тебя {name} 🌿",
            reply_markup=main_menu_keyboard()
        )
    else:
        name = get_user_name(context)
        await update.message.reply_text(
            f"{get_time_greeting()}, {name} ✦\n\nВыбери раздел:",
            reply_markup=main_menu_keyboard()
        )

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_GOAL: [CallbackQueryHandler(ask_goal, pattern='^goal_')],
        },
        fallbacks=[CommandHandler('menu', menu)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler('menu', menu))
    app.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(morning_flow, pattern='^morning$'))
    app.add_handler(CallbackQueryHandler(morning_done, pattern='^morning_done$'))
    app.add_handler(CallbackQueryHandler(morning_next, pattern='^morning_next$'))
    app.add_handler(CallbackQueryHandler(daily_intelligence, pattern='^daily$'))
    app.add_handler(CallbackQueryHandler(daily_save, pattern='^daily_save$'))
    app.add_handler(CallbackQueryHandler(daily_next, pattern='^daily_next$'))
    app.add_handler(CallbackQueryHandler(culture_note, pattern='^culture$'))
    app.add_handler(CallbackQueryHandler(culture_save, pattern='^culture_save$'))
    app.add_handler(CallbackQueryHandler(culture_next, pattern='^culture_next$'))
    app.add_handler(CallbackQueryHandler(soft_suggestion, pattern='^soft$'))
    app.add_handler(CallbackQueryHandler(soft_done, pattern='^soft_done$'))
    app.add_handler(CallbackQueryHandler(soft_next, pattern='^soft_next$'))
    app.add_handler(CallbackQueryHandler(evening_reset, pattern='^evening$'))
    app.add_handler(CallbackQueryHandler(evening_mood, pattern='^eve_(calm|tired|tense|neutral)$'))
    app.add_handler(CallbackQueryHandler(evening_meditation, pattern='^eve_meditation$'))
    app.add_handler(CallbackQueryHandler(settings, pattern='^settings$'))
    app.add_handler(CallbackQueryHandler(change_name, pattern='^change_name$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🌿 Slow Glow Bot запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
