"""
Function-Calling Router and Dispatcher for JARVIS.
Coordinates between the LLM client, tool registry, session state, and safety confirmations.
"""

import re
from typing import Any, Dict, Optional

from core.llm import LLMClient, LLMResponse
from core.state import ConversationState
from modules.base import ToolRegistry, ToolResult, registry


class Router:
    """Dispatches user commands to LLM reasoning, executes registered tools, and enforces confirmation safety."""

    def __init__(self, llm_client: Optional[LLMClient] = None, tool_registry: ToolRegistry = registry):
        self.registry = tool_registry
        self.llm = llm_client or LLMClient(tool_registry=self.registry)
        self.state = ConversationState()

    def process_input(self, user_text: str) -> str:
        """Process incoming user utterance and return the assistant's spoken response."""
        clean_text = user_text.strip()
        if not clean_text:
            return ""

        # 1. Check for Pending Confirmation
        pending = self.state.check_pending_action()
        if pending:
            return self._handle_pending_confirmation(clean_text, pending)

        # 2. Check for Conversational History Clear
        if clean_text.lower() in ("clear memory", "forget conversation", "reset context"):
            self.state.clear_history()
            return "Conversation history cleared, Sir."

        # 3. Add to Conversation State History
        self.state.add_message("user", clean_text)

        # 4. Generate LLM / Rule Engine Response
        llm_response: LLMResponse = self.llm.generate_response(clean_text, self.state.history)

        # 5. Dispatch Tool Calls if present
        if llm_response.is_tool_call and llm_response.tool_calls:
            response_text = self._execute_tool_calls(llm_response.tool_calls)
        else:
            response_text = llm_response.text or "Command understood, Sir."

        # 6. Save Assistant Response to History
        self.state.add_message("assistant", response_text)
        return response_text

    def _execute_tool_calls(self, tool_calls: list) -> str:
        """Execute one or more tool calls returned by the router."""
        responses = []
        for call in tool_calls:
            tool_name = call.get("name")
            args = call.get("arguments", {})

            tool_def = self.registry.get(tool_name)
            if not tool_def:
                responses.append(f"Tool '{tool_name}' is not registered.")
                continue

            # Check if this tool requires explicit confirmation
            if tool_def.requires_confirmation and not args.get("confirm", False):
                prompt = f"Executing '{tool_name}' requires confirmation. Are you certain you want to proceed, Sir?"
                self.state.set_pending_action(
                    tool_name=tool_name,
                    tool_func=tool_def.func,
                    kwargs={**args, "confirm": True},
                    prompt=prompt,
                )
                return prompt

            # Execute tool safely
            try:
                result: ToolResult = tool_def.func(**args)
                if isinstance(result, ToolResult):
                    if result.requires_confirmation and not args.get("confirm", False):
                        self.state.set_pending_action(
                            tool_name=tool_name,
                            tool_func=tool_def.func,
                            kwargs={**args, "confirm": True},
                            prompt=result.confirmation_prompt or result.message,
                        )
                        return result.confirmation_prompt or result.message
                    responses.append(result.message)
                else:
                    responses.append(str(result))
            except Exception as e:
                responses.append(f"An error occurred while executing {tool_name}: {e}")

        return " ".join(responses)

    def _handle_pending_confirmation(self, user_text: str, pending) -> str:
        """Evaluate affirmative or negative response for pending destructive actions."""
        text_lower = user_text.lower().strip()

        # Affirmative patterns
        if re.search(r"\b(yes|yeah|yep|proceed|confirm|do it|sure|affirmative|go ahead)\b", text_lower):
            self.state.clear_pending_action()
            try:
                result: ToolResult = pending.tool_func(**pending.kwargs)
                return f"Confirmed. {result.message if isinstance(result, ToolResult) else str(result)}"
            except Exception as e:
                return f"Failed to execute confirmed action: {e}"

        # Negative / Cancellation patterns
        elif re.search(r"\b(no|cancel|stop|abort|negative|don't|do not|nevermind)\b", text_lower):
            self.state.clear_pending_action()
            return "Action cancelled, Sir."

        else:
            return f"Action pending: {pending.prompt} Please reply with 'yes' to proceed or 'cancel' to abort."
