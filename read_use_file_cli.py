#!/usr/bin/env python3
"""
Simple utility to read use-*.txt files aloud
Enhanced with better voice handling and interruption support
"""
import argparse
import glob
import os
import re
import signal
import sys
import threading
import time

try:
    import pyttsx3
except ImportError:
    print("Installing pyttsx3...")
    import subprocess

    subprocess.call([sys.executable, "-m", "pip", "install", "pyttsx3"])
    import pyttsx3

# Global variables for interrupt handling
reading_active = False
current_engine = None
interrupt_requested = False
engine_lock = threading.Lock()


def signal_handler(signum, frame):
    """Handle Ctrl+C interrupt signal with proper audio cleanup"""
    global interrupt_requested, current_engine, reading_active

    print("\n\n🛑 Stopping TTS...")
    interrupt_requested = True
    reading_active = False

    # Give a moment for audio to finish gracefully
    time.sleep(0.1)

    with engine_lock:
        if current_engine:
            try:
                current_engine.stop()
            except Exception:
                pass  # Ignore errors during emergency stop

    print("✅ Stopped. Goodbye!")
    # Use os._exit to avoid any cleanup that might hang
    os._exit(0)


# Set up signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)


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
    text = re.sub(r"```[^`]*```", " code block omitted ", text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r"`[^`]*`", " code omitted ", text)
    # Remove headers
    text = re.sub(r"^#+ ", "", text, flags=re.MULTILINE)
    # Clean up URLs
    text = re.sub(r"https?://\S+", " URL link ", text)
    # Remove excessive whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r" +", " ", text)
    return text.strip()


def setup_female_voice(engine):
    """Set up a female voice if available with better error handling"""
    try:
        # Get all available voices
        voices = engine.getProperty("voices")

        if not voices:
            print("No voices available, using default")
            return False

        print(f"Found {len(voices)} voices available")

        # Look for female voices (common patterns)
        female_patterns = ["female", "zira", "hazel", "susan", "victoria", "karen"]
        english_patterns = ["english", "en-", "en_"]

        best_voice = None
        fallback_voice = None

        for voice in voices:
            voice_id = voice.id.lower() if voice.id else ""
            voice_name = voice.name.lower() if voice.name else ""

            # Check if it's English
            is_english = any(
                pattern in voice_id or pattern in voice_name
                for pattern in english_patterns
            )

            if is_english:
                fallback_voice = voice

                # Check if it's female
                is_female = any(
                    pattern in voice_id or pattern in voice_name
                    for pattern in female_patterns
                )

                if is_female:
                    best_voice = voice
                    break

        # Use best available voice
        selected_voice = best_voice or fallback_voice

        if selected_voice:
            engine.setProperty("voice", selected_voice.id)
            print(f"Using voice: {selected_voice.name}")
            return True
        else:
            print("No suitable voice found, using default")
            return False

    except Exception as e:
        print(f"Error setting up voice: {e}")
        return False


def chunk_text(text, max_chunk_size=400):  # Smaller chunks for better responsiveness
    """Split text into smaller chunks to prevent TTS engine issues"""
    # Split by sentences first
    sentences = re.split(r"[.!?]+", text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If adding this sentence would exceed max size, start new chunk
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
        else:
            current_chunk += sentence + ". "

    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def speak_chunk_safe(engine, text):
    """Safely speak a chunk with proper error handling"""
    global interrupt_requested

    if interrupt_requested:
        return False

    try:
        with engine_lock:
            if not interrupt_requested and current_engine:
                engine.say(text)
                # Use shorter timeout for runAndWait to be more responsive
                engine.runAndWait()
        return not interrupt_requested
    except Exception as e:
        # Suppress audio system errors during interruption
        if not interrupt_requested:
            print(f"Audio error (continuing): {e}")
        return False


def read_text(file_path, rate=150):
    """Read the file aloud with improved error handling and chunking"""
    global reading_active, current_engine, interrupt_requested

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            print("File is empty or contains no readable text")
            return

        # Initialize TTS engine
        print("🔧 Initializing TTS engine...")
        with engine_lock:
            engine = pyttsx3.init()
            current_engine = engine

        # Set properties
        engine.setProperty("rate", rate)
        engine.setProperty("volume", 1.0)

        # Set up voice
        setup_female_voice(engine)

        # Clean text for better reading
        clean_content = clean_text(content)

        if not clean_content.strip():
            print("No readable content after cleaning")
            return

        # Split into smaller chunks for better responsiveness
        chunks = chunk_text(clean_content, 400)

        print(f"📖 Reading {os.path.basename(file_path)} ({len(chunks)} parts)")
        print("⚠️  Press Ctrl+C to stop")
        print("-" * 50)

        reading_active = True
        interrupt_requested = False

        # Read each chunk
        for i, chunk in enumerate(chunks, 1):
            if interrupt_requested or not reading_active:
                print("🛑 Interrupted")
                break

            try:
                # Show what's being read
                preview = chunk[:60] + "..." if len(chunk) > 60 else chunk
                print(f"🔊 [{i}/{len(chunks)}] {preview}")

                # Speak the chunk safely
                if not speak_chunk_safe(engine, chunk):
                    break

                # Brief pause with interrupt checking
                for _ in range(2):  # 0.2 second pause
                    if interrupt_requested:
                        break
                    time.sleep(0.1)

            except Exception as e:
                if not interrupt_requested:
                    print(f"❌ Error in chunk {i}: {e}")
                continue

        if not interrupt_requested:
            print("✅ Reading completed!")

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        reading_active = False
        with engine_lock:
            try:
                if current_engine:
                    current_engine.stop()
                    current_engine = None
            except:
                pass


def test_tts():
    """Test TTS functionality"""
    global current_engine
    try:
        print("🧪 Testing TTS...")
        with engine_lock:
            engine = pyttsx3.init()
            current_engine = engine

        engine.setProperty("rate", 150)
        setup_female_voice(engine)

        print("🔊 Test message (Ctrl+C to stop)...")
        engine.say("TTS test. Press Control C to stop.")
        engine.runAndWait()
        print("✅ Test completed")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        with engine_lock:
            current_engine = None


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Read use-*.txt files aloud")
    parser.add_argument("-l", "--list", action="store_true", help="List files")
    parser.add_argument("-f", "--file", help="File name or number")
    parser.add_argument("-r", "--rate", type=int, default=150, help="Speech rate")
    parser.add_argument("-t", "--test", action="store_true", help="Test TTS")
    args = parser.parse_args()

    print("🎤 TTS File Reader")
    print("⚡ Ctrl+C Support")
    print("=" * 25)

    if args.test:
        test_tts()
        return

    use_files = find_use_files()

    if not use_files:
        print("❌ No use-*.txt files found!")
        return

    if args.list or not args.file:
        print(f"📁 Found {len(use_files)} files:")
        for i, file_path in enumerate(use_files):
            print(f"  {i+1}: {os.path.basename(file_path)}")

    if args.file:
        try:
            idx = int(args.file) - 1
            if 0 <= idx < len(use_files):
                read_text(use_files[idx], args.rate)
            else:
                print("❌ Invalid number!")
        except ValueError:
            matches = [f for f in use_files if args.file in os.path.basename(f)]
            if matches:
                read_text(matches[0], args.rate)
            else:
                print(f"❌ No file matching '{args.file}'")
    elif not args.list:
        try:
            selection = input("\n🎯 Enter file number (q to quit): ")
            if selection.lower() != "q":
                idx = int(selection) - 1
                if 0 <= idx < len(use_files):
                    read_text(use_files[idx], args.rate)
                else:
                    print("❌ Invalid selection!")
        except (ValueError, KeyboardInterrupt):
            print("\n🚪 Cancelled")


if __name__ == "__main__":
    main()
