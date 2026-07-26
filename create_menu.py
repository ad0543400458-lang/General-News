import os
import feedparser
from gtts import gTTS
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. הגדרת מקורות החדשות (RSS)
RSS_FEEDS = [
    "https://www.ynet.co.il/Integration/StoryRss2.xml",
    "https://rss.walla.co.il/feed/1"
]

def fetch_news():
    print("אוסף מבזקי חדשות...")
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:  # לוקח את 3 הכתבות הראשונות מכל מקור
                title = entry.title
                summary = entry.get('summary', '')
                articles.append(f"{title}. {summary}")
        except Exception as e:
            print(f"שגיאה באיסוף חדשות מ-{url}: {e}")
    return articles

def create_audio(text_list):
    print("יוצר קובץ שמע...")
    full_text = " שלום. הנה מבזק החדשות המעודכן. " + " ".join(text_list)
    
    # המרת הטקסט לקובץ דיבור (עברית)
    tts = gTTS(text=full_text, lang='he')
    output_filename = "news_update.mp3"
    tts.save(output_filename)
    print(f"קובץ השמע נוצר בהצלחה: {output_filename}")

def run_main_task():
    try:
        news = fetch_news()
        if news:
            create_audio(news)
        else:
            print("לא נמצאו מבזקים לעדכון.")
    except Exception as e:
        print(f"שגיאה בהרצת המשימה: {e}")

# 2. הגדרת שרת אינטרנט קטן לשמירה על Render פעיל
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - Server is running")

if __name__ == "__main__":
    # הרצת משימת איסוף החדשות
    run_main_task()
    
    # הפעלת השרת כדי ש-Render יישאר במצב Live
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"Starting server on port {port}...")
    server.serve_forever()
