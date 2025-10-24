
"""
Enhanced Speech Manager with multilingual support, voice recognition, and sound effects
"""
import pyttsx3
import speech_recognition as sr
from gtts import gTTS
import os
import sys
try:
    from googletrans import Translator
except Exception:
    Translator = None
try:
    import sounddevice as sd
    import soundfile as sf
except Exception:
    sd = None
    sf = None
import numpy as np
import threading
import tempfile
import json
from typing import Optional, Dict, List, Tuple
from enum import Enum
import random
import time

class VoiceRole(Enum):
    GENERAL = "general"
    QUIZ = "quiz"
    REMINDER = "reminder"
    ERROR = "error"
    SUCCESS = "success"

class SpeechManager:
    def __init__(self):
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        
        # Initialize voice recognition
        self.recognizer = sr.Recognizer()
        # Initialize translator if available
        self.translator = Translator() if Translator is not None else None
        
        # Set up voice profiles for different roles
        self.voice_profiles = {}
        self._setup_voice_profiles()
        
        # Set up sound effects
        self.sound_effects = self._load_sound_effects()
        self.background_thread = None
        self.stop_background = threading.Event()
        
        # Language settings
        self.current_language = 'en'
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'ja': 'Japanese'
        }
        # Load persistent config (mic device index etc.)
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config = self._load_config()
        self.default_mic_device = self.config.get('mic_device') if isinstance(self.config.get('mic_device'), int) else None
    
    def _setup_voice_profiles(self):
        """Initialize voice profiles for different roles"""
        voices = self.engine.getProperty('voices')
        
        # Categorize voices by gender and quality
        male_voices = [v for v in voices if 'male' in v.name.lower()]
        female_voices = [v for v in voices if 'female' in v.name.lower()]
        
        # Assign voices to roles
        self.voice_profiles = {
            VoiceRole.GENERAL: female_voices[0] if female_voices else voices[0],
            VoiceRole.QUIZ: male_voices[0] if male_voices else voices[0],
            VoiceRole.REMINDER: female_voices[-1] if female_voices else voices[0],
            VoiceRole.ERROR: male_voices[-1] if male_voices else voices[0],
            VoiceRole.SUCCESS: female_voices[0] if female_voices else voices[0]
        }
    
    def _load_sound_effects(self) -> Dict[str, str]:
        """Load sound effect files"""
        effects_dir = os.path.join(os.path.dirname(__file__), 'sound_effects')
        os.makedirs(effects_dir, exist_ok=True)
        
        # Generate basic sound effects if they don't exist
        effects = {
            'notification': self._generate_notification_sound(effects_dir),
            'error': self._generate_error_sound(effects_dir),
            'success': self._generate_success_sound(effects_dir),
            'background': self._generate_background_sound(effects_dir)
        }
        return effects
    
    def _generate_notification_sound(self, directory: str) -> str:
        """Generate a simple notification sound"""
        filename = os.path.join(directory, 'notification.wav')
        # If soundfile is unavailable, don't create files — return None
        if sf is None:
            return None
        if not os.path.exists(filename):
            sample_rate = 44100
            duration = 0.2
            t = np.linspace(0, duration, int(sample_rate * duration))
            signal = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
            sf.write(filename, signal, sample_rate)
        return filename
    
    def _generate_error_sound(self, directory: str) -> str:
        """Generate an error sound"""
        filename = os.path.join(directory, 'error.wav')
        if sf is None:
            return None
        if not os.path.exists(filename):
            sample_rate = 44100
            duration = 0.3
            t = np.linspace(0, duration, int(sample_rate * duration))
            signal = 0.5 * np.sin(2 * np.pi * 220 * t)  # Lower frequency
            sf.write(filename, signal, sample_rate)
        return filename
    
    def _generate_success_sound(self, directory: str) -> str:
        """Generate a success sound"""
        filename = os.path.join(directory, 'success.wav')
        if sf is None:
            return None
        if not os.path.exists(filename):
            sample_rate = 44100
            duration = 0.2
            t = np.linspace(0, duration, int(sample_rate * duration))
            signal = 0.5 * np.sin(2 * np.pi * 880 * t)  # Higher frequency
            sf.write(filename, signal, sample_rate)
        return filename
    
    def _generate_background_sound(self, directory: str) -> str:
        """Generate ambient background sound"""
        filename = os.path.join(directory, 'background.wav')
        if sf is None:
            return None
        if not os.path.exists(filename):
            sample_rate = 44100
            duration = 5.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            # Create a gentle ambient sound
            signal = 0.1 * np.sin(2 * np.pi * 60 * t)
            signal += 0.05 * np.sin(2 * np.pi * 62 * t)
            sf.write(filename, signal, sample_rate)
        return filename
    
    def speak(self, text: str, role: VoiceRole = VoiceRole.GENERAL, 
             wait: bool = True, play_sound: bool = False) -> None:
        """
        Enhanced text-to-speech with role-based voices and sound effects
        """
        if not text:
            return
            
        # Translate if not in English and translator available
        if self.current_language != 'en' and self.translator is not None:
            try:
                text = self.translator.translate(
                    text, src='en', dest=self.current_language
                ).text
            except Exception:
                # Fallback: leave text untranslated
                pass
            
        # Set appropriate voice for the role
        if role in self.voice_profiles:
            self.engine.setProperty('voice', self.voice_profiles[role].id)
            
        # Play appropriate sound effect
        if play_sound:
            effect = None
            if role == VoiceRole.ERROR:
                effect = self.sound_effects['error']
            elif role == VoiceRole.SUCCESS:
                effect = self.sound_effects['success']
            elif role == VoiceRole.REMINDER:
                effect = self.sound_effects['notification']
                
            if effect:
                self.play_wav_file(effect)
                
        # Speak the text
        if wait:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            self.engine.startLoop(False)
            self.engine.say(text)
            self.engine.iterate()
            self.engine.endLoop()
    
    def listen(self, timeout: int = 5, device_index: Optional[int] = None) -> Optional[str]:
        """
        Listen for voice input.
        Tries to use SpeechRecognition's Microphone (PyAudio). If that fails,
        falls back to recording with sounddevice and using SpeechRecognition on the captured audio.

        Args:
            timeout: seconds to listen/record
            device_index: optional sounddevice device index to use for fallback

        Returns:
            Recognized text or None if not understood
        """
        # First try the standard SpeechRecognition microphone (requires PyAudio)
        try:
            with sr.Microphone() as source:
                try:
                    print("Listening...")
                    # optional ambient noise adjustment
                    try:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    except Exception:
                        pass
                    audio = self.recognizer.listen(source, timeout=timeout)
                    text = self.recognizer.recognize_google(audio)

                    # Translate to English if in different language and translator available
                    if self.current_language != 'en' and self.translator is not None:
                        try:
                            text = self.translator.translate(
                                text, src=self.current_language, dest='en'
                            ).text
                        except Exception:
                            pass

                    return text
                except (sr.UnknownValueError, sr.RequestError):
                    return None
        except Exception:
            # Fallback: use sounddevice to record raw audio and feed into SpeechRecognition
            if sd is None:
                # No fallback available
                return None
            try:
                fs = 48000
                duration = timeout
                device = device_index
                print(f"Recording via sounddevice for {duration}s (device={device})...")
                data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32', device=device)
                sd.wait()

                # Convert float32 numpy array (-1..1) to 16-bit PCM
                pcm16 = (data.flatten() * 32767).astype('int16')
                raw_bytes = pcm16.tobytes()

                audio = sr.AudioData(raw_bytes, fs, 2)
                try:
                    text = self.recognizer.recognize_google(audio)
                    if self.current_language != 'en' and self.translator is not None:
                        try:
                            text = self.translator.translate(text, src=self.current_language, dest='en').text
                        except Exception:
                            pass
                    return text
                except Exception:
                    return None
            except Exception:
                return None

    def record_and_recognize(self, duration: int = 4, device_index: Optional[int] = None) -> Optional[str]:
        """
        Helper: record audio for `duration` seconds using sounddevice and run recognition.
        Returns recognized text or None.
        """
        if sd is None:
            return None
        try:
            fs = 48000
            # use default device if none provided
            if device_index is None:
                device_index = self.default_mic_device
            print(f"Recording {duration}s (device={device_index})...")
            data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32', device=device_index)
            sd.wait()
            pcm16 = (data.flatten() * 32767).astype('int16')
            raw_bytes = pcm16.tobytes()
            audio = sr.AudioData(raw_bytes, fs, 2)
            try:
                return self.recognizer.recognize_google(audio)
            except Exception:
                return None
        except Exception:
            return None

    def _load_config(self) -> dict:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_config(self) -> bool:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False

    def set_default_mic(self, device_index: Optional[int]) -> bool:
        """Set and persist default microphone device index (or None to unset)."""
        try:
            if device_index is not None:
                device_index = int(device_index)
            self.config['mic_device'] = device_index
            ok = self._save_config()
            if ok:
                self.default_mic_device = device_index
            return ok
        except Exception:
            return False
    
    def start_background_sound(self, volume: float = 0.1) -> None:
        """Start playing ambient background sound"""
        def play_loop():
            while not self.stop_background.is_set():
                if sf is None or sd is None:
                    time.sleep(1.0)
                    continue
                data, sample_rate = sf.read(self.sound_effects['background'])
                sd.play(data * volume, sample_rate)
                sd.wait()
                
        self.stop_background.clear()
        self.background_thread = threading.Thread(target=play_loop)
        self.background_thread.start()
    
    def stop_background_sound(self) -> None:
        """Stop the background sound"""
        if self.background_thread:
            self.stop_background.set()
            self.background_thread.join()
            self.background_thread = None
    
    def change_language(self, language_code: str) -> bool:
        """
        Change the speech language
        Args:
            language_code: Two-letter language code (e.g., 'en', 'es')
        Returns:
            bool: True if language was changed successfully
        """
        if language_code in self.supported_languages:
            self.current_language = language_code
            return True
        return False
    
    def play_wav_file(self, file_path: str) -> None:
        """Wrapper for playing WAV files that works in both test and interactive modes"""
        if not file_path or not os.path.exists(file_path):
            return
        # In test mode, just return without playing
        try:
            if not sys.stdin.isatty():
                return
        except Exception:
            return
        # Try to play the file
        if sd is not None and sf is not None:
            try:
                data, sample_rate = sf.read(file_path)
                sd.play(data, sample_rate)
                sd.wait()
            except Exception:
                pass
    
    def play_sound_effect(self, effect_type: str) -> None:
        """Play a specific sound effect"""
        path = self.sound_effects.get(effect_type)
        if not path:
            return
        # Only attempt to play if file exists
        if not os.path.exists(path):
            return
        try:
            self.play_wav_file(path)
        except Exception:
            # Fail silently during tests
            return

    def change_voice(self, gender: str = 'female') -> bool:
        """Change the voice of the speech engine by gender ('male'|'female')"""
        voices = self.engine.getProperty('voices')
        target = [v for v in voices if gender in v.name.lower()]
        if target:
            self.engine.setProperty('voice', target[0].id)
            return True
        # Fallback: if no gender-specific voice found, but voices exist, set first
        if voices:
            try:
                self.engine.setProperty('voice', voices[0].id)
                return True
            except Exception:
                return False
        return False

    def adjust_speech(self, rate: Optional[int] = None, volume: Optional[float] = None) -> None:
        """Adjust speech properties (rate and volume)"""
        if rate is not None:
            self.engine.setProperty('rate', max(50, min(300, rate)))
        if volume is not None:
            self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
    
    def stop_speaking(self) -> None:
        """Stop any ongoing speech"""
        self.engine.stop()
        
    def cleanup(self) -> None:
        """Clean up resources"""
        self.stop_background_sound()
        self.stop_speaking()