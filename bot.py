import os
import json
import time
import threading
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

BOT_TOKEN = "8972127511:AAEjvKfNUX5XiM72edNA1XnbkjummStkv14"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

MORNING_PRACTICES = [
    "🌿 Прогулка без наушников помогает мозгу восстанавливаться. Попробуй сегодня — хотя бы 10 минут тишины.",
    "🌿 Начни день с одного стакана тёплой воды — до кофе.",
    "🌿 Перед тем как открыть телефон — сделай 3 глубоких вдоха.",
    "🌿 Запиши одно намерение на сегодня. Не список задач — одно намерение.",
    "🌿 Посмотри в окно 2 минуты. Без телефона, просто наблюдай.",
]
MORNING_QUOTES = [
    "✦ «Тишина — не отсутствие звука, а присутствие себя.»",
    "✦ «Медленно — не значит плохо. Медленно — значит внимательно.»",
    "✦ «Каждое утро — это шанс начать с чистого листа.»",
    "✦ «Забота о себе — это не эгоизм. Это необходимость.»",
    "✦ «Маленькие шаги каждый день приводят к большим переменам.»",
]
DAILY = [
    {"t": "Архитектура тишины", "b": "Минималистичные пространства снижают когнитивную нагрузку. Это не эстетика, это физиология."},
    {"t": "Почему мы устаём от выбора", "b": "Усталость от выбора — реальный феномен. Упрощай рутину, чтобы сохранить энергию для важного."},
    {"t": "Сила маленьких ритуалов", "b": "Ритуалы создают предсказуемость, а предсказуемость снижает тревогу."},
    {"t": "Природа и восстановление", "b": "20 минут на природе снижают уровень кортизола на 21%."},
    {"t": "Цифровой детокс", "b": "Первые 30 минут после пробуждения без телефона улучшают концентрацию в течение всего дня."},
]
CULTURE = [
    {"t": "Wabi-sabi", "b": "Японская эстетика несовершенства — ценить простоту и незавершённость."},
    {"t": "Hygge", "b": "Датская концепция уюта — свечи, тёплый плед, близкие люди."},
    {"t": "Lagom", "b": "Шведский принцип «ровно столько, сколько нужно»."},
    {"t": "Niksen", "b": "Голландское искусство ничегонеделания — это не лень, это практика."},
    {"t": "Forest bathing", "b": "Японская практика shinrin-yoku — медленная прогулка и присутствие в природе."},
]
SOFT = [
    "🌸 Попробуй 5 минут дыхания — вдох 4 сек, задержка 4, выдох 6.",
    "🌸 Напиши одному человеку, которого давно не видела.",
    "🌸 Сделай что-то приятное для себя без причины.",
    "🌸 Убери один лишний предмет со стола.",
    "🌸 Проведи следующий час без фоновых звуков.",
]
MEDITATIONS = [
    "🌙 Закрой глаза. Три глубоких вдоха. Этот день завершён.",
    "🌙 Представь как напряжение дня растворяется с каждым выдохом.",
    "🌙 Вспомни один момент сегодня, когда тебе было хорошо.",
]

user_data = {}

def get_daily(items):
    return items[datetime.now().timetuple().tm_yday % len(items)]

def greeting():
    h = datetime.now().hour
    if 5 <= h < 12: return "Доброе утро"
    elif 12 <= h < 17: return "Добрый день"
    elif 17 <= h < 22: return "Добрый вечер"
    return "Доброй ночи"

def api_call(method, data):
    try:
        req = Request(f"{API}/{method}", data=json.dumps(data).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        log.error(f"API error {method}: {e}")
        return None

def send(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        data["reply_markup"] = {"inline_keyboard": keyboard}
    return api_call("sendMessage", data)

def edit(chat_id, msg_id, text, keyboard=None):
    data = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        data["reply_markup"] = {"inline_keyboard": keyboard}
    return api_call("editMessageText", data)

def answer_cb(cb_id, text=""):
    api_call("answerCallbackQuery", {"callback_query_id": cb_id, "text": text})

def main_menu_kb():
    return [
        [{"text": "☀️  Morning Flow", "callback_data": "morning"}],
        [{"text": "✦   Daily Intelligence", "callback_data": "daily"}],
        [{"text": "📖  Culture Note", "callback_data": "culture"}],
        [{"text": "🌸  Soft Suggestion", "callback_data": "soft"}],
        [{"text": "🌙  Evening Reset", "callback_data": "evening"}],
        [{"text": "⚙️  Настройки", "callback_data": "settings"}],
    ]

def back_kb():
    return [[{"text": "↩ В меню", "callback_data": "menu"}]]

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    uid = str(chat_id)

    if uid not in user_data:
        user_data[uid] = {"state": None, "name": "друг", "mi": 0, "di": 0, "ci": 0, "si": 0}

    u = user_data[uid]

    if text == "/start":
        u["state"] = "waiting_name"
        send(chat_id, "Привет, я <b>Slow Glow</b> ✦\n\nТвой интеллектуальный Telegram-бот, который помогает замедлиться и жить в гармонии с собой и миром.\n\nКак тебя зовут? 🌿")
    elif u["state"] == "waiting_name":
        u["name"] = text.strip()
        u["state"] = None
        send(chat_id, f"Рада знакомству, {u['name']} ✦\n\nЧто тебя привело сюда?", [
            [{"text": "🌅 Хочу лучше начинать день", "callback_data": "goal_set"}],
            [{"text": "✦ Ищу умный контент без шума", "callback_data": "goal_set"}],
            [{"text": "🌙 Хочу лучше завершать день", "callback_data": "goal_set"}],
            [{"text": "🌸 Просто хочу больше радости", "callback_data": "goal_set"}],
        ])
    elif u["state"] == "changing_name":
        u["name"] = text.strip()
        u["state"] = None
        send(chat_id, f"Отлично, теперь буду называть тебя {u['name']} 🌿", main_menu_kb())
    elif text == "/menu":
        send(chat_id, f"{greeting()}, {u['name']} ✦\n\nВыбери раздел:", main_menu_kb())
    else:
        send(chat_id, f"{greeting()}, {u['name']} ✦\n\nВыбери раздел:", main_menu_kb())

def handle_callback(cb):
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    data = cb["data"]
    cb_id = cb["id"]
    uid = str(chat_id)
    answer_cb(cb_id)

    if uid not in user_data:
        user_data[uid] = {"state": None, "name": "друг", "mi": 0, "di": 0, "ci": 0, "si": 0}
    u = user_data[uid]

    if data == "goal_set":
        edit(chat_id, msg_id, f"Отлично, {u['name']} 🌿\n\nКаждый день буду присылать тебе что-то полезное и тёплое.\n\n<i>take it slow. let it glow. ✦</i>")
        send(chat_id, f"{greeting()}, {u['name']} ✦\n\nВыбери с чего начнём:", main_menu_kb())

    elif data == "menu":
        edit(chat_id, msg_id, f"{greeting()}, {u['name']} ✦\n\nПусть этот день будет спокойным и наполненным смыслом.", main_menu_kb())

    elif data == "morning":
        p = get_daily(MORNING_PRACTICES)
        q = get_daily(MORNING_QUOTES)
        edit(chat_id, msg_id, f"☀️ <b>Morning Flow</b>\n\n{p}\n\n<i>{q}</i>", [
            [{"text": "✓ Попробую", "callback_data": "morning_done"}, {"text": "→ Ещё", "callback_data": "morning_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "morning_done":
        edit(chat_id, msg_id, f"Замечательно, {u['name']} 🌿\n\n<i>take it slow. let it glow. ✦</i>", back_kb())

    elif data == "morning_next":
        u["mi"] += 1
        p = MORNING_PRACTICES[u["mi"] % len(MORNING_PRACTICES)]
        q = MORNING_QUOTES[u["mi"] % len(MORNING_QUOTES)]
        edit(chat_id, msg_id, f"☀️ <b>Morning Flow</b>\n\n{p}\n\n<i>{q}</i>", [
            [{"text": "✓ Попробую", "callback_data": "morning_done"}, {"text": "→ Ещё", "callback_data": "morning_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "daily":
        item = get_daily(DAILY)
        cult = get_daily(CULTURE)
        edit(chat_id, msg_id, f"✦ <b>Daily Intelligence</b>\n\n<b>{item['t']}</b>\n\n{item['b']}\n\n━━━━━━━━━━\n\n📖 <b>{cult['t']}</b>\n\n{cult['b']}", [
            [{"text": "❤️ Сохранить", "callback_data": "save"}, {"text": "→ Ещё", "callback_data": "daily_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "daily_next":
        u["di"] += 1
        item = DAILY[u["di"] % len(DAILY)]
        edit(chat_id, msg_id, f"✦ <b>Daily Intelligence</b>\n\n<b>{item['t']}</b>\n\n{item['b']}", [
            [{"text": "❤️ Сохранить", "callback_data": "save"}, {"text": "→ Ещё", "callback_data": "daily_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "culture":
        item = get_daily(CULTURE)
        edit(chat_id, msg_id, f"📖 <b>Culture Note</b>\n\n<b>{item['t']}</b>\n\n{item['b']}", [
            [{"text": "❤️ Сохранить", "callback_data": "save"}, {"text": "→ Ещё", "callback_data": "culture_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "culture_next":
        u["ci"] += 1
        item = CULTURE[u["ci"] % len(CULTURE)]
        edit(chat_id, msg_id, f"📖 <b>Culture Note</b>\n\n<b>{item['t']}</b>\n\n{item['b']}", [
            [{"text": "❤️ Сохранить", "callback_data": "save"}, {"text": "→ Ещё", "callback_data": "culture_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "save":
        answer_cb(cb_id, "Сохранено ❤️")

    elif data == "soft":
        edit(chat_id, msg_id, f"🌸 <b>Soft Suggestion</b>\n\n{get_daily(SOFT)}", [
            [{"text": "✓ Сделаю", "callback_data": "soft_done"}, {"text": "↻ Другое", "callback_data": "soft_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "soft_done":
        edit(chat_id, msg_id, f"Ты замечательная, {u['name']} 🌸\n\n<i>take it slow. let it glow. ✦</i>", back_kb())

    elif data == "soft_next":
        u["si"] += 1
        edit(chat_id, msg_id, f"🌸 <b>Soft Suggestion</b>\n\n{SOFT[u['si'] % len(SOFT)]}", [
            [{"text": "✓ Сделаю", "callback_data": "soft_done"}, {"text": "↻ Другое", "callback_data": "soft_next"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "evening":
        edit(chat_id, msg_id, f"🌙 <b>Evening Reset</b>\n\nКак прошёл твой день, {u['name']}?\nВремя замедлиться и отпустить.", [
            [{"text": "😌 Спокойно", "callback_data": "eve_calm"}, {"text": "😔 Устала", "callback_data": "eve_tired"}],
            [{"text": "😤 Напряжённо", "callback_data": "eve_tense"}, {"text": "🤍 Нейтрально", "callback_data": "eve_neutral"}],
        ])

    elif data in ["eve_calm", "eve_tired", "eve_tense", "eve_neutral"]:
        r = {
            "eve_calm": "Как хорошо 😌\n\nСохрани это ощущение спокойствия — оно твоё.",
            "eve_tired": "Ты сегодня много сделала 🌿\n\nПора отдыхать.",
            "eve_tense": "Позволь себе выдохнуть 🌙\n\nЗавтра будет легче.",
            "eve_neutral": "Нейтрально — это тоже хорошо 🤍",
        }
        edit(chat_id, msg_id, f"🌙 <b>Evening Reset</b>\n\n{r[data]}\n\n<b>Три вещи, за которые ты благодарна сегодня</b> 🌿\n\nНапиши их в ответ.", [
            [{"text": "🕯️ Медитация сна", "callback_data": "meditation"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "meditation":
        edit(chat_id, msg_id, f"🕯️ <b>Медитация сна</b>\n\n{get_daily(MEDITATIONS)}\n\n<i>Спокойной ночи, {u['name']} ✦</i>\n\n<i>take it slow. let it glow.</i>", back_kb())

    elif data == "settings":
        edit(chat_id, msg_id, f"⚙️ <b>Настройки</b>\n\nИмя: {u['name']}", [
            [{"text": "✏️ Изменить имя", "callback_data": "change_name"}],
            [{"text": "↩ В меню", "callback_data": "menu"}]
        ])

    elif data == "change_name":
        u["state"] = "changing_name"
        edit(chat_id, msg_id, "Как тебя теперь называть? 🌿")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_health():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

def main():
    threading.Thread(target=run_health, daemon=True).start()
    log.info("🌿 Slow Glow Bot запущен...")

    offset = 0
    while True:
        try:
            req = Request(f"{API}/getUpdates?offset={offset}&timeout=30")
            with urlopen(req, timeout=35) as r:
                updates = json.loads(r.read()).get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                if "message" in u:
                    handle_message(u["message"])
                elif "callback_query" in u:
                    handle_callback(u["callback_query"])
        except Exception as e:
            log.error(f"Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
