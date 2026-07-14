import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment

sources = [
    "https://news.google.com/rss/search?q=בית+שמש+נדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+כלכלה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+עירייה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+פרויקטים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+תחבורה&hl=he&gl=IL&ceid=IL:he"
]

location_keywords = [
    "בית שמש",
    "רמת בית שמש",
    "בית-שמש"
]

topic_keywords = [
    "נדלן",
    "נדל״ן",
    "דירה",
    "דירות",
    "מחיר",
    "מחירים",
    "שכירות",
    "השכרה",
    "מכירה",
    "פרויקט",
    "פרויקטים",
    "בנייה",
    "בניה",
    "קרקע",
    "מכרז",
    "תשתיות",
    "כביש",
    "כבישים",
    "תחבורה",
    "רכבת",
    "אוטובוס",
    "תחנה",
    "פקקים",
    "עירייה",
    "עסקים",
    "מסחר",
    "תעסוקה"
]

items = []
seen = set()

for source in sources:
    feed = feedparser.parse(source)

    for item in feed.entries[:10]:
        title = item.title.strip()

        if (
            title not in seen
            and any(word in title for word in location_keywords)
            and any(word in title for word in topic_keywords)
        ):
            items.append(title)
            seen.add(title)

# אם אין חדשות - לא עושים כלום
if not items:
    print("אין חדשות חדשות - לא נוצר קובץ ולא הועלה דבר.")
    raise SystemExit

text = ""

for i, news in enumerate(items[:5], 1):
    text += news + "\n"

    if i < len(items[:5]):
        text += "\nעדכון נוסף.\n\n"

with open("news.txt", "w", encoding="utf-8") as f:
    f.write(text)

# יצירת קול
tts = gTTS(text, lang="iw")
tts.save("news.mp3")

# האצה והתאמה לימות המשיח
audio = AudioSegment.from_mp3("news.mp3")
audio = audio.speedup(playback_speed=1.25)
audio = audio.set_frame_rate(8000)
audio = audio.set_channels(1)
audio.export("001.wav", format="wav")

# העלאה לימות המשיח
token = os.environ["YEMOT_TOKEN"]

url = "https://www.call2all.co.il/ym/api/UploadFile"

files = {
    "file": open("001.wav", "rb")
}

data = {
    "token": token,
    "path": "ivr2:/1/",
    "autoNumbering": "true",
    "convertAudio": "1"
}

response = requests.post(url, files=files, data=data)

print(response.text)
