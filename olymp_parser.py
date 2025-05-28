import csv, json
from datetime import datetime

def parse_csv_to_json(csv_file, json_file):
    data = []
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            date = row["Дата"]
            time = row["Время"]
            dt = datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M")
            data.append({
                "id": idx,
                "title": row["Название"],
                "datetime": dt.isoformat(),
                "url": "https://postypashki.ru"  # или парсить отдельно
            })

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Пример использования:
# parse_csv_to_json("olympiads_23-25.csv", "olympiads.json")
