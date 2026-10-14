"""Собирает сообщения из публичных TG-каналов (t.me/s/<канал>), находит места, пишет data.json"""
import json, re, time, datetime as dt
import requests
from bs4 import BeautifulSoup

CHANNELS = ["channel_one", "channel_two"]   # <-- впишите имена каналов без @
MAX_AGE_H = 3

# (название, широта, долгота, [основы слов в нижнем регистре])
PLACES = [
 ("Київ",50.45,30.52,["київ","киев"]), ("Київщина",50.2,30.3,["київщин","київськ","киевск","киевщин"]),
 ("Волинь",50.75,25.33,["волин"]), ("Рівненщина",50.62,26.25,["рівн","ровн"]),
 ("Житомирщина",50.25,28.66,["житомир"]), ("Чернігівщина",51.5,31.3,["чернігів","чернигов"]),
 ("Сумщина",50.91,34.8,["сумщин","сумськ","сумск","суми","сумы"]), ("Харківщина",49.99,36.23,["харків","харьков"]),
 ("Полтавщина",49.59,34.55,["полтав"]), ("Черкащина",49.44,32.06,["черкас"]),
 ("Вінниччина",49.23,28.47,["вінниц","винниц"]), ("Хмельниччина",49.42,26.98,["хмельн"]),
 ("Тернопільщина",49.55,25.59,["терноп"]), ("Львівщина",49.84,24.03,["львів","львов"]),
 ("Івано-Франківщина",48.92,24.71,["івано-франк","ивано-франк"]), ("Закарпаття",48.62,22.29,["закарпат"]),
 ("Чернівеччина",48.29,25.93,["чернівц","черновц"]), ("Одещина",46.48,30.73,["одес"]),
 ("Миколаївщина",46.97,32.0,["миколаїв","николаев"]), ("Херсонщина",46.64,32.62,["херсон"]),
 ("Запоріжжя",47.84,35.14,["запоріж","запорож"]), ("Дніпропетровщина",48.46,35.05,["дніпр","днепр"]),
 ("Кіровоградщина",48.51,32.26,["кіровоград","кропивниц","кировоград"]),
 ("Донеччина",48.0,37.8,["донеч","донецьк","донецк"]), ("Луганщина",48.57,39.3,["луган"]),
 ("Крим",45.0,34.1,["крим","крым"]), ("Білорусь",53.0,28.0,["білорус","беларус","белорус"]),
]
STEMS = sorted(((s, p) for p in PLACES for s in p[3]), key=lambda x: -len(x[0]))

def find_places(text):
    low, hits = text.lower(), []
    for stem, p in STEMS:
        for m in re.finditer(re.escape(stem), low):
            a, b = m.span()
            if low[a:b].strip("#") and not any(h[0] <= a < h[1] for h in hits):
                hits.append((a, b, p))
    hits.sort()
    return hits

def parse(text):
    hits = find_places(text)
    low = text.lower()
    cut = max(low.find("курс"), low.find("напрям"))
    origin = [h for h in hits if cut < 0 or h[0] < cut]
    target = [h for h in hits if cut >= 0 and h[0] > cut]
    pt = lambda h: {"name": h[2][0], "lat": h[2][1], "lon": h[2][2]}
    return [pt(h) for h in origin], [pt(h) for h in target]

def fetch(ch):
    r = requests.get(f"https://t.me/s/{ch}", timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for w in soup.select(".tgme_widget_message"):
        t = w.select_one(".tgme_widget_message_text")
        tm = w.select_one("time")
        if not t or not tm: continue
        out.append({"id": w.get("data-post"), "ch": ch, "text": t.get_text(" ", strip=True),
                    "time": tm.get("datetime")})
    return out

def main():
    now = dt.datetime.now(dt.timezone.utc)
    items = []
    for ch in CHANNELS:
        try: msgs = fetch(ch)
        except Exception as e: print("ошибка", ch, e); continue
        for m in msgs:
            age = (now - dt.datetime.fromisoformat(m["time"])).total_seconds() / 3600
            if age > MAX_AGE_H: continue
            frm, to = parse(m["text"])
            if frm or to:
                m["from"], m["to"] = frm, to
                items.append(m)
    items.sort(key=lambda x: x["time"], reverse=True)
    json.dump({"updated": now.isoformat(), "items": items}, open("data.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("сообщений на карте:", len(items))

if __name__ == "__main__":
    main()
