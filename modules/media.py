"""
Media and Music Playback Module for JARVIS.
Handles playing tracks on YouTube/Spotify and controlling OS media keys (play, pause, skip, prev).
"""

import ctypes
import os
import platform
import urllib.parse
import webbrowser
from typing import Optional

from modules.base import ToolResult, tool

try:
    import pyautogui
except ImportError:
    pyautogui = None

# Windows Virtual Key Codes for Media
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def _send_windows_media_key(vk_code: int):
    """Send hardware media key event using Windows ctypes."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False


@tool(
    name="play_music",
    description="Play a song, artist, playlist, or music track on YouTube or Spotify.",
    module_name="media"
)
def play_music(query: str, platform_name: str = "youtube") -> ToolResult:
    """Search and play music on YouTube or Spotify."""
    clean_query = query.strip()
    encoded = urllib.parse.quote_plus(clean_query)
    current_os = platform.system()
    plat = platform_name.lower()

    if "spotify" in plat:
        # 1. Try Spotify URI handler
        spotify_uri = f"spotify:search:{encoded}"
        try:
            if current_os == "Windows":
                os.startfile(spotify_uri)
                return ToolResult(success=True, message=f"Playing '{clean_query}' on Spotify, Sir.")
            elif current_os == "Darwin":
                import subprocess
                subprocess.run(["open", spotify_uri], check=False)
                return ToolResult(success=True, message=f"Playing '{clean_query}' on Spotify, Sir.")
        except Exception:
            pass

        # Web fallback
        web_url = f"https://open.spotify.com/search/{encoded}"
        webbrowser.open(web_url)
        return ToolResult(success=True, message=f"Opening '{clean_query}' on Spotify Web, Sir.")

    else:
        # YouTube Playback
        # Note: We can open the direct search or search result with autoplay query
        url = f"https://www.youtube.com/results?search_query={encoded}"
        try:
            webbrowser.open(url)
            return ToolResult(
                success=True,
                message=f"Playing '{clean_query}' on YouTube, Sir.",
                data={"url": url, "platform": "YouTube"}
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to open YouTube: {e}")


@tool(
    name="media_control",
    description="Control active media playback. Actions: 'play_pause', 'pause', 'play', 'resume', 'next', 'previous', 'stop'.",
    module_name="media"
)
def media_control(action: str) -> ToolResult:
    """Trigger OS media controls (play/pause/skip)."""
    clean_action = action.strip().lower().replace(" ", "_")
    current_os = platform.system()

    if current_os == "Windows":
        if clean_action in ("play_pause", "play", "pause", "resume"):
            success = _send_windows_media_key(VK_MEDIA_PLAY_PAUSE)
            verb = "Toggled playback"
        elif clean_action in ("next", "next_track", "skip"):
            success = _send_windows_media_key(VK_MEDIA_NEXT_TRACK)
            verb = "Skipped to next track"
        elif clean_action in ("prev", "previous", "previous_track", "back"):
            success = _send_windows_media_key(VK_MEDIA_PREV_TRACK)
            verb = "Returned to previous track"
        elif clean_action == "stop":
            success = _send_windows_media_key(VK_MEDIA_STOP)
            verb = "Stopped playback"
        else:
            return ToolResult(success=False, message=f"Unknown media action '{action}'.")

        if success:
            return ToolResult(success=True, message=f"{verb}, Sir.")

    # Cross-platform / PyAutoGUI fallback
    if pyautogui is not None:
        try:
            if clean_action in ("play_pause", "play", "pause", "resume"):
                pyautogui.press("playpause")
            elif clean_action in ("next", "next_track", "skip"):
                pyautogui.press("nexttrack")
            elif clean_action in ("prev", "previous", "previous_track", "back"):
                pyautogui.press("prevtrack")
            elif clean_action == "stop":
                pyautogui.press("stop")
            return ToolResult(success=True, message=f"Media control '{clean_action}' executed, Sir.")
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to execute media key: {e}")

    return ToolResult(success=False, message="Media key control is not supported on this configuration.")
