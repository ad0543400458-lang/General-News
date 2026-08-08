from datetime import datetime
import os
from openai import OpenAI


def edit_news_with_ai(news_text, folder, current_hour=None):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise Exception("Missing OPENROUTER_API_KEY")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # אם לא הועברה שעה, קח את השעה הנוכחית במערכת
    if current_hour is None:
        current_hour = datetime.now().hour

    # הגדרת פתיח לפי השעה
    intro_text = "אתם מאזינים למהדורת החדשות."
    if 5 <= current_hour <= 8:
        intro_text = "אתם מאזינים למהדורת שש בבוקר בחדשות המידע."
    elif 11 <= current_hour <= 14:
        intro_text = "אתם מאזינים למהדורת שתים עשרה בצהריים בחדשות המידע."
    elif 17 <= current_hour <= 20:
        intro_text = "אתם מאזינים למהדורת שש בערב בחדשות המידע."
    elif current_hour >= 23 or current_hour <= 2:
        intro_text = "אתם מאזינים למהדורת חצות בחדשות המידע."

    system_prompt = """אתה עורך חדשות ברדיו. תפקידך לערוך את הידיעות לטקסט רציף המיועד להקראה.

כללים:
- שכתב בלשונך תוך שמירה על העובדות, ללא הוספת מידע חדש.
- צרף ידיעות עוסקות באותו נושא לידיעה אחת.
- חלק לקטגוריות והקפד לכתוב את שם הקטגוריה לפני הקבוצה (סדר: פוליטיקה וביטחון, בחדשות החוץ, חדשות כלליות, בכלכלה ונדל"ן, בתחבורה, תחזית לסיום).
- אל תציג קטגוריות ריקות.
- שפה טבעית להקראה, ללא כוכביות, ללא מספור, ללא כותרות Markdown, וללא מילים כמו 'מבזק' או 'עדכון'.
- החזר טקסט נקי בלבד."""

    if str(folder) == "1":
        instructions = f"""שלוחה: 1
חובה להתחיל בדיוק במילים:
"{intro_text} עיקרי החדשות מהשעות האחרונות."

לאחר מכן הקטגוריות והידיעות.

חובה לסיים בדיוק במילים:
"עד כאן מהדורת החדשות. תודה שהאזנתם ולהתראות במהדורה הבאה." """
    else:
        instructions = "שלוחה אינה 1: אין להוסיף פתיח ואין להוסיף סיום. רשום רק את הקטגוריות והידיעות."

    user_prompt = f"""{instructions}

הידיעות לקריאה:
{news_text}"""

    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",  # שם מודל תקין ב-OpenRouter
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=2500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return ""
