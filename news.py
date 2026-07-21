import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment
import json
import re
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
        # שומרים רק את 3000 הפריטים האחרונים למניעת קובץ כבד מדי
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_list[-3000:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history file: {e}")

# ===========================
# מקורות משותפים (שלוחה 1)
# ===========================
sources_1 = [
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
    "https://news.google.com/rss/search?q=ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בני+ברק&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=פיתוח+עירוני&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=תשתיות+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בנק+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+קלה&hl=he&gl=IL&ceid=IL:he",
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
    # מבזקים ועדכונים מהירים בזמן אמת
    "https://news.google.com/rss/search?q=מבזק+חדשות+זמן+אמת&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=דיווחים+שוטפים+מבזקים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עדכון+מבזק+חם&hl=he&gl=IL&ceid=IL:he",
    
    # עיתונאים וכתבים נוספים שמפרסמים עדכונים תכופים
    "https://news.google.com/rss/search?q=מיכאל+שמש+ציוץ&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עקיבא+נוביק&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מוטי+קסטל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שילה+פריד&hl=he&gl=IL&ceid=IL:he",
    
    # תחבורה, כבישים ותשתיות (מתעדכן רציף)
    "https://news.google.com/rss/search?q=עומסי+תנועה+חסימות+כבישים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שינויים+בתחבורה+הציבורית&hl=he&gl=IL&ceid=IL:he",
    "https://www.ice.co.il/rss.xml",           
    "https://www.bizportal.co.il/rss/bizportalrss.xml", 
    "https://news.google.com/rss/search?q=מבזק+חדשות+או+מבזקים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=דיווח+ראשוני+או+חדשות+מתפרצות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ציוצים+עיתונאים+או+כתבים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=אטילה+שומפלבי+או+יקיר+מויאל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=חדשות+רוטר+או+חמאל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מחירי+הדיור+או+שוק+הנדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בנק+ישראל+ריבית+משכנתא&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+ישראל+לוח+זמנים+או+קווים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=משרד+התחבורה+כבישים+חדשים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=הרכבת+הקלה+בירושלים+או+בגוש+דן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=פיתוח+עירוני+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עיריית+בני+ברק+חדשות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=תנופת+בנייה+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=פרויקטים+חדשים+טבריה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מזג+האוויר+תחזית+הימים+הקרובים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עדכונים+שוטפים+או+מבזקים+בזמן+אמת&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מבזקי+חדשות+בזמן+אמת&hl=he&gl=IL&ceid=IL:he"
]

# ===========================
# הגדרת קטגוריות
# ===========================
categories = {
    "1": {
        "sources": sources_1,
        "keywords": []
    },
    "2": {
        "sources": sources_1 + [
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
        ],
        "keywords": ["בית שמש", "רמת בית שמש", "רמה ד", "רמה ה", "רמה ג"]
    },
    "3": {
        "sources": sources_1 + [
            "https://news.google.com/rss/search?q=אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ארחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ישיבת+אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=אורחות+תורה+בני+ברק&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ראש+ישיבת+אורחות+תורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=בוגרי+אורחות+תורה&hl=he&gl=IL&ceid=IL:he"
        ],
        "keywords": ["אורחות תורה", "ארחות תורה"]
    },
    "4": {
        "sources": sources_1 + [
            "https://news.google.com/rss/search?q=טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שיכון+ד+טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=עיריית+טבריה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+חדשות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+נדלן&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+בניה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+תחבורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+כבישים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=טבריה+התפתחות&hl=he&gl=IL&ceid=IL:he"
        ],
        "keywords": ["טבריה"]
    },
    "5": {
        "sources": sources_1 + [
            "https://news.google.com/rss/search?q=רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שכונת+רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+ירושלים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+בניה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+דירות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+עירייה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+תחבורה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+כבישים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=רמת+שלמה+קהילה&hl=he&gl=IL&ceid=IL:he"
        ],
        "keywords": ["רמת שלמה"]
    }
}

# טעינת היסטוריה מקובץ לפני תחילת הריצה
old_news = load_history()
old_news_set = set(old_news)

SHORT_DOMAINS = ["maariv.co.il", "walla.co.il"]
now_il = datetime.now(TIMEZONE)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

for folder, category in categories.items():
    raw_items = []
    seen = set()
    keywords = category.get("keywords", [])

    for source in category["sources"]:
        try:
            feed = feedparser.parse(source, agent=USER_AGENT)
        except Exception as e:
            print(f"Error parsing source {source}: {e}")
            continue

        for item in feed.entries[:40]:
            # מזהה ייחודי לכתבה (ID או URL) למניעת כפילויות מושלמת
            item_id = getattr(item, "id", getattr(item, "link", ""))
            if item_id and item_id in old_news_set:
                continue

            if hasattr(item, "published_parsed") and item.published_parsed:
                published = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
                israel_time = published.astimezone(TIMEZONE)
            else:
                israel_time = now_il

            age_delta = now_il - israel_time
            age_seconds = age_delta.total_seconds()

            # התיקון: סינון לפי 7 דקות אחרונות בלבד להתאמה להרצת Cron של 5 דקות
            if age_seconds > 7 * 60 or age_seconds < -300:
                continue

            if israel_time > now_il:
                israel_time = now_il

            original_title = item.title.strip()

            title = re.sub(r'<.*?>', '', original_title)
            title = re.sub(r'[A-Za-z]+', '', title)
            title = " ".join(title.split())
            title = re.sub(r'[.,;:"\'()\-%–—-]', '', title)

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
            summary = re.sub(r'[<>/\[\]{}|*#@]', '', summary)
            summary = re.sub(r'[.,;:"\'()\-%–—-]', '', summary)
            summary = re.sub(r'[^\u0590-\u05FF0-9.,? ]', ' ', summary)
            summary = " ".join(summary.split())

            title_compare = re.sub(r'\s+', '', title)
            summary_compare = re.sub(r'\s+', '', summary)

            if summary_compare.startswith(title_compare):
                summary = summary[len(title):].lstrip(" .,:-–—?")

            summary = " ".join(summary.split())
            summary = summary.lstrip(" .,-–—:?")

            if not summary or len(summary) < 20:
                continue

            summary = re.sub(r'\bחדשות\b', '', summary).strip()
            summary = " ".join(summary.split())

            if original_title.strip().endswith('?'):
                clean_title_q = re.sub(r'[^\u0590-\u05FF0-9.,? ]', ' ', original_title).strip()
                news_content = f"{clean_title_q} {summary}"
            else:
                news_content = summary

            # סינון לפי מילות מפתח בשלוחות 2-5
            if folder != "1":
                found_keyword = any(kw in news_content or kw in title for kw in keywords)
                if not found_keyword:
                    continue

            news_content = " ".join(news_content.split())
            normalized_compare = re.sub(r'\s+', '', news_content)
            short_content_key = normalized_compare[:60] if len(normalized_compare) >= 60 else normalized_compare

            # בדיקת כפילויות מול הזיכרון השוטף ומול הקובץ השמור
            if news_content in seen or short_content_key in seen:
                continue
            if title in old_news_set or normalized_compare in old_news_set or short_content_key in old_news_set:
                continue

            seen.add(news_content)
            seen.add(short_content_key)
            
            # הוספה להיסטוריה הנשמרת
            if item_id:
                old_news.append(item_id)
                old_news_set.add(item_id)

            old_news.append(title)
            old_news.append(normalized_compare)
            old_news.append(short_content_key)
            old_news_set.add(title)
            old_news_set.add(normalized_compare)
            old_news_set.add(short_content_key)
            
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

        # מקדם בדקה אחת אם הידיעה הגיעה באותה דקה למניעת זמן זהה
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
            str_time = f"{display_hour} ו {item_time.minute} דקות"

        news_text = f"{str_time}. {item['news_content']}"
        items.append(news_text)

    # ===========================
    # יצירת הקבצים והמרת שמע
    # ===========================
    if folder in ["1", "2", "3", "4", "5"]:
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

    if folder in ["1", "2", "3", "4", "5"]:
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
            for file in result["files"]:
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

# שמירת כל הכתבות שעלו לקובץ JSON קבוע בסוף הריצה
save_history(old_news)
