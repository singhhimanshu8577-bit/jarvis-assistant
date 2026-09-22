"""
Configuration loader and validator for JARVIS Voice Assistant.
"""

import os
from pathlib import Path
from typing import Any, Dict

# Try importing yaml and dotenv safely
try:
    import yaml
except ImportError:
    yaml = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_CONFIG: Dict[str, Any] = {
    "assistant": {
        "name": "JARVIS",
        "user_name": "Sir",
        "persona_prompt": (
            "You are JARVIS, an articulate, polite, and sophisticated AI assistant. "
            "Address the user with crisp British elegance and brevity. "
            "Keep spoken answers concise and directly actionable."
        ),
    },
    "wake_word": {
        "enabled": True,
        "engine": "openwakeword",
        "keyword": "jarvis",
        "sensitivity": 0.5,
        "sample_rate": 16000,
        "chunk_size": 1280,
    },
    "stt": {
        "engine": "faster-whisper",
        "model_size": "base.en",
        "device": "auto",
        "compute_type": "int8",
        "energy_threshold": 300,
        "pause_threshold": 1.2,
        "phrase_time_limit": 15.0,
    },
    "tts": {
        "engine": "edge-tts",
        "voice": "en-GB-RyanNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "fallback_engine": "pyttsx3",
    },
    "llm": {
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "temperature": 0.7,
        "max_tokens": 500,
        "ollama_base_url": "http://localhost:11434/v1",
    },
    "modules": {
        "system": {
            "require_confirmation_for_destructive": True,
            "safe_mode": False,
        },
        "apps_and_files": {
            "search_directories": ["Desktop", "Documents", "Downloads", "Pictures", "Videos"],
            "max_search_depth": 3,
            "max_results": 5,
        },
        "browser": {
            "default_engine": "google",
            "preferred_browser": "",
        },
        "media": {
            "default_platform": "youtube",
        },
    },
}


def _deep_merge(source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries."""
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            _deep_merge(value, destination[key])
        else:
            destination[key] = value
    return destination


class Config:
    """Singleton-style wrapper for configuration access."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._find_config_file()
        self._data: Dict[str, Any] = self._load()

    def _find_config_file(self) -> str:
        current_dir = Path(__file__).parent.resolve()
        candidate = current_dir / "config.yaml"
        if candidate.exists():
            return str(candidate)
        return str(Path.cwd() / "config" / "config.yaml")

    def _load(self) -> Dict[str, Any]:
        # Start with default dictionary copy
        import copy
        merged = copy.deepcopy(DEFAULT_CONFIG)

        if self.config_path and Path(self.config_path).exists():
            if yaml is not None:
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        file_data = yaml.safe_load(f)
                        if isinstance(file_data, dict):
                            _deep_merge(file_data, merged)
                except Exception as e:
                    print(f"[Config] Warning: Failed to parse {self.config_path}: {e}")
            else:
                print("[Config] PyYAML not installed. Using default configuration.")

        # Environment variable overrides
        if os.getenv("GEMINI_API_KEY"):
            merged["llm"]["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
        if os.getenv("OPENAI_API_KEY"):
            merged["llm"]["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OLLAMA_HOST"):
            merged["llm"]["ollama_base_url"] = os.getenv("OLLAMA_HOST")

        return merged

    def get(self, *keys: str, default: Any = None) -> Any:
        """Fetch nested configuration value by key chain."""
        node = self._data
        for k in keys:
            if isinstance(node, dict) and k in node:
                node = node[k]
            else:
                return default
        return node

    @property
    def data(self) -> Dict[str, Any]:
        return self._data


# Global instance
config = Config()
