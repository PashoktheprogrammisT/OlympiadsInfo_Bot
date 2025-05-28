import random
import smtplib
from email.message import EmailMessage
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, timedelta

TELEGRAM_TOKEN = '7947643363:AAF146O9Ne0diJk1ihK2A8mYM_9wl0_KHOI'
EMAIL_ADDRESS = 'pyth.pr@gmail.com'
EMAIL_PASSWORD = 'xcay plim mjky rtdd'

# База данных
user_data = {}  # Временные данные для регистрации
registered_users = {}  # Зарегистрированные пользователи {chat_id: {email, password, last_auth}}
pending_confirmations = {}  # Ожидающие подтверждения {chat_id: email, password, code}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id in registered_users:
        await update.message.reply_text(
            "Вы уже зарегистрированы!\n"
            f"Email: {registered_users[chat_id]['email']}\n"
            "Используйте /auth для повторной аутентификации."
        )
    else:
        await update.message.reply_text(
            "Привет! Я бот для регистрации.\n"
            "Для регистрации введите команду /register"
        )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id in registered_users:
        await update.message.reply_text("Вы уже зарегистрированы!")
        return
    
    await update.message.reply_text("Введите ваш email для регистрации:")
    user_data[chat_id] = {'step': 'awaiting_email'}

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    email = update.message.text.strip()
    
    if chat_id not in user_data or user_data[chat_id]['step'] != 'awaiting_email':
        await update.message.reply_text("Пожалуйста, начните регистрацию с помощью /register")
        return
    
    if '@' not in email or '.' not in email:
        await update.message.reply_text("Неверный формат email. Попробуйте еще раз:")
        return
    
    user_data[chat_id] = {
        'email': email,
        'step': 'awaiting_password'
    }
    await update.message.reply_text("Теперь придумайте и введите пароль (минимум 6 символов):")

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    password = update.message.text.strip()
    
    if chat_id not in user_data or user_data[chat_id]['step'] != 'awaiting_password':
        await update.message.reply_text("Пожалуйста, начните регистрацию с помощью /register")
        return
    
    if len(password) < 6:
        await update.message.reply_text("Пароль слишком короткий (минимум 6 символов). Попробуйте еще раз:")
        return
    
    email = user_data[chat_id]['email']
    confirmation_code = str(random.randint(100000, 999999))
    
    pending_confirmations[chat_id] = {
        'email': email,
        'password': password,
        'code': confirmation_code
    }
    
    try:
        await send_confirmation_email(email, confirmation_code)
        await update.message.reply_text(
            f"Код подтверждения отправлен на {email}.\n"
            "Пожалуйста, введите полученный 6-значный код для подтверждения регистрации."
        )
        user_data[chat_id]['step'] = 'awaiting_confirmation'
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        await update.message.reply_text("Не удалось отправить письмо. Попробуйте позже.")
        del user_data[chat_id]

async def send_confirmation_email(email: str, code: str) -> None:
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

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_input = update.message.text.strip()
    
    if chat_id not in pending_confirmations:
        await update.message.reply_text("Пожалуйста, начните регистрацию с помощью /register")
        return
    
    if chat_id not in user_data or user_data[chat_id]['step'] != 'awaiting_confirmation':
        await update.message.reply_text("Пожалуйста, введите код подтверждения, который был отправлен на ваш email.")
        return
    
    saved_data = pending_confirmations[chat_id]
    
    if user_input == saved_data['code']:
        registered_users[chat_id] = {
            'email': saved_data['email'],
            'password': saved_data['password'],
            'last_auth': datetime.now()
        }
        del pending_confirmations[chat_id]
        del user_data[chat_id]
        await update.message.reply_text(
            "✅ Регистрация успешно завершена!\n"
            f"Email: {saved_data['email']}\n"
            "Теперь вы можете использовать бота. Раз в неделю нужно будет проходить аутентификацию."
        )
    else:
        await update.message.reply_text("❌ Неверный код подтверждения. Пожалуйста, введите правильный 6-значный код:")

async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    
    if chat_id not in registered_users:
        await update.message.reply_text("Вы не зарегистрированы. Используйте /register")
        return
    
    last_auth = registered_users[chat_id]['last_auth']
    if datetime.now() - last_auth < timedelta(days=7):
        await update.message.reply_text("Ваша аутентификация еще активна.")
        return
    
    await update.message.reply_text("Требуется повторная аутентификация. Введите ваш пароль:")
    user_data[chat_id] = {'step': 'awaiting_auth'}

async def handle_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    
    if chat_id not in user_data or user_data[chat_id]['step'] != 'awaiting_auth':
        await update.message.reply_text("Пожалуйста, начните аутентификацию с помощью /auth")
        return
    
    password = update.message.text.strip()
    
    if password == registered_users[chat_id]['password']:
        registered_users[chat_id]['last_auth'] = datetime.now()
        await update.message.reply_text("✅ Аутентификация успешна! Теперь вы можете использовать бота.")
        del user_data[chat_id]
    else:
        await update.message.reply_text("❌ Неверный пароль. Попробуйте еще раз:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    
    # Если пользователь в процессе регистрации
    if chat_id in user_data:
        if user_data[chat_id]['step'] == 'awaiting_email':
            await handle_email(update, context)
        elif user_data[chat_id]['step'] == 'awaiting_password':
            await handle_password(update, context)
        elif user_data[chat_id]['step'] == 'awaiting_confirmation':
            await handle_confirmation(update, context)
        elif user_data[chat_id]['step'] == 'awaiting_auth':
            await handle_auth(update, context)
        return
    
    # Если есть ожидающие подтверждения
    if chat_id in pending_confirmations:
        await handle_confirmation(update, context)
        return
    
    # Если пользователь зарегистрирован
    if chat_id in registered_users:
        last_auth = registered_users[chat_id]['last_auth']
        if datetime.now() - last_auth >= timedelta(days=7):
            await update.message.reply_text("Требуется повторная аутентификация. Используйте /auth")
        else:
            await update.message.reply_text(
                "Вы успешно аутентифицированы.\n"
                f"Email: {registered_users[chat_id]['email']}\n"
                f"Последняя аутентификация: {last_auth.strftime('%Y-%m-%d %H:%M')}"
            )
        return
    
    # Если новый пользователь
    await update.message.reply_text("Привет! Для начала работы зарегистрируйтесь с помощью /register")

def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("auth", auth))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
