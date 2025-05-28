import telebot
import json
import random
import re
import smtplib
from email.message import EmailMessage
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
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
user_states = {}  # {user_id: {'state': 'awaiting_email/phone/password/confirmation', ...}}
pending_confirmations = {}  # {user_id: {'email': '', 'phone': '', 'password': '', 'code': ''}}

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
    kb.row("📋 Список олимпиад", "📌 Мои подписки")
    kb.row("🔔 Подписаться", "⚙️ Настройки")
    kb.row("❓ Помощь")
    return kb

# === ПРОВЕРКА РЕГИСТРАЦИИ ===
def is_registered(user_id):
    users = load_json("users.json")
    return user_id in users and (users[user_id].get('email') or users[user_id].get('phone'))

# === МЕНЮ ВХОДА/РЕГИСТРАЦИИ ===
def auth_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📱 Войти по номеру", "📧 Войти по email")
    kb.row("📝 Зарегистрироваться")
    return kb

# === ПОИСК ПОЛЬЗОВАТЕЛЯ ===
def find_user_by_phone(phone):
    users = load_json("users.json")
    for user_id, user_data in users.items():
        if user_data.get('phone') == phone:
            return user_id, user_data
    return None, None

def find_user_by_email(email):
    users = load_json("users.json")
    for user_id, user_data in users.items():
        if user_data.get('email') == email:
            return user_id, user_data
    return None, None

# === ВАЛИДАЦИЯ НОМЕРА ТЕЛЕФОНА ===
def is_valid_phone(phone):
    # Простая проверка формата номера (можно доработать)
    return re.match(r'^\+?\d{10,15}$', phone) is not None

# === КОМАНДА START ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    
    if is_registered(user_id):
        bot.send_message(message.chat.id, "Вы уже вошли в систему!", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, 
            "Добро пожаловать! Выберите способ входа или регистрации:",
            reply_markup=auth_menu()
        )

# === ОБРАБОТКА КНОПКИ РЕГИСТРАЦИИ ===
@bot.message_handler(func=lambda m: m.text == "📝 Зарегистрироваться")
def handle_register_button(message):
    user_id = str(message.chat.id)
    
    if is_registered(user_id):
        bot.send_message(message.chat.id, "Вы уже зарегистрированы!", reply_markup=main_menu())
    else:
        # Предлагаем выбрать способ регистрации
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("📧 Регистрация по email", "📱 Регистрация по телефону")
        bot.send_message(message.chat.id, "Выберите способ регистрации:", reply_markup=kb)

# === ОБРАБОТКА ВЫБОРА СПОСОБА РЕГИСТРАЦИИ ===
@bot.message_handler(func=lambda m: m.text in ["📧 Регистрация по email", "📱 Регистрация по телефону"])
def handle_register_method(message):
    user_id = str(message.chat.id)
    
    if message.text == "📧 Регистрация по email":
        bot.send_message(message.chat.id, "Введите ваш email для регистрации:", reply_markup=ReplyKeyboardRemove())
        user_states[user_id] = {'state': 'awaiting_email', 'action': 'register'}
    else:
        bot.send_message(message.chat.id, "Введите ваш номер телефона в формате +79991234567:", reply_markup=ReplyKeyboardRemove())
        user_states[user_id] = {'state': 'awaiting_phone', 'action': 'register'}

# === ОБРАБОТКА КНОПОК ВХОДА ===
@bot.message_handler(func=lambda m: m.text in ["📱 Войти по номеру", "📧 Войти по email"])
def handle_login_method(message):
    user_id = str(message.chat.id)
    
    if is_registered(user_id):
        bot.send_message(message.chat.id, "Вы уже вошли в систему!", reply_markup=main_menu())
    else:
        if message.text == "📱 Войти по номеру":
            bot.send_message(message.chat.id, "Введите ваш номер телефона:", reply_markup=ReplyKeyboardRemove())
            user_states[user_id] = {'state': 'awaiting_phone', 'action': 'login'}
        else:
            bot.send_message(message.chat.id, "Введите ваш email:", reply_markup=ReplyKeyboardRemove())
            user_states[user_id] = {'state': 'awaiting_email', 'action': 'login'}

# === ОБРАБОТКА НОМЕРА ТЕЛЕФОНА ===
@bot.message_handler(func=lambda message: str(message.chat.id) in user_states and 
                     user_states[str(message.chat.id)]['state'] == 'awaiting_phone')
def handle_phone(message):
    user_id = str(message.chat.id)
    phone = message.text.strip()
    action = user_states[user_id]['action']
    
    if not is_valid_phone(phone):
        bot.send_message(message.chat.id, "Неверный формат номера. Пожалуйста, введите номер в формате +79991234567:")
        return
    
    if action == 'register':
        # Проверка что номер не занят
        found_user_id, _ = find_user_by_phone(phone)
        if found_user_id:
            bot.send_message(message.chat.id, "Этот номер уже зарегистрирован. Попробуйте войти.")
            del user_states[user_id]
            return
        
        user_states[user_id] = {
            'state': 'awaiting_password',
            'action': 'register',
            'phone': phone
        }
        bot.send_message(message.chat.id, "Теперь придумайте и введите пароль (минимум 6 символов):")
    
    elif action == 'login':
        found_user_id, user_data = find_user_by_phone(phone)
        if not found_user_id:
            bot.send_message(message.chat.id, "Пользователь с таким номером не найден.")
            del user_states[user_id]
            return
        
        user_states[user_id] = {
            'state': 'awaiting_password',
            'action': 'login',
            'phone': phone,
            'target_user_id': found_user_id
        }
        bot.send_message(message.chat.id, "Введите ваш пароль:")

# === ОБНОВЛЕННАЯ ОБРАБОТКА EMAIL ===
@bot.message_handler(func=lambda message: str(message.chat.id) in user_states and 
                     user_states[str(message.chat.id)]['state'] == 'awaiting_email')
def handle_email(message):
    user_id = str(message.chat.id)
    email = message.text.strip()
    action = user_states[user_id]['action']
    
    if '@' not in email or '.' not in email:
        bot.send_message(message.chat.id, "Неверный формат email. Попробуйте еще раз:")
        return
    
    if action == 'register':
        # Проверка что email не занят
        found_user_id, _ = find_user_by_email(email)
        if found_user_id:
            bot.send_message(message.chat.id, "Этот email уже зарегистрирован. Попробуйте войти.")
            del user_states[user_id]
            return
        
        user_states[user_id] = {
            'state': 'awaiting_password',
            'action': 'register',
            'email': email
        }
        bot.send_message(message.chat.id, "Теперь придумайте и введите пароль (минимум 6 символов):")
    
    elif action == 'login':
        found_user_id, user_data = find_user_by_email(email)
        if not found_user_id:
            bot.send_message(message.chat.id, "Пользователь с таким email не найден.")
            del user_states[user_id]
            return
        
        user_states[user_id] = {
            'state': 'awaiting_password',
            'action': 'login',
            'email': email,
            'target_user_id': found_user_id
        }
        bot.send_message(message.chat.id, "Введите ваш пароль:")

# === ОБНОВЛЕННАЯ ОБРАБОТКА ПАРОЛЯ ===
@bot.message_handler(func=lambda message: str(message.chat.id) in user_states and 
                     user_states[str(message.chat.id)]['state'] == 'awaiting_password')
def handle_password(message):
    user_id = str(message.chat.id)
    password = message.text.strip()
    action = user_states[user_id]['action']
    
    if action == 'register':
        if len(password) < 6:
            bot.send_message(message.chat.id, "Пароль слишком короткий (минимум 6 символов). Попробуйте еще раз:")
            return
        
        # Определяем тип регистрации (по email или телефону)
        if 'email' in user_states[user_id]:
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
        
        elif 'phone' in user_states[user_id]:
            # Для телефона просто сохраняем данные без подтверждения по email
            phone = user_states[user_id]['phone']
            
            users = load_json("users.json")
            users[user_id] = {
                'phone': phone,
                'password': password,
                'subscriptions': [],
                'notify_days_before': 2,
                'last_auth': datetime.now().isoformat()
            }
            save_json(users, "users.json")
            
            del user_states[user_id]
            bot.send_message(message.chat.id, 
                "✅ Регистрация по номеру телефона завершена!\n"
                f"Номер: {phone}\n"
                "Теперь вы можете использовать бота.", 
                reply_markup=main_menu()
            )
    
    elif action == 'login':
        target_user_id = user_states[user_id]['target_user_id']
        users = load_json("users.json")
        
        if users[target_user_id]['password'] == password:
            # Обновляем текущего пользователя
            users[user_id] = users[target_user_id].copy()
            users[user_id]['last_auth'] = datetime.now().isoformat()
            save_json(users, "users.json")
            
            del user_states[user_id]
            bot.send_message(message.chat.id, "✅ Вход выполнен успешно!", reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, "❌ Неверный пароль. Попробуйте еще раз:")

# === ОБРАБОТКА КОДА ПОДТВЕРЖДЕНИЯ ===
@bot.message_handler(func=lambda message: str(message.chat.id) in user_states and 
                     user_states[str(message.chat.id)]['state'] == 'awaiting_confirmation')
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
            "✅ Регистрация успешно завершена!\n"
            f"Email: {saved_data['email']}\n"
            "Теперь вы можете использовать бота.", 
            reply_markup=main_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Неверный код подтверждения. Пожалуйста, введите правильный 6-значный код:")

# === ОСНОВНЫЕ ФУНКЦИИ БОТА ===
def check_auth(message):
    user_id = str(message.chat.id)
    if not is_registered(user_id):
        bot.send_message(message.chat.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return False
    return True

@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_cmd(m):
    if not check_auth(m): return
    bot.send_message(m.chat.id,
        "Доступные действия:\n"
        "📋 Список олимпиад — просмотр\n"
        "🔔 Подписаться — выбрать из списка\n"
        "📌 Мои подписки — список и отписка\n"
        "⚙️ Настройки — напоминание"
    )

def get_olympiad_page(page, action="none"):
    olympiads = load_json("olympiads.json")
    total = len(olympiads)
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_data = olympiads[start:end]

    text = f"📋 Олимпиады (стр. {page+1}):\n\n"
    kb = InlineKeyboardMarkup()

    for o in page_data:
        dt = datetime.fromisoformat(o["datetime"]).strftime("%d.%m.%Y %H:%M")
        text += f"{o['id']}. {o['title']} — {dt}\n"
        if action == "subscribe":
            kb.add(InlineKeyboardButton(f"✅ Подписаться на {o['id']}", callback_data=f"sub:{o['id']}"))
        elif action == "unsubscribe":
            kb.add(InlineKeyboardButton(f"❌ Отписаться от {o['id']}", callback_data=f"unsub:{o['id']}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page:{action}:{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton("➡️ Далее", callback_data=f"page:{action}:{page+1}"))
    if nav:
        kb.row(*nav)

    return text, kb

@bot.message_handler(func=lambda m: m.text == "📋 Список олимпиад")
def show_list(m):
    if not check_auth(m): return
    text, kb = get_olympiad_page(0, action="none")
    bot.send_message(m.chat.id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🔔 Подписаться")
def show_subscribe_menu(m):
    if not check_auth(m): return
    text, kb = get_olympiad_page(0, action="subscribe")
    bot.send_message(m.chat.id, "Выберите олимпиаду для подписки:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub:"))
def handle_subscribe(call):
    user_id = str(call.from_user.id)
    if not is_registered(user_id):
        bot.answer_callback_query(call.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    oid = int(call.data.split(":")[1])
    users = load_json("users.json")
    
    if oid not in users[user_id]["subscriptions"]:
        users[user_id]["subscriptions"].append(oid)
        save_json(users, "users.json")
        bot.answer_callback_query(call.id, f"✅ Подписка на {oid} оформлена!")
    else:
        bot.answer_callback_query(call.id, "Вы уже подписаны.")

@bot.message_handler(func=lambda m: m.text == "📌 Мои подписки")
def show_my_subs(m):
    if not check_auth(m): return
    
    user_id = str(m.chat.id)
    users = load_json("users.json")
    olympiads = load_json("olympiads.json")
    subs = users[user_id]["subscriptions"]
    
    if not subs:
        bot.send_message(m.chat.id, "У вас нет подписок.")
        return

    text = "📌 Ваши подписки:\n\n"
    kb = InlineKeyboardMarkup()
    for o in olympiads:
        if o["id"] in subs:
            dt = datetime.fromisoformat(o["datetime"]).strftime("%d.%m.%Y %H:%M")
            text += f"{o['id']}. {o['title']} — {dt}\n"
            kb.add(InlineKeyboardButton(f"❌ Отписаться от {o['id']}", callback_data=f"unsub:{o['id']}"))
    bot.send_message(m.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unsub:"))
def handle_unsubscribe(call):
    user_id = str(call.from_user.id)
    if not is_registered(user_id):
        bot.answer_callback_query(call.id, "Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    oid = int(call.data.split(":")[1])
    users = load_json("users.json")
    
    if oid in users[user_id]["subscriptions"]:
        users[user_id]["subscriptions"].remove(oid)
        save_json(users, "users.json")
        bot.answer_callback_query(call.id, f"❌ Подписка на {oid} удалена.")
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

@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def show_settings_hint(m):
    if not check_auth(m): return
    bot.send_message(m.chat.id, "Введите команду: /settings <дней>\nНапример: /settings 2")

@bot.message_handler(commands=["settings"])
def handle_settings(m):
    if not check_auth(m): return
    
    user_id = str(m.chat.id)
    users = load_json("users.json")
    args = m.text.split()
    
    if len(args) != 2 or not args[1].isdigit():
        bot.send_message(m.chat.id, "Пример: /settings 2")
        return
    
    days = int(args[1])
    users[user_id]["notify_days_before"] = days
    save_json(users, "users.json")
    bot.send_message(m.chat.id, f"🔔 Уведомления за {days} дней сохранены.")

print("✅ Бот запущен с поддержкой входа по номеру телефона и email")
bot.polling()
