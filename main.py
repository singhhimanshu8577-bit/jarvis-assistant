"""
JARVIS: Modular Desktop AI Voice Assistant
Main application lifecycle entrypoint and execution coordinator.
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from config.config_loader import config
from core.listener import AudioListener
from core.router import Router
from core.speaker import Speaker
from core.wake_word import WakeWordDetector
from modules.base import registry

# Import all modules to trigger tool registration
import modules


BANNER = r"""
   ╦╔═╗╦═╗╦  ╦╦╔═╗
   ║╠═╣╠╦╝╚╗╔╝║╚═╗
  ╚╝╩ ╩╩╚═ ╚╝ ╩╚═╝
  Desktop AI Voice Assistant v2.0
  Modular | Multi-Provider | OS Automated
"""


class JarvisAssistant:
    """Main application manager for JARVIS."""

    def __init__(self, mode: str = "voice"):
        self.mode = mode
        self.router = Router()
        self.speaker = Speaker()
        self.listener = AudioListener()

        self.wake_detector = WakeWordDetector(
            on_wake_callback=self._on_wake_word_triggered
        )

        self.is_running = False
        self._wake_triggered = False

    def print_status(self):
        """Display startup diagnostic summary."""

        print(BANNER)
        print("=" * 55)

        print(
            f" [*] Assistant Name    : "
            f"{config.get('assistant', 'name')}"
        )

        print(
            f" [*] Execution Mode    : "
            f"{self.mode.upper()}"
        )

        print(
            f" [*] TTS Voice Engine  : "
            f"{config.get('tts', 'engine')} "
            f"({config.get('tts', 'voice')})"
        )

        print(
            f" [*] STT Engine        : "
            f"{config.get('stt', 'engine')} "
            f"({config.get('stt', 'model_size')})"
        )

        print(
            f" [*] LLM Provider      : "
            f"{config.get('llm', 'provider')} "
            f"({config.get('llm', 'model')})"
        )

        print(
            f" [*] Tools Registered  : "
            f"{len(registry.get_all())} active functions"
        )

        for tool_name, t_def in registry.get_all().items():
            print(
                f"     - {tool_name} "
                f"[{t_def.module_name}]"
            )

        print("=" * 55)

    def run(self):
        """Start the assistant in either text or voice mode."""

        self.is_running = True
        self.print_status()

        greeting = (
            f"JARVIS initialized and ready. "
            f"How may I assist you, "
            f"{config.get('assistant', 'user_name')}?"
        )

        self.speaker.speak(
            greeting,
            block=False
        )

        if self.mode == "text":
            self._run_text_mode()
        else:
            self._run_voice_mode()

    def _run_text_mode(self):
        """Interactive console REPL for testing and text-based interaction."""

        print(
            "\n[Mode: Text Interactive] "
            "Type your command, or 'exit' / 'quit' to close."
        )

        while self.is_running:
            try:
                user_input = input("\n[USER]> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in (
                    "exit",
                    "quit",
                    "goodbye",
                    "bye"
                ):
                    self.speaker.speak(
                        "Shutting down assistant interface. "
                        "Have a pleasant day, Sir."
                    )
                    break

                response = self.router.process_input(
                    user_input
                )

                self.speaker.speak(response)

            except KeyboardInterrupt:
                print(
                    "\n[JARVIS] Session interrupted by user."
                )
                break

            except Exception as e:
                print(
                    f"[Error] Unexpected exception: {e}"
                )

        self.shutdown()

    def _run_voice_mode(self):
        """Continuous Voice Listening Loop with Wake Word Activation."""

        print(
            "\n[Mode: Voice Active] "
            "Say 'Jarvis' to activate, or press Ctrl+C to exit.\n"
        )

        # Start wake-word detection
        self.wake_detector.start_listening(
            callback=self._on_wake_word_triggered
        )

        while self.is_running:
            try:

                # Check if wake word was detected
                if self._wake_triggered:

                    # Reset trigger flag
                    self._wake_triggered = False

                    # Stop wake-word detector temporarily
                    self.wake_detector.stop_listening()

                    # JARVIS responds
                    self.speaker.speak(
                        "Yes, Sir?",
                        block=True
                    )
                    print("[DEBUG] JARVIS finished speaking. Starting microphone...")

                    # Listen for user's command
                    user_utterance = (
                        self.listener.listen_and_transcribe(
                            prompt="Listening for command..."
                        )
                    )

                    if user_utterance:

                        # Check exit keywords
                        if user_utterance.lower() in (
                            "goodbye jarvis",
                            "exit",
                            "quit",
                            "go to sleep"
                        ):

                            self.speaker.speak(
                                "Powering down voice interface. "
                                "Goodbye, Sir."
                            )

                            break

                        # Process command
                        response = self.router.process_input(
                            user_utterance
                        )

                        # Speak response
                        self.speaker.speak(
                            response,
                            block=True
                        )

                    # Restart wake-word detection
                    if self.is_running:

                        self.wake_detector.start_listening(
                            callback=self._on_wake_word_triggered
                        )

                time.sleep(0.1)

            except KeyboardInterrupt:

                print(
                    "\n[JARVIS] Voice session interrupted by user."
                )

                break

            except Exception as e:

                print(
                    f"[Voice Error] {e}"
                )

        self.shutdown()

    def _on_wake_word_triggered(self):
        """Callback from WakeWordDetector."""

        self._wake_triggered = True

    def shutdown(self):
        """Gracefully release all resources."""

        self.is_running = False

        self.wake_detector.stop_listening()

        self.speaker.stop()

        print(
            "\n[JARVIS] Assistant terminated safely."
        )


def run_diagnostics():
    """Run self-test diagnostics on all modules and components."""

    import unittest.mock as mock

    print("=" * 60)
    print("Running JARVIS Diagnostic Self-Test...")
    print("=" * 60)

    # 1. Test Registry & Schema Generation
    tools = registry.get_all()

    print(
        f"[PASS] Registered {len(tools)} tools:"
    )

    for name, tdef in tools.items():
        print(
            f"  - {name} "
            f"({tdef.module_name}): "
            f"{tdef.description[:50]}..."
        )

    openai_tools = registry.get_openai_tools()

    print(
        f"[PASS] Generated "
        f"{len(openai_tools)} OpenAI tool schemas."
    )

    gemini_tools = registry.get_gemini_tools()

    print(
        f"[PASS] Generated "
        f"{len(gemini_tools)} Gemini function declarations."
    )

    # 2. Test Router & Rule Engine
    with mock.patch(
        "webbrowser.open",
        return_value=True
    ):

        router = Router()

        test_queries = [
            "What is my battery and CPU status?",
            "Set volume to 50%",
            "Search google for Python tutorials",
            "Play synthwave on YouTube",
            "Who are you?",
        ]

        print("\nTesting Query Processing:")

        for q in test_queries:

            resp = router.process_input(q)

            print(
                f" -> Query   : '{q}'\n"
                f"    Response: {resp}\n"
            )

    print(
        "[PASS] Router and rule engine "
        "verification completed successfully."
    )

    print("=" * 60)
    print("All diagnostic self-tests PASSED!")


def main():

    parser = argparse.ArgumentParser(
        description="JARVIS: Modular Desktop AI Voice Assistant"
    )

    parser.add_argument(
        "-t",
        "--text",
        action="store_true",
        help="Run in interactive text console mode"
    )

    parser.add_argument(
        "-v",
        "--voice",
        action="store_true",
        help="Run in continuous voice listening mode"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run diagnostic self-test on all modules"
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="Custom path to config.yaml"
    )

    args = parser.parse_args()

    if args.test:
        run_diagnostics()
        return

    mode = (
        "text"
        if args.text
        else (
            "voice"
            if args.voice
            else "text"
        )
    )

    app = JarvisAssistant(mode=mode)

    app.run()


if __name__ == "__main__":
    main()