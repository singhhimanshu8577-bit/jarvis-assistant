"""
Session State, Context Memory, and Confirmation Management for JARVIS.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PendingAction:
    """Represents a dangerous or destructive action awaiting user confirmation."""
    tool_name: str
    tool_func: Callable
    kwargs: Dict[str, Any]
    prompt: str
    created_at: float = field(default_factory=time.time)
    expires_after_seconds: float = 30.0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.expires_after_seconds


class ConversationState:
    """Tracks conversation history and pending confirmations across turns."""

    def __init__(self, max_history_turns: int = 10):
        self.max_history_turns = max_history_turns
        self.history: List[Dict[str, str]] = []
        self.pending_action: Optional[PendingAction] = None
        self.is_active: bool = False
        self.last_interaction_time: float = 0.0

    def add_message(self, role: str, content: str):
        """Add a message to conversational history (user or assistant)."""
        self.history.append({"role": role, "content": content})
        # Keep within sliding window (x2 for user + assistant pairs)
        if len(self.history) > self.max_history_turns * 2:
            self.history = self.history[-self.max_history_turns * 2:]
        self.last_interaction_time = time.time()

    def set_pending_action(self, tool_name: str, tool_func: Callable, kwargs: Dict[str, Any], prompt: str):
        """Register an action awaiting voice/text confirmation."""
        self.pending_action = PendingAction(
            tool_name=tool_name,
            tool_func=tool_func,
            kwargs=kwargs,
            prompt=prompt,
        )

    def clear_pending_action(self):
        """Clear any waiting pending action."""
        self.pending_action = None

    def check_pending_action(self) -> Optional[PendingAction]:
        """Get pending action if not expired."""
        if self.pending_action:
            if self.pending_action.is_expired:
                self.pending_action = None
                return None
            return self.pending_action
        return None

    def clear_history(self):
        """Clear all previous conversation history."""
        self.history.clear()
