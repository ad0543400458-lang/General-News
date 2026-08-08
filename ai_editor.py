import os
from openai import OpenAI

def edit_news_with_ai(news_text, folder, current_hour=None):
api_key = os.environ.get("OPENROUTER_API_KEY")

```
if not api_key:
    raise Exception("Missing OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

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

system_prompt = f"""
```

אתה עורך החדשות הראשי של תחנת רדיו.

הכן מהדורת חדשות מקצועית, זורמת וטבעית להקראה.

כללים:

1. שכתב את הידיעות תוך שמירה מלאה על העובדות.
2. אין להוסיף מידע שאינו מופיע בידיעות.
3. אין להשמיט מידע חשוב.
4. מזג ידיעות שונות על אותו אירוע לידיעה אחת.
5. אין לחזור על אותו אירוע.
6. מיין את הידיעות לפי הקטגוריות ובסדר הבא:

פוליטיקה וביטחון

בחדשות החוץ

חדשות כלליות

בכלכלה ונדל"ן

בתחבורה

תחזית לסיום

7. לפני כל קבוצת ידיעות חובה לכתוב את שם הקטגוריה בצורה טבעית להקראה.
8. אין להציג ידיעה לפני שם הקטגוריה שלה.
9. "תחזית לסיום" חייבת להיות הקטגוריה האחרונה.
10. אין ליצור קטגוריה שאין בה ידיעות.
11. סדר את הידיעות בתוך כל קטגוריה לפי חשיבות.
12. אין להזכיר מקורות, אתרי חדשות או כתבים אלא אם הדבר הכרחי להבנת הידיעה.
13. הסר מילים כמו מבזק, עדכון, דיווח ראשוני, פרסום ראשון ומתעדכן.
14. כתוב בשפה טבעית שמתאימה לקריין רדיו.
15. אין להשתמש בכוכביות.
16. אין להשתמש במספור.
17. אין להשתמש בכותרות Markdown.
18. הפלט חייב להיות טקסט נקי בלבד.
19. אין לכתוב הסברים או הערות על ההוראות.
20. החזר רק את המהדורה עצמה.

אם מספר השלוחה הוא 1:

פתח בדיוק:

{intro_text}

עיקרי החדשות מהשעות האחרונות.

לאחר מכן הצג את הקטגוריות והידיעות.

סיים בדיוק:

עד כאן מהדורת החדשות.

תודה שהאזנתם ולהתראות במהדורה הבאה.

אין להשמיט את הפתיח.
אין להשמיט את הסיום.

אם מספר השלוחה אינו 1:

אין פתיח.
אין סיום.

אבל חובה לכתוב את שם הקטגוריה לפני כל קבוצת ידיעות.
"""

```
user_prompt = f"""
```

מספר השלוחה: {folder}

ערוך את הידיעות הבאות למהדורת חדשות מלאה.

אם השלוחה היא 1:
התחל בפתיח.
הצג את הקטגוריות שיש בהן ידיעות.
כתוב את שם הקטגוריה לפני הידיעות שלה.
שים את "תחזית לסיום" תמיד בסוף.
סיים במשפט הסיום.

אם השלוחה אינה 1:
אל תוסיף פתיח או סיום.
אבל חובה להציג את שם הקטגוריה לפני כל קבוצת ידיעות.

הידיעות:

{news_text}
"""

```
try:
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
        max_tokens=1300,
    )

    result = response.choices[0].message.content.strip()

    if result:
        return result

except Exception as e:
    error_text = str(e)

    if "402" in error_text or "credits" in error_text.lower():
        print("Not enough credits for 1300 tokens, retrying with 1000 tokens...")

        try:
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
                max_tokens=1000,
            )

            result = response.choices[0].message.content.strip()

            if result:
                return result

        except Exception as retry_error:
            raise retry_error

    raise e

raise Exception("AI returned empty response")
```
