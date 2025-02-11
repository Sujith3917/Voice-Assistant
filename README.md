# 🎙Voice Assistant
A personal voice assistant built using Raspberry Pi 4, a microphone, and a speaker. It can recognize speech, schedule reminders, fetch news, define words, translate text, and more!
# 🛠 Features
✅ Speech Recognition – Understands voice commands using Google Speech API.

✅ Text-to-Speech (TTS) – Responds with spoken answers using pyttsx3.

✅ Event Scheduling – Stores and reminds events using SQLite.

✅ News Updates – Fetches top news headlines.

✅ Dictionary & Translation – Defines words and translates text.

✅ Storytelling & Quizzes – Reads short stories and asks quiz questions.
# 📦 Installation
# 1️⃣ Update Raspberry Pi
sudo apt update && sudo apt upgrade -y
# 2️⃣ Install Dependencies
sudo apt install python3 python3-pip sqlite3 espeak flac portaudio19-dev alsa-utils -y

pip3 install speechrecognition pyttsx3 requests googletrans-python dateutil pyaudio
# 3️⃣ Clone the Repository
git clone https://github.com/Sujith3917/Voice Assistant.git
cd Voice Assistant
# 4️⃣ Set Up API Keys
Get a News API Key from NewsAPI.

Get a Dictionary API Key from Merriam-Webster.

Update Voice Assistant.py with your keys:

news_api_key = "YOUR_NEWSAPI_KEY"

merriam_webster_api_key = "YOUR_DICTIONARY_API_KEY"
# 🚀 Running the Assistant
python3 Voice Assistant.py

