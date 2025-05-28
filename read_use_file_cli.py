#!/usr/bin/env python3
"""
Simple utility to read use-*.txt files aloud
"""
import os
import glob
import sys
import argparse
import re

try:
    import pyttsx3
except ImportError:
    print("Installing pyttsx3...")
    import subprocess
    subprocess.call([sys.executable, "-m", "pip", "install", "pyttsx3"])
    import pyttsx3

def find_use_files():
    """Find all use-*.txt files in the current directory and subdirectories"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    use_files = []
    
    # Track filenames to avoid duplicates
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
    """Prepare text for reading by removing markdown elements"""
    # Remove code blocks
    text = re.sub(r'```[^`]*```', ' code block omitted ', text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`[^`]*`', ' code omitted ', text)
    # Remove headers
    text = re.sub(r'^#+ ', '', text, flags=re.MULTILINE)
    # Clean up URLs
    text = re.sub(r'https?://\S+', ' URL link ', text)
    return text

def setup_female_voice(engine):
    """Set up a female voice if available"""
    try:
        # Get all available voices
        voices = engine.getProperty('voices')
        
        # Find an English voice to use as base
        english_voice = None
        for voice in voices:
            if "english" in voice.id.lower():
                english_voice = voice
                break
        
        if english_voice:
            # Configure for female voice using espeak variant
            # In espeak, adding '+f3' to the voice ID makes it female
            fem_voice = english_voice.id + '+f3'
            engine.setProperty('voice', fem_voice)
            return True
    except Exception as e:
        print(f"Could not set female voice: {e}")
    
    return False

def read_text(file_path, rate=150):
    """Read the file aloud"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Initialize TTS engine
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        
        # Set up female voice
        if setup_female_voice(engine):
            print("Using female voice")
        else:
            print("Using default voice")
        
        # Clean text for better reading
        clean_content = clean_text(content)
        
        # Read the text
        print(f"Reading {os.path.basename(file_path)}... Press Ctrl+C to stop.")
        engine.say(clean_content)
        engine.runAndWait()
        
    except KeyboardInterrupt:
        print("\nReading stopped.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Read use-*.txt files aloud")
    parser.add_argument('-l', '--list', action='store_true', help='List available files')
    parser.add_argument('-f', '--file', help='Specific file name or number to read')
    parser.add_argument('-r', '--rate', type=int, default=150, help='Speech rate (default: 150)')
    args = parser.parse_args()
    
    # Get all use files
    use_files = find_use_files()
    
    if not use_files:
        print("No use-*.txt files found!")
        return
    
    # List files if requested
    if args.list or not args.file:
        print(f"Found {len(use_files)} use files:")
        for i, file_path in enumerate(use_files):
            print(f"{i+1}: {os.path.basename(file_path)}")
    
    # Read specified file or prompt for selection
    if args.file:
        # Check if it's a number
        try:
            idx = int(args.file) - 1
            if 0 <= idx < len(use_files):
                read_text(use_files[idx], args.rate)
            else:
                print("Invalid file number!")
        except ValueError:
            # Try to find by name
            matches = [f for f in use_files if args.file in os.path.basename(f)]
            if matches:
                read_text(matches[0], args.rate)
            else:
                print(f"No file matching '{args.file}' found")
    elif not args.list:
        # Prompt for selection
        try:
            selection = input("\nEnter file number to read (q to quit): ")
            if selection.lower() != 'q':
                idx = int(selection) - 1
                if 0 <= idx < len(use_files):
                    read_text(use_files[idx], args.rate)
                else:
                    print("Invalid selection!")
        except (ValueError, KeyboardInterrupt):
            print("Operation cancelled")

if __name__ == "__main__":
    main()