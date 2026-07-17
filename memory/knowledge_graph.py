import os
import json
import sqlite3
import threading
from typing import Dict, Any, List, Optional
from core.logging import setup_logger

logger = setup_logger("knowledge_graph")
DB_FILE = "data/knowledge_graph.db"

class KnowledgeGraphManager:
    """
    SQLite-backed local Knowledge Graph.
    Maintains relationships (edges) between user nodes, projects, files, and timeline achievements.
    """
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def initialize_db(self) -> None:
        """Creates nodes and edges tables if they do not exist."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS nodes (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        properties TEXT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS edges (
                        from_id TEXT NOT NULL,
                        to_id TEXT NOT NULL,
                        relation TEXT NOT NULL,
                        PRIMARY KEY (from_id, to_id, relation),
                        FOREIGN KEY (from_id) REFERENCES nodes (id) ON DELETE CASCADE,
                        FOREIGN KEY (to_id) REFERENCES nodes (id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
                logger.info("Knowledge Graph SQLite database initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Knowledge Graph DB: {e}")
            finally:
                conn.close()

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single node by ID. Returns None if it does not exist."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, type, name, properties FROM nodes WHERE id = ?", (node_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "type": row[1],
                        "name": row[2],
                        "properties": json.loads(row[3] or "{}")
                    }
            except Exception as e:
                logger.error(f"Failed to query node {node_id}: {e}")
            finally:
                conn.close()
        return None

    def add_node(self, node_id: str, node_type: str, name: str, properties: Dict[str, Any] = None) -> None:
        """Adds or updates a node in the graph."""
        props_json = json.dumps(properties or {})
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO nodes (id, type, name, properties)
                    VALUES (?, ?, ?, ?)
                """, (node_id, node_type, name, props_json))
                conn.commit()
                logger.debug(f"Added node '{node_id}' ({node_type}) to Knowledge Graph.")
            except Exception as e:
                logger.error(f"Failed to add node {node_id}: {e}")
            finally:
                conn.close()

    def add_edge(self, from_id: str, to_id: str, relation: str) -> None:
        """Adds a directed relationship edge between two existing nodes."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO edges (from_id, to_id, relation)
                    VALUES (?, ?, ?)
                """, (from_id, to_id, relation))
                conn.commit()
                logger.debug(f"Added edge '{from_id}' --({relation})--> '{to_id}' to Knowledge Graph.")
            except Exception as e:
                logger.error(f"Failed to add edge from {from_id} to {to_id} ({relation}): {e}")
            finally:
                conn.close()

    def get_related_nodes(self, node_id: str, relation_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves all nodes directly connected to the given node ID."""
        with self._lock:
            conn = self._get_connection()
            related = []
            try:
                cursor = conn.cursor()
                if relation_filter:
                    cursor.execute("""
                        SELECT n.id, n.type, n.name, n.properties, e.relation
                        FROM edges e
                        JOIN nodes n ON e.to_id = n.id
                        WHERE e.from_id = ? AND e.relation = ?
                    """, (node_id, relation_filter))
                else:
                    cursor.execute("""
                        SELECT n.id, n.type, n.name, n.properties, e.relation
                        FROM edges e
                        JOIN nodes n ON e.to_id = n.id
                        WHERE e.from_id = ?
                    """, (node_id,))
                
                for row in cursor.fetchall():
                    related.append({
                        "id": row[0],
                        "type": row[1],
                        "name": row[2],
                        "properties": json.loads(row[3] or "{}"),
                        "relation": row[4]
                    })
            except Exception as e:
                logger.error(f"Failed to query related nodes for {node_id}: {e}")
            finally:
                conn.close()
            return related

    def delete_node(self, node_id: str) -> None:
        """Deletes a node and any of its associated edges (via cascades)."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM edges WHERE from_id = ? OR to_id = ?", (node_id, node_id))
                cursor.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
                conn.commit()
                logger.info(f"Deleted node '{node_id}' and all connecting edges.")
            except Exception as e:
                logger.error(f"Failed to delete node {node_id}: {e}")
            finally:
                conn.close()

    def reset_graph(self) -> None:
        """Clears all nodes and edges from the database."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM edges")
                cursor.execute("DELETE FROM nodes")
                conn.commit()
                logger.info("Cleared all elements in Knowledge Graph database.")
            except Exception as e:
                logger.error(f"Failed to clear Knowledge Graph database: {e}")
            finally:
                conn.close()

# Global singleton knowledge graph manager
global_knowledge_graph = KnowledgeGraphManager()
