"""
Unit tests for JARVIS Tool Modules.
"""

import unittest
from pathlib import Path
import sys

# Ensure jarvis root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from modules.base import ToolResult, registry
import modules.system as system_mod
import modules.apps_and_files as apps_mod
import modules.browser as browser_mod
import modules.media as media_mod


class TestJarvisModules(unittest.TestCase):

    def test_system_status(self):
        result = system_mod.get_system_status()
        self.assertIsInstance(result, ToolResult)
        self.assertTrue(result.success)
        self.assertIn("os", result.data)

    def test_volume_clamping(self):
        # Test volume set boundary clamping without errors
        res1 = system_mod.set_volume(level_percent=150)
        self.assertIsInstance(res1, ToolResult)
        res2 = system_mod.set_volume(level_percent=-10)
        self.assertIsInstance(res2, ToolResult)

    def test_destructive_confirmation(self):
        # Shutdown without confirmation should return requires_confirmation
        res_shutdown = system_mod.shutdown_system(confirm=False)
        self.assertTrue(res_shutdown.requires_confirmation)
        self.assertIn("Are you certain", res_shutdown.confirmation_prompt)

        # Restart without confirmation
        res_restart = system_mod.restart_system(confirm=False)
        self.assertTrue(res_restart.requires_confirmation)

    def test_open_folder(self):
        res = apps_mod.open_folder("documents")
        self.assertIsInstance(res, ToolResult)

    def test_search_web_formatting(self):
        res = browser_mod.search_web("Python documentation", engine="google")
        self.assertTrue(res.success)
        self.assertIn("Python+documentation", res.data["url"])

    def test_open_website_formatting(self):
        res = browser_mod.open_website("github.com")
        self.assertTrue(res.success)
        self.assertEqual(res.data["url"], "https://github.com")

    def test_media_control(self):
        res = media_mod.media_control("play_pause")
        self.assertIsInstance(res, ToolResult)


if __name__ == "__main__":
    unittest.main()
