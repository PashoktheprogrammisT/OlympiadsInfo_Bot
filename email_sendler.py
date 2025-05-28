import smtplib
import ssl
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

SENDER_EMAIL = "pyth.pr@gmail.com"
SENDER_PASSWORD = "xcay plim mjky rtdd"

def send_verification_code(email_to: str, code: str):
    msg = EmailMessage()
    msg["Subject"] = "Код подтверждения для Telegram-бота"
    msg["From"] = SENDER_EMAIL
    msg["To"] = email_to
    msg.set_content(f"Ваш код подтверждения: {code}")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
