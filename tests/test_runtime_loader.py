import os
import sys
import unittest
import shutil
import json
import time
from unittest.mock import MagicMock

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.runtime import AgentRuntime, TaskScheduler
from core.permissions import PermissionManager
from core.skill_loader import SkillLoader
from capabilities.base import Capability

class TestRuntimeLoader(unittest.TestCase):
    
    def setUp(self):
        # Create temp folder for test skills
        self.test_skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_skills")
        os.makedirs(self.test_skills_dir, exist_ok=True)
        
        # Temp state file configuration overrides
        self.state_file = "data/runtime_state.json"
        self.permissions_file = "data/permissions.json"
        for fpath in [self.state_file, self.permissions_file]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def tearDown(self):
        # Clean up temporary test skills folder
        if os.path.exists(self.test_skills_dir):
            shutil.rmtree(self.test_skills_dir)
            
        for fpath in [self.state_file, self.permissions_file]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def test_scheduler_once_and_recurring(self):
        runtime = AgentRuntime()
        try:
            scheduler = runtime.scheduler
            called_once = []
            called_recurring = []
            
            def run_once():
                called_once.append(True)
                
            def run_rec():
                called_recurring.append(True)
                
            # Schedule one-shot delay of 0.1s
            scheduler.schedule_once("test_once", 0.1, run_once)
            # Schedule recurring every 0.1s
            scheduler.schedule_recurring("test_rec", 0.1, run_rec)
            
            # Poll up to 3.0 seconds to wait for execution to complete under load
            for _ in range(30):
                if len(called_once) >= 1 and len(called_recurring) >= 1:
                    break
                time.sleep(0.1)
            
            self.assertTrue(len(called_once) >= 1)
            self.assertTrue(len(called_recurring) >= 1)
            
            # Cancel task
            scheduler.cancel_task("test_rec")
            rec_count = len(called_recurring)
            
            time.sleep(0.25)
            self.assertEqual(len(called_recurring), rec_count)
        finally:
            runtime.shutdown()

    def test_permission_manager(self):
        pm = PermissionManager()
        pm.permissions_cache.clear()
        
        # Test default prompt callback intercept (auto-deny)
        pm.set_prompt_callback(None)
        allowed = pm.verify_skill_permissions("test_skill", ["terminal"])
        self.assertFalse(allowed)
        
        # Test custom prompt callback (allow)
        pm.set_prompt_callback(lambda skill_id, perm: True)
        # Reset cache for testing
        pm.permissions_cache.clear()
        allowed = pm.verify_skill_permissions("test_skill", ["terminal"])
        self.assertTrue(allowed)
        self.assertEqual(pm.permissions_cache["test_skill"]["terminal"], "allow")
        
        # Test cache hit (no prompt callback invocation)
        pm.set_prompt_callback(MagicMock(side_effect=Exception("Should not prompt")))
        allowed_cache = pm.verify_skill_permissions("test_skill", ["terminal"])
        self.assertTrue(allowed_cache)
        
        # Local-only toggle
        pm.set_local_only_mode(True)
        self.assertTrue(pm.local_only_mode)

    def test_skill_loader_dynamic_import(self):
        # Setup temporary skill directories
        skill_id = "mock_skill"
        skill_folder = os.path.join(self.test_skills_dir, skill_id)
        os.makedirs(skill_folder, exist_ok=True)
        
        manifest = {
            "id": skill_id,
            "name": "Mock Skill",
            "version": "1.0.0",
            "description": "Mock Skill for Testing"
        }
        with open(os.path.join(skill_folder, "manifest.json"), "w") as f:
            json.dump(manifest, f)
            
        with open(os.path.join(skill_folder, "permissions.json"), "w") as f:
            json.dump({"permissions": ["filesystem"]}, f)
            
        handler_code = """
from capabilities.base import Capability
class MockHandler(Capability):
    def initialize(self):
        self.initialized = True
    def observe(self, context):
        pass
    def execute(self, intent, stats, energy):
        return "mock_execute"
    def reflect(self):
        return {"trust_increment": 5}
    def update_memory(self):
        pass
    def shutdown(self):
        pass
"""
        with open(os.path.join(skill_folder, "handler.py"), "w") as f:
            f.write(handler_code)
            
        # Register a mock prompt callback in the global permission manager
        from core.permissions import global_permission_manager
        global_permission_manager.set_prompt_callback(lambda sid, perm: True)
        
        loader = SkillLoader(self.test_skills_dir)
        skills = loader.discover_and_load_skills()
        
        self.assertIn(skill_id, skills)
        self.assertEqual(skills[skill_id]["manifest"]["name"], "Mock Skill")
        self.assertEqual(skills[skill_id]["permissions"], ["filesystem"])
        self.assertEqual(skills[skill_id]["instance"].execute({}, {}, 100), "mock_execute")
        
        # Test disable/enable/unload
        loader.disable_skill(skill_id)
        self.assertEqual(loader.loaded_skills[skill_id]["status"], "disabled")
        
        loader.enable_skill(skill_id)
        self.assertEqual(loader.loaded_skills[skill_id]["status"], "enabled")
        
        loader.unload_skill(skill_id)
        self.assertNotIn(skill_id, loader.loaded_skills)

if __name__ == "__main__":
    unittest.main()
