"""
Text-to-Speech (TTS) Speaker Subsystem for JARVIS.
Supports low-latency Microsoft Edge Neural Voices (edge-tts) with pyttsx3 offline fallback.
"""

import asyncio
import os
import platform
import tempfile
import threading
import time
from typing import Optional

from config.config_loader import config

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import pygame
    _pygame_available = True
except ImportError:
    _pygame_available = False


class Speaker:
    """TTS Audio synthesis and playback manager."""

    def __init__(self):
        self.engine_type = config.get("tts", "engine", default="edge-tts").lower()
        self.voice = config.get("tts", "voice", default="en-GB-RyanNeural")
        self.rate = config.get("tts", "rate", default="+0%")
        self.pitch = config.get("tts", "pitch", default="+0Hz")
        self.volume = config.get("tts", "volume", default="+0%")
        self.is_speaking = False
        self._lock = threading.Lock()

        # Initialize pygame audio mixer if present
        if _pygame_available:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception:
                pass

        # Initialize pyttsx3 fallback engine
        self.pyttsx3_engine = None
        if pyttsx3 is not None:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self.pyttsx3_engine.setProperty("rate", 185)
            except Exception:
                self.pyttsx3_engine = None

    def speak(self, text: str, block: bool = True):
        """Speak the given text using the configured TTS pipeline."""
        clean_text = text.strip()
        if not clean_text:
            return

        # Print speech banner in console
        print(f"\n[JARVIS]: {clean_text}")

        if block:
            self._speak_sync(clean_text)
        else:
            thread = threading.Thread(target=self._speak_sync, args=(clean_text,), daemon=True)
            thread.start()

    def _speak_sync(self, text: str):
        """Synchronous speech execution."""
        with self._lock:
            self.is_speaking = True
            try:
                # 1. Try edge-tts if enabled and available
                if self.engine_type == "edge-tts" and edge_tts is not None:
                    success = self._speak_edge_tts(text)
                    if success:
                        return

                # 2. Try pyttsx3 offline fallback
                if self.pyttsx3_engine is not None:
                    self._speak_pyttsx3(text)
                    return

            except Exception as e:
                print(f"[Speaker] TTS Error: {e}")
            finally:
                self.is_speaking = False

    def _speak_edge_tts(self, text: str) -> bool:
        """Synthesize and play audio with edge-tts."""
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_file = f.name

            # Run async edge-tts synthesis
            async def _synthesize():
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice,
                    rate=self.rate,
                    pitch=self.pitch,
                    volume=self.volume,
                )
                await communicate.save(temp_file)

            asyncio.run(_synthesize())

            # Play generated audio
            self._play_audio_file(temp_file)
            return True
        except Exception as e:
            print(f"[Speaker] edge-tts synthesis failed: {e}. Falling back to pyttsx3.")
            return False
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    # Give audio lock time to release
                    time.sleep(0.05)
                    os.remove(temp_file)
                except Exception:
                    pass

    def _speak_pyttsx3(self, text: str):
        """Offline speech synthesis using pyttsx3."""
        try:
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
        except Exception as e:
            print(f"[Speaker] pyttsx3 failed: {e}")

    def _play_audio_file(self, file_path: str):
        """Play audio file via pygame mixer or platform sound players."""
        if _pygame_available:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.music.unload()
                return
            except Exception:
                pass

        # Windows PowerShell Sound Player fallback
        if platform.system() == "Windows":
            try:
                import subprocess
                ps_command = f"""
                $player = New-Object -ComObject WMPlayer.OCX;
                $player.URL = '{file_path}';
                $player.controls.play();
                while ($player.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }};
                """
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], check=False)
            except Exception:
                pass

    def stop(self):
        """Stop current speech output."""
        if _pygame_available and pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.is_speaking = False
