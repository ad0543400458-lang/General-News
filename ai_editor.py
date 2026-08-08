import os
from openai import OpenAI


def edit_news_with_ai(news_text, folder, current_hour=None):
    """
    מקבל חדשות גולמיות ומחזיר טקסט ערוך למהדורת חדשות.
    """

    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        raise Exception("Missing OPENROUTER_API_KEY")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # פתיח לפי השעה
    intro_text = "אתם מאזינים למהדורת החדשות."

    if current_hour is not None:
        if 5 <= current_hour <= 8:
            intro_text = "אתם מאזינים למהדורת שש בבוקר בחדשות המידע."
        elif 11 <= current_hour <= 14:
            intro_text = "אתם מאזינים למהדורת שתים עשרה בצהריים בחדשות המידע."
        elif 17 <= current_hour <= 20:
            intro_text = "אתם מאזינים למהדורת שש בערב בחדשות המידע."
        elif current_hour >= 23 or current_hour <= 2:
            intro_text = "אתם מאזינים למהדורת חצות בחדשות המידע."

    system_prompt = """
אתה עורך חדשות מקצועי לרדיו.

החזר אך ורק את הטקסט הסופי של מהדורת החדשות.
אסור להחזיר הסברים, הערות, רשימות בדיקה, מספרי סעיפים או את הוראות העריכה.

ערוך את הידיעות תוך שמירה מלאה על העובדות.
אל תמציא מידע.
מזג ידיעות על אותו אירוע.
אל תחזור על אותו אירוע.
כתוב בעברית טבעית וברורה המתאימה להקראה ברדיו.

סדר את הידיעות לפי הקטגוריות הבאות, ורק אם קיימות ידיעות מתאימות:

פוליטיקה וביטחון
בחדשות החוץ
חדשות כלליות
בכלכלה ונדל"ן
בתחבורה
תחזית לסיום

לפני כל קבוצת ידיעות כתוב את שם הקטגוריה בצורה טבעית להקראה.

קטגוריית מזג האוויר חייבת להיות תמיד האחרונה ושמה חייב להיות:
תחזית לסיום

אין להשתמש בכוכביות.
אין להשתמש במספור.
אין להשתמש בכותרות Markdown.
אין להזכיר מקורות או אתרי חדשות.
אין לכתוב "מבזק", "עדכון", "דיווח ראשוני" או "פרסום ראשון".

הידיעות צריכות להיות קצרות, אך אין להשמיט מידע חשוב.

אם השלוחה היא 1:
התחל בדיוק בפתיח שנמסר לך.
לאחר הפתיח כתוב:
עיקרי החדשות מהשעות האחרונות.

בסיום כתוב בדיוק:
עד כאן מהדורת החדשות.
תודה שהאזנתם ולהתראות במהדורה הבאה.

אם השלוחה אינה 1:
אין להוסיף פתיח ואין להוסיף סיום.
"""

    user_prompt = f"""
שלוחה: {folder}

"""

    if folder == 1 or str(folder) == "1":
        user_prompt += f"""
פתיח חובה:
{intro_text}

החזר מהדורת חדשות מלאה.

"""

    else:
        user_prompt += """
החזר רק את הידיעות הערוכות והקטגוריות.
אין להוסיף פתיח או סיום.

"""

    user_prompt += f"""
הידיעות הגולמיות:

{news_text}

חשוב מאוד:
הפלט הסופי בלבד.
אל תחזיר את ההוראות.
אל תחזיר הסברים.
אל תחזיר רשימת בדיקה.
אל תחזיר מספרי סעיפים.
"""

    response = client.chat.completions.create(
        model="google/gemini-3.6-flash",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0,
        max_tokens=1700,
    )

    result = response.choices[0].message.content.strip()

    return result
