from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import json, pathlib, time


CHROME_PATH  = r"C:/Users/User/OneDrive/Рабочий стол/OLIMBOT/chrome/chrome.exe"
DRIVER_PATH  = r"chromedriver.exe"

YEARS  = [2023, 2024, 2025]
MONTHS = range(1, 13)
BASE   = "https://postypashki.ru/ecwd_calendar/calendar/?date={y}-{m}-1&t=list"
OUT_JSON = "olympiads.json"


opt = webdriver.ChromeOptions()
opt.binary_location = CHROME_PATH
opt.add_experimental_option("detach", True)
service = Service(DRIVER_PATH)
driver  = webdriver.Chrome(service=service, options=opt)
wait    = WebDriverWait(driver, 15)

def grab_events():
    titles = driver.find_elements(By.CSS_SELECTOR, "h3.event-title a")
    dates  = driver.find_elements(By.CSS_SELECTOR, ".ecwd-date .metainfo")
    times  = driver.find_elements(By.CSS_SELECTOR, ".ecwd-time .metainfo")
    return [
        (t.text.strip(), d.text.strip(), tm.text.strip())
        for t, d, tm in zip(titles, dates, times)
    ]

data = []
id_counter = 1

def extract_first_part(text: str) -> str:
    return text.split("-")[0].strip().split("–")[0].strip()

try:
    for y in YEARS:
        for m in MONTHS:
            url = BASE.format(y=y, m=m)
            driver.get(url)

            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ecwd-page-full")
                ))
            except:
                print(f"⚠️  {y}-{m:02}: страница не открылась.")
                continue

            time.sleep(1.5)
            month_events = grab_events()
            if month_events:
                print(f"✅  {y}-{m:02}: {len(month_events)} шт.")
                for title, date_str, time_str in month_events:
                    try:
                        clean_date = extract_first_part(date_str)
                        clean_time = extract_first_part(time_str)

                        dt = datetime.strptime(f"{clean_date} {clean_time}", "%d.%m.%Y %H:%M")

                        data.append({
                            "id": id_counter,
                            "title": title,
                            "datetime": dt.isoformat(),
                            "url": "https://postypashki.ru"
                        })
                        id_counter += 1
                    except Exception as e:
                        print(f"❌ Проблема с датой: {title} — {date_str} {time_str}")
                        continue
            else:
                print(f"—  {y}-{m:02}: пусто")

    if data:
        out = pathlib.Path(__file__).with_name(OUT_JSON)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Готово! Сохранено {len(data)} олимпиад → {OUT_JSON}")
    else:
        print("❌ Ничего не найдено.")

finally:
    pass
