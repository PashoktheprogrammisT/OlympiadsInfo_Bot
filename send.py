import telebot
import json
import random
import smtplib
from email.message import EmailMessage
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

TOKEN = "7807718978:AAEE4pDJSrnDHHDh8uW4mPoumCaMwBoYq_s"
bot = telebot.TeleBot(TOKEN)

# Настройки email для подтверждения
EMAIL_ADDRESS = 'pyth.pr@gmail.com'
EMAIL_PASSWORD = 'xcay plim mjky rtdd'

ITEMS_PER_PAGE = 5

# === БАЗА ДАННЫХ ===
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Состояния пользователей
user_states = {}  # {user_id: {'state': 'awaiting_email/awaiting_password/awaiting_confirmation', 'email': '', 'password': ''}}
pending_confirmations = {}  # {user_id: {'email': '', 'password': '', 'code': ''}}

# === ОТПРАВКА EMAIL ===
def send_confirmation_email(email, code):
    msg = EmailMessage()
    msg['Subject'] = 'Код подтверждения регистрации'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    
    msg.set_content(
        f"Ваш код подтверждения: {code}\n\n"
        "Введите этот код в боте для завершения регистрации."
    )
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# === ГЛАВНОЕ МЕНЮ ===
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Список олимпиад", "Мои подписки")
    kb.row("Подписаться", "⚙Настройки")
    kb.row("Помощь")
    return kb

# === КОМАНДА START ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    users = load_json("users.json")
    
    if user_id in users:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы!", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Добро пожаловать! Для использования бота необходимо зарегистрироваться.")
        bot.send_message(message.chat.id, "Введите ваш email:")
        user_states[user_id] = {'state': 'awaiting_email'}

# === ОБРАБОТКА EMAIL ===
@bot.message_handler(func=lambda message: str(message.chat.id) in user_states and user_states[str(message.chat.id)]['state'] == 'awaiting_email')
def handle_email(message):
    user_id = str(message.chat.id)
    email = message.text.strip()
    
    if '@' not in email or '.' not in email:
        bot.send_message(message.chat.id, "Неверный формат email. Попробуйте еще раз:")
        return
    
    user_states[user_id] = {
        'state': 'awaiting_password',
        'email': email
    }
    bot.send_message(message.chat.id, "Теперь придумайте и введите пароль (минимум 6 символов):")

# === ОБРАБОТКА ПАРОЛЯ ===
@bot.message_handler(func=lambda message: str(message.chat.id) in user_states and user_states[str(message.chat.id)]['state'] == 'awaiting_password')
def handle_password(message):
    user_id = str(message.chat.id)
    password = message.text.strip()
    
    if len(password) < 6:
        bot.send_message(message.chat.id, "Пароль слишком короткий (минимум 6 символов). Попробуйте еще раз:")
        return
    
    email = user_states[user_id]['email']
    confirmation_code = str(random.randint(100000, 999999))
    
    pending_confirmations[user_id] = {
        'email': email,
        'password': password,
        'code': confirmation_code
    }
    
    try:
        send_confirmation_email(email, confirmation_code)
        user_states[user_id]['state'] = 'awaiting_confirmation'
        bot.send_message(message.chat.id, 
            f"Код подтверждения отправлен на {email}.\n"
            "Пожалуйста, введите полученный 6-значный код для подтверждения регистрации."
        )
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        bot.send_message(message.chat.id, "Не удалось отправить письмо. Попробуйте позже.")
        del user_states[user_id]

# === ОБРАБОТКА КОДА ПОДТВЕРЖДЕНИЯ ===
@bot.message_handler(func=lambda message: str(message.chat.id) in user_states and user_states[str(message.chat.id)]['state'] == 'awaiting_confirmation')
def handle_confirmation(message):
    user_id = str(message.chat.id)
    user_input = message.text.strip()
    
    if user_id not in pending_confirmations:
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, начните регистрацию снова с помощью /start")
        return
    
    saved_data = pending_confirmations[user_id]
    
    if user_input == saved_data['code']:
        # Сохраняем пользователя
        users = load_json("users.json")
        users[user_id] = {
            'email': saved_data['email'],
            'password': saved_data['password'],
            'subscriptions': [],
            'notify_days_before': 2,
            'last_auth': datetime.now().isoformat()
        }
        save_json(users, "users.json")
        
        # Очищаем временные данные
        del pending_confirmations[user_id]
        del user_states[user_id]
        
        bot.send_message(message.chat.id, 
            "Регистрация успешно завершена!\n"
            f"Email: {saved_data['email']}\n"
            "Теперь вы можете использовать бота.", 
            reply_markup=main_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Неверный код подтверждения. Пожалуйста, введите правильный 6-значный код:")

# === ОСТАЛЬНЫЕ ФУНКЦИИ БОТА (без изменений) ===
@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_cmd(m):
    bot.send_message(m.chat.id,
        "Доступные действия:\n"
        "Список олимпиад — просмотр\n"
        "Подписаться — выбрать из списка\n"
        "Мои подписки — список и отписка\n"
        "Настройки — напоминание"
    )

def get_olympiad_page(page, action="none"):
    olympiads = load_json("olympiads.json")
    total = len(olympiads)
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_data = olympiads[start:end]

    text = f"Олимпиады (стр. {page+1}):\n\n"
    kb = InlineKeyboardMarkup()

    for o in page_data:
        dt = datetime.fromisoformat(o["datetime"]).strftime("%d.%m.%Y %H:%M")
        text += f"{o['id']}. {o['title']} — {dt}\n"
        if action == "subscribe":
            kb.add(InlineKeyboardButton(f"Подписаться на {o['id']}", callback_data=f"sub:{o['id']}"))
        elif action == "unsubscribe":
            kb.add(InlineKeyboardButton(f"Отписаться от {o['id']}", callback_data=f"unsub:{o['id']}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("Назад", callback_data=f"page:{action}:{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton("Далее", callback_data=f"page:{action}:{page+1}"))
    if nav:
        kb.row(*nav)

    return text, kb

@bot.message_handler(func=lambda m: m.text == "📋 Список олимпиад")
def show_list(m):
    user_id = str(m.chat.id)
    users = load_json("users.json")
    
    if user_id not in users:
        bot.send_message(m.chat.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    text, kb = get_olympiad_page(0, action="none")
    bot.send_message(m.chat.id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "Подписаться")
def show_subscribe_menu(m):
    user_id = str(m.chat.id)
    users = load_json("users.json")
    
    if user_id not in users:
        bot.send_message(m.chat.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    text, kb = get_olympiad_page(0, action="subscribe")
    bot.send_message(m.chat.id, "Выберите олимпиаду для подписки:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub:"))
def handle_subscribe(call):
    user_id = str(call.from_user.id)
    users = load_json("users.json")
    
    if user_id not in users:
        bot.answer_callback_query(call.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    oid = int(call.data.split(":")[1])
    
    if oid not in users[user_id]["subscriptions"]:
        users[user_id]["subscriptions"].append(oid)
        save_json(users, "users.json")
        bot.answer_callback_query(call.id, f"Подписка на {oid} оформлена!")
    else:
        bot.answer_callback_query(call.id, "Вы уже подписаны.")

@bot.message_handler(func=lambda m: m.text == "Мои подписки")
def show_my_subs(m):
    user_id = str(m.chat.id)
    users = load_json("users.json")
    
    if user_id not in users:
        bot.send_message(m.chat.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    olympiads = load_json("olympiads.json")
    subs = users[user_id]["subscriptions"]
    
    if not subs:
        bot.send_message(m.chat.id, "У вас нет подписок.")
        return

    text = "Ваши подписки:\n\n"
    kb = InlineKeyboardMarkup()
    for o in olympiads:
        if o["id"] in subs:
            dt = datetime.fromisoformat(o["datetime"]).strftime("%d.%m.%Y %H:%M")
            text += f"{o['id']}. {o['title']} — {dt}\n"
            kb.add(InlineKeyboardButton(f"Отписаться от {o['id']}", callback_data=f"unsub:{o['id']}"))
    bot.send_message(m.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unsub:"))
def handle_unsubscribe(call):
    user_id = str(call.from_user.id)
    users = load_json("users.json")
    
    if user_id not in users:
        bot.answer_callback_query(call.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    oid = int(call.data.split(":")[1])
    
    if oid in users[user_id]["subscriptions"]:
        users[user_id]["subscriptions"].remove(oid)
        save_json(users, "users.json")
        bot.answer_callback_query(call.id, f"Подписка на {oid} удалена.")
    else:
        bot.answer_callback_query(call.id, "Вы не были подписаны.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("page:"))
def handle_page_nav(call):
    _, action, page = call.data.split(":")
    page = int(page)
    text, kb = get_olympiad_page(page, action=action)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kb
    )

@bot.message_handler(func=lambda m: m.text == "Настройки")
def show_settings_hint(m):
    bot.send_message(m.chat.id, "Введите команду: /settings <дней>\nНапример: /settings 2")

@bot.message_handler(commands=["settings"])
def handle_settings(m):
    user_id = str(m.chat.id)
    users = load_json("users.json")
    
    if user_id not in users:
        bot.send_message(m.chat.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    args = m.text.split()
    
    if len(args) != 2 or not args[1].isdigit():
        bot.send_message(m.chat.id, "Пример: /settings 2")
        return
    
    days = int(args[1])
    users[user_id]["notify_days_before"] = days
    save_json(users, "users.json")
    bot.send_message(m.chat.id, f"Уведомления за {days} дней сохранены.")

print("Бот запущен с интерактивной подпиской и регистрацией")
bot.polling()
