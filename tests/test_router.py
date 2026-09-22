"""
Unit tests for JARVIS Tool Registry, Schemas, State, and Router.
"""

import unittest
from pathlib import Path
import sys

# Ensure jarvis root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from modules.base import ToolRegistry, ToolResult, tool
from core.state import ConversationState
from core.router import Router
from core.llm import RuleBasedEngine


class TestJarvisRouter(unittest.TestCase):

    def setUp(self):
        self.router = Router()
        self.rule_engine = RuleBasedEngine()

    def test_tool_registration_and_schemas(self):
        # Define a sample test function
        @tool(name="sample_test_tool", description="A sample testing tool")
        def sample_test_tool(param1: str, param2: int = 10) -> ToolResult:
            return ToolResult(success=True, message=f"Got {param1} and {param2}")

        t_def = self.router.registry.get("sample_test_tool")
        self.assertIsNotNone(t_def)
        self.assertEqual(t_def.name, "sample_test_tool")

        # Verify JSON schema structure
        schema = t_def.parameters_schema
        self.assertEqual(schema["type"], "object")
        self.assertIn("param1", schema["properties"])
        self.assertIn("param2", schema["properties"])
        self.assertEqual(schema["properties"]["param1"]["type"], "string")
        self.assertEqual(schema["properties"]["param2"]["type"], "integer")
        self.assertIn("param1", schema["required"])
        self.assertNotIn("param2", schema["required"])

    def test_rule_engine_matching(self):
        res1 = self.rule_engine.match("What is the battery and cpu status?")
        self.assertIsNotNone(res1)
        self.assertTrue(res1.is_tool_call)
        self.assertEqual(res1.tool_calls[0]["name"], "get_system_status")

        res2 = self.rule_engine.match("Lock computer")
        self.assertIsNotNone(res2)
        self.assertEqual(res2.tool_calls[0]["name"], "lock_workstation")

        res3 = self.rule_engine.match("Set volume to 75%")
        self.assertIsNotNone(res3)
        self.assertEqual(res3.tool_calls[0]["name"], "set_volume")
        self.assertEqual(res3.tool_calls[0]["arguments"]["level_percent"], 75)

    def test_confirmation_lifecycle(self):
        state = ConversationState()
        # Set a dummy pending action
        def dummy_action(confirm=False):
            return ToolResult(success=True, message="Action Executed!")

        state.set_pending_action(
            tool_name="dummy_action",
            tool_func=dummy_action,
            kwargs={"confirm": True},
            prompt="Are you sure?"
        )

        pending = state.check_pending_action()
        self.assertIsNotNone(pending)
        self.assertEqual(pending.tool_name, "dummy_action")

        # Test affirmative execution
        self.router.state = state
        confirm_resp = self.router.process_input("yes, proceed")
        self.assertIn("Confirmed", confirm_resp)
        self.assertIsNone(self.router.state.check_pending_action())

    def test_history_memory(self):
        state = ConversationState(max_history_turns=3)
        for i in range(10):
            state.add_message("user", f"query {i}")
            state.add_message("assistant", f"reply {i}")

        # Should be capped to 3*2 = 6 messages
        self.assertEqual(len(state.history), 6)
        self.assertEqual(state.history[-1]["content"], "reply 9")


if __name__ == "__main__":
    unittest.main()
