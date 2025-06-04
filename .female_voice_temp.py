#!/usr/bin/env python3
import glob
import os
import re
import sys

import pyttsx3


def find_use_files():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    use_files = []
    filenames_seen = set()

    for root, _, _ in os.walk(base_dir):
        files = glob.glob(os.path.join(root, "use-*.txt"))
        for file_path in files:
            filename = os.path.basename(file_path)
            if filename not in filenames_seen:
                use_files.append(file_path)
                filenames_seen.add(filename)

    return sorted(use_files)


def clean_text(text):
    text = re.sub(r"]*[^", " code omitted ", text)
    text = re.sub(r"^#+ ", "", text, flags=re.MULTILINE)
    text = re.sub(r"https?://\S+", " URL link ", text)
    return text


def setup_female_voice(engine):
    try:
        voices = engine.getProperty("voices")
        english_voice = None
        for voice in voices:
            if "english" in voice.id.lower():
                english_voice = voice
                break

        if english_voice:
            fem_voice = english_voice.id + "+f3"
            engine.setProperty("voice", fem_voice)
            return True
    except Exception as e:
        print(f"Could not set female voice: {e}")
    return False


def read_file(filename):
    files = find_use_files()
    found = False

    for file_path in files:
        if filename.lower() in file_path.lower():
            print(f"Reading {file_path}... Press Ctrl+C to stop.")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                engine = pyttsx3.init()
                engine.setProperty("rate", 150)

                if setup_female_voice(engine):
                    print("Using female voice")

                clean_content = clean_text(content)
                engine.say(clean_content)
                engine.runAndWait()
                found = True
                break
            except Exception as e:
                print(f"Error: {e}")
                break

    if not found:
        print(f"No use file matching '{filename}' found.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        read_file(sys.argv[1])
