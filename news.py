import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
import pytz

# ===========================
# הגדרות אזור זמן וזיכרון קבוע עבור Cron
# ===========================
TIMEZONE = pytz.timezone('Asia/Jerusalem')
HISTORY_FILE = 'seen_news.json'

def load_history():
    """טעינת היסטוריית הכתבות שכבר עובדו כדי למנוע כפילויות בין הרצות Cron"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history file: {e}")
            return []
    return []

def save_history(history_list):
    """שמירת ההיסטוריה לקובץ JSON"""
    try:
        # שומרים את 5000 הפריטים האחרונים למניעת חזרות לאורך זמן
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_list[-5000:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history file: {e}")

# ===========================
# מיפוי עיתונאים לציון שמם בהקראה
# ===========================
JOURNALISTS_MAP = {
    "עמית+סגל": "עמית סגל",
    "מיכאל+שמש": "מיכאל שמש",
    "יעקב+ברדוגו": "יעקב ברדוגו",
    "יאיר+שרקי": "יאיר שרקי",
    "שלמה+ריזל": "שלמה ריזל",
    "אבישי+גרינצייג": "אבישי גרינצייג",
    "מנחם+קולדצקי": "מנחם קולדצקי",
    "דורון+קדוש": "דורון קדוש",
    "יוסי+יהושוע": "יוסי יהושוע",
    "ינון+מגל": "ינון מגל",
    "עקיבא+נוביק": "עקיבא נוביק",
    "מוטי+קסטל": "מוטי קסטל",
    "שילה+פריד": "שילה פריד",
    "אטילה+שומפלבי": "אטילה שומפלבי",
    "יקיר+מויאל": "יקיר מויאל"
}

# ===========================
# חלוקת מקורות לפי קטגוריות
# ===========================

# 1. חדשות כלליות, מבזקים ועיתונאים (ללא כלכלה ותחבורה)
sources_general = [
    "https://news.google.com/rss/search?q=חדשות+היום&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=חדשות+בארץ&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מזג+אוויר&hl=he&gl=IL&ceid=IL:he",
    "https://www.maariv.co.il/Rss/RssFeedsMivzakim",
    "https://rss.walla.co.il/feed/22", 
    "https://news.google.com/rss/search?q=עמית+סגל+ציוץ&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מיכאל+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=יעקב+ברדוגו&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=דיווח+ראשוני&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מבזק+חם&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=פרסום+ראשון&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ציוץ+או+סטטוס+או+קבוצה+או+דיווח&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=כתבים+או+פרשנים+או+עיתונאים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מבזקים+רוטר+או+חמאל+או+חדשות+מתפרצות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ברשתות+החברתיות+או+קבוצות+עדכון&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=יאיר+שרקי&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שלמה+ריזל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=אבישי+גרינצייג&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מנחם+קולדצקי&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=דורון+קדוש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=יוסי+יהושוע&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ינון+מגל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מבזק+חדשות+זמן+אמת&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=דיווחים+שוטפים+מבזקים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עדכון+מבזק+חם&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מיכאל+שמש+ציוץ&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עקיבא+נוביק&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מוטי+קסטל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שילה+פריד&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מבזק+חדשות+או+מבזקים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=דיווח+ראשוני+או+חדשות+מתפרצות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ציוצים+עיתונאים+או+כתבים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=אטילה+שומפלבי+או+יקיר+מויאל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=חדשות+רוטר+או+חמאל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מזג+האוויר+תחזית+הימים+הקרובים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עדכונים+שוטפים+או+מבזקים+בזמן+אמת&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מבזקי+חדשות+בזמן+אמת&hl=he&gl=IL&ceid=IL:he"
]

# 2. כלכלה ונדל"ן (שלוחה 3 בלבד)
sources_economy = [
    "https://news.google.com/rss/search?q=כלכלה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מחירי+דירות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=נדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=משכנתאות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בנק+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://www.ice.co.il/rss.xml",           
    "https://www.bizportal.co.il/rss/bizportalrss.xml", 
    "https://news.google.com/rss/search?q=מחירי+הדיור+או+שוק+הנדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בנק+ישראל+ריבית+משכנתא&hl=he&gl=IL&ceid=IL:he"
]

# 3. תחבורה וכבישים (שלוחה 4 בלבד)
sources_transport = [
    "https://news.google.com/rss/search?q=תחבורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=כבישים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+קלה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עומסי+תנועה+חסימות+כבישים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שינויים+בתחבורה+הציבורית&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+ישראל+לוח+זמנים+או+קווים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=משרד+התחבורה+כבישים+חדשים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=הרכבת+הקלה+בירושלים+או+בגוש+דן&hl=he&gl=IL&ceid=IL:he"
]

# 4. מקורות מקומיים (שלוחה 2)
sources_local = [
    "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עיריית+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+חדשות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+נדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמה+ד+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמה+ה+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ארחות+תורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ישיבת+אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=טבריה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שיכון+ד+טבריה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עיריית+טבריה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שכונת+רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+שלמה+ירושלים&hl=he&gl=IL&ceid=IL:he"
]

# מילות מפתח לשלוחות
keywords_folder_2 = [
    "בית שמש", "רמת בית שמש", "רמה ד", "רמה ה", "רמה ג",
    "אורחות תורה", "ארחות תורה", "טבריה", "טבריא", "שיכון ד", "רמת שלמה"
]

keywords_folder_3 = [
    "ירידת מחירים", "ירידה במחירי הדירות", "מחירי הדירות ירדו", "הוזלת דירות",
    "ירידת מחירי הנדלן", "ירידה במחירי הנדלן", "הוזלת מחירי הדיור", "הוזלה במחירי הדירות",
    "נפילת מחירי הדירות", "האטה במחירי הדיור", "הוזלת הדירות", "ירידה במחירי הדיור",
    "כלכלה", "משכנתא", "משכנתאות", "בנק ישראל", "ריבית", "נדלן", "דיור"
]

keywords_folder_4 = [
    "תחבורה", "כביש", "כבישים", "רכבת", "רכבת ישראל", "רכבת קלה",
    "פקק", "פקקים", "עומס תנועה", "עומסי תנועה", "חסימה", "חסימות", "משרד התחבורה"
]

categories = {
    "1": {
        "sources": sources_general,
        "keywords": []  # שלוחה 1: מקבלת את כל המבזקים הכלליים
    },
    "2": {
        "sources": sources_general + sources_local,
        "keywords": keywords_folder_2
    },
    "3": {
        "sources": sources_economy,
        "keywords": keywords_folder_3
    },
    "4": {
        "sources": sources_transport,
        "keywords": keywords_folder_4
    }
}

# טעינת היסטוריה מקובץ JSON
old_news = load_history()
old_news_set = set(old_news)

SHORT_DOMAINS = ["maariv.co.il", "walla.co.il"]
now_il = datetime.now(TIMEZONE)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

def clean_text_for_tts(text):
    """מנקה סימני פיסוק מיותרים ומקפים שגורמים לעצירות מיותרות בהקראה"""
    text = re.sub(r'[\"\']', '', text)               # הסרת מרכאות ובגרים
    text = re.sub(r'[\-–—]', ' ', text)              # המרת מקפים לרווח
    text = re.sub(r'[,;:]', ' ', text)               # הסרת פסיקים ונקודתיים שקוטעים משפט
    text = re.sub(r'[\(\)\[\]\{\}]', '', text)       # הסרת סוגריים
    text = re.sub(r'\s+', ' ', text).strip()         # ניקוי רווחים כפולים
    return text

for folder, category in categories.items():
    raw_items = []
    seen = set()
    keywords = category.get("keywords", [])

    for source in category["sources"]:
        # זיהוי עיתונאי לפי מנוע החיפוש בפיד
        journalist_name = None
        for key, name in JOURNALISTS_MAP.items():
            if key in source:
                journalist_name = name
                break

        try:
            feed = feedparser.parse(source, agent=USER_AGENT)
        except Exception as e:
            print(f"Error parsing source {source}: {e}")
            continue

        for item in feed.entries[:40]:
            if hasattr(item, "published_parsed") and item.published_parsed:
                published = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
                israel_time = published.astimezone(TIMEZONE)
            else:
                israel_time = now_il

            age_delta = now_il - israel_time
            age_seconds = age_delta.total_seconds()

            # חלון זמן של חצי שעה בלבד (1800 שניות)
            if age_seconds > 1800 or age_seconds < -300:
                continue

            if israel_time > now_il:
                israel_time = now_il

            original_title = item.title.strip()

            # בדיקה האם הידיעה היא בנושא מזג אוויר/תחזית
            is_weather = "תחזית" in original_title or "מזג אוויר" in original_title

            # הסרת שם האתר מסוף הכותרת בגוגל ניוז
            clean_title = re.sub(r'\s*-\s*[^\-]+\s*$', '', original_title)
            clean_title = re.sub(r'<.*?>', '', clean_title)
            clean_title = re.sub(r'[A-Za-z]+', '', clean_title)

            link = getattr(item, "link", "")
            is_short_source = any(domain in link for domain in SHORT_DOMAINS)

            summary = ""
            if is_short_source:
                if hasattr(item, "content"):
                    summary = item.content[0].value.strip()
                elif hasattr(item, "summary"):
                    summary = item.summary.strip()
            else:
                if hasattr(item, "summary"):
                    summary = item.summary.strip()

            summary = re.sub(r'<.*?>', '', summary)
            summary = re.sub(
                r'(ynet|וואלה|מעריב|ישראל היום|כאן חדשות|חדשות 12|חדשות 13|N12)',
                '',
                summary,
                flags=re.IGNORECASE
            )
            summary = re.sub(r'[A-Za-z]+', '', summary)

            if "תחזית" in summary or "מזג אוויר" in summary:
                is_weather = True

            # טיפול במזג אוויר - הבאת הכתבה במלואה
            if is_weather:
                news_content = f"{clean_title}. {summary}"
            else:
                # ניקוי רגיל לכתבות
                clean_title_fmt = clean_text_for_tts(clean_title)
                clean_summary_fmt = clean_text_for_tts(summary)

                title_compare = re.sub(r'\s+', '', clean_title_fmt)
                summary_compare = re.sub(r'\s+', '', clean_summary_fmt)

                if summary_compare.startswith(title_compare):
                    clean_summary_fmt = clean_summary_fmt[len(clean_title_fmt):].strip()

                if not clean_summary_fmt or len(clean_summary_fmt) < 15:
                    news_content = clean_title_fmt
                else:
                    news_content = clean_summary_fmt

            news_content = re.sub(r'\bחדשות\b', '', news_content).strip()
            news_content = clean_text_for_tts(news_content)

            if not news_content or len(news_content) < 10:
                continue

            # אם זו כתבת עיתונאי - הוספת שמו במידה ולא מוזכר בתחילת הכתבה
            if journalist_name and not news_content.startswith(journalist_name):
                news_content = f"{journalist_name} מדווח: {news_content}"

            # סינון לפי מילות מפתח בשלוחות 2, 3, 4
            if folder != "1" and keywords:
                found_keyword = any(kw in news_content or kw in clean_title for kw in keywords)
                if not found_keyword:
                    continue

            # ===========================
            # מנגנון זיהוי כפילויות היקפי (Hash-Based)
            # ===========================
            hebrew_words = re.findall(r'[\u0590-\u05FF]+', news_content)
            if len(hebrew_words) < 3:
                continue

            # יצירת טביעת אצבע ייחודית מהקישור ומתחילת הכתבה
            unique_str = f"{folder}_{link}_{''.join(hebrew_words[:8])}"
            fingerprint = hashlib.md5(unique_str.encode('utf-8')).hexdigest()

            if fingerprint in seen or fingerprint in old_news_set:
                continue

            seen.add(fingerprint)
            old_news.append(fingerprint)
            old_news_set.add(fingerprint)

            raw_items.append({
                "time_obj": israel_time,
                "news_content": news_content
            })

    if not raw_items:
        continue

    # מיון לפי זמן הידיעה מהישן לחדש
    raw_items.sort(key=lambda x: x["time_obj"])

    # ===========================
    # עיבוד הזמנים ובניית הטקסט
    # ===========================
    items = []
    last_assigned_time = None

    for item in raw_items:
        item_time = item["time_obj"]

        if last_assigned_time and item_time <= last_assigned_time:
            item_time = last_assigned_time + timedelta(minutes=1)

        last_assigned_time = item_time

        display_hour = item_time.hour % 12
        if display_hour == 0:
            display_hour = 12

        if item_time.minute == 0:
            str_time = f"השעה {display_hour}"
        elif item_time.minute == 1:
            str_time = f"{display_hour} ודקה"
        else:
            str_time = f"{display_hour} ו-{item_time.minute} דקות"

        news_text = f"{str_time}. {item['news_content']}"
        items.append(news_text)

    # ===========================
    # יצירת הקבצים והמרת שמע
    # ===========================
    if folder in ["1", "2", "3", "4"]:
        for index, news in enumerate(items):
            tts = gTTS(news.strip(), lang="iw")

            mp3_name = f"news_{folder}_{index}.mp3"
            wav_name = f"news_{folder}_{index}.wav"

            tts.save(mp3_name)

            audio = AudioSegment.from_mp3(mp3_name)
            audio = audio.speedup(playback_speed=1.25)
            audio = audio.set_frame_rate(8000)
            audio = audio.set_channels(1)
            audio.export(wav_name, format="wav")

    # ===========================
    # העלאה לימות המשיח
    # ===========================
    token = os.environ.get("YEMOT_TOKEN", "")
    url = "https://www.call2all.co.il/ym/api/UploadFile"

    if folder in ["1", "2", "3", "4"]:
        list_url = "https://www.call2all.co.il/ym/api/GetIVR2Dir"
        list_data = {
            "token": token,
            "path": f"ivr2:/{folder}/"
        }

        try:
            result = requests.post(list_url, data=list_data).json()
        except Exception as e:
            print(f"Error fetching directory info: {e}")
            result = {}

        max_number = 0

        if "files" in result:
            for file in result.get("files", []):
                name = file.get("name", "")
                number = re.findall(r'\d+', name)
                if number:
                    max_number = max(max_number, int(number[0]))

        for index, wav_name in enumerate(
            [f"news_{folder}_{i}.wav" for i in range(len(items))],
            start=1
        ):
            new_number = str(max_number + index).zfill(3)

            try:
                with open(wav_name, "rb") as f:
                    files = {"file": f}
                    data = {
                        "token": token,
                        "path": f"ivr2:/{folder}/{new_number}.wav",
                        "convertAudio": "1"
                    }
                    response = requests.post(url, files=files, data=data)
                    print(folder, new_number, response.text)
            except Exception as e:
                print(f"Error uploading file {wav_name}: {e}")

            mp3_name = wav_name.replace(".wav", ".mp3")
            if os.path.exists(wav_name): os.remove(wav_name)
            if os.path.exists(mp3_name): os.remove(mp3_name)

# שמירת היסטוריית הכתבות בסוף הריצה
save_history(old_news)

import time

while True:
    time.sleep(60)
