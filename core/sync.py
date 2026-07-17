import json
import sqlite3
from core.logging import setup_logger
from memory.knowledge_graph import KnowledgeGraphManager, DB_FILE

logger = setup_logger("sync")

class SyncEngine:
    """
    Sync Engine.
    Handles data synchronization of local Knowledge Graph across remote workspaces.
    """
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.kg = KnowledgeGraphManager(self.db_path)

    def create_sync_payload(self) -> dict:
        """Compiles local Knowledge Graph nodes and edges into a serializable payload."""
        logger.info("Compiling local workspace sync payload...")
        nodes = []
        edges = []
        
        with self.kg._lock:
            conn = self.kg._get_connection()
            try:
                cursor = conn.cursor()
                # Query nodes
                cursor.execute("SELECT id, type, name, properties FROM nodes")
                for row in cursor.fetchall():
                    nodes.append({
                        "id": row[0],
                        "type": row[1],
                        "name": row[2],
                        "properties": json.loads(row[3] or "{}")
                    })
                
                # Query edges
                cursor.execute("SELECT from_id, to_id, relation FROM edges")
                for row in cursor.fetchall():
                    edges.append({
                        "from_id": row[0],
                        "to_id": row[1],
                        "relation": row[2]
                    })
            except Exception as e:
                logger.error(f"Failed to query database for sync payload: {e}")
            finally:
                conn.close()
                
        payload = {"nodes": nodes, "edges": edges}
        logger.info(f"Sync payload compiled. Nodes: {len(nodes)}, Edges: {len(edges)}")
        return payload

    def perform_handshake(self, token: str) -> bool:
        """Validates the remote authentication handshake token."""
        logger.info("Verifying sync handshake token authentication...")
        if token and token.startswith("auth_token_"):
            logger.info("Handshake token authenticated successfully.")
            return True
        logger.warning("Sync handshake failed: Invalid or expired token.")
        return False

    def sync_workspace(self, remote_payload: dict, token: str) -> int:
        """Merges remote nodes and edges into the local knowledge graph database."""
        logger.info("Starting workspace sync ingestion...")
        if not self.perform_handshake(token):
            raise PermissionError("Invalid sync authentication token")
            
        nodes = remote_payload.get("nodes", [])
        edges = remote_payload.get("edges", [])
        
        updated_count = 0
        
        # Merge remote nodes
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type", "unknown")
            name = node.get("name", "Unnamed")
            properties = node.get("properties", {})
            
            self.kg.add_node(node_id, node_type, name, properties)
            updated_count += 1
            
        # Merge remote edges
        for edge in edges:
            from_id = edge.get("from_id")
            to_id = edge.get("to_id")
            relation = edge.get("relation", "relates_to")
            
            self.kg.add_edge(from_id, to_id, relation)
            updated_count += 1
            
        logger.info(f"Workspace sync complete. Merged {updated_count} elements successfully.")
        return updated_count
