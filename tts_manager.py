import logging
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from typing import Optional, List, Callable
import re
import os

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class TTSManager:
    """Manages all Text-to-Speech functionality for the application."""
    
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.engine = None
        self.is_speaking = False
        self.speech_thread = None
        
        if TTS_AVAILABLE:
            self._initialize_engine()
        
    def _initialize_engine(self) -> bool:
        """Initialize the TTS engine with default settings."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)
            self.engine.setProperty("volume", 0.8)
            self.engine.setProperty("voice", "english")
            
            # Load saved settings if available
            if self.config:
                self._load_settings()
                
            return True
        except Exception as e:
            logging.error(f"Failed to initialize TTS engine: {e}")
            return False
    
    @property
    def is_available(self) -> bool:
        """Check if TTS functionality is available."""
        return TTS_AVAILABLE and self.engine is not None
    
    def speak_text(self, text: str, background: bool = True) -> None:
        """Speak the provided text."""
        if not self.is_available:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return
            
        if not text.strip():
            return
            
        # Clean and preprocess text
        cleaned_text = self.preprocess_text_for_speech(text)
        
        if background:
            self._speak_in_background(cleaned_text)
        else:
            self._speak_direct(cleaned_text)
    
    def _speak_direct(self, text: str) -> None:
        """Speak text directly (blocking)."""
        try:
            chunks = self.chunk_text(text)
            for chunk in chunks:
                self.engine.say(chunk)
            self.engine.runAndWait()
        except Exception as e:
            logging.error(f"TTS playback error: {e}")
            messagebox.showerror("TTS Error", f"Failed to read text: {e}")
    
    def _speak_in_background(self, text: str) -> None:
        """Speak text in a background thread."""
        if self.is_speaking:
            self.stop_speech()
            
        self.speech_thread = threading.Thread(
            target=self._speak_direct, 
            args=(text,), 
            daemon=True
        )
        self.is_speaking = True
        self.speech_thread.start()
    
    def stop_speech(self) -> None:
        """Stop current speech playback."""
        if not self.is_available:
            return
            
        try:
            self.engine.stop()
            self.is_speaking = False
        except Exception as e:
            logging.error(f"Error stopping TTS: {e}")
    
    def pause_speech(self) -> None:
        """Pause current speech playback."""
        if not self.is_available:
            return
        try:
            self.engine.pause()
        except Exception as e:
            logging.error(f"Error pausing TTS: {e}")
    
    def resume_speech(self) -> None:
        """Resume paused speech playback."""
        if not self.is_available:
            return
        try:
            self.engine.resume()
        except Exception as e:
            logging.error(f"Error resuming TTS: {e}")
    
    def preprocess_text_for_speech(self, text: str) -> str:
        """Clean and prepare text for better TTS pronunciation."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle common abbreviations and technical terms
        replacements = {
            'CSV': 'C S V', 'JSON': 'Jason', 'XML': 'X M L', 'HTML': 'H T M L',
            'URL': 'U R L', 'API': 'A P I', 'GUI': 'G U I', 'CLI': 'C L I',
            'DB': 'database', 'SQL': 'S Q L', 'ID': 'I D', 'UUID': 'U U I D',
            'HTTP': 'H T T P', 'HTTPS': 'H T T P S', 'FTP': 'F T P', 'SSH': 'S S H',
            'TCP': 'T C P', 'UDP': 'U D P', 'IP': 'I P', 'DNS': 'D N S',
            'CPU': 'C P U', 'GPU': 'G P U', 'RAM': 'ram', 'ROM': 'rom',
            'USB': 'U S B', 'PDF': 'P D F', 'JPG': 'J P G', 'PNG': 'P N G',
            'GIF': 'gif', 'MP3': 'M P 3', 'MP4': 'M P 4', 'WAV': 'wave',
            'ZIP': 'zip', 'RAR': 'rar', 'TAR': 'tar', 'GZ': 'G Z',
            'EXE': 'executable', 'DLL': 'D L L', 'SO': 'S O', 'LIB': 'library',
        }
        
        for abbrev, replacement in replacements.items():
            text = re.sub(r'\b' + re.escape(abbrev) + r'\b', replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def chunk_text(self, text: str, max_length: int = 400) -> List[str]:
        """Split text into smaller chunks for smoother playback."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 > max_length:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(word)
            current_length += len(word) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
    
    def setup_female_voice(self) -> bool:
        """Attempt to set up a female voice if available."""
        if not self.is_available:
            return False
            
        try:
            voices = self.engine.getProperty('voices')
            if not voices:
                return False
            
            # Look for female voices
            female_indicators = ['female', 'zira', 'hazel', 'susan', 'anna', 'catherine']
            
            for voice in voices:
                voice_name = voice.name.lower() if voice.name else ''
                voice_id = voice.id.lower() if voice.id else ''
                
                if any(indicator in voice_name or indicator in voice_id for indicator in female_indicators):
                    self.engine.setProperty('voice', voice.id)
                    return True
            
            # If no female voice found, use the second voice if available
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
                return True
                
            return False
        except Exception as e:
            logging.error(f"Error setting up female voice: {e}")
            return False
    
    def show_settings_dialog(self, parent_window) -> None:
        """Show TTS configuration dialog."""
        if not self.is_available:
            messagebox.showinfo("TTS Not Available", "Text-to-speech functionality is not available.")
            return
        
        try:
            settings_window = tk.Toplevel(parent_window)
            settings_window.title("Speech Settings")
            settings_window.geometry("400x350")
            settings_window.transient(parent_window)
            settings_window.grab_set()
            
            # Voice selection
            ttk.Label(settings_window, text="Voice:").pack(pady=5)
            voices = self.engine.getProperty('voices')
            voice_names = [voice.name for voice in voices] if voices else ['Default']
            
            voice_var = tk.StringVar()
            current_voice = self.engine.getProperty('voice')
            for voice in voices:
                if voice.id == current_voice:
                    voice_var.set(voice.name)
                    break
            else:
                voice_var.set(voice_names[0] if voice_names else 'Default')
            
            voice_combo = ttk.Combobox(settings_window, textvariable=voice_var, values=voice_names, state="readonly")
            voice_combo.pack(pady=5, padx=20, fill="x")
            
            # Female voice option
            female_voice_var = tk.BooleanVar()
            ttk.Checkbutton(settings_window, text="Prefer female voice", variable=female_voice_var).pack(pady=5)
            
            # Speed control
            ttk.Label(settings_window, text="Speaking Speed:").pack(pady=(10,5))
            speed_var = tk.IntVar(value=self.engine.getProperty('rate'))
            speed_scale = tk.Scale(settings_window, from_=50, to=300, orient="horizontal", variable=speed_var)
            speed_scale.pack(pady=5, padx=20, fill="x")
            
            # Volume control
            ttk.Label(settings_window, text="Volume:").pack(pady=(10,5))
            volume_var = tk.DoubleVar(value=self.engine.getProperty('volume'))
            volume_scale = tk.Scale(settings_window, from_=0.0, to=1.0, resolution=0.1, orient="horizontal", variable=volume_var)
            volume_scale.pack(pady=5, padx=20, fill="x")
            
            # Test button
            def test_voice():
                self.engine.setProperty("rate", speed_var.get())
                self.engine.setProperty("volume", volume_var.get())
                self.speak_text("This is a test of the speech settings.", background=False)
            
            ttk.Button(settings_window, text="Test Voice", command=test_voice).pack(pady=5)

            # Apply button
            def apply_settings():
                try:
                    # Set voice
                    selected_voice = voice_var.get()
                    for voice in voices:
                        if voice.name == selected_voice:
                            if female_voice_var.get():
                                self.setup_female_voice()
                            else:
                                self.engine.setProperty("voice", voice.id)
                            break

                    # Set speed and volume
                    self.engine.setProperty("rate", speed_var.get())
                    self.engine.setProperty("volume", volume_var.get())
                    
                    # Save settings
                    self._save_settings()
                    
                    settings_window.destroy()
                    messagebox.showinfo("Settings Applied", "Speech settings have been applied successfully.")
                    
                except Exception as e:
                    logging.error(f"Error applying speech settings: {e}")
                    messagebox.showerror("Error", f"Failed to apply settings: {e}")
            
            # Buttons
            buttons_frame = ttk.Frame(settings_window)
            buttons_frame.pack(pady=10)
            ttk.Button(buttons_frame, text="Apply", command=apply_settings).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Cancel", command=settings_window.destroy).pack(side="left", padx=5)

        except Exception as e:
            logging.error(f"Error showing speech settings: {e}")
            messagebox.showerror("Error", f"Failed to open speech settings: {e}")
    
    def save_to_file(self, text: str, file_path: str) -> bool:
        """Save text as audio file."""
        if not self.is_available:
            messagebox.showinfo("TTS Not Available", "Text-to-speech functionality is not available.")
            return False
        
        try:
            cleaned_text = self.preprocess_text_for_speech(text)
            self.engine.save_to_file(cleaned_text, file_path)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logging.error(f"Error saving speech to file: {e}")
            messagebox.showerror("Save Error", f"Failed to save speech: {e}")
            return False
    
    def _save_settings(self) -> None:
        """Save current TTS settings to config."""
        if not self.config or not self.is_available:
            return
            
        try:
            self.config.set("tts_voice", self.engine.getProperty("voice"))
            self.config.set("tts_rate", self.engine.getProperty("rate"))
            self.config.set("tts_volume", self.engine.getProperty("volume"))
        except Exception as e:
            logging.error(f"Error saving TTS settings: {e}")
    
    def _load_settings(self) -> None:
        """Load TTS settings from config."""
        if not self.config or not self.is_available:
            return
            
        try:
            voice = self.config.get("tts_voice")
            rate = self.config.get("tts_rate")
            volume = self.config.get("tts_volume")
            
            if voice:
                self.engine.setProperty("voice", voice)
            if rate:
                self.engine.setProperty("rate", int(rate))
            if volume:
                self.engine.setProperty("volume", float(volume))
        except Exception as e:
            logging.error(f"Error loading TTS settings: {e}")
    
    def test_speech(self) -> None:
        """Test TTS functionality with a sample message."""
        if not self.is_available:
            messagebox.showerror("TTS Error", "Text-to-speech functionality is not available.")
            return
            
        self.speak_text("This is a test of the text-to-speech system.", background=False)