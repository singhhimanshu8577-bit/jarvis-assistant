"""
Web and Browser Automation Module for JARVIS.
Handles web searching, direct URL navigation, and browser tab controls.
"""

import urllib.parse
import webbrowser
from typing import Optional

from modules.base import ToolResult, tool

try:
    import pyautogui
except ImportError:
    pyautogui = None


@tool(
    name="search_web",
    description="Search the web using Google, YouTube, DuckDuckGo, or Wikipedia.",
    module_name="browser"
)
def search_web(query: str, engine: str = "google") -> ToolResult:
    """Perform a web search on the preferred engine."""
    clean_query = query.strip()
    encoded = urllib.parse.quote_plus(clean_query)
    engine_lower = engine.lower()

    if "youtube" in engine_lower:
        url = f"https://www.youtube.com/results?search_query={encoded}"
        target_name = "YouTube"
    elif "duck" in engine_lower:
        url = f"https://duckduckgo.com/?q={encoded}"
        target_name = "DuckDuckGo"
    elif "wiki" in engine_lower:
        url = f"https://en.wikipedia.org/wiki/Special:Search?search={encoded}"
        target_name = "Wikipedia"
    else:
        url = f"https://www.google.com/search?q={encoded}"
        target_name = "Google"

    try:
        webbrowser.open(url)
        return ToolResult(
            success=True,
            message=f"Searching {target_name} for '{clean_query}', Sir.",
            data={"url": url, "engine": target_name}
        )
    except Exception as e:
        return ToolResult(success=False, message=f"Failed to open browser search: {e}")


@tool(
    name="open_website",
    description="Open a specific website URL or domain (e.g., 'github.com', 'reddit.com', 'gmail.com', 'news.ycombinator.com').",
    module_name="browser"
)
def open_website(url_or_domain: str) -> ToolResult:
    """Navigate directly to a website URL or domain."""
    target = url_or_domain.strip().lower()

    # Domain shortcut mapping
    domain_shortcuts = {
        "gmail": "https://mail.google.com",
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://github.com",
        "reddit": "https://reddit.com",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "chatgpt": "https://chat.openai.com",
        "linkedin": "https://www.linkedin.com",
        "amazon": "https://www.amazon.com",
        "netflix": "https://www.netflix.com",
    }

    if target in domain_shortcuts:
        final_url = domain_shortcuts[target]
    elif not target.startswith("http://") and not target.startswith("https://"):
        final_url = f"https://{target}"
    else:
        final_url = target

    try:
        webbrowser.open(final_url)
        return ToolResult(
            success=True,
            message=f"Navigating to {url_or_domain}, Sir.",
            data={"url": final_url}
        )
    except Exception as e:
        return ToolResult(success=False, message=f"Failed to open {url_or_domain}: {e}")


@tool(
    name="close_browser_tab",
    description="Close the currently active browser tab.",
    module_name="browser"
)
def close_browser_tab() -> ToolResult:
    """Close the active browser tab via Ctrl+W / Command+W."""
    if pyautogui is None:
        return ToolResult(success=False, message="pyautogui is required for tab control.")

    try:
        import platform
        if platform.system() == "Darwin":
            pyautogui.hotkey("command", "w")
        else:
            pyautogui.hotkey("ctrl", "w")
        return ToolResult(success=True, message="Closed active tab, Sir.")
    except Exception as e:
        return ToolResult(success=False, message=f"Could not close tab: {e}")


@tool(
    name="switch_browser_tab",
    description="Switch to the next or previous browser tab ('next' or 'previous').",
    module_name="browser"
)
def switch_browser_tab(direction: str = "next") -> ToolResult:
    """Switch browser tab via Ctrl+Tab or Ctrl+Shift+Tab."""
    if pyautogui is None:
        return ToolResult(success=False, message="pyautogui is required for tab control.")

    try:
        import platform
        is_mac = platform.system() == "Darwin"
        modifier = "command" if is_mac else "ctrl"

        if "prev" in direction.lower():
            pyautogui.hotkey(modifier, "shift", "tab")
            action = "previous"
        else:
            pyautogui.hotkey(modifier, "tab")
            action = "next"

        return ToolResult(success=True, message=f"Switched to {action} tab, Sir.")
    except Exception as e:
        return ToolResult(success=False, message=f"Could not switch tab: {e}")


@tool(
    name="new_browser_tab",
    description="Open a new blank browser tab.",
    module_name="browser"
)
def new_browser_tab() -> ToolResult:
    """Open a new browser tab via Ctrl+T."""
    if pyautogui is None:
        return ToolResult(success=False, message="pyautogui is required for tab control.")

    try:
        import platform
        if platform.system() == "Darwin":
            pyautogui.hotkey("command", "t")
        else:
            pyautogui.hotkey("ctrl", "t")
        return ToolResult(success=True, message="Opened a new tab, Sir.")
    except Exception as e:
        return ToolResult(success=False, message=f"Could not open new tab: {e}")
