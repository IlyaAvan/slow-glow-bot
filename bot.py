import os, json, time, threading, logging, random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request

BOT_TOKEN = "8972127511:AAEjvKfNUX5XiM72edNA1XnbkjummStkv14"
GROQ_API_KEY = "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"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger(__name__)

PHOTOS = {
    "welcome":   "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img1.jpg",
    "morning":   "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img7.jpg",
    "wellness":  "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img17.jpg",
    "beauty":    "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img12.jpg",
    "culture":   "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img5.jpg",
    "travel":    "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img16.jpg",
    "evening":   "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img15.jpg",
    "pinterest": "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img2.jpg",
    "profile":   "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img9.jpg",
    "paris":     "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img9.jpg",
    "tokyo":     "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img14.jpg",
    "lisbon":    "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img6.jpg",
    "default":   "https://raw.githubusercontent.com/IlyaAvan/slow-glow-bot/main/img8.jpg",
}

SYSTEM_PROMPT = (
    "Ты — Slow Glow, персональный AI lifestyle companion для девушек.\n\n"
    "Твоя миссия: помочь пользователю превратить жизнь, которую она видит на Pinterest, в свою реальную жизнь.\n\n"
    "Тон: спокойный, тёплый, эстетичный. Как умная подруга с хорошим вкусом.\n"
    "Никогда: давление, чувство вины, токсичная мотивация.\n"
    "Фразы: «Попробуй сегодня...», «Обрати внимание...», «Возможно тебе понравится...»\n"
    "Ответы: до 200 слов, без markdown, на русском языке."
)

PINTEREST_SYSTEM = (
    "Ты — Slow Glow, AI lifestyle analyst.\n\n"
    "Пользователь описывает образы, которые его вдохновляют — с Pinterest, из фильмов, из жизни.\n\n"
    "Твоя задача — провести глубокий анализ в 6 этапов:\n\n"
    "ЭТАП 1 — ЭСТЕТИКА: определи эстетику (French Summer, Quiet Luxury, Coastal Living и т.д.)\n"
    "ЭТАП 2 — LIFESTYLE: что именно привлекает за внешностью образов\n"
    "ЭТАП 3 — СКРЫТЫЕ ЖЕЛАНИЯ: что пользователь ищет на самом деле\n"
    "ЭТАП 4 — ЧТО УЖЕ ЕСТЬ: что уже присутствует в её жизни\n"
    "ЭТАП 5 — ЧТО МОЖНО ДОБАВИТЬ: реалистичные маленькие шаги\n"
    "ЭТАП 6 — ПЛАН: 1 действие сегодня, 3 на неделе, 5 в месяце\n\n"
    "Тон: тёплый, вдохновляющий. Без покупок и давления. На русском."
)

OB_QUESTIONS = [
    {
        "key": "name_q", "type": "text",
        "q": "Привет ✦\n\nЯ — <b>Slow Glow</b>, твой личный lifestyle companion.\n\nПомогу тебе превратить жизнь которую ты сохраняешь на Pinterest — в свою реальную жизнь.\n\nКак тебя зовут?"
    },
    {
        "key": "age", "type": "choice",
        "q": "Сколько тебе лет?",
        "opts": [("18–22", "age1"), ("23–28", "age2"), ("29–35", "age3"), ("36–45", "age4")]
    },
    {
        "key": "improve", "type": "multi", "max": 3,
        "q": "Что хочется улучшить прямо сейчас?\n\n<i>Выбери до 3 вариантов</i>",
        "opts": [("Энергия и здоровье", "imp1"), ("Красота и уход", "imp2"), ("Стиль и гардероб", "imp3"), ("Дом и пространство", "imp4"), ("Путешествия", "imp5"), ("Отношения с собой", "imp6"), ("Карьера и рост", "imp7")]
    },
    {
        "key": "aesthetic", "type": "multi", "max": 3,
        "q": "Какие эстетики тебя привлекают?\n\n<i>Выбери до 3</i>",
        "opts": [("French Summer", "aes1"), ("Quiet Luxury", "aes2"), ("Coastal Living", "aes3"), ("Ballet Core", "aes4"), ("Scandinavian", "aes5"), ("Romantic Minimalism", "aes6"), ("Mediterranean Living", "aes7"), ("City Chic", "aes8")]
    },
    {
        "key": "feel", "type": "multi", "max": 3,
        "q": "Как ты хочешь себя чувствовать?\n\n<i>Выбери до 3</i>",
        "opts": [("Спокойно", "feel1"), ("Уверенно", "feel2"), ("Вдохновлённо", "feel3"), ("Энергично", "feel4"), ("Женственно", "feel5"), ("Свободно", "feel6")]
    },
    {
        "key": "topics", "type": "multi", "max": 4,
        "q": "Любимые темы?\n\n<i>Выбери до 4</i>",
        "opts": [("Wellness и здоровье", "top1"), ("Beauty и уход", "top2"), ("Путешествия", "top3"), ("Книги и культура", "top4"), ("Интерьер и эстетика", "top5"), ("Еда и рецепты", "top6"), ("Психология", "top7"), ("Мода и стиль", "top8")]
    },
    {
        "key": "challenges", "type": "multi", "max": 3,
        "q": "Что сейчас даётся сложнее всего?\n\n<i>Выбери до 3</i>",
        "opts": [("Нет энергии", "ch1"), ("Нет времени", "ch2"), ("Сложно начать", "ch3"), ("Много тревоги", "ch4"), ("Нет мотивации", "ch5"), ("Не знаю с чего начать", "ch6")]
    },
    {
        "key": "identity", "type": "choice",
        "q": "Какой образ тебе ближе всего?",
        "opts": [("Спокойная и ухоженная парижанка", "id1"), ("Energetic wellness girl", "id2"), ("Творческая и эстетичная", "id3"), ("Уверенная и минималистичная", "id4")]
    },
    {
        "key": "energy", "type": "choice",
        "q": "Твой текущий уровень энергии?",
        "opts": [("Очень низкий — нужно восстановление", "en1"), ("Средний — хочу больше", "en2"), ("Хороший — хочу развиваться", "en3"), ("Высокий — готова к переменам", "en4")]
    },
    {
        "key": "goal", "type": "choice",
        "q": "Главная цель на ближайшие месяцы?",
        "opts": [("Создать красивые ежедневные ритуалы", "g1"), ("Улучшить здоровье и самочувствие", "g2"), ("Развить свою эстетику и стиль", "g3"), ("Найти внутреннее спокойствие", "g4")]
    },
]

TODAY_CONTENT = [
    {"thought": "Красота повседневности не требует особых условий.", "action": "Сделай одно красивое действие сегодня — накрой стол, купи цветы, зажги свечу.", "wellness": "Выпей стакан воды с лимоном прямо сейчас."},
    {"thought": "Медленно — не значит мало. Медленно — значит осознанно.", "action": "Прогуляйся без наушников хотя бы 10 минут.", "wellness": "Сделай 3 глубоких вдоха перед каждым приёмом пищи сегодня."},
    {"thought": "Твой стиль жизни начинается с маленьких ежедневных выборов.", "action": "Запиши одно намерение на сегодня. Не список задач — одно намерение.", "wellness": "Ляг спать сегодня на 30 минут раньше обычного."},
    {"thought": "Женственность — это не внешность. Это способ присутствовать в мире.", "action": "Оденься красиво — даже если никуда не идёшь. Для себя.", "wellness": "Добавь в рацион что-то зелёное сегодня."},
    {"thought": "Уют создаётся не дизайном, а вниманием к деталям.", "action": "Убери одну поверхность в доме. Пустое пространство — тоже красота.", "wellness": "Проведи 20 минут без телефона — просто будь."},
    {"thought": "Самая красивая жизнь — та, в которой ты чувствуешь себя собой.", "action": "Сделай что-то что давно откладывала. Одно маленькое действие.", "wellness": "Выйди на улицу хотя бы на 15 минут сегодня."},
    {"thought": "Вдохновение живёт в деталях — в запахе кофе, в свете из окна, в книге рядом с кроватью.", "action": "Создай один красивый момент сегодня — для себя.", "wellness": "Выпей травяной чай вечером вместо телефона."},
]

CULTURE_CONTENT = [
    {"category": "Книга", "title": "«Нормальные люди» — Салли Руни", "body": "История о том как два человека находят и теряют друг друга. Руни пишет о близости, уязвимости и том как сложно быть по-настоящему увиденным.\n\nПодходит если: хочется красивой прозы и честного взгляда на отношения."},
    {"category": "Концепция", "title": "Wabi-sabi — японская эстетика несовершенства", "body": "Видеть красоту в простом, незавершённом, быстротечном. Трещина в чашке — не изъян, а история.\n\nПопробуй сегодня: найти красоту в чём-то несовершенном рядом с тобой."},
    {"category": "Фильм", "title": "«Амели» — Жан-Пьер Жёне", "body": "О девушке которая находит радость в маленьких деталях жизни. Об одиночестве, воображении и смелости быть счастливой.\n\nСмотреть когда: хочется нежного и вдохновляющего."},
    {"category": "Художник", "title": "Бо Бартлетт — американский реализм", "body": "Картины о тихих моментах повседневности. Фигуры в пространстве, свет, одиночество и связь.\n\nЧто смотреть: серия работ о семье и времени."},
    {"category": "Концепция", "title": "Hygge — датское искусство уюта", "body": "Не про вещи, а про атмосферу. Свечи, тёплые напитки, близкие люди, ощущение безопасности.\n\nПопробуй сегодня: создать один hygge-момент."},
    {"category": "Книга", "title": "«Essentialism» — Грег МакКеон", "body": "О том как делать меньше но лучше. Убирать лишнее чтобы сосредоточиться на важном.\n\nГлавная мысль: почти всё несущественно. Найди то что действительно важно."},
    {"category": "Фильм", "title": "«Под тосканским солнцем» — Одри Уэллс", "body": "О женщине которая после развода купила дом в Тоскане и начала жизнь заново.\n\nСмотреть когда: нужно вдохновение для больших перемен."},
]

TRAVEL_GUIDES = {
    "paris": {
        "name": "Париж", "photo": "paris",
        "desc": "Город света, медленных прогулок и красоты повседневности",
        "days": "День 1: Монмартр — художники, кафе, закат\nДень 2: Музей Орсе + набережные Сены\nДень 3: Маре — галереи, винтаж, лучший фалафель",
        "tips": "Лучшее время: апрель–май, сентябрь\nЖить: 11-й или 3-й округ\nПопробовать: круассан в Du Pain et des Idées"
    },
    "tokyo": {
        "name": "Токио", "photo": "tokyo",
        "desc": "Контраст тишины и шума, традиций и будущего",
        "days": "День 1: Асакуса — храм Сенсодзи, традиции\nДень 2: Сибуя и Харадзюку — современный Токио\nДень 3: Янака — старый Токио, тишина",
        "tips": "Лучшее время: март–апрель (сакура)\nJR Pass для транспорта\nПопробовать: омакасе, матча"
    },
    "lisbon": {
        "name": "Лиссабон", "photo": "lisbon",
        "desc": "Свет, трамваи и меланхоличная красота",
        "days": "День 1: Алфама — фаду, азулежу, закат\nДень 2: Белен — монастырь, пастель де ната\nДень 3: LX Factory — маркет, рестораны",
        "tips": "Лучшее время: май–июнь, сентябрь\nОбязательно: трамвай 28\nПопробовать: пастель де ната"
    },
}

user_data = {}
chat_history = {}
pinterest_history = {}

def get_user(uid):
    uid = str(uid)
    if uid not in user_data:
        user_data[uid] = {
            "state": None, "name": "", "ob_step": 0,
            "profile": {}, "glow_identity": "",
            "di": 0, "ci": 0, "ti": 0,
        }
    return user_data[uid]

def get_daily(items):
    return items[datetime.now().timetuple().tm_yday % len(items)]

def greeting():
    h = datetime.now().hour
    if 5 <= h < 12: return "Доброе утро"
    elif 12 <= h < 17: return "Добрый день"
    elif 17 <= h < 22: return "Добрый вечер"
    return "Доброй ночи"

def build_glow_identity(profile):
    aes_map = {"aes1": "French Summer", "aes2": "Quiet Luxury", "aes3": "Coastal Living", "aes4": "Ballet Core", "aes5": "Scandinavian", "aes6": "Romantic Minimalism", "aes7": "Mediterranean Living", "aes8": "City Chic"}
    feel_map = {"feel1": "спокойствие", "feel2": "уверенность", "feel3": "вдохновение", "feel4": "энергию", "feel5": "женственность", "feel6": "свободу"}
    id_map = {"id1": "спокойной и ухоженной парижанки", "id2": "energetic wellness girl", "id3": "творческой и эстетичной", "id4": "уверенной и минималистичной"}
    g_map = {"g1": "красивые ежедневные ритуалы", "g2": "здоровье и самочувствие", "g3": "эстетику и стиль", "g4": "внутреннее спокойствие"}

    aesthetics = [aes_map.get(a, a) for a in profile.get("aesthetic_sel", [])]
    feels = [feel_map.get(f, f) for f in profile.get("feel_sel", [])]
    identity = id_map.get(profile.get("identity_sel", [""])[0] if profile.get("identity_sel") else "", "себя")
    goal = g_map.get(profile.get("goal_sel", [""])[0] if profile.get("goal_sel") else "", "")

    aes_text = ", ".join(aesthetics) if aesthetics else "свою уникальную"
    feel_text = ", ".join(feels) if feels else "лучше"

    return (
        f"Ты создаёшь жизнь в эстетике {aes_text}.\n\n"
        f"Ты стремишься к образу {identity}.\n\n"
        f"Ты хочешь чувствовать: {feel_text}.\n\n"
        f"Твой фокус: {goal}."
    )

def call_groq(messages, system=None):
    try:
        sys = system or SYSTEM_PROMPT
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": sys}] + messages,
            "max_tokens": 500,
            "temperature": 0.8,
        }
        req = Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + GROQ_API_KEY, "Content-Type": "application/json"},
            method="POST"
        )
        with urlopen(req, timeout=25) as r:
            result = json.loads(r.read())
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        log.error("Groq: " + str(e))
        return "Что-то пошло не так. Попробуй ещё раз ✦"

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

def send_photo(chat_id, photo_key, caption, kb=None):
    url = PHOTOS.get(photo_key, PHOTOS["default"])
    d = {"chat_id": chat_id, "photo": url, "caption": caption, "parse_mode": "HTML"}
    if kb: d["reply_markup"] = {"inline_keyboard": kb}
    result = api("sendPhoto", d)
    if not result or not result.get("ok"):
        return send(chat_id, caption, kb)
    return result

def edit(chat_id, msg_id, text, kb=None):
    d = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"}
    if kb: d["reply_markup"] = {"inline_keyboard": kb}
    return api("editMessageText", d)

def answer_cb(cb_id, text=""):
    api("answerCallbackQuery", {"callback_query_id": cb_id, "text": text})

def typing(chat_id):
    api("sendChatAction", {"chat_id": chat_id, "action": "typing"})

def main_menu_kb():
    return [
        [{"text": "✨  Today's Glow", "callback_data": "today"}],
        [{"text": "📌  Pinterest Analysis", "callback_data": "pinterest"}],
        [{"text": "🌿  Wellness", "callback_data": "wellness"}],
        [{"text": "💄  Beauty", "callback_data": "beauty"}],
        [{"text": "🏛  Culture", "callback_data": "culture"}],
        [{"text": "✈️  Travel", "callback_data": "travel"}],
        [{"text": "🌙  Evening Reflection", "callback_data": "evening"}],
        [{"text": "💬  Ask Slow Glow", "callback_data": "ask"}],
        [{"text": "👤  My Glow Identity", "callback_data": "identity"}],
    ]

def back_menu():
    return [[{"text": "← В меню", "callback_data": "menu"}]]

def send_ob_step(chat_id, u):
    step = u["ob_step"]
    if step >= len(OB_QUESTIONS):
        finish_onboarding(chat_id, u)
        return
    q = OB_QUESTIONS[step]
    if q["type"] == "text":
        send(chat_id, q["q"])
    elif q["type"] == "choice":
        kb = [[{"text": label, "callback_data": "ob_" + cb}] for label, cb in q["opts"]]
        send(chat_id, q["q"], kb)
    elif q["type"] == "multi":
        sel = u["profile"].get(q["key"] + "_sel", [])
        kb = []
        for label, cb in q["opts"]:
            check = "✓ " if cb in sel else ""
            kb.append([{"text": check + label, "callback_data": "ob_" + cb}])
        max_val = q["max"]
        cnt = len(sel)
        kb.append([{"text": f"Продолжить ({cnt}/{max_val}) →", "callback_data": "ob_next"}])
        send(chat_id, q["q"], kb)

def finish_onboarding(chat_id, u):
    u["state"] = None
    u["glow_identity"] = build_glow_identity(u["profile"])
    name = u["name"]
    send_photo(chat_id, "welcome",
        f"<b>Твой Glow Identity готов, {name}</b> ✦\n\n"
        f"{u['glow_identity']}\n\n"
        f"Я буду помогать тебе каждый день делать маленькие шаги к этой жизни.\n\n"
        f"<i>Turn your Pinterest life into your real life. ✦</i>",
        main_menu_kb()
    )

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    u = get_user(chat_id)

    if text == "/start":
        u.update({"state": "onboarding", "ob_step": 0, "profile": {}, "name": "", "glow_identity": ""})
        send_ob_step(chat_id, u)
        return

    if text == "/menu":
        name = u["name"] or "друг"
        send(chat_id, f"{greeting()}, <b>{name}</b> ✦\n\nВыбери раздел:", main_menu_kb())
        return

    if u["state"] == "onboarding":
        step = u["ob_step"]
        if step < len(OB_QUESTIONS) and OB_QUESTIONS[step]["type"] == "text":
            name = text.strip()
            u["name"] = name
            u["ob_step"] += 1
            send(chat_id, "Приятно познакомиться, <b>" + u["name"] + "</b> ✦\n\nЗадам ещё несколько вопросов — чтобы Slow Glow был по-настоящему твоим.")
            time.sleep(0.5)
            send_ob_step(chat_id, u)
        return

    if u["state"] == "ask_mode":
        uid = str(chat_id)
        if uid not in chat_history: chat_history[uid] = []
        chat_history[uid].append({"role": "user", "content": text})
        if len(chat_history[uid]) > 12: chat_history[uid] = chat_history[uid][-12:]
        typing(chat_id)
        identity_ctx = f"\n\nПрофиль пользователя:\n{u.get('glow_identity', '')}" if u.get("glow_identity") else ""
        system = SYSTEM_PROMPT + identity_ctx
        reply = call_groq(chat_history[uid], system)
        chat_history[uid].append({"role": "assistant", "content": reply})
        send(chat_id, reply, [
            [{"text": "Спросить ещё", "callback_data": "ask"}],
            [{"text": "← В меню", "callback_data": "menu"}],
        ])
        return

    if u["state"] == "pinterest_mode":
        uid = str(chat_id)
        if uid not in pinterest_history: pinterest_history[uid] = []
        pinterest_history[uid].append({"role": "user", "content": text})
        typing(chat_id)
        identity_ctx = f"\n\nПрофиль пользователя:\n{u.get('glow_identity', '')}" if u.get("glow_identity") else ""
        system = PINTEREST_SYSTEM + identity_ctx
        reply = call_groq(pinterest_history[uid], system)
        pinterest_history[uid].append({"role": "assistant", "content": reply})
        send(chat_id, reply, [
            [{"text": "Описать ещё образы", "callback_data": "pinterest"}],
            [{"text": "← В меню", "callback_data": "menu"}],
        ])
        return

    if u["state"] == "evening_mode":
        typing(chat_id)
        messages = [{"role": "user", "content": f"Пользователь делится: {text}"}]
        system = (
            SYSTEM_PROMPT +
            "\n\nТы отвечаешь на вечернюю рефлексию. Будь мягкой, поддерживающей. "
            "Помоги завершить день красиво. Задай один тихий вопрос для размышления."
        )
        reply = call_groq(messages, system)
        send(chat_id, reply, [
            [{"text": "Написать ещё", "callback_data": "evening"}],
            [{"text": "← В меню", "callback_data": "menu"}],
        ])
        return

    name = u["name"] or "друг"
    send(chat_id, f"{greeting()}, <b>{name}</b> ✦\n\nВыбери раздел:", main_menu_kb())


def handle_callback(cb):
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    data = cb["data"]
    cb_id = cb["id"]
    u = get_user(chat_id)
    answer_cb(cb_id)
    name = u["name"] or "друг"

    # ОНБОРДИНГ
    if data.startswith("ob_"):
        step = u["ob_step"]
        if step >= len(OB_QUESTIONS): return
        q = OB_QUESTIONS[step]
        cb_val = data[3:]

        if cb_val == "next":
            u["ob_step"] += 1
            send_ob_step(chat_id, u)
            return

        if q["type"] == "choice":
            u["profile"][q["key"] + "_sel"] = [cb_val]
            u["ob_step"] += 1
            send_ob_step(chat_id, u)
        elif q["type"] == "multi":
            sel = u["profile"].get(q["key"] + "_sel", [])
            if cb_val in sel: sel.remove(cb_val)
            elif len(sel) < q["max"]: sel.append(cb_val)
            u["profile"][q["key"] + "_sel"] = sel
            kb = []
            for label, opt in q["opts"]:
                check = "✓ " if opt in sel else ""
                kb.append([{"text": check + label, "callback_data": "ob_" + opt}])
            cnt = len(sel)
            max_val = q["max"]
            kb.append([{"text": f"Продолжить ({cnt}/{max_val}) →", "callback_data": "ob_next"}])
            edit(chat_id, msg_id, q["q"], kb)
        return

    # МЕНЮ
    if data == "menu":
        edit(chat_id, msg_id, f"{greeting()}, <b>{name}</b> ✦\n\nВыбери раздел:", main_menu_kb())

    elif data == "today":
        content = get_daily(TODAY_CONTENT)
        identity_reminder = ""
        if u.get("glow_identity"):
            lines = u["glow_identity"].split("\n\n")
            if lines:
                identity_reminder = f"\n\n<i>Напоминание: {lines[0].lower()}</i>"
        send_photo(chat_id, "morning",
            f"<b>Today's Glow ✨</b>\n\n"
            f"<b>Мысль дня:</b>\n{content['thought']}\n\n"
            f"<b>Маленькое действие:</b>\n{content['action']}\n\n"
            f"<b>Wellness:</b>\n{content['wellness']}"
            f"{identity_reminder}",
            [
                [{"text": "📌 Pinterest Analysis", "callback_data": "pinterest"}],
                [{"text": "← В меню", "callback_data": "menu"}],
            ]
        )

    elif data == "pinterest":
        u["state"] = "pinterest_mode"
        if str(chat_id) in pinterest_history:
            pinterest_history[str(chat_id)] = []
        edit(chat_id, msg_id,
            "<b>📌 Pinterest Analysis</b>\n\n"
            "Опиши мне образы которые тебя вдохновляют — с Pinterest, из фильмов, из жизни.\n\n"
            "<i>Примеры:\n"
            "«Мне нравятся фото парижских кафе, белые рубашки, книги у окна»\n"
            "«Люблю минималистичные интерьеры, утреннее солнце, тихие пространства»\n"
            "«Вдохновляют образы wellness-девушек — йога, зелёные смузи, чистая кожа»</i>\n\n"
            "Напиши в свободной форме — чем больше деталей, тем точнее анализ:",
            [[{"text": "← В меню", "callback_data": "menu"}]]
        )

    elif data == "wellness":
        typing(chat_id)
        identity_ctx = f"\nПрофиль: {u.get('glow_identity', '')}" if u.get("glow_identity") else ""
        messages = [{"role": "user", "content": f"Дай мне персональный wellness-совет на сегодня. Включи рецепт или идею для питания, движение и восстановление.{identity_ctx}"}]
        reply = call_groq(messages)
        send_photo(chat_id, "wellness",
            f"<b>🌿 Wellness</b>\n\n{reply}",
            [
                [{"text": "Ещё совет", "callback_data": "wellness"}],
                [{"text": "← В меню", "callback_data": "menu"}],
            ]
        )

    elif data == "beauty":
        typing(chat_id)
        identity_ctx = f"\nПрофиль: {u.get('glow_identity', '')}" if u.get("glow_identity") else ""
        messages = [{"role": "user", "content": f"Дай персональный beauty-совет или ритуал на сегодня. Уход за кожей, волосами или body care.{identity_ctx}"}]
        reply = call_groq(messages)
        send_photo(chat_id, "beauty",
            f"<b>💄 Beauty</b>\n\n{reply}",
            [
                [{"text": "Ещё совет", "callback_data": "beauty"}],
                [{"text": "← В меню", "callback_data": "menu"}],
            ]
        )

    elif data == "culture":
        item = get_daily(CULTURE_CONTENT)
        send_photo(chat_id, "culture",
            f"<b>🏛 Culture Note</b>\n\n<b>{item['category']}: {item['title']}</b>\n\n{item['body']}",
            [
                [{"text": "Следующее →", "callback_data": "culture_next"}],
                [{"text": "← В меню", "callback_data": "menu"}],
            ]
        )

    elif data == "culture_next":
        u["ci"] = u.get("ci", 0) + 1
        item = CULTURE_CONTENT[u["ci"] % len(CULTURE_CONTENT)]
        send_photo(chat_id, "culture",
            f"<b>🏛 Culture Note</b>\n\n<b>{item['category']}: {item['title']}</b>\n\n{item['body']}",
            [
                [{"text": "Следующее →", "callback_data": "culture_next"}],
                [{"text": "← В меню", "callback_data": "menu"}],
            ]
        )

    elif data == "travel":
        edit(chat_id, msg_id,
            "<b>✈️ Travel</b>\n\nКуда хочешь отправиться?",
            [
                [{"text": "🗼 Париж", "callback_data": "travel_paris"}],
                [{"text": "🇯🇵 Токио", "callback_data": "travel_tokyo"}],
                [{"text": "🇵🇹 Лиссабон", "callback_data": "travel_lisbon"}],
                [{"text": "✨ Персональный гайд", "callback_data": "travel_custom"}],
                [{"text": "← В меню", "callback_data": "menu"}],
            ]
        )

    elif data.startswith("travel_") and data != "travel_custom":
        city_key = data.replace("travel_", "")
        if city_key in TRAVEL_GUIDES:
            g = TRAVEL_GUIDES[city_key]
            send_photo(chat_id, g["photo"],
                f"<b>✈️ {g['name']}</b>\n<i>{g['desc']}</i>\n\n"
                f"<b>Маршрут:</b>\n{g['days']}\n\n"
                f"<b>Советы:</b>\n{g['tips']}",
                [
                    [{"text": "← Travel", "callback_data": "travel"}],
                    [{"text": "← В меню", "callback_data": "menu"}],
                ]
            )

    elif data == "travel_custom":
        u["state"] = "ask_mode"
        if str(chat_id) in chat_history: chat_history[str(chat_id)] = []
        edit(chat_id, msg_id,
            "<b>✈️ Персональный travel-гайд</b>\n\nКуда хочешь поехать и что тебя интересует?\n\n<i>Например: «Париж на 4 дня, люблю кафе, искусство и шоппинг»</i>\n\nНапиши:",
            [[{"text": "← В меню", "callback_data": "menu"}]]
        )

    elif data == "evening":
        u["state"] = "evening_mode"
        questions = [
            "Что сегодня получилось лучше, чем вчера?",
            "Где сегодня ты была близка к той версии себя, которой хочешь стать?",
            "Что можно отпустить из сегодняшнего дня?",
            "За что ты благодарна сегодня?",
            "Что дало тебе сегодня энергию?",
        ]
        q = get_daily(questions)
        send_photo(chat_id, "evening",
            f"<b>🌙 Evening Reflection</b>\n\n<i>Мягкий вечерний ритуал</i>\n\n{q}\n\nНапиши в ответ — я здесь.",
            [[{"text": "← В меню", "callback_data": "menu"}]]
        )

    elif data == "ask":
        u["state"] = "ask_mode"
        if str(chat_id) in chat_history: chat_history[str(chat_id)] = []
        edit(chat_id, msg_id,
            "<b>💬 Ask Slow Glow</b> ✦\n\n"
            "Я здесь. Спроси о чём угодно:\n\n"
            "<i>«Что приготовить сегодня?»\n"
            "«Еду в Париж на 4 дня»\n"
            "«Составь beauty routine»\n"
            "«Посоветуй книгу»\n"
            "«Я чувствую тревогу»\n"
            "«Помоги вернуться к тренировкам»</i>\n\n"
            "Напиши:",
            [[{"text": "← В меню", "callback_data": "menu"}]]
        )

    elif data == "identity":
        identity = u.get("glow_identity", "")
        if identity:
            edit(chat_id, msg_id,
                f"<b>👤 My Glow Identity</b>\n\n{identity}\n\n"
                f"<i>Каждый день ты делаешь маленькие шаги к этой жизни. ✦</i>",
                [
                    [{"text": "📌 Pinterest Analysis", "callback_data": "pinterest"}],
                    [{"text": "← В меню", "callback_data": "menu"}],
                ]
            )
        else:
            edit(chat_id, msg_id,
                "<b>👤 My Glow Identity</b>\n\nПройди онбординг чтобы создать свой профиль.\n\nНапиши /start",
                back_menu()
            )


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def log_message(self, *args): pass

def run_health():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

def main():
    threading.Thread(target=run_health, daemon=True).start()
    log.info("Slow Glow Bot 2.0 запущен")
    # Clear any existing webhook
    try:
        req = Request(f"{API}/deleteWebhook", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10) as r:
            log.info("Webhook cleared")
    except:
        pass
    time.sleep(2)
    offset = 0
    while True:
        try:
            req = Request(f"{API}/getUpdates?offset={offset}&timeout=30")
            with urlopen(req, timeout=35) as r:
                updates = json.loads(r.read()).get("result", [])
            for upd in updates:
                offset = upd["update_id"] + 1
                if "message" in upd: handle_message(upd["message"])
                elif "callback_query" in upd: handle_callback(upd["callback_query"])
        except Exception as e:
            log.error(f"Error: {e}"); time.sleep(3)

if __name__ == "__main__":
    main()
