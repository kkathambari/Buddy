import os
import sys
import unittest
import shutil
import json
import asyncio
from unittest.mock import MagicMock, patch
from PIL import Image

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from brain.vision import DesktopVisionEngine
from core.os_control import OSController
from core.file_system import SmartFileSystem
from brain.agents.automation_agent import AutomationAgent
from brain.planner import TaskNode
from core.permissions import global_permission_manager

class TestComputerInteraction(unittest.TestCase):
    
    def setUp(self):
        self.test_index_file = "data/test_file_index.json"
        self.test_workspace = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_fs_workspace")
        os.makedirs(self.test_workspace, exist_ok=True)
        
        # Create mock file structure for testing search
        self.mock_file_1 = os.path.join(self.test_workspace, "fastapi_notes.md")
        self.mock_file_2 = os.path.join(self.test_workspace, "app_main.py")
        
        with open(self.mock_file_1, "w") as f:
            f.write("FastAPI study notes")
        with open(self.mock_file_2, "w") as f:
            f.write("print('hello')")
            
        self.fs = SmartFileSystem(self.test_index_file)
        
        # Whitelist permissions
        global_permission_manager.set_local_only_mode(True)
        global_permission_manager.grant_permission("automation_agent", "terminal")

    def tearDown(self):
        # Cleanup files
        for f in [self.test_index_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
                    
        if os.path.exists(self.test_workspace):
            shutil.rmtree(self.test_workspace)

    def test_desktop_vision_capture(self):
        img = DesktopVisionEngine.capture_screen()
        self.assertIsInstance(img, Image.Image)
        
        elements = DesktopVisionEngine.detect_ui_elements()
        self.assertEqual(len(elements), 3)
        self.assertEqual(elements[0]["label"], "start_button")
        
        title = DesktopVisionEngine.get_active_window_title()
        self.assertTrue(len(title) > 0)

    def test_os_controller_emulations(self):
        self.assertTrue(OSController.click_at(100, 200))
        self.assertTrue(OSController.drag_drop(10, 10, 100, 100))
        self.assertTrue(OSController.scroll(5))
        self.assertTrue(OSController.send_keys("hello"))

    def test_smart_file_system_indexing(self):
        self.fs.reindex_workspace(self.test_workspace)
        self.assertTrue(os.path.exists(self.test_index_file))
        
        # Verify index structure
        with open(self.test_index_file, "r") as f:
            data = json.load(f)
        self.assertTrue(len(data["files"]) >= 2)
        
        # Fuzzy search FastAPI
        matches = self.fs.fuzzy_search_files("fastapi")
        self.assertEqual(len(matches), 1)
        self.assertIn("fastapi_notes.md", matches[0])
        
        # Fuzzy search main
        matches_main = self.fs.fuzzy_search_files("main")
        self.assertEqual(len(matches_main), 1)
        self.assertIn("app_main.py", matches_main[0])

    async def _run_automation_agent_tool_integration_async(self, mock_capture, mock_send, mock_click):
        mock_capture.return_value = Image.new("RGB", (100, 100))
        agent = AutomationAgent()
        
        # 1. Click task
        node_click = TaskNode("task_0", "click start icon", "automation")
        res_click = await agent.execute_task(node_click)
        mock_click.assert_called_once_with(500, 500)
        self.assertIn("clicked coordinate location", res_click)
        
        # 2. Type task
        node_type = TaskNode("task_1", "type workspace setup", "automation")
        res_type = await agent.execute_task(node_type)
        mock_send.assert_called_once_with("Hello World")
        self.assertIn("input keys successfully", res_type)
        
        # 3. Vision capture task
        node_cap = TaskNode("task_2", "capture screen visual", "automation")
        res_cap = await agent.execute_task(node_cap)
        mock_capture.assert_called_once()
        self.assertIn("screen captured successfully", res_cap)

    @patch('core.os_control.OSController.click_at')
    @patch('core.os_control.OSController.send_keys')
    @patch('brain.vision.DesktopVisionEngine.capture_screen')
    def test_automation_agent_tool_integration(self, mock_capture, mock_send, mock_click):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._run_automation_agent_tool_integration_async(mock_capture, mock_send, mock_click))
        finally:
            loop.close()

if __name__ == "__main__":
    unittest.main()
