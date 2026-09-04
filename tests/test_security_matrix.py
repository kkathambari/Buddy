import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import tempfile
import asyncio

# Resolve workspace root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.main import app
from tools.terminal.tool import TerminalTool
from tools.manager import ToolManager
from tools.filesystem.tool import FilesystemTool

class TestSecurityMatrix(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides = {}
        self.client = TestClient(app)
        # Clear terminal env to ensure default fail-closed
        if "BUDDY_ENABLE_TERMINAL_TOOL" in os.environ:
            del os.environ["BUDDY_ENABLE_TERMINAL_TOOL"]

    # ---------------------------------------------------------
    # 1. Configuration Fails Closed & Auth
    # ---------------------------------------------------------
    def test_auth_missing_token(self):
        response = self.client.get("/sync/api_test_buddy")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing or invalid", response.json()["detail"])

    def test_auth_malformed_token(self):
        response = self.client.get("/sync/api_test_buddy", headers={"Authorization": "InvalidFormat token123"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing or invalid", response.json()["detail"])

    @patch('backend.routers.auth.identity_service.verify_token')
    def test_auth_invalid_token(self, mock_verify):
        mock_verify.return_value = None
        response = self.client.get("/sync/api_test_buddy", headers={"Authorization": "Bearer badtoken"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid or expired", response.json()["detail"])

    # ---------------------------------------------------------
    # 2. Ownership Regression Matrix
    # ---------------------------------------------------------
    @patch('backend.routers.auth.identity_service.verify_token')
    @patch('backend.routers.sync.user_owns_companion')
    def test_ownership_matrix(self, mock_owns, mock_verify):
        # We simulate the ownership function logic via mock side_effect
        def mock_owns_impl(user_uid, comp_id):
            return (user_uid == "userA" and comp_id == "compA") or (user_uid == "userB" and comp_id == "compB")
        
        mock_owns.side_effect = mock_owns_impl

        # User A -> Companion A -> Allowed
        mock_verify.return_value = {"uid": "userA"}
        res = self.client.get("/sync/compA", headers={"Authorization": "Bearer tokenA"})
        self.assertEqual(res.status_code, 200)

        # User B -> Companion B -> Allowed
        mock_verify.return_value = {"uid": "userB"}
        res = self.client.get("/sync/compB", headers={"Authorization": "Bearer tokenB"})
        self.assertEqual(res.status_code, 200)

        # User A -> Companion B -> Denied
        mock_verify.return_value = {"uid": "userA"}
        res = self.client.get("/sync/compB", headers={"Authorization": "Bearer tokenA"})
        self.assertEqual(res.status_code, 403)

        # User B -> Companion A -> Denied
        mock_verify.return_value = {"uid": "userB"}
        res = self.client.get("/sync/compA", headers={"Authorization": "Bearer tokenB"})
        self.assertEqual(res.status_code, 403)

    # ---------------------------------------------------------
    # 3. Command Execution Boundary & Terminal
    # ---------------------------------------------------------
    @patch('asyncio.create_subprocess_shell')
    def test_terminal_denied_default(self, mock_subprocess):
        # Test that without the env var, execution never reaches subprocess
        tool = TerminalTool()
        params = {"command": "echo malicious"}
        
        async def run_test():
            # validate should fail
            is_valid = await tool.validate(params)
            self.assertFalse(is_valid)
            
            # If we bypassed validate somehow and got to execute
            # it should technically run, but in the registry flow it won't.
            # Let's verify the full manager flow.
            
        asyncio.run(run_test())
        mock_subprocess.assert_not_called()

    @patch('asyncio.create_subprocess_shell')
    def test_terminal_denied_via_manager(self, mock_subprocess):
        manager = ToolManager()
        manager.registry.register_tool(TerminalTool())
        
        async def run_test():
            res = await manager.execute_tool("terminal", {"command": "echo malicious"})
            self.assertEqual(res.status, "validation_error")
            
        asyncio.run(run_test())
        mock_subprocess.assert_not_called()

    # ---------------------------------------------------------
    # 4. Filesystem Path Traversal (including symlinks)
    # ---------------------------------------------------------
    def test_filesystem_path_traversal(self):
        tool = FilesystemTool()
        # Mock workspace to a temp dir
        temp_ws = tempfile.mkdtemp()
        os.environ["BUDDY_WORKSPACE"] = temp_ws
        
        async def run_test():
            await tool.initialize()
            
            # 1. Parent traversal
            with self.assertRaises(ValueError):
                await tool.execute({"operation": "read", "path": "../outside.txt"})
            
            # 2. Absolute path outside
            with self.assertRaises(ValueError):
                await tool.execute({"operation": "read", "path": "/etc/passwd"})

            # 3. Sneaky traversal
            with self.assertRaises(ValueError):
                await tool.execute({"operation": "read", "path": "test/../../outside.txt"})
            
            # 4. Symlink escape (if OS supports symlinks cleanly in tests)
            try:
                outside_file = tempfile.NamedTemporaryFile(delete=False)
                outside_file.write(b"secret")
                outside_file.close()
                
                symlink_path = os.path.join(temp_ws, "link_to_outside")
                os.symlink(outside_file.name, symlink_path)
                
                with self.assertRaises(ValueError):
                    await tool.execute({"operation": "read", "path": "link_to_outside"})
            except OSError:
                # Windows might not allow unprivileged symlink creation, skip if it fails
                pass
            finally:
                if 'outside_file' in locals():
                    os.unlink(outside_file.name)
            
        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
