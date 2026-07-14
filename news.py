import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment

# ===========================
# מקורות RSS
# ===========================

sources = [

    # ---------- אורחות תורה ----------
    "https://news.google.com/rss/search?q=ישיבת+אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=אורחות&hl=he&gl=IL&ceid=IL:he",

    # ---------- רמת שלמה ----------
    "https://news.google.com/rss/search?q=רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שכונת+רמת+שלמה&hl=he&gl=IL&ceid=IL:he",

    # ---------- בית שמש ----------
    "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עיריית+בית+שמש&hl=he&gl=IL&ceid=IL:he",

    # ---------- שיכון ד' טבריה ----------
    "https://news.google.com/rss/search?q=שיכון+ד+טבריה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שיכון+ד'+טבריה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שיכון+ד&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=טבריה&hl=he&gl=IL&ceid=IL:he"
]

# ===========================
# מילות סינון
# ===========================

keywords = [

    "ישיבת אורחות תורה",
    "אורחות תורה",
   

    "ישיבת ארחות תורה",
    "ארחות תורה",
   
    
    "רמת שלמה",
    "שכונת רמת שלמה",

    "בית שמש",
    "רמת בית שמש",
    "עיריית בית שמש",

    "שיכון ד",
    "שיכון ד'",
    "טבריה"
]

items = []
seen = set()

# ===========================
# קריאת כל מקורות ה-RSS
# ===========================

for source in sources:

    feed = feedparser.parse(source)

    for item in feed.entries[:20]:

        title = item.title.strip()

        # הסרת כפילויות
        if title in seen:
            continue

        # חייב להכיל לפחות אחת מהמילים
        if not any(keyword in title for keyword in keywords):
            continue

        seen.add(title)
        items.append(title)

# אם אין חדשות - לא יוצרים קובץ
if not items:
    print("אין חדשות חדשות.")
    raise SystemExit

# מקסימום 10 ידיעות
items = items[:15]

# ===========================
# יצירת הטקסט להקראה
# ===========================

text = ""

for i, news in enumerate(items):

    text += news.strip()

    if i != len(items) - 1:
        text += "\n\nעדכון נוסף.\n\n"

# שמירת טקסט
with open("news.txt", "w", encoding="utf-8") as f:
    f.write(text)

# ===========================
# יצירת קול
# ===========================

tts = gTTS(text, lang="iw")
tts.save("news.mp3")

# ===========================
# האצת הדיבור
# ===========================

audio = AudioSegment.from_mp3("news.mp3")

audio = audio.speedup(
    playback_speed=1.25
)

# התאמה לימות המשיח
audio = audio.set_frame_rate(8000)
audio = audio.set_channels(1)

audio.export(
    "news.wav",
    format="wav"
)

# ===========================
# העלאה לימות המשיח
# ===========================

token = os.environ["YEMOT_TOKEN"]

url = "https://www.call2all.co.il/ym/api/UploadFile"

files = {
    "file": open("news.wav", "rb")
}

data = {
    "token": token,
    "path": "ivr2:/1/",
    "autoNumbering": "true",
    "convertAudio": "1"
}

response = requests.post(
    url,
    files=files,
    data=data
)

print(response.text)
