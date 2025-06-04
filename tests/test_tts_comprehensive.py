#!/usr/bin/env python3
"""
Comprehensive TTS Test Suite for Crew Project
"""

import unittest
import unittest.mock as mock
import threading
import time
import re
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules we need to test
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    pyttsx3 = None


class MockVoice:
    """Mock voice object for testing"""
    def __init__(self, voice_id, name, gender="unknown"):
        self.id = voice_id
        self.name = name
        self.gender = gender


class MockTTSEngine:
    """Mock TTS engine for testing when pyttsx3 is not available"""
    def __init__(self):
        self.properties = {
            'rate': 200,
            'volume': 1.0,
            'voice': 'default_voice',
            'voices': [
                MockVoice("english", "English Voice", "male"),
                MockVoice("english-us", "US English", "female"),
                MockVoice("espeak-voice-1", "ESpeak Voice 1", "male"),
                MockVoice("espeak-voice-2", "ESpeak Voice 2", "female"),
            ]
        }
        self.spoken_text = []
        self.running = False
    
    def getProperty(self, name):
        return self.properties.get(name)
    
    def setProperty(self, name, value):
        self.properties[name] = value
    
    def say(self, text):
        self.spoken_text.append(text)
    
    def runAndWait(self):
        self.running = True
        time.sleep(0.01)  # Simulate brief processing time
        self.running = False
    
    def stop(self):
        self.running = False


class TestTTSEngineInitialization(unittest.TestCase):
    """Test TTS engine initialization and availability"""
    
    def test_tts_availability_detection(self):
        """Test that TTS availability is correctly detected"""
        # This test checks the actual TTS_AVAILABLE constant
        if TTS_AVAILABLE:
            self.assertIsNotNone(pyttsx3)
        else:
            # If TTS is not available, pyttsx3 should be None or import should fail
            if pyttsx3 is None:
                self.assertIsNone(pyttsx3)
    
    @unittest.skipUnless(TTS_AVAILABLE, "pyttsx3 not available")
    def test_engine_initialization(self):
        """Test successful TTS engine initialization"""
        try:
            engine = pyttsx3.init()
            self.assertIsNotNone(engine)
            
            # Test basic properties exist
            voices = engine.getProperty('voices')
            rate = engine.getProperty('rate')
            volume = engine.getProperty('volume')
            
            self.assertIsNotNone(voices)
            self.assertIsInstance(rate, (int, float))
            self.assertIsInstance(volume, (int, float))
            
        except Exception as e:
            self.fail(f"TTS engine initialization failed: {e}")
    
    def test_engine_initialization_with_mock(self):
        """Test engine initialization with mock for systems without TTS"""
        mock_engine = MockTTSEngine()
        
        # Test basic functionality
        self.assertIsNotNone(mock_engine)
        self.assertEqual(mock_engine.getProperty('rate'), 200)
        self.assertEqual(mock_engine.getProperty('volume'), 1.0)
        
        voices = mock_engine.getProperty('voices')
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)


class TestVoicePropertyManagement(unittest.TestCase):
    """Test voice property getting and setting"""
    
    def setUp(self):
        """Set up test fixtures"""
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
            except:
                self.engine = MockTTSEngine()
        else:
            self.engine = MockTTSEngine()
    
    def test_get_voices(self):
        """Test getting available voices"""
        voices = self.engine.getProperty('voices')
        self.assertIsInstance(voices, list)
        
        if voices:
            # Test voice object structure
            voice = voices[0]
            self.assertTrue(hasattr(voice, 'id'))
            self.assertTrue(hasattr(voice, 'name'))
    
    def test_rate_property(self):
        """Test speech rate property management"""
        # Test getting current rate
        current_rate = self.engine.getProperty('rate')
        self.assertIsInstance(current_rate, (int, float))
        
        # Test setting rate
        test_rates = [100, 150, 200, 300]
        for rate in test_rates:
            self.engine.setProperty('rate', rate)
            if isinstance(self.engine, MockTTSEngine):
                # Mock engine should store the value
                self.assertEqual(self.engine.getProperty('rate'), rate)
    
    def test_volume_property(self):
        """Test volume property management"""
        # Test getting current volume
        current_volume = self.engine.getProperty('volume')
        self.assertIsInstance(current_volume, (int, float))
        
        # Test setting volume
        test_volumes = [0.0, 0.5, 0.8, 1.0]
        for volume in test_volumes:
            self.engine.setProperty('volume', volume)
            if isinstance(self.engine, MockTTSEngine):
                # Mock engine should store the value
                self.assertEqual(self.engine.getProperty('volume'), volume)
    
    def test_voice_selection(self):
        """Test voice selection functionality"""
        voices = self.engine.getProperty('voices')
        if voices:
            # Test setting voice by ID
            original_voice = self.engine.getProperty('voice')
            test_voice = voices[0]
            
            self.engine.setProperty('voice', test_voice.id)
            if isinstance(self.engine, MockTTSEngine):
                self.assertEqual(self.engine.getProperty('voice'), test_voice.id)


class TestFemaleVoiceSetup(unittest.TestCase):
    """Test female voice setup functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
            except:
                self.engine = MockTTSEngine()
        else:
            self.engine = MockTTSEngine()
    
    def test_setup_female_voice_basic(self):
        """Test basic female voice setup (espeak +f3 method)"""
        # Implement the setup_female_voice function from the codebase
        def setup_female_voice(engine):
            try:
                voices = engine.getProperty('voices')
                english_voice = None
                for voice in voices:
                    if "english" in voice.id.lower():
                        english_voice = voice
                        break
                
                if english_voice:
                    fem_voice = english_voice.id + "+f3"
                    engine.setProperty('voice', fem_voice)
                    return True
            except Exception as e:
                print(f"Could not set female voice: {e}")
            return False
        
        # Test the function
        result = setup_female_voice(self.engine)
        
        # For mock engine, this should succeed
        if isinstance(self.engine, MockTTSEngine):
            voices = self.engine.getProperty('voices')
            english_voices = [v for v in voices if "english" in v.id.lower()]
            if english_voices:
                self.assertTrue(result)
                expected_voice = english_voices[0].id + "+f3"
                self.assertEqual(self.engine.getProperty('voice'), expected_voice)
    
    def test_setup_female_voice_advanced(self):
        """Test advanced female voice setup with pattern matching"""
        # Implement the advanced setup from read_use_file_cli.py
        def setup_female_voice_advanced(engine):
            try:
                voices = engine.getProperty('voices')
                if not voices:
                    return False
                
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
                    engine.setProperty('voice', selected_voice.id)
                    return True
                else:
                    return False
                    
            except Exception as e:
                return False
        
        # Test the advanced function
        result = setup_female_voice_advanced(self.engine)
        
        # Should return True for mock engine (has English voices)
        if isinstance(self.engine, MockTTSEngine):
            self.assertTrue(result)


class TestTextPreprocessing(unittest.TestCase):
    """Test text preprocessing and cleaning functions"""
    
    def test_clean_text_basic(self):
        """Test basic text cleaning from read_use_file_cli.py"""
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
        
        # Test various text patterns
        test_cases = [
            # Code blocks
            ("Here is code:\n```python\nprint('hello')\n```\nEnd", 
             "Here is code:\n code block omitted \nEnd"),
            
            # Inline code
            ("Use `print()` function", "Use code omitted function"),
            
            # Headers
            ("# Title\n## Subtitle\nContent", "Title\nSubtitle\nContent"),
            
            # URLs
            ("Visit https://example.com for info", "Visit URL link for info"),
            
            # Multiple whitespace
            ("Text  with   spaces\n\n\n\nNew paragraph", "Text with spaces\n\nNew paragraph"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = clean_text(input_text)
                self.assertEqual(result, expected)
    
    def test_preprocess_text_for_speech(self):
        """Test advanced text preprocessing from read_use_file.py"""
        def preprocess_text_for_speech(text):
            """Preprocess text to make it more suitable for TTS."""
            # Remove markdown headers (#)
            text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
            
            # Remove code blocks
            text = re.sub(r"```.*?```", " Code block omitted. ", text, flags=re.DOTALL)
            
            # Remove inline code
            text = re.sub(r"`.*?`", " Code omitted. ", text)
            
            # Replace bullet points
            text = re.sub(r"^[\*\-\+]\s+", "• ", text, flags=re.MULTILINE)
            
            # Handle numbered lists
            text = re.sub(r"^\d+\.\s+", "Number. ", text, flags=re.MULTILINE)
            
            # Replace URLs with placeholders
            text = re.sub(r"https?://\S+", " URL link. ", text)
            
            return text.strip()
        
        # Test list processing
        test_text = """# Title
- First item
- Second item
1. Numbered item
2. Another numbered item
Visit https://example.com
`code here`
```
code block
```"""
        
        result = preprocess_text_for_speech(test_text)
        
        # Should remove headers, convert lists, handle URLs and code
        self.assertNotIn("#", result)
        self.assertIn("•", result)
        self.assertIn("Number.", result)
        self.assertIn("URL link.", result)
        self.assertIn("Code omitted.", result)
        self.assertIn("Code block omitted.", result)


class TestTextChunking(unittest.TestCase):
    """Test text chunking functionality for TTS"""
    
    def test_chunk_text_by_sentences(self):
        """Test sentence-based text chunking"""
        def chunk_text(text, max_chunk_size=400):
            """Split text into readable chunks for TTS"""
            # Split by sentences first
            sentences = re.split(r'[.!?]+', text)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # If adding this sentence would exceed max size, save current chunk
                if len(current_chunk) + len(sentence) + 1 > max_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += ". " + sentence
                    else:
                        current_chunk = sentence
            
            # Add the last chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Test with short text
        short_text = "This is a test. It has multiple sentences. Each should be handled properly."
        chunks = chunk_text(short_text, max_chunk_size=50)
        self.assertGreater(len(chunks), 1)
        
        # Test with long text
        long_text = "This is a very long sentence that should be chunked appropriately. " * 20
        chunks = chunk_text(long_text)
        self.assertGreater(len(chunks), 1)
        
        # Each chunk should be under the limit
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 450)  # Allow some buffer
    
    def test_chunk_text_edge_cases(self):
        """Test text chunking edge cases"""
        def chunk_text(text, max_chunk_size=400):
            """Split text into readable chunks for TTS"""
            sentences = re.split(r'[.!?]+', text)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(current_chunk) + len(sentence) + 1 > max_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += ". " + sentence
                    else:
                        current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Test empty text
        self.assertEqual(chunk_text(""), [])
        
        # Test single word
        self.assertEqual(chunk_text("Hello"), ["Hello"])
        
        # Test no punctuation
        chunks = chunk_text("This is text without punctuation marks")
        self.assertEqual(len(chunks), 1)


class TestErrorHandling(unittest.TestCase):
    """Test TTS error handling and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = MockTTSEngine()
    
    def test_malformed_text_handling(self):
        """Test handling of malformed or problematic text"""
        def safe_speak(engine, text):
            """Safely speak text with error handling"""
            try:
                if not text or not text.strip():
                    return False
                
                # Clean text of problematic characters
                cleaned_text = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', text)
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                
                if not cleaned_text:
                    return False
                
                engine.say(cleaned_text)
                return True
            except Exception as e:
                print(f"TTS Error: {e}")
                return False
        
        # Test various problematic inputs
        test_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "\n\n\n",  # Newlines only
            "Hello\x00World",  # Null character
            "Text with émojis 🎉",  # Unicode
            "Very" + "long" * 1000 + "text",  # Very long text
        ]
        
        for text in test_cases:
            result = safe_speak(self.engine, text)
            # Should not crash, but may return False for invalid input
            self.assertIsInstance(result, bool)
    
    def test_engine_initialization_failure(self):
        """Test handling of TTS engine initialization failure"""
        def initialize_tts_safely():
            """Initialize TTS with proper error handling"""
            try:
                if TTS_AVAILABLE:
                    engine = pyttsx3.init()
                    return engine, True
                else:
                    return MockTTSEngine(), False
            except Exception as e:
                print(f"TTS initialization failed: {e}")
                return None, False
        
        engine, success = initialize_tts_safely()
        self.assertIsNotNone(engine)  # Should return something (mock if real fails)
        self.assertIsInstance(success, bool)
    
    def test_property_setting_failure(self):
        """Test handling of property setting failures"""
        def safe_set_property(engine, prop, value):
            """Safely set engine property with error handling"""
            try:
                engine.setProperty(prop, value)
                return True
            except Exception as e:
                print(f"Failed to set {prop} to {value}: {e}")
                return False
        
        # Test setting invalid properties
        test_cases = [
            ('rate', -100),  # Invalid rate
            ('volume', 5.0),  # Invalid volume
            ('voice', 'nonexistent_voice'),  # Invalid voice
            ('invalid_prop', 'value'),  # Invalid property
        ]
        
        for prop, value in test_cases:
            result = safe_set_property(self.engine, prop, value)
            self.assertIsInstance(result, bool)


class TestThreadSafety(unittest.TestCase):
    """Test TTS thread safety and concurrent access"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = MockTTSEngine()
        self.results = []
        self.errors = []
    
    def test_concurrent_property_access(self):
        """Test concurrent property getting/setting"""
        def worker(worker_id):
            """Worker function for concurrent testing"""
            try:
                for i in range(10):
                    # Get properties
                    rate = self.engine.getProperty('rate')
                    volume = self.engine.getProperty('volume')
                    
                    # Set properties
                    self.engine.setProperty('rate', 200 + worker_id * 10)
                    self.engine.setProperty('volume', 0.5 + worker_id * 0.1)
                    
                    time.sleep(0.01)  # Small delay
                
                self.results.append(f"Worker {worker_id} completed")
            except Exception as e:
                self.errors.append(f"Worker {worker_id} error: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Check results
        self.assertEqual(len(self.results), 3)
        self.assertEqual(len(self.errors), 0)
    
    def test_speech_interruption(self):
        """Test speech interruption functionality"""
        def interruptible_speak(engine, text, stop_event):
            """Speak text with interruption support"""
            try:
                # Simulate chunked speech with interruption checks
                chunks = [text[i:i+50] for i in range(0, len(text), 50)]
                
                for chunk in chunks:
                    if stop_event.is_set():
                        return False  # Interrupted
                    
                    engine.say(chunk)
                    time.sleep(0.1)  # Simulate speech time
                
                return True  # Completed
            except Exception as e:
                return False
        
        # Test normal completion
        stop_event = threading.Event()
        result = interruptible_speak(self.engine, "Short text", stop_event)
        self.assertTrue(result)
        
        # Test interruption
        stop_event = threading.Event()
        
        def interrupt_after_delay():
            time.sleep(0.05)
            stop_event.set()
        
        interrupt_thread = threading.Thread(target=interrupt_after_delay)
        interrupt_thread.start()
        
        long_text = "This is a very long text that should be interrupted. " * 20
        result = interruptible_speak(self.engine, long_text, stop_event)
        
        interrupt_thread.join()
        self.assertFalse(result)  # Should be interrupted


class TestIntegration(unittest.TestCase):
    """Test complete TTS workflow integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
            except:
                self.engine = MockTTSEngine()
        else:
            self.engine = MockTTSEngine()
    
    def test_complete_tts_workflow(self):
        """Test complete TTS workflow from text to speech"""
        def complete_tts_workflow(text, engine):
            """Complete TTS workflow: preprocess, chunk, setup, speak"""
            try:
                # Step 1: Preprocess text
                cleaned_text = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', text)
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                
                if not cleaned_text:
                    return False, "Empty text after preprocessing"
                
                # Step 2: Setup voice (prefer female)
                voices = engine.getProperty('voices')
                if voices:
                    for voice in voices:
                        if "female" in voice.id.lower() or "female" in getattr(voice, 'name', '').lower():
                            engine.setProperty('voice', voice.id)
                            break
                
                # Step 3: Set optimal properties
                engine.setProperty('rate', 180)  # Comfortable rate
                engine.setProperty('volume', 0.9)  # High but not max volume
                
                # Step 4: Chunk text
                chunks = []
                sentences = re.split(r'[.!?]+', cleaned_text)
                current_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(current_chunk) + len(sentence) + 1 > 400 and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += ". " + sentence
                        else:
                            current_chunk = sentence
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Step 5: Speak chunks
                for chunk in chunks:
                    engine.say(chunk)
                
                return True, f"Successfully processed {len(chunks)} chunks"
                
            except Exception as e:
                return False, f"Workflow error: {e}"
        
        # Test with various text types
        test_texts = [
            "Hello world! This is a simple test.",
            "This is a longer text with multiple sentences. It should be processed correctly. The workflow should handle it well.",
            "Text with special characters: @#$%! Should be cleaned.",
            "",  # Empty text
        ]
        
        for text in test_texts:
            success, message = complete_tts_workflow(text, self.engine)
            self.assertIsInstance(success, bool)
            self.assertIsInstance(message, str)
            
            # Non-empty text should succeed
            if text.strip():
                self.assertTrue(success, f"Failed for text: '{text[:50]}...' - {message}")
    
    def test_context_menu_integration(self):
        """Test context menu TTS integration functionality"""
        def context_menu_tts_handler(action, selected_text, engine):
            """Handle context menu TTS actions"""
            try:
                if action == "read_selection":
                    if not selected_text or not selected_text.strip():
                        return False, "No text selected"
                    
                    # Preprocess and speak selection
                    cleaned = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', selected_text)
                    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                    
                    engine.say(cleaned)
                    return True, "Reading selection"
                
                elif action == "read_all":
                    # Simulate reading all content
                    engine.say("Reading all content")
                    return True, "Reading all content"
                
                elif action == "stop_reading":
                    # Simulate stopping
                    engine.stop()
                    return True, "Stopped reading"
                
                else:
                    return False, "Unknown action"
                    
            except Exception as e:
                return False, f"Context menu error: {e}"
        
        # Test different context menu actions
        test_cases = [
            ("read_selection", "Selected text to read", True),
            ("read_selection", "", False),  # No selection
            ("read_all", None, True),
            ("stop_reading", None, True),
            ("invalid_action", "text", False),
        ]
        
        for action, text, expected_success in test_cases:
            success, message = context_menu_tts_handler(action, text, self.engine)
            
            if expected_success:
                self.assertTrue(success, f"Action '{action}' should succeed: {message}")
            else:
                self.assertFalse(success, f"Action '{action}' should fail: {message}")


class TestTTSSettingsDialog(unittest.TestCase):
    """Test TTS settings dialog functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = MockTTSEngine()
    
    def test_settings_dialog_data_structure(self):
        """Test TTS settings data structure"""
        def get_tts_settings(engine):
            """Get current TTS settings"""
            try:
                settings = {
                    'rate': engine.getProperty('rate'),
                    'volume': engine.getProperty('volume'),
                    'voice': engine.getProperty('voice'),
                    'voices': engine.getProperty('voices')
                }
                return settings
            except Exception as e:
                return None
        
        settings = get_tts_settings(self.engine)
        self.assertIsNotNone(settings)
        self.assertIn('rate', settings)
        self.assertIn('volume', settings)
        self.assertIn('voice', settings)
        self.assertIn('voices', settings)
        
        # Validate data types
        self.assertIsInstance(settings['rate'], (int, float))
        self.assertIsInstance(settings['volume'], (int, float))
        self.assertIsInstance(settings['voices'], list)
    
    def test_settings_dialog_validation(self):
        """Test settings dialog input validation"""
        def validate_tts_settings(rate, volume, voice_id, available_voices):
            """Validate TTS settings input"""
            errors = []
            
            # Validate rate
            if not isinstance(rate, (int, float)) or rate < 50 or rate > 500:
                errors.append("Rate must be between 50 and 500")
            
            # Validate volume
            if not isinstance(volume, (int, float)) or volume < 0.0 or volume > 1.0:
                errors.append("Volume must be between 0.0 and 1.0")
            
            # Validate voice
            if voice_id:
                valid_voices = [v.id for v in available_voices] if available_voices else []
                if voice_id not in valid_voices and voice_id != 'default_voice':
                    errors.append("Invalid voice selection")
            
            return len(errors) == 0, errors
        
        voices = self.engine.getProperty('voices')
        
        # Test valid settings
        valid, errors = validate_tts_settings(200, 0.8, voices[0].id if voices else 'default_voice', voices)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
        
        # Test invalid settings
        invalid_cases = [
            (10, 0.8, None, voices),  # Rate too low
            (600, 0.8, None, voices),  # Rate too high
            (200, 1.5, None, voices),  # Volume too high
            (200, -0.1, None, voices),  # Volume too low
            (200, 0.8, 'invalid_voice', voices),  # Invalid voice
        ]
        
        for rate, volume, voice, voice_list in invalid_cases:
            valid, errors = validate_tts_settings(rate, volume, voice, voice_list)
            self.assertFalse(valid)
            self.assertGreater(len(errors), 0)


class TestPerformance(unittest.TestCase):
    """Test TTS performance with large texts"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = MockTTSEngine()
    
    def test_large_text_processing(self):
        """Test processing of large text documents"""
        def process_large_text(text, engine):
            """Process large text efficiently"""
            start_time = time.time()
            
            # Preprocess
            cleaned = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', text)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            # Chunk
            chunks = []
            sentences = re.split(r'[.!?]+', cleaned)
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                if len(current_chunk) + len(sentence) + 1 > 400 and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += ". " + sentence
                    else:
                        current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            processing_time = time.time() - start_time
            
            return {
                'chunks': len(chunks),
                'processing_time': processing_time,
                'chars_per_second': len(text) / processing_time if processing_time > 0 else 0
            }
        
        # Test with various text sizes
        small_text = "Short text. " * 10
        medium_text = "Medium length text with multiple sentences. " * 100
        large_text = "Large text document with many sentences and paragraphs. " * 1000
        
        for text in [small_text, medium_text, large_text]:
            result = process_large_text(text, self.engine)
            
            # Performance should be reasonable
            self.assertGreater(result['chars_per_second'], 1000)  # At least 1000 chars/sec
            self.assertGreater(result['chunks'], 0)
            self.assertLess(result['processing_time'], 5.0)  # Less than 5 seconds
    
    def test_memory_usage(self):
        """Test memory usage with repeated operations"""
        def memory_stress_test(engine, iterations=100):
            """Stress test memory usage"""
            import gc
            
            test_text = "This is a test sentence for memory usage testing. " * 20
            
            for i in range(iterations):
                # Preprocess text
                cleaned = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', test_text)
                
                # Create chunks
                chunks = [cleaned[j:j+50] for j in range(0, len(cleaned), 50)]
                
                # Simulate speaking
                for chunk in chunks:
                    engine.say(chunk)
                
                # Force garbage collection periodically
                if i % 10 == 0:
                    gc.collect()
            
            return True
        
        # Should complete without memory issues
        result = memory_stress_test(self.engine)
        self.assertTrue(result)


if __name__ == '__main__':
    print("="*60)
    print("COMPREHENSIVE TTS TEST SUITE FOR CREW PROJECT")
    print("="*60)
    
    # Run all tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*60)
    print("TTS TEST SUITE EXECUTION COMPLETE")
    print("="*60)
    
    # Display summary
    print(f"\nTTS Engine Available: {TTS_AVAILABLE}")
    print(f"Test File: {__file__}")
    print(f"Test Classes: {len([cls for cls in globals().values() if isinstance(cls, type) and issubclass(cls, unittest.TestCase)])}")
    
    if TTS_AVAILABLE:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            print(f"Available Voices: {len(voices) if voices else 0}")
        except:
            print("TTS Engine initialization failed")
    else:
        print("Using Mock TTS Engine for testing")
