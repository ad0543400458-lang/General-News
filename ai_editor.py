import os
from openai import OpenAI


def edit_news_with_ai(news_text):
    """
    מקבל חדשות גולמיות ומחזיר טקסט ערוך למהדורת חדשות
    """

    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        raise Exception("Missing OPENROUTER_API_KEY")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    prompt = f"""
אתה עורך חדשות מקצועי בעברית.

קיבלת רשימת ידיעות שכבר נאספו ממקורות אמיתיים.

המשימה שלך:
- להפוך אותן למהדורת חדשות זורמת להקראה.
- לא להוסיף שום מידע שלא קיים בטקסט.
- לא להמציא פרטים.
- לא לשנות עובדות.
- להסיר כפילויות.
- לסדר לפי נושאים.
- לכתוב עברית תקינה וברורה.

אין להזכיר שמות אתרים.
אין לכתוב סימנים מיוחדים.
הטקסט מיועד לקריינות קולית.

הידיעות:

{news_text}
"""

    response = client.chat.completions.create(
        model="qwen/qwen-2.5-72b-instruct:free",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()
