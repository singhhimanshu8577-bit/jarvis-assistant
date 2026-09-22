"""
Speech-to-Text (STT) and Microphone Capture Subsystem for JARVIS.
Supports faster-whisper local quantized models and SpeechRecognition Google/Whisper fallback.
"""

import os
import tempfile
import time
from typing import Optional

from config.config_loader import config

try:
    import speech_recognition as sr
    _sr_available = True
except ImportError:
    _sr_available = False

try:
    from faster_whisper import WhisperModel
    _faster_whisper_available = True
except ImportError:
    _faster_whisper_available = False


class AudioListener:
    """Microphone audio capture and STT transcription engine."""

    def __init__(self):
        self.engine_type = config.get("stt", "engine", default="faster-whisper").lower()
        self.model_size = config.get("stt", "model_size", default="base.en")
        self.device = config.get("stt", "device", default="auto")
        self.compute_type = config.get("stt", "compute_type", default="int8")
        self.pause_threshold = config.get("stt", "pause_threshold", default=1.2)
        self.phrase_time_limit = config.get("stt", "phrase_time_limit", default=15.0)

        self.recognizer = None
        self.whisper_model = None

        # Initialize SpeechRecognizer
        if _sr_available:
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = self.pause_threshold
            self.recognizer.energy_threshold = config.get("stt", "energy_threshold", default=300)
            self.recognizer.dynamic_energy_threshold = True

        # Initialize faster-whisper model lazily or on startup
        if _faster_whisper_available and self.engine_type == "faster-whisper":
            try:
                print(f"[STT] Loading faster-whisper model '{self.model_size}'...")
                self.whisper_model = WhisperModel(
                    self.model_size,
                    device="cpu" if self.device == "auto" else self.device,
                    compute_type=self.compute_type
                )
                print("[STT] faster-whisper model loaded successfully.")
            except Exception as e:
                print(f"[STT] Could not load faster-whisper model: {e}. Will fallback to SpeechRecognition.")

    def listen_and_transcribe(self, prompt: str = "Listening...") -> str:
        """Capture microphone audio and return transcribed text."""
        if not _sr_available:
            print("[STT] SpeechRecognition not installed. Please input command via console:")
            return input("[USER]: ").strip()

        print(f"\n[JARVIS]: {prompt}")
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise briefly
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                print("[Audio] Recording utterance...")
                audio = self.recognizer.listen(
                    source,
                    timeout=8.0,
                    phrase_time_limit=self.phrase_time_limit
                )
                print("[Audio] Audio captured. Transcribing...")

            # 1. Transcribe with faster-whisper if available
            if self.whisper_model is not None:
                transcription = self._transcribe_with_whisper(audio)
                if transcription:
                    return transcription

            # 2. Fallback to SpeechRecognition (Google STT)
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"[STT User]: {text}")
                return text
            except sr.UnknownValueError:
                print("[STT] Could not understand audio.")
                return ""
            except sr.RequestError as e:
                print(f"[STT] Google STT service error: {e}")
                return ""

        except sr.WaitTimeoutError:
            print("[STT] Listening timed out (no speech detected).")
            return ""
        except Exception as e:
            print(f"[STT] Audio capture error: {e}")
            return ""

    def _transcribe_with_whisper(self, audio_data: "sr.AudioData") -> Optional[str]:
        """Convert captured AudioData to WAV and run faster-whisper transcription."""
        temp_wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav = f.name
                f.write(audio_data.get_wav_data())

            segments, info = self.whisper_model.transcribe(
                temp_wav,
                beam_size=5,
                language="en",
                vad_filter=True,
            )

            text_parts = [segment.text.strip() for segment in segments]
            full_text = " ".join(text_parts).strip()
            print(f"[STT faster-whisper]: {full_text}")
            return full_text
        except Exception as e:
            print(f"[STT] faster-whisper transcription failed: {e}")
            return None
        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass
