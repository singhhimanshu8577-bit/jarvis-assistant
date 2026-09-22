"""
Automated Desktop & Start Menu Shortcut Installer for JARVIS.
Places one-click shortcuts on the Windows Desktop.
"""

import os
import platform
from pathlib import Path


def create_desktop_shortcuts():
    """Create one-click Windows Desktop launchers."""
    project_dir = Path(__file__).parent.resolve()
    desktop_dir = Path.home() / "Desktop"

    if not desktop_dir.exists():
        print(f"[Shortcuts] Desktop directory not found at {desktop_dir}. Skipping desktop shortcut.")
        return

    # 1. Create JARVIS (Voice Mode) Desktop Launcher
    voice_shortcut_path = desktop_dir / "JARVIS (Voice).bat"
    voice_content = f"""@echo off
title JARVIS Voice Assistant
cd /d "{project_dir}"
call JARVIS_Voice.bat
"""
    try:
        with open(voice_shortcut_path, "w", encoding="utf-8") as f:
            f.write(voice_content)
        print(f"[Shortcuts] Created Voice Launcher at: {voice_shortcut_path}")
    except Exception as e:
        print(f"[Shortcuts] Failed to create voice shortcut: {e}")

    # 2. Create JARVIS (Console Mode) Desktop Launcher
    text_shortcut_path = desktop_dir / "JARVIS (Console).bat"
    text_content = f"""@echo off
title JARVIS Interactive Console
cd /d "{project_dir}"
call JARVIS_Text.bat
"""
    try:
        with open(text_shortcut_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        print(f"[Shortcuts] Created Console Launcher at: {text_shortcut_path}")
    except Exception as e:
        print(f"[Shortcuts] Failed to create console shortcut: {e}")


if __name__ == "__main__":
    create_desktop_shortcuts()
