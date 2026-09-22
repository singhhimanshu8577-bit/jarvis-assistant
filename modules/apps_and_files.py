"""
Application and File Management Module for JARVIS.
Handles application discovery & launching, and fuzzy searching & opening user files/directories.
"""

import difflib
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from modules.base import ToolResult, tool

# Common application aliases and direct execution commands
COMMON_APP_COMMANDS: Dict[str, List[str]] = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "chrome": ["chrome.exe", "google-chrome", "google chrome"],
    "google chrome": ["chrome.exe", "google-chrome"],
    "firefox": ["firefox.exe", "firefox"],
    "edge": ["msedge.exe", "microsoft-edge"],
    "vscode": ["code.cmd", "code.exe", "code"],
    "vs code": ["code.cmd", "code.exe", "code"],
    "visual studio code": ["code.cmd", "code.exe", "code"],
    "spotify": ["spotify.exe", "spotify"],
    "discord": ["discord.exe", "discord"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "files": ["explorer.exe"],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "command prompt": ["cmd.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "powerpoint": ["powerpnt.exe"],
    "task manager": ["taskmgr.exe"],
    "settings": ["ms-settings:"],
}


def _get_user_search_roots() -> List[Path]:
    """Retrieve standard user personal directories to index/search."""
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Videos",
        home / "Music",
    ]
    return [p for p in candidates if p.exists()]


def _find_windows_shortcuts() -> Dict[str, str]:
    """Index .lnk files from Start Menu and ProgramData."""
    shortcuts = {}
    if platform.system() != "Windows":
        return shortcuts

    search_dirs = [
        Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]

    for root_dir in search_dirs:
        if not root_dir.exists():
            continue
        try:
            for p in root_dir.rglob("*.lnk"):
                clean_name = p.stem.lower()
                shortcuts[clean_name] = str(p)
        except Exception:
            pass

    return shortcuts


@tool(
    name="launch_application",
    description="Launch an installed desktop application by name (e.g., 'Notepad', 'Chrome', 'VS Code', 'Spotify', 'Calculator').",
    module_name="apps_and_files"
)
def launch_application(app_name: str) -> ToolResult:
    """Launch a desktop application by name."""
    clean_query = app_name.strip().lower()
    current_os = platform.system()

    # 1. Direct match in common command mapping
    if clean_query in COMMON_APP_COMMANDS:
        for cmd in COMMON_APP_COMMANDS[clean_query]:
            try:
                if current_os == "Windows":
                    if cmd.endswith(":"):  # URI protocol like ms-settings:
                        os.startfile(cmd)
                        return ToolResult(success=True, message=f"Opening {app_name}, Sir.")
                    else:
                        subprocess.Popen(cmd, shell=True)
                        return ToolResult(success=True, message=f"Launched {app_name}, Sir.")
                elif current_os == "Darwin":
                    subprocess.Popen(["open", "-a", cmd])
                    return ToolResult(success=True, message=f"Launched {app_name}, Sir.")
                elif current_os == "Linux":
                    subprocess.Popen([cmd])
                    return ToolResult(success=True, message=f"Launched {app_name}, Sir.")
            except Exception:
                continue

    # 2. Windows Start Menu Shortcut matching
    if current_os == "Windows":
        shortcuts = _find_windows_shortcuts()
        # Direct exact or substring match
        matched_shortcut = None
        for name, path in shortcuts.items():
            if clean_query == name or clean_query in name or name in clean_query:
                matched_shortcut = path
                break

        # Fuzzy match if no substring match
        if not matched_shortcut and shortcuts:
            matches = difflib.get_close_matches(clean_query, list(shortcuts.keys()), n=1, cutoff=0.5)
            if matches:
                matched_shortcut = shortcuts[matches[0]]

        if matched_shortcut:
            try:
                os.startfile(matched_shortcut)
                return ToolResult(success=True, message=f"Launching {Path(matched_shortcut).stem}, Sir.")
            except Exception as e:
                return ToolResult(success=False, message=f"Failed to open shortcut: {e}")

        # 3. Attempt direct Windows start
        try:
            os.startfile(clean_query)
            return ToolResult(success=True, message=f"Opening {app_name}, Sir.")
        except Exception:
            pass

    # 4. Fallback execution via shell
    try:
        if current_os == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
            return ToolResult(success=True, message=f"Opening {app_name}, Sir.")
        elif current_os == "Linux":
            subprocess.Popen([app_name])
            return ToolResult(success=True, message=f"Opening {app_name}, Sir.")
    except Exception:
        pass

    return ToolResult(
        success=False,
        message=f"I could not locate an installed application matching '{app_name}'. Please verify the application name."
    )


@tool(
    name="search_and_open_file",
    description="Search for a file or document across user folders (Desktop, Documents, Downloads, etc.) and open it.",
    module_name="apps_and_files"
)
def search_and_open_file(file_name: str, directory_hint: Optional[str] = None) -> ToolResult:
    """Search for a file matching file_name and open it with the default OS handler."""
    query = file_name.strip().lower()
    roots = _get_user_search_roots()

    if directory_hint:
        hint_lower = directory_hint.strip().lower()
        matching_roots = [r for r in roots if hint_lower in r.name.lower()]
        if matching_roots:
            roots = matching_roots

    found_files: List[Path] = []
    max_depth = 3

    for root in roots:
        try:
            for current_root, dirs, files in os.walk(root):
                # Calculate relative depth
                rel_depth = len(Path(current_root).relative_to(root).parts)
                if rel_depth > max_depth:
                    dirs.clear()
                    continue

                # Don't recurse into hidden or system folders
                dirs[:] = [d for d in dirs if not d.startswith(".") and not d.startswith("$")]

                for f in files:
                    if f.startswith("."):
                        continue
                    if query in f.lower():
                        found_files.append(Path(current_root) / f)
                        if len(found_files) >= 5:
                            break
                if len(found_files) >= 5:
                    break
        except Exception:
            continue

    if not found_files:
        return ToolResult(
            success=False,
            message=f"I could not find any files matching '{file_name}' in your user directories."
        )

    # Open the first best match
    target_file = found_files[0]
    try:
        current_os = platform.system()
        if current_os == "Windows":
            os.startfile(str(target_file))
        elif current_os == "Darwin":
            subprocess.run(["open", str(target_file)], check=False)
        else:
            subprocess.run(["xdg-open", str(target_file)], check=False)

        return ToolResult(
            success=True,
            message=f"Opened {target_file.name} from {target_file.parent.name}, Sir.",
            data={"path": str(target_file), "matches_found": len(found_files)}
        )
    except Exception as e:
        return ToolResult(success=False, message=f"Found {target_file.name}, but failed to open it: {e}")


@tool(
    name="open_folder",
    description="Open a specific user folder such as Downloads, Documents, Desktop, Pictures, or custom path.",
    module_name="apps_and_files"
)
def open_folder(folder_name: str) -> ToolResult:
    """Open a folder in the file explorer."""
    clean = folder_name.strip().lower()
    home = Path.home()
    mapping = {
        "desktop": home / "Desktop",
        "downloads": home / "Downloads",
        "documents": home / "Documents",
        "my documents": home / "Documents",
        "pictures": home / "Pictures",
        "photos": home / "Pictures",
        "videos": home / "Videos",
        "music": home / "Music",
        "home": home,
        "root": Path("C:\\" if platform.system() == "Windows" else "/"),
    }

    target_path = mapping.get(clean)
    if not target_path or not target_path.exists():
        # Check if it's an absolute path
        candidate = Path(folder_name)
        if candidate.exists() and candidate.is_dir():
            target_path = candidate
        else:
            return ToolResult(success=False, message=f"Folder '{folder_name}' could not be found.")

    try:
        current_os = platform.system()
        if current_os == "Windows":
            os.startfile(str(target_path))
        elif current_os == "Darwin":
            subprocess.run(["open", str(target_path)], check=False)
        else:
            subprocess.run(["xdg-open", str(target_path)], check=False)

        return ToolResult(success=True, message=f"Opening {target_path.name} folder, Sir.")
    except Exception as e:
        return ToolResult(success=False, message=f"Failed to open folder: {e}")
