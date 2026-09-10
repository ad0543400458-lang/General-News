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

async def create_tts(text, output_file):
    # ניתן לשנות את הקצב (למשל "+10%" להאצה קלה, "+15%" להאצה משמעותית יותר, או "-10%" להאטה)
    communicate = edge_tts.Communicate(text, "he-IL-AvriNeural", rate="+15%")
    await communicate.save(output_file)

# ===========================
# הגדרות כלליות
# ===========================
TIMEZONE = pytz.timezone('Asia/Jerusalem')
HISTORY_FILE = 'seen_news.json'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

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
    "https://news.google.com/rss/search?q=%22רכס+שועפאט%22&hl=he&gl=IL&ceid=IL:he"
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
    "2": {
        "name": "רמת שלמה",
        "sources": sources_ramat_shlomo,
        "keywords": ["רמת שלמה", "ברמת שלמה", "רכס שועפאט"],
        "max_age_seconds": 86400  # 24 שעות
    },
    "3": {
        "name": "כלכלה ונדל\"ן",
        "sources": sources_economy,
        "keywords": ["ירידת מחירי הדיור", "ירידת מחירי הדירות", "הורדת מחירי", "ירידת מחירי", "הורדת מחירי הדיור"],
        "max_age_seconds": 21600
    },
    "4": {
        "name": "תחבורה",
        "sources": sources_transport,
        "keywords": ["תחבורה", "כביש", "רכבת", "פקק", "חסימה"],
        "max_age_seconds": 21600
    },
    "5": {
        "name": "מזג אוויר",
        "sources": sources_weather,
        "keywords": ["תחזית", "מזג אוויר", "גשם", "טמפרטורות"],
        "max_age_seconds": 21600
    }
}

def main():
    old_news = load_history()
    old_news_set = set(old_news)
    now_il = datetime.now(TIMEZONE)

    # שעות הפעלה מוגדרות לכל שלוחה (None = רץ בכל שעה)
    SCHEDULED_HOURS = {
        "1": None,              # שעה-שעה (רציף)
        "2": [0, 7, 14, 19],      # רמת שלמה: 3 פעמים ביום בלבד
        "3": [0, 7, 14, 19],
        "4": [0, 7, 14, 19],
        "5": [0, 7, 14, 19]
    }

    # חלון איסוף מורחב לשלוחה 1 בשעות המהדורות המרכזיות
    extended_windows_folder_1 = {
        7: 7 * 3600,   # מהדורת בוקר
        14: 7 * 3600,  # מהדורת צהריים
        19: 5 * 3600,  # מהדורת ערב
        0: 17 * 3600   # מהדורת חצות
    }

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
            print(f"No new items for folder {folder}")
            continue

        raw_items.sort(key=lambda x: x["time_obj"])
        raw_news_text = "\n---\n".join([item['news_content'] for item in raw_items])

        # עיבוד ב-AI
        try:
            print(f"Processing Folder {folder} ({category['name']}) with AI...")
            full_edition_text = edit_news_with_ai(raw_news_text, folder, current_hour=now_il.hour)
        except Exception as e:
            print(f"AI failed for folder {folder}, using raw text: {e}")
            full_edition_text = raw_news_text

        if len(full_edition_text.strip()) < 40:
            print(f"Output text too short for folder {folder}, skipping audio generation.")
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
