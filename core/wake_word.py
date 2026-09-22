"""
Wake Word Detection Subsystem for JARVIS.

Supports openWakeWord neural models, energy-based threshold detection,
and keyword triggers.
"""

import threading
import time
from typing import Callable, Optional

from config.config_loader import config


# ---------------------------------------------------------
# PyAudio
# ---------------------------------------------------------
try:
    import pyaudio
    _pyaudio_available = True
except ImportError:
    _pyaudio_available = False


# ---------------------------------------------------------
# NumPy
# ---------------------------------------------------------
try:
    import numpy as np
    _numpy_available = True
except ImportError:
    _numpy_available = False


# ---------------------------------------------------------
# openWakeWord
# ---------------------------------------------------------
try:
    import openwakeword
    from openwakeword.model import Model as OWWModel
    _oww_available = True
except ImportError:
    _oww_available = False


class WakeWordDetector:
    """Always-on lightweight listener for wake word activation."""

    def __init__(self, on_wake_callback: Optional[Callable] = None):

        self.on_wake_callback = on_wake_callback

        self.enabled = config.get(
            "wake_word",
            "enabled",
            default=True
        )

        self.engine_type = config.get(
            "wake_word",
            "engine",
            default="openwakeword"
        )

        self.keyword = config.get(
            "wake_word",
            "keyword",
            default="jarvis"
        ).lower()

        self.sensitivity = config.get(
            "wake_word",
            "sensitivity",
            default=0.35
        )

        self.sample_rate = config.get(
            "wake_word",
            "sample_rate",
            default=16000
        )

        self.chunk_size = config.get(
            "wake_word",
            "chunk_size",
            default=1280
        )

        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._oww_model = None

        # -------------------------------------------------
        # Load openWakeWord model
        # -------------------------------------------------
        if _oww_available and self.engine_type == "openwakeword":

            try:

                self._oww_model = OWWModel(
                    wakeword_models=["hey_jarvis"],
                    inference_framework="onnx"
                )

                print(
                    "[WakeWord] openWakeWord model loaded successfully."
                )

            except Exception as e:

                print(
                    f"[WakeWord] Failed to load openWakeWord model: "
                    f"{e}. Falling back to audio listener."
                )

    # -----------------------------------------------------
    # START LISTENING
    # -----------------------------------------------------
    def start_listening(self, callback: Optional[Callable] = None):
        """Start wake word detection in a background thread."""

        if callback:
            self.on_wake_callback = callback

        if self.is_running:
            return

        self.is_running = True

        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )

        self._thread.start()

        print(
            f"[WakeWord] Wake word detector active "
            f"(Listening for '{self.keyword}')..."
        )

    # -----------------------------------------------------
    # STOP LISTENING
    # -----------------------------------------------------
    def stop_listening(self):
        """Stop wake word detection thread."""

        self.is_running = False

        if self._thread and self._thread.is_alive():

            self._thread.join(timeout=1.0)

        print("[WakeWord] Wake word detector stopped.")

    # -----------------------------------------------------
    # MAIN LISTENING LOOP
    # -----------------------------------------------------
    def _listen_loop(self):
        """Continuous audio stream processing."""

        if not _pyaudio_available:

            print(
                "[WakeWord] PyAudio not installed. "
                "Wake word streaming inactive. "
                "Use voice prompt or text mode."
            )

            return

        pa = pyaudio.PyAudio()

        # -------------------------------------------------
        # Open microphone
        # -------------------------------------------------
        try:

            stream = pa.open(
                rate=self.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

        except Exception as e:

            print(
                f"[WakeWord] Failed to open microphone input stream: {e}"
            )

            pa.terminate()
            return

        # -------------------------------------------------
        # Continuous processing
        # -------------------------------------------------
        try:

            while self.is_running:

                try:

                    audio_chunk = stream.read(
                        self.chunk_size,
                        exception_on_overflow=False
                    )

                except Exception:

                    continue

                if not audio_chunk:

                    time.sleep(0.01)
                    continue

                # =================================================
                # 1. openWakeWord neural detection
                # =================================================
                if self._oww_model and _numpy_available:

                    # Convert microphone bytes to NumPy audio
                    audio_data = np.frombuffer(
                        audio_chunk,
                        dtype=np.int16
                    )

                    # -------------------------------------------------
                    # Boost microphone input
                    # -------------------------------------------------
                    gain = 2.0

                    audio_data = np.clip(
                        audio_data.astype(np.float32) * gain,
                        -32768,
                        32767
                    ).astype(np.int16)

                    # -------------------------------------------------
                    # Run wake-word prediction
                    # -------------------------------------------------
                    prediction = self._oww_model.predict(
                        audio_data
                    )

                    # -------------------------------------------------
                    # Check model predictions
                    # -------------------------------------------------
                    for mdl_name, score in (
                        self._oww_model.prediction_buffer.items()
                    ):

                        confidence = score[-1]

                        # Debug confidence
                        print(
                            f"\r[WakeWord] {mdl_name}: "
                            f"{confidence:.3f}",
                            end="",
                            flush=True
                        )

                        # -------------------------------------------------
                        # Wake-word condition
                        # -------------------------------------------------
                        if (
                            "hey_jarvis" in mdl_name.lower()
                            and confidence >= self.sensitivity
                        ):

                            print(
                                "\n>>> WAKE WORD CONDITION TRIGGERED <<<"
                            )

                            print(
                                f"\n[WakeWord] Wake word detected: "
                                f"'{mdl_name}' "
                                f"(confidence: {confidence:.2f})"
                            )

                            # Reset model after detection
                            self._oww_model.reset()

                            # Call JARVIS callback
                            if self.on_wake_callback:

                                self.on_wake_callback()

                            # Prevent immediate repeated detection
                            time.sleep(1.0)

                            break

                # =================================================
                # 2. Simple audio volume fallback
                # =================================================
                elif _numpy_available:

                    audio_data = np.frombuffer(
                        audio_chunk,
                        dtype=np.int16
                    )

                    peak = np.abs(audio_data).mean()

                    if peak > 2500:

                        # Fallback trigger
                        # Currently disabled intentionally.
                        pass

        # -----------------------------------------------------
        # Cleanup
        # -----------------------------------------------------
        finally:

            try:

                stream.stop_stream()
                stream.close()

            except Exception:

                pass

            pa.terminate()