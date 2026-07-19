import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment
import json
import re
from datetime import datetime, timezone

# ===========================
# קטגוריות ושלוחות מורחבות (מתעדכן כל כמה דקות)
# ===========================

categories = {
    "5": {
        "sources": [
            "https://news.google.com/rss/search?q=רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שכונת+רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+ירושלים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+בניה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+דירות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+עירייה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+תחבורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+כבישים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+קהילה&hl=he&gl=IL&ceid=IL:he"
        ]
    },

    "2": {
        "sources": [
            "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=עיריית+בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש+חדשות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש+נדלן&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש+בניה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש+תחבורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש+כבישים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמה+ד+בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמה+ה+בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+בית+שמש+ג&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=פתרונות+דיור+בית+שמש&hl=he&gl=IL&ceid=IL:he"
        ]
    },

    "3": {
        "sources": [
            "https://news.google.com/rss/search?q=אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ארחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ישיבת+אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=אורחות+תורה+בני+ברק&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ראש+ישיבת+אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בוגרי+אורחות+תורה&hl=he&gl=IL&ceid=IL:he"
        ]
    },

    "4": {
        "sources": [
            "https://news.google.com/rss/search?q=טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שיכון+ד+טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=עיריית+טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+חדשות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+נדלן&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+בניה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+תחבורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+כבישים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+התפתחות&hl=he&gl=IL&ceid=IL:he"
        ]
    },

    "1": {
        "sources": [
            "https://news.google.com/rss/search?q=חדשות+היום&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=חדשות+בארץ&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ישראל&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=כלכלה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=מחירי+דירות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=נדלן&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=משכנתאות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=תחבורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=כבישים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רכבת+ישראל&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=מזג+אוויר&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טכנולוגיה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בינה+מלאכותית&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ירושלים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בני+ברק&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בריאות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=מדע&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=פיתוח+עירוני&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=תשתיות+ישראל&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בנק+ישראל&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רכבת+קלה&hl=he&gl=IL&ceid=IL:he"
        ]
    }
}

# טעינת כתבות ותכנים שכבר הוקראו בעבר
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
            if hasattr(item, "published_parsed"):
                published = datetime(
                    *item.published_parsed[:6],
                    tzinfo=timezone.utc
                )
                age = datetime.now(timezone.utc) - published
                if age.days > 2:
                    continue

            # ניקוי וסינון כותרת הכתבה
            title = item.title.strip()
            title = re.sub(r'<.*?>', '', title)
            title = re.sub(r'[A-Za-z]+', '', title)
            title = " ".join(title.split())
            title = re.sub(r'[.,;:"\'()\-%–—-]', '', title)

            summary = ""
            if hasattr(item, "summary"):
                summary = item.summary.strip()

            summary = re.sub(r'<.*?>', '', summary)

            # הסרת שמות אתרי מדיה נפוצים
            summary = re.sub(
                r'(ynet|וואלה|מעריב|ישראל היום|כאן חדשות|חדשות 12|חדשות 13|N12)',
                '',
                summary,
                flags=re.IGNORECASE
            )

            summary = re.sub(r'[A-Za-z]+', '', summary)
            summary = re.sub(r'[<>/\[\]{}|*#@]', '', summary)
            summary = re.sub(r'[.,;:"\'()\-%–—-]', '', summary)
            summary = re.sub(r'[^\u0590-\u05FF0-9., ]', ' ', summary)
            summary = " ".join(summary.split())

            title_compare = re.sub(r'\s+', '', title)
            summary_compare = re.sub(r'\s+', '', summary)

            if summary_compare.startswith(title_compare):
                summary = summary[len(title):].lstrip(" .,:-–—")

            summary = " ".join(summary.split())
            summary = summary.lstrip(" .,-–—:")
            summary = summary[:350]

            if not summary or len(summary) < 20:
                continue

            # --- שיפור: הסרת המילה "חדשות" מתוכן ההקראה ---
            summary = re.sub(r'\bחדשות\b', '', summary).strip()
            summary = " ".join(summary.split())  # ניקוי רווחים כפולים שנוצרו מהמחיקה

            news_text = summary

            # מפתח ייחודי למניעת כפילויות של דיווחים זהים באתרי RSS שונים
            normalized_compare = re.sub(r'\s+', '', news_text)

            if news_text in seen:
                continue
            if title in old_news or normalized_compare in old_news:
                continue

            seen.add(news_text)
            old_news.append(title)
            old_news.append(normalized_compare)  # שמירת המזהה הייחודי למניעת חזרות בעתיד
            items.append(news_text)  

    if not items:
        continue

    items = items[:15]

    # ===========================
    # יצירת הטקסט להקראה והמרה ל-WAV
    # ===========================
    if folder in ["1", "2", "3", "4", "5"]:
        for index, news in enumerate(items[:15]):
            tts = gTTS(news.strip(), lang="iw")

            mp3_name = f"news_{folder}_{index}.mp3"
            wav_name = f"news_{folder}_{index}.wav"

            tts.save(mp3_name)

            audio = AudioSegment.from_mp3(mp3_name)
            audio = audio.speedup(playback_speed=1.25)
            audio = audio.set_frame_rate(8000)
            audio = audio.set_channels(1)
            audio.export(wav_name, format="wav")

    else:
        text = ""
        for i, news in enumerate(items[:15]):
            text += news.strip()
            if i != len(items[:15]) - 1:
                text += "\n\nעדכון נוסף.\n\n"

        tts = gTTS(text, lang="iw")
        tts.save(f"news_{folder}.mp3")

        audio = AudioSegment.from_mp3(f"news_{folder}.mp3")
        audio = audio.speedup(playback_speed=1.25)
        audio = audio.set_frame_rate(8000)
        audio = audio.set_channels(1)
        audio.export(f"news_{folder}.wav", format="wav")

    # ===========================
    # העלאה למערכות ימות המשיח
    # ===========================
    token = os.environ["YEMOT_TOKEN"]
    url = "https://www.call2all.co.il/ym/api/UploadFile"

    if folder in ["1", "2", "3", "4", "5"]:
        list_url = "https://www.call2all.co.il/ym/api/GetIVR2Dir"
        list_data = {
            "token": token,
            "path": f"ivr2:/{folder}/"
        }

        result = requests.post(list_url, data=list_data).json()
        max_number = 0

        if "files" in result:
            for file in result["files"]:
                name = file.get("name", "")
                number = re.findall(r'\d+', name)
                if number:
                    max_number = max(max_number, int(number[0]))

        for index, wav_name in enumerate(
            [f"news_{folder}_{i}.wav" for i in range(len(items[:15]))],
            start=1
        ):
            new_number = str(max_number + index).zfill(3)
            files = {"file": open(wav_name, "rb")}
            data = {
                "token": token,
                "path": f"ivr2:/{folder}/{new_number}.wav",
                "convertAudio": "1"
            }
            response = requests.post(url, files=files, data=data)
            print(folder, new_number, response.text)

    else:
        files = {"file": open(f"news_{folder}.wav", "rb")}
        data = {
            "token": token,
            "path": f"ivr2:/{folder}/",
            "autoNumbering": "true",
            "convertAudio": "1"
        }
        response = requests.post(url, files=files, data=data)
        print(folder, response.text)

# שמירת רשימת הכתבות העדכנית למניעת חזרות בריצות הבאות
with open("seen_news.json", "w", encoding="utf-8") as f:
    json.dump(
        old_news[-500:],  # הגדלת הזיכרון ל-500 פריטים כדי להכיל את כמות המקורות החדשה
        f,
        ensure_ascii=False,
        indent=2
    )
