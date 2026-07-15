import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment
import json
import re

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
    },

        "5": {
        "sources": [
            # חדשות כלליות
            "https://news.google.com/rss/search?q=חדשות+היום&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=חדשות+בארץ&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ישראל&hl=he&gl=IL&ceid=IL:he",
            
            # כלכלה וכסף
            "https://news.google.com/rss/search?q=כלכלה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שוק+ההון&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=מחירי+דירות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=נדלן&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=משכנתאות&hl=he&gl=IL&ceid=IL:he",

            # תחבורה ותשתיות
            "https://news.google.com/rss/search?q=תחבורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=כבישים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רכבת+ישראל&hl=he&gl=IL&ceid=IL:he",

            # מזג אוויר
            "https://news.google.com/rss/search?q=מזג+אוויר&hl=he&gl=IL&ceid=IL:he",

            # טכנולוגיה
            "https://news.google.com/rss/search?q=טכנולוגיה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בינה+מלאכותית&hl=he&gl=IL&ceid=IL:he",

            # חדשות ערים
            "https://news.google.com/rss/search?q=ירושלים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בני+ברק&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=מודיעין+עילית&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=אלעד&hl=he&gl=IL&ceid=IL:he",

            # בריאות ומדע
            "https://news.google.com/rss/search?q=בריאות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=מדע&hl=he&gl=IL&ceid=IL:he"
        ],

        "keywords": [
            "ישראל",
            "חדשות",
            "כלכלה",
            "כסף",
            "מחירים",
            "דירות",
            "נדלן",
            "בנייה",
            "תחבורה",
            "כבישים",
            "רכבת",
            "מזג",
            "טכנולוגיה",
            "ירושלים",
            "בית שמש",
            "בריאות",
            "מדע"
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

            title = re.sub(r'<.*?>', '', title)
            title = re.sub(r'[A-Za-z]+', '', title)
            title = " ".join(title.split())

            summary = ""

            if hasattr(item, "summary"):
                summary = item.summary.strip()

            # ניקוי HTML וסימנים
            summary = re.sub(r'<.*?>', '', summary)

            # הסרת מילים באנגלית
            summary = re.sub(r'[A-Za-z]+', '', summary)

            # הסרת סימנים מיותרים
            summary = re.sub(r'[<>/\[\]{}|*#@]', '', summary)

            # ניקוי רווחים כפולים
            summary = " ".join(summary.split())


            # לשלוחה 5 - כותרת + תקציר
            if folder == "5" and summary:
                news_text = title + ". " + summary
            else:
                news_text = title

            if news_text in seen:
                continue

            if title in old_news:
                continue

            if folder != "5":
                if not any(keyword in title for keyword in category["keywords"]):
                    continue

            seen.add(news_text)
            old_news.append(title)
            items.append(news_text)
            
    if not items:
        continue

    items = items[:15]

    # ===========================
    # יצירת הטקסט להקראה
    # ===========================

    # ===========================
    # שלוחה 5 - כל עדכון קובץ נפרד
    # ===========================

    if folder == "5":

        for index, news in enumerate(items[:15]):

            tts = gTTS(news.strip(), lang="iw")

            mp3_name = f"news_{folder}_{index}.mp3"
            wav_name = f"news_{folder}_{index}.wav"

            tts.save(mp3_name)

            audio = AudioSegment.from_mp3(mp3_name)

            audio = audio.speedup(
                playback_speed=1.25
            )

            audio = audio.set_frame_rate(8000)
            audio = audio.set_channels(1)

            audio.export(
                wav_name,
                format="wav"
            )


    # ===========================
    # שלוחות 1-4 - נשאר כמו שהיה
    # ===========================

    else:

        text = ""

        for i, news in enumerate(items[:15]):

            text += news.strip()

            if i != len(items[:15]) - 1:
                text += "\n\nעדכון נוסף.\n\n"


        tts = gTTS(text, lang="iw")
        tts.save(f"news_{folder}.mp3")


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


if folder == "5":

    for index in range(len(items[:15])):

        wav_name = f"news_{folder}_{index}.wav"

        files = {
            "file": open(wav_name, "rb")
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

        print(folder, index, response.text)


else:

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
