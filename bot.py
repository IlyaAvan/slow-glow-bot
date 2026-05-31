import os
import asyncio
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8972127511:AAEjvKfNUX5XiM72edNA1XnbkjummStkv14"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

MORNING_PRACTICES = [
    "🌿 Прогулка без наушников помогает мозгу восстанавливаться от информационного шума. Попробуй сегодня — хотя бы 10 минут тишины.",
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
    {"title": "Природа и восстановление", "body": "20 минут на природе снижают уровень кортизола на 21%. Не нужен лес — достаточно парка или вида на деревья из окна."},
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
    "🌸 Попробуй 5 минут диафрагмального дыхания — вдох 4 секунды, задержка 4, выдох 6.",
    "🌸 Напиши одному человеку, которого давно не видела. Просто «привет, думала о тебе».",
    "🌸 Сделай что-то приятное для себя без причины — любимый чай, свеча, музыка которую любишь.",
    "🌸 Убери один лишний предмет со своего рабочего стола. Пространство влияет на мысли.",
    "🌸 Проведи следующий час без фоновых звуков. Просто тишина.",
]
EVENING_MEDITATIONS = [
    "🌙 Закрой глаза. Сделай три глубоких вдоха. Этот день завершён — ты сделала всё что могла.",
    "🌙 Представь как всё напряжение дня растворяется с каждым выдохом. Ты в безопасности.",
    "🌙 Вспомни один момент сегодня, когда тебе было хорошо. Пусть оно будет последним перед сном.",
]

class Form(StatesGroup):
    waiting_name = State()
    waiting_goal = State()
    changing_name = State()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

def get_daily(items):
    return items[datetime.now().timetuple().tm_yday % len(items)]

def get_greeting():
    h = datetime.now().hour
    if 5 <= h < 12: return "Доброе утро"
    elif 12 <= h < 17: return "Добрый день"
    elif 17 <= h < 22: return "Добрый вечер"
    return "Доброй ночи"

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="☀️  Morning Flow", callback_data="morning")
    kb.button(text="✦   Daily Intelligence", callback_data="daily")
    kb.button(text="📖  Culture Note", callback_data="culture")
    kb.button(text="🌸  Soft Suggestion", callback_data="soft")
    kb.button(text="🌙  Evening Reset", callback_data="evening")
    kb.button(text="⚙️  Настройки", callback_data="settings")
    kb.adjust(1)
    return kb.as_markup()

def back_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="↩ В меню", callback_data="menu")
    return kb.as_markup()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_name)
    await message.answer("Привет, я Slow Glow ✦\n\nТвой интеллектуальный Telegram-бот, который помогает замедлиться и жить в гармонии с собой и миром.\n\nКак тебя зовут? 🌿")

@dp.message(StateFilter(Form.waiting_name))
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(Form.waiting_goal)
    kb = InlineKeyboardBuilder()
    kb.button(text="🌅 Хочу лучше начинать день", callback_data="goal_morning")
    kb.button(text="✦ Ищу умный контент без шума", callback_data="goal_intel")
    kb.button(text="🌙 Хочу лучше завершать день", callback_data="goal_evening")
    kb.button(text="🌸 Просто хочу больше радости", callback_data="goal_soft")
    kb.adjust(1)
    await message.answer(f"Рада знакомству, {name} ✦\n\nЧто тебя привело сюда?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("goal_"), StateFilter(Form.waiting_goal))
async def process_goal(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    name = data.get("name", "друг")
    await callback.message.edit_text(f"Отлично, {name} 🌿\n\nКаждый день буду присылать тебе что-то полезное и тёплое.\n\ntake it slow. let it glow. ✦")
    await callback.message.answer(f"{get_greeting()}, {name} ✦\n\nВыбери с чего начнём:", reply_markup=main_menu())
    await callback.answer()

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "друг")
    await message.answer(f"{get_greeting()}, {name} ✦\n\nПусть этот день будет спокойным и наполненным смыслом.", reply_markup=main_menu())

@dp.callback_query(F.data == "menu")
async def cb_menu(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "друг")
    await callback.message.edit_text(f"{get_greeting()}, {name} ✦\n\nПусть этот день будет спокойным и наполненным смыслом.", reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "morning")
async def cb_morning(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="✓ Попробую", callback_data="morning_done")
    kb.button(text="→ Ещё", callback_data="morning_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"☀️ *Morning Flow*\n\n{get_daily(MORNING_PRACTICES)}\n\n_{get_daily(MORNING_QUOTES)}_", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "morning_done")
async def cb_morning_done(callback: types.CallbackQuery):
    await callback.message.edit_text("Замечательно 🌿\n\n_take it slow\\. let it glow\\. ✦_", parse_mode="MarkdownV2", reply_markup=back_menu())
    await callback.answer("Отлично! 🌿")

@dp.callback_query(F.data == "morning_next")
async def cb_morning_next(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data.get("mi", 0) + 1
    await state.update_data(mi=idx)
    kb = InlineKeyboardBuilder()
    kb.button(text="✓ Попробую", callback_data="morning_done")
    kb.button(text="→ Ещё", callback_data="morning_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"☀️ *Morning Flow*\n\n{MORNING_PRACTICES[idx % len(MORNING_PRACTICES)]}\n\n_{MORNING_QUOTES[idx % len(MORNING_QUOTES)]}_", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "daily")
async def cb_daily(callback: types.CallbackQuery):
    item = get_daily(DAILY_INTELLIGENCE)
    cult = get_daily(CULTURE_NOTES)
    kb = InlineKeyboardBuilder()
    kb.button(text="❤️ Сохранить", callback_data="save")
    kb.button(text="→ Ещё", callback_data="daily_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"✦ *Daily Intelligence*\n\n*{item['title']}*\n\n{item['body']}\n\n━━━━━━━━━━\n\n📖 *{cult['title']}*\n\n{cult['body']}", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "daily_next")
async def cb_daily_next(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data.get("di", 0) + 1
    await state.update_data(di=idx)
    item = DAILY_INTELLIGENCE[idx % len(DAILY_INTELLIGENCE)]
    kb = InlineKeyboardBuilder()
    kb.button(text="❤️ Сохранить", callback_data="save")
    kb.button(text="→ Ещё", callback_data="daily_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"✦ *Daily Intelligence*\n\n*{item['title']}*\n\n{item['body']}", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "culture")
async def cb_culture(callback: types.CallbackQuery):
    item = get_daily(CULTURE_NOTES)
    kb = InlineKeyboardBuilder()
    kb.button(text="❤️ Сохранить", callback_data="save")
    kb.button(text="→ Ещё", callback_data="culture_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"📖 *Culture Note*\n\n*{item['title']}*\n\n{item['body']}", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "culture_next")
async def cb_culture_next(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data.get("ci", 0) + 1
    await state.update_data(ci=idx)
    item = CULTURE_NOTES[idx % len(CULTURE_NOTES)]
    kb = InlineKeyboardBuilder()
    kb.button(text="❤️ Сохранить", callback_data="save")
    kb.button(text="→ Ещё", callback_data="culture_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"📖 *Culture Note*\n\n*{item['title']}*\n\n{item['body']}", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "save")
async def cb_save(callback: types.CallbackQuery):
    await callback.answer("Сохранено ❤️")

@dp.callback_query(F.data == "soft")
async def cb_soft(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="✓ Сделаю", callback_data="soft_done")
    kb.button(text="↻ Другое", callback_data="soft_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"🌸 *Soft Suggestion*\n\n{get_daily(SOFT_SUGGESTIONS)}", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "soft_done")
async def cb_soft_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "друг")
    await callback.message.edit_text(f"Ты замечательная, {name} 🌸\n\n_take it slow\\. let it glow\\. ✦_", parse_mode="MarkdownV2", reply_markup=back_menu())
    await callback.answer("Здорово! 🌸")

@dp.callback_query(F.data == "soft_next")
async def cb_soft_next(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data.get("si", 0) + 1
    await state.update_data(si=idx)
    kb = InlineKeyboardBuilder()
    kb.button(text="✓ Сделаю", callback_data="soft_done")
    kb.button(text="↻ Другое", callback_data="soft_next")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(2, 1)
    await callback.message.edit_text(f"🌸 *Soft Suggestion*\n\n{SOFT_SUGGESTIONS[idx % len(SOFT_SUGGESTIONS)]}", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "evening")
async def cb_evening(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "друг")
    kb = InlineKeyboardBuilder()
    kb.button(text="😌 Спокойно", callback_data="eve_calm")
    kb.button(text="😔 Устала", callback_data="eve_tired")
    kb.button(text="😤 Напряжённо", callback_data="eve_tense")
    kb.button(text="🤍 Нейтрально", callback_data="eve_neutral")
    kb.adjust(2)
    await callback.message.edit_text(f"🌙 *Evening Reset*\n\nКак прошёл твой день, {name}?\nВремя замедлиться и отпустить.", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("eve_") & ~F.data.contains("meditation"))
async def cb_evening_mood(callback: types.CallbackQuery):
    r = {
        "eve_calm": "Как хорошо 😌\n\nСохрани это ощущение спокойствия — оно твоё.",
        "eve_tired": "Ты сегодня много сделала 🌿\n\nТвоя усталость — это след от усилий. Пора отдыхать.",
        "eve_tense": "Напряжение — это сигнал тела 🌙\n\nПозволь себе выдохнуть. Завтра будет легче.",
        "eve_neutral": "Нейтрально — это тоже хорошо 🤍\n\nНе каждый день должен быть ярким.",
    }
    kb = InlineKeyboardBuilder()
    kb.button(text="🕯️ Медитация сна", callback_data="eve_meditation")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(1)
    await callback.message.edit_text(f"🌙 *Evening Reset*\n\n{r.get(callback.data, 'Спасибо 🌿')}\n\n*Три вещи, за которые ты благодарна сегодня* 🌿\n\nНапиши их в ответ.", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "eve_meditation")
async def cb_meditation(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "друг")
    await callback.message.edit_text(f"🕯️ *Медитация сна*\n\n{get_daily(EVENING_MEDITATIONS)}\n\n_Спокойной ночи, {name} ✦_\n\n_take it slow\\. let it glow\\._", parse_mode="MarkdownV2", reply_markup=back_menu())
    await callback.answer()

@dp.callback_query(F.data == "settings")
async def cb_settings(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "друг")
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Изменить имя", callback_data="change_name")
    kb.button(text="↩ В меню", callback_data="menu")
    kb.adjust(1)
    await callback.message.edit_text(f"⚙️ *Настройки*\n\nИмя: {name}", parse_mode="Markdown", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "change_name")
async def cb_change_name(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.changing_name)
    await callback.message.edit_text("Как тебя теперь называть? 🌿")
    await callback.answer()

@dp.message(StateFilter(Form.changing_name))
async def process_change_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(None)
    await message.answer(f"Отлично, теперь буду называть тебя {name} 🌿", reply_markup=main_menu())

@dp.message()
async def handle_any(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "друг")
    await message.answer(f"{get_greeting()}, {name} ✦\n\nВыбери раздел:", reply_markup=main_menu())

async def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    print("🌿 Slow Glow Bot запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
