"""
LLM Client Interface for JARVIS.
Provides multi-provider support for Google Gemini, OpenAI, Ollama, and an Offline Rule Engine.
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from config.config_loader import config
from modules.base import ToolRegistry, registry
from modules.chat import SYSTEM_PROMPT


@dataclass
class LLMResponse:
    """Standardized response from LLM."""
    text: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    is_tool_call: bool = False
    provider: str = "offline"


class RuleBasedEngine:
    """Fast offline pattern matching when no LLM API is available or configured."""

    def match(self, text: str) -> Optional[LLMResponse]:
        query = text.strip().lower()

        # 1. System status queries
        if re.search(r"\b(battery|cpu|ram|memory|system status|specs|hardware)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "get_system_status", "arguments": {}}],
                provider="rule_engine"
            )

        # 2. Lock workstation
        if re.search(r"\b(lock|lock computer|lock pc|lock workstation|lock screen)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "lock_workstation", "arguments": {}}],
                provider="rule_engine"
            )

        # 3. Shutdown
        if re.search(r"\b(shutdown|shut down|turn off pc|power off)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "shutdown_system", "arguments": {"confirm": False}}],
                provider="rule_engine"
            )

        # 4. Restart
        if re.search(r"\b(restart|reboot)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "restart_system", "arguments": {"confirm": False}}],
                provider="rule_engine"
            )

        # 5. Sleep
        if re.search(r"\b(sleep|suspend|go to sleep)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "sleep_system", "arguments": {"confirm": False}}],
                provider="rule_engine"
            )

        # 6. Volume Control
        vol_match = re.search(r"\b(?:set\s+volume\s+to|volume)\s+(\d{1,3})%?\b", query)
        if vol_match:
            vol_val = int(vol_match.group(1))
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "set_volume", "arguments": {"level_percent": vol_val}}],
                provider="rule_engine"
            )
        if re.search(r"\b(mute|silence audio|mute volume)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "mute_volume", "arguments": {"mute": True}}],
                provider="rule_engine"
            )
        if re.search(r"\b(unmute|resume sound|turn sound back on)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "mute_volume", "arguments": {"mute": False}}],
                provider="rule_engine"
            )

        # 7. Media Controls
        if re.search(r"\b(pause|pause music|pause video|resume|resume music|play pause)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "media_control", "arguments": {"action": "play_pause"}}],
                provider="rule_engine"
            )
        if re.search(r"\b(next track|next song|skip song|skip track|next)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "media_control", "arguments": {"action": "next"}}],
                provider="rule_engine"
            )
        if re.search(r"\b(previous track|previous song|last song|prev song)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "media_control", "arguments": {"action": "previous"}}],
                provider="rule_engine"
            )

        # 8. Play music on YouTube/Spotify
        music_play = re.search(r"\b(?:play)\s+(.+?)(?:\s+on\s+(spotify|youtube))?$", query)
        if music_play:
            track = music_play.group(1).strip()
            platform_target = music_play.group(2) or "youtube"
            # avoid matching 'play pause'
            if track not in ("pause", "next", "previous"):
                return LLMResponse(
                    is_tool_call=True,
                    tool_calls=[{"name": "play_music", "arguments": {"query": track, "platform_name": platform_target}}],
                    provider="rule_engine"
                )

        # 9. App Launching
        app_match = re.search(r"\b(?:open|launch|start)\s+(chrome|notepad|calculator|calc|vscode|spotify|discord|paint|terminal|explorer|word|excel)\b", query)
        if app_match:
            app_name = app_match.group(1).strip()
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "launch_application", "arguments": {"app_name": app_name}}],
                provider="rule_engine"
            )

        # 10. Folder opening
        folder_match = re.search(r"\b(?:open)\s+(downloads|documents|desktop|pictures|videos|music)\s*(?:folder)?\b", query)
        if folder_match:
            folder_name = folder_match.group(1).strip()
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "open_folder", "arguments": {"folder_name": folder_name}}],
                provider="rule_engine"
            )

        # 11. Search Web / Google
        search_match = re.search(r"\b(?:search\s+google\s+for|search\s+for|google|search|look\s+up)\s+(.+)$", query)
        if search_match:
            search_query = search_match.group(1).strip()
            # Clean leading 'google for' or 'for' if leftover
            search_query = re.sub(r"^(?:google\s+for|for)\s+", "", search_query).strip()
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "search_web", "arguments": {"query": search_query, "engine": "google"}}],
                provider="rule_engine"
            )

        # 12. Open website
        web_match = re.search(r"\b(?:open|go to|navigate to)\s+([a-zA-Z0-9-]+\.(?:com|org|net|io|ai|gov|edu|co))\b", query)
        if web_match:
            domain = web_match.group(1).strip()
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "open_website", "arguments": {"url_or_domain": domain}}],
                provider="rule_engine"
            )

        # 13. File search
        file_match = re.search(r"\b(?:find|locate|search for file)\s+(.+)$", query)
        if file_match:
            file_name = file_match.group(1).strip()
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "search_and_open_file", "arguments": {"file_name": file_name}}],
                provider="rule_engine"
            )

        # 14. Tab controls
        if re.search(r"\b(close tab|close active tab)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "close_browser_tab", "arguments": {}}],
                provider="rule_engine"
            )
        if re.search(r"\b(next tab|switch tab)\b", query):
            return LLMResponse(
                is_tool_call=True,
                tool_calls=[{"name": "switch_browser_tab", "arguments": {"direction": "next"}}],
                provider="rule_engine"
            )

        # Default conversational greeting / fallback
        if re.search(r"\b(hello|hi|hey jarvis|good morning|good evening|who are you)\b", query):
            return LLMResponse(
                text="Good day, Sir. All systems are online and functioning within normal parameters. How may I be of assistance?",
                is_tool_call=False,
                provider="rule_engine"
            )

        return None


class LLMClient:
    """Unified LLM client interface supporting Gemini, OpenAI, Ollama, and Rule Engine fallback."""

    def __init__(self, tool_registry: ToolRegistry = registry):
        self.tool_registry = tool_registry
        self.provider = config.get("llm", "provider", default="gemini").lower()
        self.model = config.get("llm", "model", default="gemini-1.5-flash")
        self.rule_engine = RuleBasedEngine()

        # Initialize clients
        self.gemini_key = os.getenv("GEMINI_API_KEY") or config.get("llm", "gemini_api_key")
        self.openai_key = os.getenv("OPENAI_API_KEY") or config.get("llm", "openai_api_key")
        self.ollama_url = os.getenv("OLLAMA_HOST") or config.get("llm", "ollama_base_url", default="http://localhost:11434/v1")

    def generate_response(self, user_query: str, history: List[Dict[str, str]] = None) -> LLMResponse:
        """Process user input with LLM tools or rule engine."""
        history = history or []

        # 1. Try Gemini Provider if configured
        if self.gemini_key and self.provider in ("gemini", "auto"):
            try:
                res = self._call_gemini(user_query, history)
                if res:
                    return res
            except Exception as e:
                print(f"[LLM] Gemini call failed: {e}. Trying fallback.")

        # 2. Try OpenAI Provider if configured
        if self.openai_key and self.provider in ("openai", "auto"):
            try:
                res = self._call_openai(user_query, history)
                if res:
                    return res
            except Exception as e:
                print(f"[LLM] OpenAI call failed: {e}. Trying fallback.")

        # 3. Try Local Ollama if explicitly chosen
        if self.provider == "ollama":
            try:
                res = self._call_ollama(user_query, history)
                if res:
                    return res
            except Exception:
                pass

        # 4. Deterministic Rule Matching Fallback
        rule_res = self.rule_engine.match(user_query)
        if rule_res:
            return rule_res

        # 5. Default conversational fallback
        return LLMResponse(
            text=f"Command received, Sir. I have registered: '{user_query}'.",
            is_tool_call=False,
            provider="offline_fallback"
        )

    def _call_openai(self, user_query: str, history: List[Dict[str, str]]) -> Optional[LLMResponse]:
        """Execute OpenAI tool-calling."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)
            tools = self.tool_registry.get_openai_tools()

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(history)
            messages.append({"role": "user", "content": user_query})

            completion = client.chat.completions.create(
                model=self.model if "gpt" in self.model else "gpt-4o-mini",
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.7,
            )

            msg = completion.choices[0].message
            if msg.tool_calls:
                parsed_calls = []
                for tc in msg.tool_calls:
                    parsed_calls.append({
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments or "{}"),
                    })
                return LLMResponse(
                    text=msg.content,
                    tool_calls=parsed_calls,
                    is_tool_call=True,
                    provider="openai"
                )
            else:
                return LLMResponse(
                    text=msg.content,
                    is_tool_call=False,
                    provider="openai"
                )
        except Exception as e:
            print(f"[LLM] OpenAI Error: {e}")
            return None

    def _call_ollama(self, user_query: str, history: List[Dict[str, str]]) -> Optional[LLMResponse]:
        """Execute Ollama OpenAI-compatible tool calling."""
        try:
            import openai
            client = openai.OpenAI(base_url=self.ollama_url, api_key="ollama")
            tools = self.tool_registry.get_openai_tools()

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(history)
            messages.append({"role": "user", "content": user_query})

            completion = client.chat.completions.create(
                model="llama3.1:latest",
                messages=messages,
                tools=tools if tools else None,
                temperature=0.7,
            )

            msg = completion.choices[0].message
            if msg.tool_calls:
                parsed_calls = []
                for tc in msg.tool_calls:
                    parsed_calls.append({
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments or "{}"),
                    })
                return LLMResponse(
                    text=msg.content,
                    tool_calls=parsed_calls,
                    is_tool_call=True,
                    provider="ollama"
                )
            else:
                return LLMResponse(
                    text=msg.content,
                    is_tool_call=False,
                    provider="ollama"
                )
        except Exception:
            return None

    def _call_gemini(self, user_query: str, history: List[Dict[str, str]]) -> Optional[LLMResponse]:
        """Execute Google Gemini function calling."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)

            # Register tools functions with Gemini
            tools_list = [t.func for t in self.tool_registry.get_all().values()]
            model_name = self.model if "gemini" in self.model else "gemini-1.5-flash"
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
                tools=tools_list,
            )

            chat = model.start_chat(enable_automatic_function_calling=False)
            response = chat.send_message(user_query)

            # Check for function calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fn_name = part.function_call.name
                        fn_args = dict(part.function_call.args)
                        return LLMResponse(
                            text=None,
                            tool_calls=[{"name": fn_name, "arguments": fn_args}],
                            is_tool_call=True,
                            provider="gemini"
                        )

            return LLMResponse(
                text=response.text,
                is_tool_call=False,
                provider="gemini"
            )
        except Exception as e:
            print(f"[LLM] Gemini Error: {e}")
            return None
