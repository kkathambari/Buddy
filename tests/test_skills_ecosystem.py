import os
import sys
import unittest
import shutil
import json

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.skill_manager import SkillManager
from core.skill_loader import SkillLoader
from capabilities.connectors.github import GitHubConnector
from capabilities.connectors.vscode import VSCodeConnector
from capabilities.connectors.communication import CommConnector
from capabilities.connectors.chrome import ChromeConnector

class TestSkillsEcosystem(unittest.TestCase):
    
    def setUp(self):
        self.test_src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src_skill")
        self.test_dest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dest_skills")
        os.makedirs(self.test_src_dir, exist_ok=True)
        os.makedirs(self.test_dest_dir, exist_ok=True)
        
        # Staging mock handler code
        self.handler_code = """
from capabilities.base import Capability
class MockHandler(Capability):
    def initialize(self):
        self.initialized = True
    def observe(self, context):
        pass
    def execute(self, intent, stats, energy):
        return "mock_executed"
    def reflect(self):
        return {"trust_increment": 1}
    def update_memory(self):
        pass
"""
        with open(os.path.join(self.test_src_dir, "handler.py"), "w") as f:
            f.write(self.handler_code)

    def tearDown(self):
        for path in [self.test_src_dir, self.test_dest_dir]:
            if os.path.exists(path):
                shutil.rmtree(path)

    def test_skill_manager_manifest_schema_validation(self):
        bad_manifest = {"id": "test_skill", "version": "1.0.0"}
        self.assertFalse(SkillManager.validate_manifest(bad_manifest))
        
        good_manifest = {
            "id": "test_skill",
            "name": "Test Skill",
            "version": "1.0.0",
            "description": "This is a valid test manifest"
        }
        self.assertTrue(SkillManager.validate_manifest(good_manifest))

    def test_skill_manager_install_uninstall(self):
        manifest = {
            "id": "my_test_skill",
            "name": "My Test Skill",
            "version": "2.0.0",
            "description": "Dynamic installation test"
        }
        with open(os.path.join(self.test_src_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)
            
        success = SkillManager.install_skill(self.test_src_dir, self.test_dest_dir)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(os.path.join(self.test_dest_dir, "my_test_skill", "handler.py")))
        
        deleted = SkillManager.uninstall_skill("my_test_skill", self.test_dest_dir)
        self.assertTrue(deleted)
        self.assertFalse(os.path.exists(os.path.join(self.test_dest_dir, "my_test_skill")))

    def test_github_connector(self):
        conn = GitHubConnector()
        prs = conn.fetch_pull_requests("kkath/Buddy")
        self.assertEqual(len(prs), 2)
        self.assertEqual(prs[0]["id"], 101)
        
        issue = conn.create_issue("kkath/Buddy", "Test Title", "Test Body")
        self.assertEqual(issue["issue_id"], 999)
        
        conn.set_credentials({"token": "xyz", "scopes": ["repo"]})
        prs_authed = conn.fetch_pull_requests("kkath/Buddy")
        self.assertEqual(len(prs_authed), 0)
        
        issue_authed = conn.create_issue("kkath/Buddy", "Test Title", "Test Body")
        self.assertEqual(issue_authed["issue_id"], 1)

    def test_vscode_connector(self):
        conn = VSCodeConnector()
        self.assertIn("planner.py", conn.get_active_editor_file())
        self.assertTrue(conn.insert_text_at_cursor("hello"))
        
        conn.set_credentials({"scopes": ["read_editor", "write_editor"]})
        self.assertIn("runtime.py", conn.get_active_editor_file())
        self.assertTrue(conn.insert_text_at_cursor("hello"))

    def test_communication_connector(self):
        conn = CommConnector()
        self.assertTrue(conn.send_email("test@example.com", "Subject", "Body"))
        self.assertTrue(conn.post_slack_message("#general", "Message"))
        
        conn.set_credentials({"scopes": ["send_mail", "slack_webhook"]})
        self.assertTrue(conn.send_email("test@example.com", "Subject", "Body"))
        self.assertTrue(conn.post_slack_message("#general", "Message"))

    def test_chrome_connector(self):
        conn = ChromeConnector()
        self.assertTrue(conn.open_url("http://google.com"))
        self.assertIn("tiangolo", conn.get_active_tab_url())
        
        conn.set_credentials({"scopes": ["browser_navigate", "read_tabs"]})
        self.assertTrue(conn.open_url("http://google.com"))
        self.assertIn("github.com", conn.get_active_tab_url())

if __name__ == "__main__":
    unittest.main()
