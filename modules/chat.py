"""
Conversational Chat and General Knowledge Module for JARVIS.
Handles persona framing, casual dialogue, summarization, and direct answers.
"""

from typing import Dict, Optional
from modules.base import ToolResult, tool


SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System), an exceptionally capable, articulate, polite, and sophisticated AI assistant.
Your demeanor is inspired by the iconic British AI butler: refined, efficient, with subtle dry wit, absolute composure, and unwavering loyalty.

Guidelines:
1. Address the user as 'Sir' or 'Ma'am' naturally when suitable.
2. Keep spoken answers concise, elegant, and directly to the point. Avoid bloated bullet points unless requested.
3. If an action or command was completed, provide a brief, professional acknowledgment.
4. When answering factual queries, be accurate, clear, and articulate.
5. If you do not know something or cannot perform an action, politely state so and suggest an alternative.
"""


@tool(
    name="general_chat",
    description="Respond to general conversation, greetings, questions, explanations, and casual dialogue.",
    module_name="chat"
)
def general_chat(query: str) -> ToolResult:
    """Fallback handler for open-ended conversation."""
    return ToolResult(
        success=True,
        message=f"I hear you: {query}",
        data={"query": query}
    )
