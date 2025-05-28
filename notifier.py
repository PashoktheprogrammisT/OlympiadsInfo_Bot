import schedule, time
from datetime import datetime, timedelta
from utils import load_json
from telebot import TeleBot

TOKEN = "7807718978:AAEE4pDJSrnDHHDh8uW4mPoumCaMwBoYq_s"
bot = TeleBot(TOKEN)

def notify_users():
    users = load_json("users.json")
    olympiads = load_json("olympiads.json")
    today = datetime.now().date()

    for uid, info in users.items():
        days_before = info.get("notify_days_before", 2)
        targets = []

        for oid in info.get("subscriptions", []):
            for o in olympiads:
                if o["id"] == oid:
                    dt = datetime.fromisoformat(o["datetime"]).date()
                    if (dt - today).days == days_before:
                        targets.append(o)

        for o in targets:
            msg = f"🔔 Напоминание!\n{ o['title'] }\nДата: {o['datetime']}"
            try:
                bot.send_message(uid, msg)
            except:
                pass

# Планировщик
def run_scheduler():
    schedule.every().day.at("09:00").do(notify_users)
    print("Уведомления активны.")
    while True:
        schedule.run_pending()
        time.sleep(30)

# Запуск
if __name__ == "__main__":
    run_scheduler()
