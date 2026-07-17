import os
import sys
import unittest

# Add root folder to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.sync import SyncEngine
from memory.knowledge_graph import KnowledgeGraphManager

class TestRemoteSync(unittest.TestCase):
    
    def setUp(self):
        self.test_db_file = "data/test_knowledge_graph_sync.db"
        if os.path.exists(self.test_db_file):
            try:
                os.remove(self.test_db_file)
            except OSError:
                pass
                
        self.engine = SyncEngine(db_path=self.test_db_file)

    def tearDown(self):
        if os.path.exists(self.test_db_file):
            try:
                os.remove(self.test_db_file)
            except OSError:
                pass

    def test_create_sync_payload(self):
        # 1. Add mock nodes & edges to test DB
        self.engine.kg.add_node("node_1", "project", "Buddy Project", {"version": "2.0"})
        self.engine.kg.add_node("node_2", "skill", "Python Coding", {})
        self.engine.kg.add_edge("node_1", "node_2", "uses_skill")
        
        # 2. Compile payload
        payload = self.engine.create_sync_payload()
        self.assertIn("nodes", payload)
        self.assertIn("edges", payload)
        
        # 3. Check values
        nodes_list = payload["nodes"]
        self.assertEqual(len(nodes_list), 2)
        n1 = next(n for n in nodes_list if n["id"] == "node_1")
        self.assertEqual(n1["name"], "Buddy Project")
        self.assertEqual(n1["properties"].get("version"), "2.0")
        
        edges_list = payload["edges"]
        self.assertEqual(len(edges_list), 1)
        self.assertEqual(edges_list[0]["from_id"], "node_1")
        self.assertEqual(edges_list[0]["to_id"], "node_2")
        self.assertEqual(edges_list[0]["relation"], "uses_skill")

    def test_handshake_authentication(self):
        # Valid token
        self.assertTrue(self.engine.perform_handshake("auth_token_secret_123"))
        
        # Invalid tokens
        self.assertFalse(self.engine.perform_handshake("bad_token_456"))
        self.assertFalse(self.engine.perform_handshake(""))
        self.assertFalse(self.engine.perform_handshake(None))

    def test_sync_workspace_ingestion_success(self):
        # Build mock remote payload
        remote_payload = {
            "nodes": [
                {"id": "remote_n1", "type": "user", "name": "Alice", "properties": {"level": 5}},
                {"id": "remote_n2", "type": "goal", "name": "Deploy API", "properties": {}}
            ],
            "edges": [
                {"from_id": "remote_n1", "to_id": "remote_n2", "relation": "assignee"}
            ]
        }
        
        # Ingest remote payload with valid token
        token = "auth_token_secure_999"
        elements_count = self.engine.sync_workspace(remote_payload, token)
        self.assertEqual(elements_count, 3)
        
        # Verify local database nodes exist
        alice_node = self.engine.kg.get_node("remote_n1")
        self.assertIsNotNone(alice_node)
        self.assertEqual(alice_node["name"], "Alice")
        self.assertEqual(alice_node["properties"].get("level"), 5)

    def test_sync_workspace_ingestion_denied(self):
        remote_payload = {"nodes": [], "edges": []}
        
        # Ingest remote payload with invalid token
        with self.assertRaises(PermissionError):
            self.engine.sync_workspace(remote_payload, "invalid_handshake")

if __name__ == "__main__":
    unittest.main()
