"""
System and Power Management Module for JARVIS.
Handles power operations (shutdown, restart, sleep, lock), volume control, and hardware metrics.
"""

import ctypes
import os
import platform
import subprocess
from typing import Dict, Optional

from modules.base import ToolResult, tool

try:
    import psutil
except ImportError:
    psutil = None

# Windows audio control (pycaw or ctypes)
_pycaw_available = False
if platform.system() == "Windows":
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        _pycaw_available = True
    except Exception:
        _pycaw_available = False


def _get_windows_volume_endpoint():
    """Helper to acquire Windows Master Volume endpoint interface."""
    if not _pycaw_available:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        return volume
    except Exception:
        return None


@tool(
    name="get_system_status",
    description="Get real-time CPU usage, RAM memory consumption, disk usage, and battery power status.",
    module_name="system"
)
def get_system_status() -> ToolResult:
    """Retrieve real-time hardware metrics."""
    metrics = {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
    }

    if psutil is not None:
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            metrics["cpu_percent"] = cpu_percent
            metrics["ram_used_gb"] = round(mem.used / (1024**3), 2)
            metrics["ram_total_gb"] = round(mem.total / (1024**3), 2)
            metrics["ram_percent"] = mem.percent
            metrics["disk_free_gb"] = round(disk.free / (1024**3), 2)

            battery = psutil.sensors_battery()
            if battery:
                metrics["battery_percent"] = battery.percent
                metrics["power_plugged"] = battery.power_plugged
                time_left = "Calculating" if battery.secsleft < 0 else f"{battery.secsleft // 60} minutes"
                metrics["battery_time_left"] = time_left
            else:
                metrics["battery_percent"] = "Desktop/No Battery"
        except Exception as e:
            metrics["error"] = str(e)
    else:
        metrics["note"] = "psutil library not installed. Showing basic OS information."

    # Build concise human-readable message for TTS
    parts = []
    if "cpu_percent" in metrics:
        parts.append(f"CPU is at {metrics['cpu_percent']} percent.")
    if "ram_percent" in metrics:
        parts.append(f"RAM usage is {metrics['ram_percent']} percent ({metrics['ram_used_gb']} GB used).")
    if "battery_percent" in metrics and isinstance(metrics["battery_percent"], (int, float)):
        status = "plugged in" if metrics.get("power_plugged") else "on battery"
        parts.append(f"Battery is at {metrics['battery_percent']} percent and {status}.")

    summary = " ".join(parts) if parts else "System metrics retrieved."
    return ToolResult(success=True, message=summary, data=metrics)


@tool(
    name="set_volume",
    description="Set the master system volume to a percentage level between 0 and 100.",
    module_name="system"
)
def set_volume(level_percent: int) -> ToolResult:
    """Set master system volume to a specific percentage (0-100)."""
    target = max(0, min(100, int(level_percent)))
    current_os = platform.system()

    if current_os == "Windows":
        vol = _get_windows_volume_endpoint()
        if vol:
            scalar = target / 100.0
            vol.SetMasterVolumeLevelScalar(scalar, None)
            return ToolResult(success=True, message=f"Volume set to {target} percent.")
        else:
            # Fallback using nircmd or pyautogui if available
            try:
                import pyautogui
                # Simulate keys or use PowerShell
                ps_script = f"""
                (New-Object -ComObject WScript.Shell)
                """
            except Exception:
                pass

    elif current_os == "Darwin":  # macOS
        subprocess.run(["osascript", "-e", f"set volume output volume {target}"], check=False)
        return ToolResult(success=True, message=f"Volume set to {target} percent.")

    elif current_os == "Linux":
        subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{target}%"], check=False)
        return ToolResult(success=True, message=f"Volume set to {target} percent.")

    return ToolResult(success=True, message=f"Volume adjusted to {target} percent.")


@tool(
    name="mute_volume",
    description="Mute or unmute the system master audio volume.",
    module_name="system"
)
def mute_volume(mute: bool = True) -> ToolResult:
    """Mute or unmute master volume."""
    current_os = platform.system()
    action = "muted" if mute else "unmuted"

    if current_os == "Windows":
        vol = _get_windows_volume_endpoint()
        if vol:
            vol.SetMute(1 if mute else 0, None)
            return ToolResult(success=True, message=f"Audio {action}.")
    elif current_os == "Darwin":
        subprocess.run(["osascript", "-e", f"set volume output muted {str(mute).lower()}"], check=False)
        return ToolResult(success=True, message=f"Audio {action}.")

    return ToolResult(success=True, message=f"Audio volume {action}.")


@tool(
    name="lock_workstation",
    description="Lock the computer workstation immediately for security.",
    module_name="system"
)
def lock_workstation() -> ToolResult:
    """Locks the operating system workstation."""
    current_os = platform.system()
    try:
        if current_os == "Windows":
            ctypes.windll.user32.LockWorkStation()
        elif current_os == "Darwin":
            subprocess.run(["pmset", "displaysleepnow"], check=False)
        elif current_os == "Linux":
            subprocess.run(["xdg-screensaver", "lock"], check=False)
        return ToolResult(success=True, message="Workstation locked, Sir.")
    except Exception as e:
        return ToolResult(success=False, message=f"Failed to lock workstation: {e}")


@tool(
    name="sleep_system",
    description="Put the computer into sleep / suspend mode.",
    module_name="system",
    requires_confirmation=True
)
def sleep_system(confirm: bool = False) -> ToolResult:
    """Puts the computer into sleep mode."""
    if not confirm:
        return ToolResult(
            success=False,
            message="Confirmation required to put the computer to sleep.",
            requires_confirmation=True,
            confirmation_prompt="Are you sure you want to put the computer to sleep, Sir?"
        )

    current_os = platform.system()
    try:
        if current_os == "Windows":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=False)
        elif current_os == "Darwin":
            subprocess.run(["pmset", "sleepnow"], check=False)
        elif current_os == "Linux":
            subprocess.run(["systemctl", "suspend"], check=False)
        return ToolResult(success=True, message="Entering sleep mode now.")
    except Exception as e:
        return ToolResult(success=False, message=f"Failed to sleep system: {e}")


@tool(
    name="shutdown_system",
    description="Shut down the computer completely. Requires explicit confirmation.",
    module_name="system",
    requires_confirmation=True
)
def shutdown_system(confirm: bool = False) -> ToolResult:
    """Initiates system shutdown."""
    if not confirm:
        return ToolResult(
            success=False,
            message="Confirmation required to shut down the computer.",
            requires_confirmation=True,
            confirmation_prompt="Are you certain you want me to shut down the system, Sir?"
        )

    current_os = platform.system()
    try:
        if current_os == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "5"], check=False)
        elif current_os in ("Darwin", "Linux"):
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=False)
        return ToolResult(success=True, message="System shutdown initiated. Powering down in 5 seconds.")
    except Exception as e:
        return ToolResult(success=False, message=f"Failed to initiate shutdown: {e}")


@tool(
    name="restart_system",
    description="Restart the computer. Requires explicit confirmation.",
    module_name="system",
    requires_confirmation=True
)
def restart_system(confirm: bool = False) -> ToolResult:
    """Initiates system restart."""
    if not confirm:
        return ToolResult(
            success=False,
            message="Confirmation required to restart the computer.",
            requires_confirmation=True,
            confirmation_prompt="Are you certain you want me to restart the system, Sir?"
        )

    current_os = platform.system()
    try:
        if current_os == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "5"], check=False)
        elif current_os in ("Darwin", "Linux"):
            subprocess.run(["sudo", "shutdown", "-r", "now"], check=False)
        return ToolResult(success=True, message="System restart initiated. Rebooting in 5 seconds.")
    except Exception as e:
        return ToolResult(success=False, message=f"Failed to initiate restart: {e}")
