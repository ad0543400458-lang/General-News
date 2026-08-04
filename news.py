import feedparser
import os
import requests
from gtts import gTTS
from pydub import AudioSegment
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from ai_editor import edit_news_with_ai
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
# מאגר מקורות כללי
# ===========================
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

# ===========================
# מקורות מקומיים
# ===========================
sources_local = [
    "https://news.google.com/rss/search?q=בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עיריית+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+חדשות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בית+שמש+נדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמה+ד+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמה+ה+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמה+ג+בית+שמש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=קריית+גת+חרדית&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22שיכון+ד+טבריה%22&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22שכון+ד+טבריה%22&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שכונת+רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+שלמה+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עיריית+ירושלים+שכונות&hl=he&gl=IL&ceid=IL:he"
]

# ===========================
# מקורות כלכלה ונדל"ן
# ===========================
sources_economy = [
    "https://www.ice.co.il/rss.xml",           
    "https://www.bizportal.co.il/rss/bizportalrss.xml", 
    "https://news.google.com/rss/search?q=כלכלה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מחירי+דירות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=נדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=משכנתאות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בנק+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מחירי+הדיור+או+שוק+הנדלן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=בנק+ישראל+ריבית+משכנתא&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ריבית+בנק+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שוק+הדיור&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירידת+מחירי+הדירות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=הגרלות+דירה+בהנחה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=משרד+הבינוי+והשיכון&hl=he&gl=IL&ceid=IL:he"
]

# ===========================
# מקורות תחבורה וכבישים
# ===========================
sources_transport = [
    "https://news.google.com/rss/search?q=תחבורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=כבישים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+קלה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עומסי+תנועה+חסימות+כבישים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שינויים+בתחבורה+הציבורית&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רכבת+ישראל+לוח+זמנים+או+קווים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=משרד+התחבורה+כבישים+חדשים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=הרכבת+הקלה+בירושלים+או+בגוש+דן&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=משרד+התחבורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=נתיבי+ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=חסימת+כביש&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=פקק+תנועה&hl=he&gl=IL&ceid=IL:he"
]

# ===========================
# מקורות מזג אוויר
# ===========================
sources_weather = [
    "https://news.google.com/rss/search?q=מזג+אוויר&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=תחזית+מזג+האוויר&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=תחזית+הימים+הקרובים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מעלות+חום+גשם+שלג&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=השירות+המטאורולוגי&hl=he&gl=IL&ceid=IL:he"
]

# ===========================
# מילות מפתח לסיווג הכתבות
# ===========================
keywords_folder_2 = [
    "בית שמש", "רמת בית שמש", "רמה ד", "רמה ה", "רמה ג",
    "שיכון ד טבריה", "שכון ד טבריה", "שיכון ד, טבריה", "שכון ד, טבריה", 
    "שיכון ד' טבריה", "שכון ד' טבריה", "שיכון ד", "שכון ד", "שכון ד'", "שיכון ד'",
    "רמת שלמה", "קריית גת"
]

keywords_folder_3 = [
    "ירידת מחירים", "ירידה במחירי הדירות", "מחירי הדירות ירדו", "הוזלת דירות",
    "ירידת מחירי הנדלן", "ירידה במחירי הנדלן", "הוזלת מחירי הדיור", "הוזלה במחירי הדירות",
    "נפילת מחירי הדירות", "האטה במחירי הדיור", "הוזלת הדירות", "ירידה במחירי הדיור",
    "כלכלה", "משכנתא", "משכנתאות", "בנק ישראל", "ריבית", "נדלן", "דיור"
]

keywords_folder_4 = [
    "תחבורה", "כביש", "כבישים", "רכבת", "רכבת ישראל", "רכבת קלה",
    "פקק", "פקקים", "עומס תנועה", "עומסי תנועה", "חסימה", "חסימות", "משרד התחבורה", "תאונה"
]

keywords_folder_5 = [
    "תחזית", "מזג אוויר", "מזג האוויר", "מעלות", "גשם", "שקע", "שרב", "עננות", "הטמפרטורות", "טמפרטורות"
]

categories = {
    "1": {
        "sources": list(set(sources_general + sources_local + sources_economy + sources_transport)),
        "keywords": [],
        "max_age_seconds": 21600  # 6 שעות
    },
    "2": {
        "sources": sources_general + sources_local,
        "keywords": keywords_folder_2,
        "max_age_seconds": 21600
    },
    "3": {
        "sources": sources_general + sources_economy,
        "keywords": keywords_folder_3,
        "max_age_seconds": 21600
    },
    "4": {
        "sources": sources_general + sources_transport,
        "keywords": keywords_folder_4,
        "max_age_seconds": 21600
    },
    "5": {
        "sources": sources_weather + sources_general,
        "keywords": keywords_folder_5,
        "max_age_seconds": 21600
    }
}

old_news = load_history()
old_news_set = set(old_news)

EDITION_HOURS = 6

SHORT_DOMAINS = ["maariv.co.il", "walla.co.il"]
now_il = datetime.now(TIMEZONE)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

def clean_text_for_tts(text):
    """מנקה סימני פיסוק מיותרים ומקפים שגורמים לעצירות מיותרות בהקראה"""
    text = re.sub(r'[\"\']', '', text)
    text = re.sub(r'[\-–—]', ' ', text)
    text = re.sub(r'[,;:]', ' ', text)
    text = re.sub(r'[\(\)\[\]\{\}]', '', text)
    
    # אם המילה "וגם" מופיעה פעמיים ברצף (עם רווחים או פיסוק ביניהן), מוחק את שתיהן
    text = re.sub(r'\bוגם\s+וגם\b', '', text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    return text

for folder, category in categories.items():
    raw_items = []
    seen = set()
    keywords = category.get("keywords", [])
    max_age = category.get("max_age_seconds", 21600)

    for source in category["sources"]:
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

            if age_seconds > max_age or age_seconds < -300:
                continue

            if israel_time > now_il:
                israel_time = now_il

            original_title = item.title.strip()

            clean_title = re.sub(r'\s*-\s*[^\-]+\s*$', '', original_title)
            clean_title = re.sub(r'<.*?>', '', clean_title)
            clean_title = re.sub(r'[A-Za-z]+', '', clean_title)

            link = getattr(item, "link", "")

            summary = ""
            if hasattr(item, "content"):
                summary = item.content[0].value.strip()
            elif hasattr(item, "summary"):
                summary = item.summary.strip()

            summary = re.sub(r'<.*?>', '', summary)
            summary = re.sub(
                r'(ynet|וואלה|מעריב|ישראל היום|כאן חדשות|חדשות 12|חדשות 13|N12)',
                '',
                summary,
                flags=re.IGNORECASE
            )
            summary = re.sub(r'[A-Za-z]+', '', summary)

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

            if journalist_name and not news_content.startswith(journalist_name):
                news_content = f"{journalist_name} מדווח: {news_content}"

            # סינון לפי מילות מפתח בשלוחות הנגדיות
            if keywords:
                found_keyword = any(kw in news_content or kw in clean_title for kw in keywords)
                if not found_keyword:
                    continue

            hebrew_words = re.findall(r'[\u0590-\u05FF]+', news_content)
            if len(hebrew_words) < 3:
                continue

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

    raw_items.sort(key=lambda x: x["time_obj"])

    items = []
    for item in raw_items:
        items.append(item['news_content'])

    # בניית הטקסט הרציף למהדורה השלמה (פתיח + כל המבזקים + סגיר)
    full_edition_text = "מהדורת החדשות של השעות האחרונות. " + ", ".join(items) + " עד כאן מהדורת החדשות."

    # יצירת קובץ השמע היחיד למהדורה

    try:
        full_edition_text = edit_news_with_ai(full_edition_text)
        print("AI editing completed")
    except Exception as e:
        print("AI failed, using original text:", e)
        
    tts = gTTS(full_edition_text.strip(), lang="iw")

    mp3_name = f"news_{folder}.mp3"
    wav_name = f"news_{folder}.wav"

    tts.save(mp3_name)

    audio = AudioSegment.from_mp3(mp3_name)
    audio = audio.speedup(playback_speed=1.25)
    audio = audio.set_frame_rate(8000)
    audio = audio.set_channels(1)
    audio.export(wav_name, format="wav")

    # העלאה לימות המשיח
    token = os.environ.get("YEMOT_TOKEN", "")
    url = "https://www.call2all.co.il/ym/api/UploadFile"
    list_url = "https://www.call2all.co.il/ym/api/GetIVR2Dir"

    try:
        result = requests.post(list_url, data={"token": token, "path": f"ivr2:/{folder}/"}).json()
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

    new_number = str(max_number + 1).zfill(3)

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

    if os.path.exists(wav_name): os.remove(wav_name)
    if os.path.exists(mp3_name): os.remove(mp3_name)

# שמירת היסטוריית הכתבות בסוף הריצה
save_history(old_news)
