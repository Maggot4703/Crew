
import pyaudio
import wave
import threading
import os
import sys
import subprocess
import logging

# Robust logging setup: always write to absolute crew_gui.log, force flush
log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'crew_gui.log'))
logger = logging.getLogger("audio_manager")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - AUDIO - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    handler.flush = handler.stream.flush  # Ensure flush is available

def log_info(msg):
    logger.info(msg)
    for h in logger.handlers:
        h.flush()

def log_error(msg):
    logger.error(msg)
    for h in logger.handlers:
        h.flush()

RECORD_SECONDS = 60 * 10  # Max 10 minutes
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Default, will auto-detect per device
RATE = 16000

def start_recording(device=None, output_path=None):
    """Start recording from the specified device. Returns (path, process/thread)."""
    try:
        pa = pyaudio.PyAudio()
        device_index = None
        channels_to_try = []
        if device:
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if device in info.get('name', ''):
                    device_index = i
                    max_channels = int(info.get('maxInputChannels', 1))
                    # Try maxInputChannels first, then 1, then 2 (if not already tried)
                    if max_channels > 0:
                        channels_to_try.append(max_channels)
                    if 1 not in channels_to_try:
                        channels_to_try.append(1)
                    if 2 not in channels_to_try:
                        channels_to_try.append(2)
                    break
        else:
            channels_to_try = [CHANNELS, 1, 2]
        if output_path is None:
            output_path = os.path.abspath("recording.wav")
        last_error = None
        stream = None
        for channels in channels_to_try:
            try:
                log_info(f"Attempting to start recording: device={device} (index={device_index}), output={output_path}, channels={channels}")
                stream = pa.open(format=FORMAT, channels=channels, rate=RATE, input=True,
                                frames_per_buffer=CHUNK, input_device_index=device_index)
                log_info(f"Recording started successfully with channels={channels}")
                break
            except Exception as e:
                log_error(f"Failed to open stream with channels={channels}: {e}")
                last_error = e
                stream = None
        if not stream:
            log_error(f"All attempts to start recording failed for device={device} (index={device_index})")
            raise last_error if last_error else RuntimeError("Could not open audio stream.")
        frames = []
        stop_flag = threading.Event()
        def record():
            try:
                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    if stop_flag.is_set():
                        break
                    data = stream.read(CHUNK)
                    frames.append(data)
                stream.stop_stream()
                stream.close()
                pa.terminate()
                with wave.open(output_path, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(pa.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                log_info(f"Recording finished and saved: {output_path}")
            except Exception as e:
                log_error(f"Error during recording: {e}")
        t = threading.Thread(target=record, daemon=True)
        t.start()
        return output_path, (t, stop_flag)
    except Exception as e:
        logging.error(f"Failed to start recording: {e}")
        raise

def stop_recording(process):
    """Stop the recording process/thread."""
    try:
        t, stop_flag = process
        stop_flag.set()
        t.join(timeout=5)
        log_info("Recording stopped by user.")
    except Exception as e:
        log_error(f"Failed to stop recording: {e}")
        raise

def play_audio(path):
    """Play a WAV file using system default or pyaudio."""
    try:
        log_info(f"Playing audio: {path}")
        if sys.platform.startswith('linux'):
            # Try aplay or paplay
            for player in ['aplay', 'paplay', 'play']:
                if subprocess.call(['which', player], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    subprocess.Popen([player, path])
                    return
        elif sys.platform == 'darwin':
            subprocess.Popen(['afplay', path])
            return
        elif sys.platform == 'win32':
            os.startfile(path)
            return
        # Fallback: try pyaudio
        pa = pyaudio.PyAudio()
        wf = wave.open(path, 'rb')
        stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                         channels=wf.getnchannels(),
                         rate=wf.getframerate(),
                         output=True)
        data = wf.readframes(CHUNK)
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK)
        stream.stop_stream()
        stream.close()
        pa.terminate()
        wf.close()
        log_info(f"Audio playback finished: {path}")
    except Exception as e:
        log_error(f"Failed to play audio {path}: {e}")
        raise

def save_audio(src_path, dest_path):
    """Copy WAV file from src to dest."""
    try:
        with open(src_path, 'rb') as fsrc, open(dest_path, 'wb') as fdst:
            fdst.write(fsrc.read())
        log_info(f"Audio file saved: {src_path} -> {dest_path}")
    except Exception as e:
        log_error(f"Failed to save audio {src_path} to {dest_path}: {e}")
        raise
