import os
import json
import time
import threading
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError

BOT_TOKEN = "8972127511:AAEjvKfNUX5XiM72edNA1XnbkjummStkv14"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

MORNING_COMPASS = [
    {"title": "Сегодня не обязательно делать больше", "body": "Можно делать важнее.\n\nГде сегодня можно выбрать спокойствие вместо спешки?"},
    {"title": "Утро начинается с намерения", "body": "Не с телефона, не с новостей.\n\nС одного тихого вопроса: как я хочу себя чувствовать сегодня?"},
    {"title": "Маленькое действие меняет день", "body": "Не нужен подвиг.\n\nОдна чашка чая. Одна минута тишины. Один осознанный вдох."},
    {"title": "Ты уже достаточно", "body": "Напомни себе об этом прямо сейчас.\n\nЧто сегодня можно сделать с заботой о себе?"},
    {"title": "Медленно — это тоже движение", "body": "Иногда лучший выбор — замедлиться.\n\nЧто сегодня можно отпустить без сожаления?"},
]

DAILY_INTELLIGENCE = [
    {"title": "Наш мозг любит предсказуемость", "body": "Когда у нас есть простые ритуалы, мозгу легче снижать уровень стресса и принимать решения.\n\nПопробуйте маленький ритуал сегодня."},
    {"title": "Архитектура тишины", "body": "Минималистичные пространства снижают когнитивную нагрузку. Мозг тратит меньше ресурсов на фильтрацию визуального шума.\n\nЭто не эстетика — это физиология."},
    {"title": "Почему мы устаём от выбора", "body": "Каждый день мы принимаем тысячи решений. Усталость от выбора — реальный феномен.\n\nУпрощай рутину, чтобы сохранить энергию для важного."},
    {"title": "Природа и восстановление", "body": "20 минут на природе снижают уровень кортизола на 21%.\n\nНе нужен лес — достаточно парка или вида на деревья из окна."},
    {"title": "Цифровой детокс", "body": "Первые 30 минут после пробуждения без телефона улучшают концентрацию в течение всего дня.\n\nМозг успевает настроиться на собственный ритм."},
]

CULTURE_NOTES = [
    {"title": "Красота в деталях", "body": "Искусство учит нас замечать то, что делает мир глубже и богаче.\n\nСегодня: обратите внимание на детали вокруг вас."},
    {"title": "Wabi-sabi", "body": "Японская эстетика несовершенства учит ценить простоту и незавершённость.\n\nТрещина в чашке — не изъян, а история."},
    {"title": "Hygge", "body": "Датская концепция уюта — это не о вещах, а об атмосфере.\n\nСвечи, тёплый плед, близкие люди и ощущение безопасности."},
    {"title": "Lagom", "body": "Шведский принцип «ровно столько, сколько нужно».\n\nНе слишком много, не слишком мало — идеальный баланс."},
    {"title": "Slow living", "body": "Это не про скорость — это про осознанность.\n\nДелать меньше, но с полным присутствием."},
]

SOFT_ACTIONS = [
    "Выпейте стакан воды у окна и подышите свежим воздухом.",
    "Напишите одному человеку, которого давно не видели. Просто «привет, думала о тебе».",
    "Сделайте что-то приятное для себя без причины — чай, свеча, любимая музыка.",
    "Уберите один лишний предмет со стола. Пространство влияет на мысли.",
    "Проведите следующий час без фоновых звуков. Просто тишина.",
]

RECIPES = [
    {
        "name": "Green Glow Bowl",
        "desc": "Лёгкий, питательный и очень красивый завтрак",
        "ingredients": "• Авокадо — 1 шт\n• Шпинат — горсть\n• Яйцо — 1 шт\n• Лимонный сок — 1 ч.л.\n• Кунжут, соль по вкусу",
        "steps": "1. Сварите яйцо всмятку (6 минут)\n2. Нарежьте авокадо\n3. Выложите шпинат, авокадо, яйцо\n4. Сбрызните лимоном, посыпьте кунжутом",
        "benefit": "Омега-3, железо, витамин D",
        "time": "15 мин",
        "difficulty": "Легко"
    },
    {
        "name": "Golden Oat Bowl",
        "desc": "Тёплый завтрак с куркумой и мёдом",
        "ingredients": "• Овсянка — 50г\n• Молоко — 200мл\n• Куркума — щепотка\n• Мёд — 1 ч.л.\n• Банан, орехи",
        "steps": "1. Сварите овсянку на молоке\n2. Добавьте куркуму и мёд\n3. Нарежьте банан, добавьте орехи",
        "benefit": "Клетчатка, антиоксиданты, энергия",
        "time": "10 мин",
        "difficulty": "Легко"
    },
    {
        "name": "Berry Chia Pudding",
        "desc": "Нежный пудинг с ягодами — готовится с вечера",
        "ingredients": "• Семена чиа — 3 ст.л.\n• Кокосовое молоко — 200мл\n• Мёд — 1 ч.л.\n• Ягоды — горсть",
        "steps": "1. Смешайте чиа с молоком и мёдом\n2. Уберите в холодильник на ночь\n3. Утром добавьте ягоды",
        "benefit": "Омега-3, антиоксиданты, клетчатка",
        "time": "5 мин + ночь",
        "difficulty": "Легко"
    },
]

CITY_GUIDES = {
    "париж": {
        "name": "Париж",
        "emoji": "🗼",
        "desc": "Эстетичный, спокойный, вдохновляющий",
        "days": [
            "День 1: Монмартр — маленькие кафе, художники, вид на город",
            "День 2: Музей Орсе — импрессионисты, потом набережные Сены",
            "День 3: Район Маре — галереи, винтаж, лучший фалафель",
            "День 4: Версаль или Фонтенбло — парки, дворцы, тишина",
        ],
        "tips": "Лучшее время: апрель–май, сентябрь–октябрь\nБюджет: от €80/день\nЖить лучше: 11-й или 3-й округ"
    },
    "копенгаген": {
        "name": "Копенгаген",
        "emoji": "🇩🇰",
        "desc": "Дизайн, hygge и открытые пространства",
        "days": [
            "День 1: Норребро — кофейни, стрит-арт, рынки",
            "День 2: Музей Louisiana — современное искусство у моря",
            "День 3: Фредериксберг — парки, дворец, тихие улочки",
        ],
        "tips": "Лучшее время: июнь–август\nОбязательно: велосипед\nTry: смёрребрёд и новая нордическая кухня"
    },
    "милан": {
        "name": "Милан",
        "emoji": "🇮🇹",
        "desc": "Архитектура, мода и aperitivo",
        "days": [
            "День 1: Дуомо и галерея Виктора Эммануила II",
            "День 2: Брера — галерея, рынок, лучшие рестораны",
            "День 3: Навильи — каналы, aperitivo, атмосфера",
        ],
        "tips": "Лучшее время: март–май, сентябрь–октябрь\nАperitivo: с 18:00 — напиток + еда\nОбязательно: Тайная вечеря Да Винчи (бронировать заранее)"
    },
    "токио": {
        "name": "Токио",
        "emoji": "🇯🇵",
        "desc": "Культура, детали и удивительный контраст",
        "days": [
            "День 1: Асакуса — храм Сенсодзи, традиционный рынок",
            "День 2: Сибуя и Харадзюку — современный Токио",
            "День 3: Янака — старый Токио, кошачьи кафе, тофу",
            "День 4: Никко или Камакура — природа и храмы",
        ],
        "tips": "Лучшее время: март–апрель (сакура), октябрь–ноябрь\nJR Pass экономит на транспорте\nПопробовать: омакасе, рамен, моти"
    },
    "лиссабон": {
        "name": "Лиссабон",
        "emoji": "🇵🇹",
        "desc": "Свет, трамваи и меланхоличная красота",
        "days": [
            "День 1: Алфама — фаду, азулежу, закат с мирадору",
            "День 2: Белен — монастырь Жеронимуш, пастель де ната",
            "День 3: LX Factory — маркет, рестораны, атмосфера",
        ],
        "tips": "Лучшее время: май–июнь, сентябрь\nОбязательно: трамвай 28\nПопробовать: пастель де ната в Pastéis de Belém"
    },
}

EVENING_QUESTIONS = [
    "Что сегодня получилось хорошо?",
    "Где сегодня я была близка к тому, кем хочу стать?",
    "Что можно отпустить из сегодняшнего дня?",
    "За что я благодарна сегодня?",
]

# Unsplash фото по темам
PHOTOS = {
    "morning": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
    "intelligence": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800",
    "culture": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
    "recipe": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=800",
    "soft": "https://images.unsplash.com/photo-1544027993-37dbfe43562a?w=800",
    "reflect": "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800",
    "guides": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800",
    "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800",
    "copenhagen": "https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?w=800",
    "milan": "https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800",
    "tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800",
    "lisbon": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=800",
    "default": "https://images.unsplash.com/photo-1416339306562-f3d12fefd36f?w=800",
}

user_data = {}

def get_user(uid):
    uid = str(uid)
    if uid not in user_data:
        user_data[uid] = {
            "state": None,
            "name": "",
            "onboarding": {},
            "ob_step": 0,
            "di": 0, "ci": 0, "si": 0,
        }
    return user_data[uid]

def get_daily(items, offset=0):
    return items[(datetime.now().timetuple().tm_yday + offset) % len(items)]

def greeting():
    h = datetime.now().hour
    if 5 <= h < 12: return "Доброе утро"
    elif 12 <= h < 17: return "Добрый день"
    elif 17 <= h < 22: return "Добрый вечер"
    return "Доброй ночи"

def api(method, data):
    try:
        req = Request(f"{API}/{method}", data=json.dumps(data).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        log.error(f"API {method}: {e}")
        return None

def send(chat_id, text, kb=None):
    d = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if kb: d["reply_markup"] = {"inline_keyboard": kb}
    return api("sendMessage", d)

def send_photo(chat_id, photo_url, caption, kb=None):
    d = {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    if kb: d["reply_markup"] = {"inline_keyboard": kb}
    result = api("sendPhoto", d)
    if not result or not result.get("ok"):
        return send(chat_id, caption, kb)
    return result

def edit(chat_id, msg_id, text, kb=None):
    d = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"}
    if kb: d["reply_markup"] = {"inline_keyboard": kb}
    return api("editMessageText", d)

def answer(cb_id, text=""):
    api("answerCallbackQuery", {"callback_query_id": cb_id, "text": text})

def main_menu_kb():
    return [
        [{"text": "☀️  Daily", "callback_data": "daily_menu"}],
        [{"text": "🧭  My Compass", "callback_data": "compass"}],
        [{"text": "✨  Explore", "callback_data": "explore"}],
        [{"text": "📚  Guides", "callback_data": "guides"}],
        [{"text": "🌙  Reflect", "callback_data": "reflect"}],
    ]

def back_kb():
    return [[{"text": "↩ В меню", "callback_data": "menu"}]]

def daily_kb():
    return [
        [{"text": "Morning Compass", "callback_data": "morning"}],
        [{"text": "Daily Intelligence", "callback_data": "intelligence"}],
        [{"text": "Culture Note", "callback_data": "culture"}],
        [{"text": "Recipe of the Day", "callback_data": "recipe"}],
        [{"text": "Soft Action", "callback_data": "soft"}],
        [{"text": "↩ В меню", "callback_data": "menu"}],
    ]

OB_STEPS = [
    {
        "key": "goal",
        "q": "Что привело вас в Slow Glow? ✦",
        "multi": False,
        "options": [
            ("Меньше стресса", "ob_stress"),
            ("Больше вдохновения", "ob_inspire"),
            ("Полезные привычки", "ob_habits"),
            ("Лучше понимать себя", "ob_self"),
            ("Всё вместе", "ob_all"),
        ]
    },
    {
        "key": "qualities",
        "q": "Каким человеком вы хотите становиться?\n\n<i>Выберите до 5 качеств</i>",
        "multi": True,
        "options": [
            ("спокойная", "q_calm"), ("уверенная", "q_confident"),
            ("любознательная", "q_curious"), ("заботящаяся о себе", "q_selfcare"),
            ("творческая", "q_creative"), ("эстетичная", "q_aesthetic"),
            ("дисциплинированная", "q_disciplined"), ("свободная", "q_free"),
        ]
    },
    {
        "key": "inspiration",
        "q": "Что вас вдохновляет?",
        "multi": True,
        "options": [
            ("Книги", "i_books"), ("Искусство", "i_art"),
            ("Архитектура", "i_arch"), ("Путешествия", "i_travel"),
            ("Wellness", "i_wellness"), ("Красота", "i_beauty"),
        ]
    },
    {
        "key": "topics",
        "q": "Какие темы вам интересны?",
        "multi": True,
        "options": [
            ("Психология", "t_psych"), ("Beauty", "t_beauty"),
            ("Рецепты", "t_recipes"), ("Travel", "t_travel"),
            ("Культура", "t_culture"), ("Книги", "t_books"),
        ]
    },
    {
        "key": "rhythm",
        "q": "Какой ритм жизни вам ближе?",
        "multi": False,
        "options": [
            ("Медленный", "r_slow"),
            ("Баланс", "r_balance"),
            ("Активный", "r_active"),
        ]
    },
]

def send_ob_step(chat_id, u):
    step = u["ob_step"]
    if step >= len(OB_STEPS):
        finish_onboarding(chat_id, u)
        return
    s = OB_STEPS[step]
    selected = u["onboarding"].get(s["key"] + "_selected", [])
    if s["multi"]:
        kb = []
        for label, cb in s["options"]:
            check = "✓ " if cb in selected else ""
            kb.append([{"text": f"{check}{label}", "callback_data": f"ob_{cb}"}])
        kb.append([{"text": "Продолжить →", "callback_data": "ob_next"}])
    else:
        kb = [[{"text": label, "callback_data": f"ob_{cb}"}] for label, cb in s["options"]]
    send(chat_id, s["q"], kb)

def finish_onboarding(chat_id, u):
    name = u["name"]
    u["state"] = None
    qualities = u["onboarding"].get("qualities_selected", [])
    q_labels = {
        "q_calm": "спокойная", "q_confident": "уверенная",
        "q_curious": "любознательная", "q_selfcare": "заботящаяся о себе",
        "q_creative": "творческая", "q_aesthetic": "эстетичная",
        "q_disciplined": "дисциплинированная", "q_free": "свободная",
    }
    q_text = ", ".join([q_labels.get(q, q) for q in qualities]) if qualities else "прекрасной"
    send_photo(chat_id, PHOTOS["default"],
        f"Всё готово, <b>{name}</b> ✦\n\n"
        f"Я запомнила, что вы хотите становиться: <b>{q_text}</b>.\n\n"
        f"Каждый день буду присылать вам то, что поможет жить ближе к этому образу.\n\n"
        f"<i>take it slow. let it glow. ✦</i>",
        main_menu_kb()
    )

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    u = get_user(chat_id)

    if text == "/start":
        u["state"] = "waiting_name"
        u["ob_step"] = 0
        u["onboarding"] = {}
        u["name"] = ""
        send(chat_id,
            "Привет ✦\n\n"
            "Я — <b>Slow Glow</b>, ваш персональный lifestyle companion.\n\n"
            "Помогу вам жить ближе к тому, кем вы хотите быть — без спешки, с вдохновением и заботой о себе.\n\n"
            "Как вас зовут?"
        )
        return

    if text == "/menu":
        name = u["name"] or "друг"
        send(chat_id, f"{greeting()}, <b>{name}</b> ✦\n\nВыберите раздел:", main_menu_kb())
        return

    if u["state"] == "waiting_name":
        name = text.strip()
        u["name"] = name
        u["state"] = "onboarding"
        send(chat_id,
            f"Рада знакомству, <b>{name}</b> ✦\n\n"
            f"Прежде чем начать, задам несколько вопросов — чтобы Slow Glow был по-настоящему вашим.\n\n"
            f"Это займёт меньше минуты"
        )
        time.sleep(0.5)
        send_ob_step(chat_id, u)
        return

    if u["state"] == "reflect_mode":
        name = u["name"] or "друг"
        import random
        responses = [
            f"Спасибо, что поделились, <b>{name}</b> ✦\n\nЭто важно — замечать и называть то, что внутри.",
            f"Слышу вас ✦\n\nИногда просто высказать мысль вслух уже помогает.",
            f"Это звучит честно ✦\n\nВы уже делаете кое-что важное — обращаете на себя внимание.",
        ]
        send_photo(chat_id, PHOTOS["reflect"], random.choice(responses), [
            [{"text": "Написать ещё", "callback_data": "reflect_more"}],
            [{"text": "↩ В меню", "callback_data": "menu"}],
        ])
        return

    if u["state"] == "explore_mode":
        query = text.strip().lower()
        # Поиск города
        city_key = None
        for key in CITY_GUIDES:
            if key in query or CITY_GUIDES[key]["name"].lower() in query:
                city_key = key
                break
        if city_key:
            u["state"] = None
            show_city_guide(chat_id, city_key)
        else:
            u["explore_query"] = text.strip()
            u["state"] = None
            send(chat_id,
                f"✨ Вы написали: «{text.strip()}» ✦\n\n"
                f"Уточните запрос:",
                [
                    [{"text": "Подробнее", "callback_data": "explore_detail"}],
                    [{"text": "Другой запрос", "callback_data": "explore_new"}],
                    [{"text": "↩ В меню", "callback_data": "menu"}],
                ]
            )
        return

    if u["state"] == "city_search":
        query = text.strip().lower()
        u["state"] = None
        city_key = None
        for key in CITY_GUIDES:
            if key in query or CITY_GUIDES[key]["name"].lower() in query:
                city_key = key
                break
        if city_key:
            show_city_guide(chat_id, city_key)
        else:
            send(chat_id,
                f"Пока у меня нет гайда по этому городу.\n\n"
                f"Есть гайды по: Париж, Копенгаген, Милан, Токио, Лиссабон\n\n"
                f"Или напишите другой город:",
                [[{"text": "↩ Guides", "callback_data": "guides"}]]
            )
        return

    name = u["name"] or "друг"
    send(chat_id, f"{greeting()}, <b>{name}</b> ✦\n\nВыберите раздел:", main_menu_kb())

def show_city_guide(chat_id, city_key):
    g = CITY_GUIDES[city_key]
    days_text = "\n".join([f"• {d}" for d in g["days"]])
    photo_key = city_key if city_key in PHOTOS else "guides"
    send_photo(chat_id, PHOTOS[photo_key],
        f"{g['emoji']} <b>{g['name']}</b>\n<i>{g['desc']}</i>\n\n"
        f"<b>Маршрут:</b>\n{days_text}\n\n"
        f"<b>Советы:</b>\n{g['tips']}",
        [
            [{"text": "Сохранить гайд", "callback_data": "save"}],
            [{"text": "Другой город", "callback_data": "city_search"}],
            [{"text": "↩ Guides", "callback_data": "guides"}],
        ]
    )

def handle_callback(cb):
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    data = cb["data"]
    cb_id = cb["id"]
    u = get_user(chat_id)
    answer(cb_id)
    name = u["name"] or "друг"

    if data.startswith("ob_"):
        step = u["ob_step"]
        if step >= len(OB_STEPS): return
        s = OB_STEPS[step]
        cb_val = data[3:]
        if cb_val == "next":
            u["ob_step"] += 1
            send_ob_step(chat_id, u)
            return
        key = s["key"]
        if s["multi"]:
            selected = u["onboarding"].get(key + "_selected", [])
            if cb_val in selected:
                selected.remove(cb_val)
            elif len(selected) < 5:
                selected.append(cb_val)
            u["onboarding"][key + "_selected"] = selected
            kb = []
            for label, opt in s["options"]:
                check = "✓ " if opt in selected else ""
                kb.append([{"text": f"{check}{label}", "callback_data": f"ob_{opt}"}])
            kb.append([{"text": "Продолжить →", "callback_data": "ob_next"}])
            edit(chat_id, msg_id, s["q"], kb)
        else:
            u["onboarding"][key] = cb_val
            u["ob_step"] += 1
            send_ob_step(chat_id, u)
        return

    if data == "menu":
        edit(chat_id, msg_id, f"{greeting()}, <b>{name}</b> ✦\n\nВыберите раздел:", main_menu_kb())

    elif data == "daily_menu":
        edit(chat_id, msg_id, f"☀️ <b>Daily</b>\n\n{greeting()}, <b>{name}</b> ✦\n\nВаш ежедневный поток вдохновения:", daily_kb())

    elif data == "morning":
        item = get_daily(MORNING_COMPASS)
        send_photo(chat_id, PHOTOS["morning"],
            f"<b>Morning Compass</b>\n\n<b>{item['title']}</b>\n\n{item['body']}",
            [
                [{"text": "Моя фокус-точка дня", "callback_data": "morning_focus"}],
                [{"text": "Другое действие", "callback_data": "soft"}, {"text": "Мысль дня", "callback_data": "intelligence"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "morning_focus":
        action = get_daily(SOFT_ACTIONS)
        send_photo(chat_id, PHOTOS["soft"],
            f"<b>Ваша фокус-точка сегодня</b>\n\n{action}\n\n<i>Маленькое действие меняет день ✦</i>",
            [[{"text": "↩ Morning Compass", "callback_data": "morning"}]]
        )

    elif data == "intelligence":
        item = get_daily(DAILY_INTELLIGENCE)
        send_photo(chat_id, PHOTOS["intelligence"],
            f"<b>Daily Intelligence</b>\n\n<b>{item['title']}</b>\n\n{item['body']}",
            [
                [{"text": "Сохранить", "callback_data": "save"}, {"text": "Следующее", "callback_data": "intel_next"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "intel_next":
        u["di"] = u.get("di", 0) + 1
        item = DAILY_INTELLIGENCE[u["di"] % len(DAILY_INTELLIGENCE)]
        send_photo(chat_id, PHOTOS["intelligence"],
            f"<b>Daily Intelligence</b>\n\n<b>{item['title']}</b>\n\n{item['body']}",
            [
                [{"text": "Сохранить", "callback_data": "save"}, {"text": "Следующее", "callback_data": "intel_next"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "culture":
        item = get_daily(CULTURE_NOTES)
        send_photo(chat_id, PHOTOS["culture"],
            f"<b>Culture Note</b>\n\n<b>{item['title']}</b>\n\n{item['body']}",
            [
                [{"text": "Сохранить", "callback_data": "save"}, {"text": "Следующее", "callback_data": "culture_next"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "culture_next":
        u["ci"] = u.get("ci", 0) + 1
        item = CULTURE_NOTES[u["ci"] % len(CULTURE_NOTES)]
        send_photo(chat_id, PHOTOS["culture"],
            f"<b>Culture Note</b>\n\n<b>{item['title']}</b>\n\n{item['body']}",
            [
                [{"text": "Сохранить", "callback_data": "save"}, {"text": "Следующее", "callback_data": "culture_next"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "recipe":
        r = get_daily(RECIPES)
        send_photo(chat_id, PHOTOS["recipe"],
            f"<b>Recipe of the Day</b>\n\n<b>{r['name']}</b>\n<i>{r['desc']}</i>\n\n"
            f"<b>Ингредиенты:</b>\n{r['ingredients']}\n\n"
            f"<b>Приготовление:</b>\n{r['steps']}\n\n"
            f"✦ {r['benefit']}  •  {r['time']}  •  {r['difficulty']}",
            [
                [{"text": "Сохранить рецепт", "callback_data": "save"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "soft":
        action = get_daily(SOFT_ACTIONS)
        send_photo(chat_id, PHOTOS["soft"],
            f"<b>Soft Action</b>\n\n{action}\n\n<i>Маленькое действие — это уже забота о себе ✦</i>",
            [
                [{"text": "Сделаю", "callback_data": "soft_done"}, {"text": "Другое", "callback_data": "soft_next"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "soft_done":
        send(chat_id, f"Замечательно, <b>{name}</b> ✦\n\n<i>take it slow. let it glow.</i>", back_kb())

    elif data == "soft_next":
        u["si"] = u.get("si", 0) + 1
        action = SOFT_ACTIONS[u["si"] % len(SOFT_ACTIONS)]
        send_photo(chat_id, PHOTOS["soft"],
            f"<b>Soft Action</b>\n\n{action}",
            [
                [{"text": "Сделаю", "callback_data": "soft_done"}, {"text": "Другое", "callback_data": "soft_next"}],
                [{"text": "↩ Daily", "callback_data": "daily_menu"}],
            ]
        )

    elif data == "compass":
        ob = u.get("onboarding", {})
        qualities = ob.get("qualities_selected", [])
        inspiration = ob.get("inspiration_selected", [])
        q_labels = {
            "q_calm": "спокойная", "q_confident": "уверенная",
            "q_curious": "любознательная", "q_selfcare": "заботящаяся о себе",
            "q_creative": "творческая", "q_aesthetic": "эстетичная",
            "q_disciplined": "дисциплинированная", "q_free": "свободная",
        }
        i_labels = {
            "i_books": "Книги", "i_art": "Искусство",
            "i_arch": "Архитектура", "i_travel": "Путешествия",
            "i_wellness": "Wellness", "i_beauty": "Красота",
        }
        q_text = " · ".join([q_labels.get(q, q) for q in qualities]) if qualities else "ещё не выбраны"
        i_text = " · ".join([i_labels.get(i, i) for i in inspiration]) if inspiration else "ещё не выбраны"
        edit(chat_id, msg_id,
            f"🧭 <b>My Compass</b>\n\n"
            f"<b>Я становлюсь человеком, который:</b>\n{q_text}\n\n"
            f"<b>Мои интересы:</b>\n{i_text}\n\n"
            f"<b>Мой прогресс</b>\nВы осознанно выбираете себя каждый день ✦",
            [[{"text": "↩ В меню", "callback_data": "menu"}]]
        )

    elif data == "explore":
        u["state"] = "explore_mode"
        edit(chat_id, msg_id,
            "✨ <b>Explore</b>\n\n<b>Чем я могу помочь?</b>\n\n"
            "Напишите мне что угодно:\n\n"
            "<i>«Париж на 4 дня»\n«Что почитать если устала»\n«Подбери красивый завтрак»\n«Идеи для воскресенья»\n«Уход за кожей зимой»</i>\n\n"
            "Напишите ваш запрос:",
            [[{"text": "↩ В меню", "callback_data": "menu"}]]
        )

    elif data == "explore_detail":
        query = u.get("explore_query", "")
        send(chat_id,
            f"✨ Отличный запрос — «{query}» ✦\n\n"
            f"Персонализированные рекомендации появятся в следующем обновлении.\n\n"
            f"А пока загляните в <b>Guides</b> — там уже есть кое-что интересное",
            [
                [{"text": "Открыть Guides", "callback_data": "guides"}],
                [{"text": "↩ В меню", "callback_data": "menu"}],
            ]
        )

    elif data == "explore_new":
        u["state"] = "explore_mode"
        send(chat_id, "✨ Напишите новый запрос:", [[{"text": "↩ В меню", "callback_data": "menu"}]])

    elif data == "guides":
        send_photo(chat_id, PHOTOS["guides"],
            "📚 <b>Guides</b>\n\nГотовые мини-гайды для вашей красивой жизни:",
            [
                [{"text": "Найти город", "callback_data": "city_search"}],
                [{"text": "Beauty", "callback_data": "guide_beauty"}, {"text": "Wellness", "callback_data": "guide_wellness"}],
                [{"text": "Books", "callback_data": "guide_books"}, {"text": "Lifestyle", "callback_data": "guide_lifestyle"}],
                [{"text": "↩ В меню", "callback_data": "menu"}],
            ]
        )

    elif data == "city_search":
        u["state"] = "city_search"
        send(chat_id,
            "Напишите название города — я найду гайд:\n\n"
            "<i>Например: Париж, Токио, Лиссабон, Копенгаген, Милан</i>",
            [[{"text": "↩ Guides", "callback_data": "guides"}]]
        )

    elif data == "guide_beauty":
        send_photo(chat_id, PHOTOS["soft"],
            "<b>Beauty Guide</b>\n\n"
            "<b>Уход за кожей зимой</b>\n\n"
            "1. Мягкое очищение — дважды в день\n"
            "2. Тоник с гиалуроновой кислотой\n"
            "3. Сыворотка с витамином С утром\n"
            "4. Насыщенный крем вечером\n"
            "5. Масло для губ — обязательно\n\n"
            "<i>Меньше агрессивных ингредиентов, больше питания ✦</i>",
            [[{"text": "Сохранить", "callback_data": "save"}], [{"text": "↩ Guides", "callback_data": "guides"}]]
        )

    elif data == "guide_wellness":
        send_photo(chat_id, PHOTOS["morning"],
            "<b>Wellness Guide</b>\n\n"
            "<b>Утренний ритуал за 10 минут</b>\n\n"
            "1. Стакан воды с лимоном\n"
            "2. 3 минуты дыхания (4-4-6)\n"
            "3. Одно намерение дня\n"
            "4. 2 минуты смотреть в окно\n\n"
            "<b>Вечерний ритуал</b>\n\n"
            "1. Телефон за час до сна\n"
            "2. Три благодарности\n"
            "3. Любимый чай и тишина\n\n"
            "<i>Маленькие ритуалы создают большие перемены ✦</i>",
            [[{"text": "Сохранить", "callback_data": "save"}], [{"text": "↩ Guides", "callback_data": "guides"}]]
        )

    elif data == "guide_books":
        send_photo(chat_id, PHOTOS["intelligence"],
            "<b>Books Guide</b>\n\n"
            "<b>Для slow living:</b>\n"
            "• «В защиту праздности» — Том Ходжкинсон\n"
            "• «Радикальное принятие» — Тара Брах\n"
            "• «Дао Пуха» — Бенджамин Хофф\n\n"
            "<b>Для вдохновения:</b>\n"
            "• «Год волшебного мышления» — Джоан Дидион\n"
            "• «Essentialism» — Грег МакКеон\n"
            "• «Украдите как художник» — Остин Клеон",
            [[{"text": "Сохранить", "callback_data": "save"}], [{"text": "↩ Guides", "callback_data": "guides"}]]
        )

    elif data == "guide_lifestyle":
        send_photo(chat_id, PHOTOS["reflect"],
            "<b>Lifestyle Guide</b>\n\n"
            "<b>Идеи для воскресенья:</b>\n"
            "• Медленный завтрак без телефона\n"
            "• Прогулка в новом месте города\n"
            "• Приготовить новый рецепт\n"
            "• Написать письмо себе\n\n"
            "<b>Маленькие удовольствия каждый день:</b>\n"
            "• Цветы дома\n• Любимая свеча\n• Красивая посуда\n"
            "• Музыка за завтраком",
            [[{"text": "Сохранить", "callback_data": "save"}], [{"text": "↩ Guides", "callback_data": "guides"}]]
        )

    elif data == "reflect":
        u["state"] = "reflect_mode"
        q = get_daily(EVENING_QUESTIONS)
        send_photo(chat_id, PHOTOS["reflect"],
            f"<b>Reflect</b>\n\n<i>Поделитесь тем, что у вас на уме</i>\n\n"
            f"Я здесь, чтобы вас поддержать.\n\n"
            f"<b>Вопрос для рефлексии:</b>\n{q}\n\n"
            f"Напишите в ответ",
            [[{"text": "↩ В меню", "callback_data": "menu"}]]
        )

    elif data == "reflect_more":
        u["state"] = "reflect_mode"
        q = get_daily(EVENING_QUESTIONS)
        send(chat_id, f"{q}\n\nНапишите в ответ:", [[{"text": "↩ В меню", "callback_data": "menu"}]])

    elif data == "save":
        answer(cb_id, "Сохранено ✦")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): pass

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
            for upd in updates:
                offset = upd["update_id"] + 1
                if "message" in upd:
                    handle_message(upd["message"])
                elif "callback_query" in upd:
                    handle_callback(upd["callback_query"])
        except Exception as e:
            log.error(f"Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
