import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment
import json

# ===========================
# מקורות RSS
# ===========================

# ===========================
# קטגוריות ושלוחות
# ===========================

categories = {

    "1": {
        "sources": [
            "https://news.google.com/rss/search?q=רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שכונת+רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+ירושלים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+בניה&hl=he&gl=IL&ceid=IL:he"
        ],
        "keywords": [
            "רמת שלמה",
            "שכונת רמת שלמה"
        ]
    },


    "2": {
        "sources": [
            "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=עיריית+בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש+נדלן&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש+תחבורה&hl=he&gl=IL&ceid=IL:he"
        ],
        "keywords": [
            "בית שמש",
            "רמת בית שמש",
            "עיריית בית שמש",
            "נדלן בית שמש",
            "בנייה בבית שמש",
            "תחבורה בית שמש"
        ]
    },


    "3": {
        "sources": [
            "https://news.google.com/rss/search?q=אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ארחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ישיבת+אורחות+תורה&hl=he&gl=IL&ceid=IL:he"
        ],
        "keywords": [
            "אורחות תורה",
            "ארחות תורה",
            "ישיבת אורחות תורה"
        ]
    },


    "4": {
        "sources": [
            "https://news.google.com/rss/search?q=שיכון+ד+טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+עירייה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+נדלן&hl=he&gl=IL&ceid=IL:he"
        ],
        "keywords": [
            "שיכון ד",
            "טבריה",
            "עיריית טבריה",
            "נדלן טבריה"
        ]
    }

}
# טעינת כתבות שכבר הוקראו

try:
    with open("seen_news.json", "r", encoding="utf-8") as f:
        old_news = json.load(f)
except:
    old_news = []

for folder, category in categories.items():

    items = []
    seen = set()

    for source in category["sources"]:

        feed = feedparser.parse(source)

        for item in feed.entries[:20]:

            title = item.title.strip()

                     if title in seen:
                continue

            if title in old_news:
                continue

            if not any(keyword in title for keyword in category["keywords"]):
                continue

            seen.add(title)
            old_news.append(title)
            items.append(title)


    if not items:
        continue

    items = items[:15]

    # ===========================
    # יצירת הטקסט להקראה
    # ===========================

    text = ""

    for i, news in enumerate(items[:15]):

        text += news.strip()

        if i != len(items[:15]) - 1:
            text += "\n\nעדכון נוסף.\n\n"


    # יצירת קול

    tts = gTTS(text, lang="iw")
    tts.save(f"news_{folder}.mp3")


    # האצת הדיבור

    audio = AudioSegment.from_mp3(f"news_{folder}.mp3")

    audio = audio.speedup(
        playback_speed=1.25
    )

    audio = audio.set_frame_rate(8000)
    audio = audio.set_channels(1)

    audio.export(
        f"news_{folder}.wav",
        format="wav"
    )


    # העלאה לימות המשיח

    token = os.environ["YEMOT_TOKEN"]

    url = "https://www.call2all.co.il/ym/api/UploadFile"

    files = {
        "file": open(f"news_{folder}.wav", "rb")
    }

    data = {
        "token": token,
        "path": f"ivr2:/{folder}/",
        "autoNumbering": "true",
        "convertAudio": "1"
    }

    response = requests.post(
        url,
        files=files,
        data=data
    )

    print(folder, response.text)

with open("seen_news.json", "w", encoding="utf-8") as f:
    json.dump(old_news[-200:], f, ensure_ascii=False, indent=2)
