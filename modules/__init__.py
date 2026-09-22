"""
Modules package initialization.
Importing modules automatically registers all tools with the ToolRegistry.
"""

from modules.base import ToolResult, ToolDefinition, ToolRegistry, registry, tool
import modules.system
import modules.apps_and_files
import modules.browser
import modules.media
import modules.chat

__all__ = [
    "ToolResult",
    "ToolDefinition",
    "ToolRegistry",
    "registry",
    "tool",
]
