"""
JARVIS Windows System Tray Application.
Allows running JARVIS resident in the Windows Notification Tray with quick controls.
"""

import os
import subprocess
import sys
import threading
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    from PIL import Image, ImageDraw
    _pil_available = True
except ImportError:
    _pil_available = False

try:
    import pystray
    _pystray_available = True
except ImportError:
    _pystray_available = False


def _create_tray_icon_image():
    """Generate a high-tech glowing blue icon for the system tray."""
    width = 64
    height = 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Outer glow
    draw.ellipse((4, 4, 60, 60), fill=(10, 30, 60, 200), outline=(0, 200, 255, 255), width=3)
    # Inner reactor core
    draw.ellipse((16, 16, 48, 48), fill=(0, 180, 255, 255), outline=(255, 255, 255, 255), width=2)
    # Center dot
    draw.ellipse((26, 26, 38, 38), fill=(255, 255, 255, 255))
    return image


class JarvisTrayApp:
    """System tray manager for JARVIS."""

    def __init__(self):
        self.project_dir = Path(__file__).parent.resolve()
        self.voice_process = None

    def launch_voice_mode(self, icon=None, item=None):
        """Launch voice assistant in a separate window or background process."""
        python_exe = sys.executable
        venv_python = self.project_dir / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)

        main_script = str(self.project_dir / "main.py")
        subprocess.Popen([python_exe, main_script, "--voice"], creationflags=subprocess.CREATE_NEW_CONSOLE)

    def launch_text_mode(self, icon=None, item=None):
        """Launch text interactive console."""
        python_exe = sys.executable
        venv_python = self.project_dir / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)

        main_script = str(self.project_dir / "main.py")
        subprocess.Popen([python_exe, main_script, "--text"], creationflags=subprocess.CREATE_NEW_CONSOLE)

    def open_config_folder(self, icon=None, item=None):
        """Open project configuration in Explorer."""
        os.startfile(str(self.project_dir / "config"))

    def exit_tray(self, icon, item):
        """Exit system tray."""
        icon.stop()

    def run(self):
        """Run the system tray event loop."""
        if not _pystray_available or not _pil_available:
            print("[TrayApp] pystray or Pillow not installed. Launching console directly.")
            self.launch_text_mode()
            return

        icon_image = _create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("JARVIS Voice Assistant", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🎙️ Start Voice Mode", self.launch_voice_mode, default=True),
            pystray.MenuItem("💬 Open Interactive Console", self.launch_text_mode),
            pystray.MenuItem("⚙️ Open Settings Folder", self.open_config_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit Tray", self.exit_tray),
        )

        icon = pystray.Icon("JARVIS", icon_image, "JARVIS Desktop AI Assistant", menu)
        print("[TrayApp] JARVIS System Tray running. Check your Windows taskbar notification area.")
        icon.run()


if __name__ == "__main__":
    app = JarvisTrayApp()
    app.run()
