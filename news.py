import os
import re
import json
import hashlib
import pytz
import requests
import feedparser
import asyncio
import edge_tts
from datetime import datetime, timezone
from pydub import AudioSegment
from ai_editor import edit_news_with_ai
from google import genai

async def create_tts(text, output_file):
    # ניתן לשנות את הקצב (למשל "+10%" להאצה קלה, "+15%" להאצה משמעותית יותר, או "-10%" להאטה)
    communicate = edge_tts.Communicate(text, "he-IL-AvriNeural", rate="+12%")
    await communicate.save(output_file)

# ===========================
# הגדרות כלליות
# ===========================
TIMEZONE = pytz.timezone('Asia/Jerusalem')
HISTORY_FILE = 'seen_news.json'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"


from zmanim.util.geo_location import GeoLocation
from zmanim.zmanim_calendar import ZmanimCalendar
from datetime import timedelta

def is_shabbat_time(now_il):
    weekday = now_il.weekday()

    if weekday not in [4, 5, 6]:
        return False

    geo_location = GeoLocation(
        "Jerusalem",
        31.778,
        35.235,
        "Asia/Jerusalem",
        elevation=800
    )

    zmanim_cal = ZmanimCalendar(geo_location=geo_location)

    if weekday == 4:
        zmanim_cal.date = now_il.date()
        sunset = zmanim_cal.sunset()

        if sunset:
            candle_lighting = sunset.astimezone(TIMEZONE) - timedelta(minutes=40)
            if now_il >= candle_lighting:
                return True

    elif weekday == 5:
        return True

    elif weekday == 6:
        yesterday = now_il.date() - timedelta(days=1)
        zmanim_cal.date = yesterday
        sunset = zmanim_cal.sunset()

        if sunset:
            tzeit_shabbat = sunset.astimezone(TIMEZONE) + timedelta(minutes=50)
            if now_il <= tzeit_shabbat:
                return True

    return False

    zmanim_cal = ZmanimCalendar(geo_location=geo_location)

    if weekday == 4:  # יום שישי
        zmanim_cal.date = now_il.date()
        sunset = zmanim_cal.sunset()

        if sunset:
            candle_lighting = sunset.astimezone(TIMEZONE) - timedelta(minutes=40)
            if now_il >= candle_lighting:
                return True

    elif weekday == 5:  # שבת
        return True

    elif weekday == 6:  # מוצאי שבת
        yesterday = now_il.date() - timedelta(days=1)
        zmanim_cal.date = yesterday
        sunset = zmanim_cal.sunset()

        if sunset:
            tzeit_shabbat = sunset.astimezone(TIMEZONE) + timedelta(minutes=50)
            if now_il <= tzeit_shabbat:
                return True

    return False   
# ===========================
# ניהול היסטוריה
# ===========================
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history file: {e}")
            return []
    return []

def save_history(history_list):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_list[-5000:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history file: {e}")

def clean_text_for_tts(text):
    text = re.sub(r'&+', ' ', text)
    text = re.sub(r'[\"\']', '', text)
    text = re.sub(r'[\-–—]', ' ', text)
    text = re.sub(r'[,;:]', ' ', text)
    text = re.sub(r'[\(\)\[\]\{\}]', '', text)
    text = re.sub(r'[^\w\s\u0590-\u05FF.]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ===========================
# מאגרי מקורות
# ===========================
sources_general = [
    "https://news.google.com/rss/search?q=חדשות+היום&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=חדשות+בארץ&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ישראל&hl=he&gl=IL&ceid=IL:he",
    "https://www.maariv.co.il/Rss/RssFeedsMivzakim",
    "https://rss.walla.co.il/feed/22",
    "https://news.google.com/rss/search?q=דיווח+ראשוני&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=מבזק+חם&hl=he&gl=IL&ceid=IL:he"
]

sources_ramat_shlomo = [
    "https://news.google.com/rss/search?q=%22רמת+שלמה%22&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=רמת+שלמה+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=שכונת+רמת+שלמה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22רכס+שועפאט%22&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22חזון+איש%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22דרוק%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22אגרות+משה%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22גולדקנופף%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22לובביץ%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22זולטי%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22ברים%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22פטאל%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22כהנמן%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22הרשלר%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22קהילות+יעקב%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22שטפנשט%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22קלכהיים%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22ברכת+אברהם%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22סדיגורה%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22חדש%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22לופיאן%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22בוקסבוים%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22יגאל+ידין%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22מבוא+הברכה%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22קלואינימוס%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22טולדנו%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=%22מוצפי%22+ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+חדשות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+מבזק&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+שכונות&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+כבישים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+עירייה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+תחבורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+בנייה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+חדשות+חרדים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=ירושלים+רמת+שלמה&hl=he&gl=IL&ceid=IL:he"
]

sources_economy = [
    "https://www.ice.co.il/rss.xml",
    "https://www.bizportal.co.il/rss/bizportalrss.xml",
    "https://news.google.com/rss/search?q=כלכלה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=נדלן&hl=he&gl=IL&ceid=IL:he"
]

sources_transport = [
    "https://news.google.com/rss/search?q=תחבורה&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=כבישים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=עומסי+תנועה&hl=he&gl=IL&ceid=IL:he"
]

sources_weather = [
    "https://news.google.com/rss/search?q=מזג+אוויר&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=תחזית+מזג+האוויר&hl=he&gl=IL&ceid=IL:he",
    # הזנה ישירה של תחזית מזג האוויר מ-Ynet ו-Walla (מכיל תחזית יומית מפורטת)
    "https://www.ynet.co.il/Integration/StoryRss185.xml",
    "https://rss.walla.co.il/feed/1",
    # חיפושים ממוקדים בגוגל חדשות
    "https://news.google.com/rss/search?q=%22תחזית+מזג+האוויר%22+הימים+הקרובים&hl=he&gl=IL&ceid=IL:he",
    "https://news.google.com/rss/search?q=תחזית+מזג+האוויר+השבוע&hl=he&gl=IL&ceid=IL:he"
]

# ===========================
# הגדרת השלוחות (Categories)
# ===========================
categories = {
    "1": {
        "name": "מהדורה כללית",
        "sources": list(set(sources_general + sources_economy + sources_transport + sources_weather)),
        "keywords": [],
        "max_age_seconds": 3600  # ברירת מחדל: שעה אחת
    },
    "5": {
        "name": "מזג אוויר",
        "sources": sources_weather,
        "keywords": [],
        "max_age_seconds": 21600
    },
    "6": {
        "name": "תחבורה",
        "sources": sources_transport,
        "keywords": [],
        "max_age_seconds": 21600
    },
    "7": {
        "name": "כלכלה ונדל\"ן",
        "sources": sources_economy,
        "keywords": [],
        "max_age_seconds": 21600
    },
    "8": {
        "name": "רמת שלמה",
        "sources": sources_ramat_shlomo,
        "keywords": [],
        "max_age_seconds": 86400
    }
}


def run_truth_segment(now_il):
    """יצירת קטע יומי: בדיקת הצהרות ופערים בפוליטיקה והעלאה לשלוחה 2."""

    if now_il.hour != 14:
        return

    token = os.environ.get("YEMOT_TOKEN", "")
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if not token or not api_key:
        print("Truth segment skipped: missing API keys.")
        return

    date_tag = now_il.strftime("%Y%m%d")
    marker_name = f"truth_{date_tag}.txt"

    list_url = "https://www.call2all.co.il/ym/api/GetIVR2Dir"
    upload_url = "https://www.call2all.co.il/ym/api/UploadFile"

    try:
        # בדיקה אם כבר נוצר קטע היום
        response = requests.post(
            list_url,
            data={"token": token, "path": "ivr2:/2/"},
            timeout=30
        )
        response.raise_for_status()

        files_data = response.json()
        existing_files = [
            f.get("name", "") for f in files_data.get("files", [])
        ]

        if marker_name in existing_files:
            print("Truth segment already uploaded today.")
            return

        # מקורות חדשות ממוקדים
        sources = [
            "https://news.google.com/rss/search?q=פוליטיקה+ישראל&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=הצהרות+פוליטיקאים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=הבטחות+ממשלה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=חברי+כנסת+התבטאות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ממשלה+החלטות+ביקורת&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שרים+אמרו+בעבר&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=פוליטיקה+ישראל&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=הצהרות+פוליטיקאים&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=הבטחות+ממשלה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=חברי+כנסת+התבטאות&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שרים+אמרו+בעבר&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=פוליטיקאי+הבטיח+בעבר&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=שינה+את+עמדתו+פוליטיקה&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=הצבעה+קודמת+הצהרה+שר&hl=he&gl=IL&ceid=IL:he",
            "https://news.google.com/rss/search?q=ציטוטים+קודמים+פוליטיקאים&hl=he&gl=IL&ceid=IL:he",
          
        ]

        news_items = []
        seen_links = set()

        for source in sources:
            try:
                feed = feedparser.parse(source, agent=USER_AGENT)

                for item in feed.entries[:20]:
                    link = getattr(item, "link", "")

                    if not link or link in seen_links:
                        continue

                    seen_links.add(link)

                    title = getattr(item, "title", "")
                    summary = getattr(item, "summary", "")

                    if not title and not summary:
                        continue

                    news_items.append(
                        f"כותרת: {title}\n"
                        f"תוכן: {summary}\n"
                        f"קישור מקור: {link}"
                    )

            except Exception as e:
                print(f"Truth RSS error: {e}")

        if not news_items:
            print("No political news found for truth segment.")
            return

        raw_text = "\n\n---\n\n".join(news_items)

        # יצירת בדיקת עובדות באמצעות Gemini
        client = genai.Client(api_key=api_key)

        prompt = f"""
אתה עורך תחקירים עיתונאיים.

מטרת הקטע היא לחשוף פערים אמיתיים בין הצהרות של אנשי ציבור,
הבטחות פוליטיות, הצבעות, החלטות ומעשים.

עליך לבדוק את החדשות שהתקבלו ולחפש מקרה אחד בלבד
שבו יש ראיה ברורה לפער משמעותי בין אמירה קודמת
לבין אמירה או מעשה מאוחרים יותר.

כללים מחייבים:

1. אסור להמציא ציטוטים, תאריכים, אירועים או עובדות.
2. אין לקבוע שאדם שיקר אם אין לכך הוכחה.
3. יש להבחין בין שינוי עמדה, סתירה, הבטחה שלא קוימה
   וטענה שקרית. אלה אינם אותו הדבר.
4. כדי לפרסם סתירה בין שתי אמירות, שתי האמירות חייבות
   להופיע במפורש בטקסט המקורות שסופק.
5. אם אין שתי אמירות מפורשות, אין לפרסם סתירה.
6. אין להסתמך על זיכרון כללי או ידע חיצוני.
7. יש לבחור רק נושא הקשור ישירות לחדשות האקטואליות.
8. אם אין ממצא משמעותי ומבוסס, יש להחזיר publish=false.
9. אין ליצור קטע רק כדי למלא את השלוחה.
10. הקטע צריך להיות קצר, חד, מעניין וברור להקראה,
    באורך של כדקה לכל היותר.

החזר JSON בלבד במבנה הבא:

{{
  "publish": true,
  "headline": "כותרת קצרה",
  "current_quote": "ציטוט מדויק מהמקורות",
  "previous_quote": "ציטוט מדויק מהמקורות",
  "explanation": "הסבר עובדתי קצר על הפער",
  "sources": ["קישור מקור ראשון", "קישור מקור שני"]
}}

אם אין ממצא מתאים, החזר:

{{
  "publish": false
}}

החדשות והמקורות:
{raw_text}
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        if not response.text:
            print("Gemini returned empty truth segment.")
            return

        result_text = response.text.strip()
        result_text = re.sub(r"^```(?:json)?\s*", "", result_text)
        result_text = re.sub(r"\s*```$", "", result_text)

        result = json.loads(result_text)

        if not result.get("publish"):
            print("No sufficiently verified finding. Nothing uploaded.")
            return

        current_quote = result.get("current_quote", "").strip()
        previous_quote = result.get("previous_quote", "").strip()
        explanation = result.get("explanation", "").strip()
        headline = result.get("headline", "").strip()
        selected_sources = result.get("sources", [])

        # אימות שהציטוטים והמקורות אכן נמצאים בחומר שנאסף
        if (
            len(current_quote) < 15
            or len(previous_quote) < 15
            or current_quote not in raw_text
            or previous_quote not in raw_text
            or len(set(selected_sources)) < 2
            or any(source not in raw_text for source in selected_sources)
            or not explanation
            or not headline
        ):
            print("Truth segment failed source verification. Nothing uploaded.")
            return

        final_text = (
            "האמת שמאחורי הפוליטיקה.\n\n"
            f"{headline}.\n\n"
            f"ההתבטאות שפורסמה כעת: {current_quote}.\n\n"
            f"ומנגד, בהתבטאות קודמת נאמר: {previous_quote}.\n\n"
            f"{explanation}\n\n"
            "אנחנו נמשיך לבדוק את העובדות שמאחורי הכותרות."
        )

        # יצירת קובץ שמע
        mp3_name = "truth_segment.mp3"
        wav_name = "truth_segment.wav"

        asyncio.run(create_tts(final_text, mp3_name))

        audio = AudioSegment.from_mp3(mp3_name)
        audio = audio.set_frame_rate(8000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)
        audio.export(wav_name, format="wav")

        # מציאת המספר הבא בשלוחה 2
        max_number = 0

        for file in files_data.get("files", []):
            name = file.get("name", "")
            match = re.match(r"^(\d+)\.wav$", name, re.IGNORECASE)

            if match:
                max_number = max(max_number, int(match.group(1)))

        new_number = str(max_number + 1).zfill(3)

        with open(wav_name, "rb") as audio_file:
            upload_response = requests.post(
                upload_url,
                files={"file": audio_file},
                data={
                    "token": token,
                    "path": f"ivr2:/2/{new_number}.wav",
                    "convertAudio": "1"
                },
                timeout=60
            )

        upload_response.raise_for_status()
        upload_data = upload_response.json()

        if upload_data.get("responseStatus") != "OK":
            raise RuntimeError(f"Yemot upload failed: {upload_data}")

        # סימון שהתהליך כבר בוצע היום
        marker_response = requests.post(
            upload_url,
            files={"file": (marker_name, date_tag.encode("utf-8"))},
            data={
                "token": token,
                "path": f"ivr2:/2/{marker_name}"
            },
            timeout=30
        )

        marker_response.raise_for_status()

        print(f"Truth segment uploaded successfully: 2/{new_number}.wav")

    except Exception as e:
        print(f"Truth segment failed: {e}")

    finally:
        for filename in ["truth_segment.mp3", "truth_segment.wav"]:
            if os.path.exists(filename):
                os.remove(filename)


def main():
    old_news = load_history()
    old_news_set = set(old_news)
    now_il = datetime.now(TIMEZONE)

    # שעות הפעלה מוגדרות לכל שלוחה (None = רץ בכל שעה)
    SCHEDULED_HOURS = {
        "1": None,              # שעה-שעה (רציף)
        "5": [0, 7, 14, 19],      # רמת שלמה: 4 פעמים ביום בלבד
        "6": [0, 7, 14, 19],
        "7": [0, 7, 14, 19],
        "8": [0, 7, 14, 19]
    }

    # חלון איסוף מורחב לשלוחה 1 בשעות המהדורות המרכזיות
    extended_windows_folder_1 = {
        7: 7 * 3600,   # מהדורת בוקר
        14: 7 * 3600,  # מהדורת צהריים
        19: 5 * 3600,  # מהדורת ערב
        0: 17 * 3600   # מהדורת חצות
    }

# אם זו השבת - עוצרים לחלוטין את הריצה של כל השלוחות הרגילות
    if is_shabbat_time(now_il):
        print("Shabbat mode active - skipping regular news run.")
        return

         # קטע יומי: האמת שמאחורי הפוליטיקה
    run_truth_segment(now_il)
    
    for folder, category in categories.items():
        # בדיקה אם השלוחה מתוכננת לרוץ בשעה הנוכחית
        allowed_hours = SCHEDULED_HOURS.get(str(folder))
        if allowed_hours is not None and now_il.hour not in allowed_hours:
            print(f"Skipping folder {folder} ({category['name']}) - not scheduled for hour {now_il.hour}")
            continue

        

        raw_items = []
        seen = set()
        keywords = category.get("keywords", [])

        # קביעת טווח זמנים לאיסוף ידיעות
        if str(folder) == "1":
            max_age = extended_windows_folder_1.get(now_il.hour, 3600)
        else:
            max_age = category.get("max_age_seconds", 21600)

        # סריקת מקורות השלוחה
        for source in category["sources"]:
            try:
                feed = feedparser.parse(source, agent=USER_AGENT)
            except Exception as e:
                print(f"Error parsing {source}: {e}")
                continue

            for item in feed.entries[:30]:
                if hasattr(item, "published_parsed") and item.published_parsed:
                    published = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
                    israel_time = published.astimezone(TIMEZONE)
                else:
                    israel_time = now_il

                age_seconds = (now_il - israel_time).total_seconds()
                if age_seconds > max_age or age_seconds < -300:
                    continue

                original_title = item.title.strip()
                clean_title = re.sub(r'\s*-\s*[^\-]+\s*$', '', original_title)
                clean_title = re.sub(r'<.*?>|[A-Za-z]+', '', clean_title)

                link = getattr(item, "link", "")
                summary = getattr(item, "summary", getattr(item, "content", [{}])[0].get("value", ""))
                summary = re.sub(r'<.*?>|[A-Za-z]+', '', summary)

                clean_title_fmt = clean_text_for_tts(clean_title)
                clean_summary_fmt = clean_text_for_tts(summary)

                if len(clean_summary_fmt) < 15:
                    news_content = clean_title_fmt
                else:
                    news_content = clean_summary_fmt

                news_content = clean_text_for_tts(news_content)
                if not news_content or len(news_content) < 10:
                    continue

                # סינון לפי מילות מפתח במידה ובלוק המילות מפתח מוגדר
                if keywords:
                    found_keyword = any(kw in news_content or kw in clean_title for kw in keywords)
                    if not found_keyword:
                        continue

                hebrew_words = re.findall(r'[\u0590-\u05FF]+', news_content)
                if len(hebrew_words) < 3:
                    continue

                # יצירת טביעת אצבע למניעת כפילויות
                unique_str = f"{folder}_{link}_{''.join(hebrew_words[:8])}"
                fingerprint = hashlib.md5(unique_str.encode('utf-8')).hexdigest()

                is_extended_edition = (
                    str(folder) == "1"
                    and now_il.hour in extended_windows_folder_1
                )

                if not is_extended_edition:
                    if fingerprint in seen or fingerprint in old_news_set:
                        continue

                seen.add(fingerprint)

                if not is_extended_edition:
                    old_news.append(fingerprint)
                    old_news_set.add(fingerprint)

                raw_items.append({
                    "time_obj": israel_time,
                    "news_content": news_content
                })

        if not raw_items:
            print(f"No new items for folder {folder}")
            continue

        raw_items.sort(key=lambda x: x["time_obj"])
        raw_news_text = "\n---\n".join([item['news_content'] for item in raw_items])

        # עיבוד ב-AI
        try:
            print(f"Processing Folder {folder} ({category['name']}) with AI...")
            full_edition_text = edit_news_with_ai(
                raw_news_text,
                folder,
                current_hour=now_il.hour,
                TIMEZONE=TIMEZONE
            )
        except Exception as e:
            print(f"AI editing failed for folder {folder}: {e}")
            print(f"Skipping folder {folder} - no raw news will be uploaded.")
            continue

        if not full_edition_text or len(full_edition_text.strip()) < 40:
            print(f"AI returned no valid edition for folder {folder}. Skipping upload.")
            continue

        # יצירת הקובץ הקולי
        mp3_name = f"news_{folder}.mp3"
        wav_name = f"news_{folder}.wav"

        asyncio.run(create_tts(full_edition_text.strip(), mp3_name))

        audio = AudioSegment.from_mp3(mp3_name)
        audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)
        audio.export(wav_name, format="wav")

        # העלאה לימות המשיח
        token = os.environ.get("YEMOT_TOKEN", "")
        url = "https://www.call2all.co.il/ym/api/UploadFile"
        list_url = "https://www.call2all.co.il/ym/api/GetIVR2Dir"

        try:
            res = requests.post(list_url, data={"token": token, "path": f"ivr2:/{folder}/"}).json()
            max_number = 0
            for file in res.get("files", []):
                num_match = re.findall(r'\d+', file.get("name", ""))
                if num_match:
                    max_number = max(max_number, int(num_match[0]))
            
            new_number = str(max_number + 1).zfill(3)

            with open(wav_name, "rb") as f:
                upload_res = requests.post(url, files={"file": f}, data={
                    "token": token,
                    "path": f"ivr2:/{folder}/{new_number}.wav",
                    "convertAudio": "1"
                })
                print(f"Uploaded to folder {folder}/{new_number}.wav: Status {upload_res.status_code}")
        except Exception as e:
            print(f"Error uploading file to Yemot: {e}")

        # ניקוי קבצים זמניים
        if os.path.exists(wav_name): os.remove(wav_name)
        if os.path.exists(mp3_name): os.remove(mp3_name)

    save_history(old_news)
    print("Execution completed successfully.")

if __name__ == "__main__":
    main()
