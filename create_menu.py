from gtts import gTTS
from pydub import AudioSegment

text = """
ברוכים הבאים לחדשות המידע.
לחדשות הקישו 1.
לחדשות בית שמש הקישו 2.
לחדשות אורחות הקישו 3.
לחדשות טבריה הקישו 4.
לחדשות רמת שלמה הקישו 5.
"""

# יצירת MP3
tts = gTTS(text, lang="iw")
tts.save("menu.mp3")

# המרה ל-WAV מתאים לקו טלפוני
audio = AudioSegment.from_mp3("menu.mp3")

audio = audio.speedup(
    playback_speed=1.25
)

audio = audio.set_frame_rate(8000)
audio = audio.set_channels(1)

audio.export(
    "menu.wav",
    format="wav"
)

print("נוצר הקובץ menu.wav")
