import requests
from datetime import datetime, timedelta
import speech_recognition as sr
import pyttsx3
import sqlite3
import os
import dateutil.parser
from googletrans import Translator
import time
import threading
import random

# Initialize pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 130)
news_api_key = "9418fb20ee6f46ff8fa490b718adece2"
merriam_webster_api_key = "b43367a0-479c-452b-a323-c568ed302b63"

# Get the current script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# SQLite database setup in the same directory
db_file = "database1.db"
db_path = os.path.join(script_dir, db_file)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create events table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT,
        event_time TEXT,
        event_day TEXT,
        event_month TEXT,
        event_date TEXT
    )
''')
conn.commit()

current_year = datetime.now().year

def extract_time_day_and_month(text):
    try:
        parsed_date = dateutil.parser.parse(text, fuzzy=True)
        if "tomorrow" in text.lower():
            parsed_date += timedelta(days=1)
        return (
            parsed_date.strftime("%I:%M %p"),
            parsed_date.strftime("%A"),  # Extract day
            parsed_date.strftime("%B"),
            parsed_date.strftime("%d")  # Extract date
        )
    except ValueError:
        print("Error parsing date and time.")
        return None, None, None, None

def parse_spoken_text(spoken_text):
    # Initialize event_name to None
    event_name = None
    # Extract time, day, month, and date using the helper function extract_time_day_and_month
    event_time, event_day, event_month, event_date = extract_time_day_and_month(spoken_text)

    # Check if the spoken text includes "remind me to" or "schedule a"
    if "remind me to" in spoken_text.lower():
        event_name_split = spoken_text.lower().split("remind me to")
        if len(event_name_split) > 1:
            event_name = event_name_split[1].strip()

    elif "schedule" in spoken_text.lower():
        event_name_split = spoken_text.lower().split("schedule")
        if len(event_name_split) > 1:
            event_name = event_name_split[1].strip()

        
    # If no specific event name is extracted, use a default one ("default_event_name")
    if not event_name:
        event_name = "default_event_name"

    # Return the extracted information
    return event_name, event_time, event_day, event_month, event_date



def get_today_events():
    try:
        # Get the current day and month
        current_day = datetime.now().strftime("%A")
        current_month = datetime.now().strftime("%B")

        # Print current day and month for debugging
        print(f"Current day: {current_day}, Current month: {current_month}")

        # Query the database for events scheduled for today's day and month
        cursor.execute("SELECT event_name, event_time FROM events WHERE event_day = ? AND event_month = ?", (current_day, current_month))
        today_events = cursor.fetchall()

        return today_events
    except Exception as e:
        print(f"Error fetching today's events: {e}")
        return None


        
def get_news(api_key, country_code='in'):
    try:
        url = f'https://newsapi.org/v2/top-headlines?country={country_code}&apiKey={api_key}'
        response = requests.get(url)
        news_data = response.json()
        
        # Extract headlines
        headlines = [article['title'] for article in news_data['articles']]
        
        # Print headlines in the terminal
        for idx, headline in enumerate(headlines, start=1):
            print(f"{idx}. {headline}")

        return headlines
    except Exception as e:
        print(f"Error fetching news: {e}")
        return None

def get_date_from_user():
    while True:
        user_input = input("When would you like to be reminded? ")
        try:
            parsed_date = dateutil.parser.parse(user_input, fuzzy=True)
            return (
                parsed_date.strftime("%I:%M %p"),
                parsed_date.strftime("%A"),  # Extract day
                parsed_date.strftime("%B"),
                parsed_date.strftime("%d")  # Extract date
            )
        except ValueError:
            print("Invalid date. Please provide a valid date like 'tomorrow', '20th January', or 'February 1st'.")


def get_time_from_user():
    while True:
        user_input = input("What time would you like to be reminded? ")
        try:
            parsed_time = dateutil.parser.parse(user_input, fuzzy=True)
            return parsed_time.strftime("%I:%M %p")
        except ValueError:
            print("Invalid time. Please provide a valid time in the format '2:00 PM'.")


def store_event_in_database(event_name, event_time, event_day, event_month, event_date):
    cursor.execute("INSERT INTO events (event_name, event_time, event_day, event_month, event_date) VALUES (?, ?, ?, ?, ?)",
                   (event_name, event_time, event_day, event_month, event_date))
    conn.commit()

    print(f"Event '{event_name}' successfully stored in the database.")

# ...

def schedule_event(event_name, event_time, event_day, event_month, event_date):
    # Check if day and month are provided
    if event_day and event_month:
        event_datetime_str = f"{event_month} {event_date} {current_year} {event_time}"
    else:
        print("Error: Both day and month must be provided for the event.")
        return None

    try:
        # Use dateutil.parser.parse for flexible parsing
        event_datetime = dateutil.parser.parse(event_datetime_str, fuzzy=True)

        # Check if AM or PM is specified in the event_time
        if "am" in event_time.lower() or "pm" in event_time.lower():
            event_datetime_str = event_datetime.strftime("%I:%M %p")  # Use the parsed AM/PM information
        else:
            print("Error: Please specify AM or PM in the event time.")
            return None

    except ValueError:
        print(f"Failed to parse event details: {event_name} at {event_time} on {event_day}, {event_month}")
        return None

    alert_time = event_datetime - timedelta(minutes=15)

    store_event_in_database(event_name, event_datetime_str, event_day, event_month, event_date)  # Store event in the database

    print(f"Event scheduled: {event_name} at {event_datetime_str} on {event_day}, {event_month}, {event_date}")

    return alert_time




def alert_user(event_name, event_time):
    print(f"Event alert: {event_name} at {event_time}")
    engine.say(f"Event alert: {event_name} at {event_time}")
    engine.runAndWait()


def check_scheduled_events():

    try:

        current_date = datetime.now().strftime("%d")
        current_time = datetime.now().strftime("%I:%M %p")
        current_day = datetime.now().strftime("%A")  # Get the current day
        current_month = datetime.now().strftime("%B")  # Get the current month

        

        # Print current date and time for debugging

        print(f"Current date: {current_date}, Current time: {current_time}")

        

        # Query the database for events scheduled for today's date and time

        cursor.execute("SELECT event_name, event_time FROM events WHERE event_date LIKE ? AND event_time <= ?", ('%-{}%'.format(current_date), current_time))

        today_events = cursor.fetchall()

        

        for row in today_events:

            event_name, event_time = row

            

            # Print intermediate values for debugging

            print(f"Event Details: {event_name}, {event_time}")

            

            event_datetime_str = f"{current_date} {current_month} {event_time}"

            

            try:

                # Use datetime.strptime for parsing datetime string

                event_datetime = datetime.strptime(event_datetime_str, "%d %B %I:%M %p")

            except ValueError:

                print(f"Failed to parse event_datetime_str: {event_datetime_str}")

                continue

            

            now = datetime.now()

            

            # Set the alert time 15 minutes before the scheduled event

            alert_time = event_datetime - timedelta(minutes=15)

            

            if now >= alert_time and now <= event_datetime:

                alert_user(event_name, event_time)

                print(f"Alert: Scheduled event '{event_name}' at {event_time} is approaching.")

            

            if now >= event_datetime:

                print(f"Scheduled event arrived: {event_name} at {event_time}")

                formatted_time = event_datetime.strftime("%I:%M %p")

                print(f"The event is scheduled for {formatted_time}")

    except Exception as e:

        print(f"Error checking scheduled events: {e}")



def get_quiz_questions(amount=5, category=19, difficulty="easy"):
    url = f"https://opentdb.com/api.php?amount={amount}&category={category}&difficulty={difficulty}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    else:
        print(f"Failed to fetch quiz questions. Status code: {response.status_code}")
        return []

def ask_question(question, options):
    engine.say(question)
    engine.runAndWait()
    for i, option in enumerate(options, start=1):
        engine.say(f"Option {i}: {option}")
        engine.runAndWait()
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your answer...")
        audio_data = recognizer.listen(source)
        print("Processing your answer...")
        try:
            user_answer = recognizer.recognize_google(audio_data).lower()
            return user_answer
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand your answer. Please try again.")
            return None
        except sr.RequestError:
            print("Failed to reach Google Speech Recognition service.")
            return None

def run_quiz():
    questions = get_quiz_questions()
    if not questions:
        print("No quiz questions available.")
        return
    correct_answers = 0
    total_questions = len(questions)
    engine.say(f"Welcome to the Quiz! You have {total_questions} questions to answer.")
    engine.runAndWait()
    for i, q in enumerate(questions, start=1):
        engine.say(f"Question {i} out of {total_questions}:")
        engine.runAndWait()
        question = q['question']
        options = q['incorrect_answers'] + [q['correct_answer']]
        random.shuffle(options)
        user_answer = ask_question(question, options)
        correct_answer = q['correct_answer'].lower()
        if user_answer == correct_answer:
            engine.say("Correct!")
            engine.runAndWait()
            correct_answers += 1
        else:
            engine.say(f"Wrong! The correct answer is: {correct_answer}")
            engine.runAndWait()
    engine.say(f"Quiz complete! You got {correct_answers} out of {total_questions} questions correct.")
    engine.runAndWait()            
        
        
def get_news_headlines(country='in', category='general', language='en', page_size=5):
    url = f'https://newsapi.org/v2/top-headlines'
    params = {
        'apiKey':'9418fb20ee6f46ff8fa490b718adece2',
        'country': country,
        'category': category,
        'language': language,
        'pageSize': page_size
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get('articles', [])
    else:
        print(f"Failed to fetch news headlines. Status code: {response.status_code}")
        return []



def get_word_meaning(word, api_key):
    url = f"https://www.dictionaryapi.com/api/v3/references/learners/json/{word}?key={api_key}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                if data:
                    meaning = data[0].get('shortdef', ['Meaning not found'])[0]
                    return meaning
                else:
                    return "Meaning not found"
            else:
                return "Meaning not found"
        else:
            return "Meaning not found"

    except Exception as e:
        print(f"Error fetching meaning for '{word}': {e}")
        return "Meaning not found"
        
translator = Translator()


def fetch_random_story():
    url = "https://shortstories-api.onrender.com/"
    response = requests.get(url)
    if response.status_code == 200:
        story_data = response.json()
        return story_data
    else:
        print("Failed to fetch story from the API.")
        return None

def tell_story():
    random_story = fetch_random_story()
    if random_story:
        title = random_story["title"]
        author = random_story["author"]
        story = random_story["story"]

        # Narrate the story
        engine.say(f"Here's a story titled {title}, written by {author}.")
        engine.say(story)
        engine.runAndWait()
    else:
        engine.say("Sorry, I couldn't fetch a story at the moment. Please try again later.")
        engine.runAndWait()


def separate_event_name_and_time(event_name, event_time):
    # Split event time from the event name
    parts = event_name.split(" at ")
    if len(parts) == 2:
        event_name = parts[0].strip()  # Event name without time
        event_time = parts[1].strip()  # Event time
        
    return event_name, event_time

def start_translation():
    engine.say("Which language would you like to translate to?")
    engine.runAndWait()
    target_language = get_user_input()
    if target_language:
        engine.say("Please speak your sentence to translate...")
        engine.runAndWait()
        spoken_text = get_user_input()
        if spoken_text:
            translated_text = translate_text(spoken_text, target_language)
            if translated_text:
                engine.say(f"The translation to {target_language} is: {translated_text}")
                engine.runAndWait()
            else:
                engine.say("Failed to translate. Please try again.")
                engine.runAndWait()
        else:
            engine.say("No input received. Ending translation.")
            engine.runAndWait()
    else:
        engine.say("No target language received. Ending translation.")
        engine.runAndWait()

def get_user_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio_data = recognizer.listen(source)
    try:
        user_input = recognizer.recognize_google(audio_data)
        return user_input
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return None
    except sr.RequestError:
        print("Sorry, I couldn't request results.")
        return None

def translate_text(text, target_language='en'):
    try:
        translation = translator.translate(text, dest=target_language)
        return translation.text
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def recognize_and_respond():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        recognizer.dynamic_energy_threshold = 3000

        while True:
            try:
                print("Listening... ")
                audio_data = recognizer.listen(source, timeout=None)

                spoken_text = recognizer.recognize_google(audio_data)
                print(spoken_text)

                if "jarvis" in spoken_text.lower():
                    print(f"Recognized text: {spoken_text}")

                    if "can you hear me" in spoken_text.lower():
                        engine.say("Yes, I can hear you.")
                        engine.runAndWait()
                    elif "tell me a story" in spoken_text.lower():
                        tell_story();
                    elif "ask me a quiz" in spoken_text.lower():
                        print(f"Recognized text: {spoken_text}")
                        run_quiz()
                    elif "start translation" in spoken_text.lower():
                        start_translation()        
                    elif any(keyword in spoken_text.lower() for keyword in ["today's news", "what's in the news", "news today"]):
                        # Fetch and print today's news headlines
                        headlines = get_news_headlines()
                        if headlines:
                            print("\nToday's News Headlines:")
                            for idx, article in enumerate(headlines, start=1):
                                title = article.get('title', 'N/A')
                                try:
                                    print(f"{idx}. {title}")
                                    engine.say(f"Headline {idx}: {title}")  # Read out the headline
                                    engine.runAndWait()
                                except UnicodeEncodeError:
                                    print(f"{idx}. Unable to display headline due to encoding issue.")
                                    engine.say(f"Headline {idx}: Unable to display headline due to encoding issue.")
                                    engine.runAndWait()
                            print("\n")
                            engine.say("Those were today's top news headlines.")
                            engine.runAndWait()
                        else:
                            print("Sorry, I couldn't fetch the news headlines.")
                            engine.say("Sorry, I couldn't fetch the news headlines.")
                            engine.runAndWait()
                    elif "define" in spoken_text.lower():
                        words = spoken_text.lower().split("define")
                        if len(words) > 1:
                            word_to_define = words[1].strip()
                            meaning = get_word_meaning(word_to_define, merriam_webster_api_key)
                            if meaning:
                                print(f"The meaning of '{word_to_define}' is: {meaning}")
                                engine.say(f"The meaning of '{word_to_define}' is: {meaning}")
                                engine.runAndWait()
                            else:
                                print(f"Failed to fetch meaning for '{word_to_define}'.")
                                engine.say(f"Failed to fetch meaning for '{word_to_define}'.")
                                engine.runAndWait()
                        else:
                            print("No word specified for definition.")
                            engine.say("No word specified for definition.")
                            engine.runAndWait()
                    elif "translate the word" in spoken_text.lower():
                        words = spoken_text.lower().split("translate the word")
                        if len(words) > 1:
                            word_to_translate = words[1].strip().split()[0]
                            target_language = words[1].strip().split()[-1]
                            translated_text = translate_text(word_to_translate, target_language)
                            if translated_text:
                                print(f"The translation of '{word_to_translate}' to {target_language.capitalize()} is: {translated_text.encode('utf-8')}")
                                engine.say(f"The translation of '{word_to_translate}' to {target_language.capitalize()} is: {translated_text}")
                                engine.runAndWait()
                            else:
                                print(f"Failed to translate '{word_to_translate}' to {target_language.capitalize()}.")
                                engine.say(f"Failed to translate '{word_to_translate}' to {target_language.capitalize()}.")
                                engine.runAndWait()
                        else:
                            print("No word specified for translation.")
                            engine.say("No word specified for translation.")
                            engine.runAndWait()
                        # Fetch today's events from the database
                    elif "today events" in spoken_text.lower():
                        # Fetch today's events from the database
                        today_events = get_today_events()
                        if today_events:
                            print("\nToday's Events:")
                            for idx, event in enumerate(today_events, start=1):
                                event_name, event_time = event
                                print(f"{idx}. {event_name} at {event_time}")
                                engine.say(f"Event {idx}: {event_name} at {event_time}")
                                engine.runAndWait()
                        else:
                            print("No events scheduled for today.")
                            engine.say("No events scheduled for today.")
                            engine.runAndWait()
                    else:
                        event_name, event_time, event_day, event_month, event_date = parse_spoken_text(spoken_text)
                        if event_name and event_time and event_month and event_date:
                            response = f"Scheduled: {event_name} at {event_time} on {event_day}, {event_month}, {event_date}"
                            engine.say(response)
                            engine.runAndWait()
                            alert_time = schedule_event(event_name, event_time, event_day, event_month, event_date)
                            # Continuous checking for scheduled events
                            event_details = check_scheduled_events()
                            if event_details:
                                response = f"Scheduled event arrived: {event_details[0]} at {event_details[1]}"
                                engine.say(response)
                                engine.runAndWait()
                        else:
                            print("Failed to parse event details.")
            except sr.UnknownValueError:
                print("Didn't recognize anything.")
            except sr.RequestError as e:
                print(f"Error with the Google Speech Recognition service: {e}")


if __name__ == "__main__":

    try:
        recognize_and_respond()

    except KeyboardInterrupt:

        print("\nExiting the program.")

        conn.close()


