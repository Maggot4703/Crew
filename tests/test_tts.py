#!/usr/bin/env python3
import pyttsx3

print("Testing female voice...")
engine = pyttsx3.init()

# Get voice properties
voices = engine.getProperty("voices")

# Find an English voice
english_voice = None
for voice in voices:
    if "english" in voice.id.lower():
        english_voice = voice
        print(f"Found English voice: {voice.id}")
        break

if english_voice:
    # Configure for female voice using espeak variant
    # In espeak, adding '+f3' to the voice ID makes it female
    fem_voice = english_voice.id + "+f3"
    engine.setProperty("voice", fem_voice)
    print(f"Set female voice: {fem_voice}")

    # Test the voice
    engine.say("This is a test of the female voice in text to speech.")
    print("Running engine...")
    engine.runAndWait()
else:
    print("No English voice found")

print("Test completed.")
