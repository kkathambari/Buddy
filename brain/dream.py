import os
import re
import sqlite3
from core.logging import setup_logger
from memory.knowledge_graph import KnowledgeGraphManager, DB_FILE
from memory.working_memory import get_recent_context

logger = setup_logger("dream")

class DreamEngine:
    """
    Dream Engine.
    Executes background memory consolidation and SQLite space reclaiming.
    """
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.kg = KnowledgeGraphManager(self.db_path)

    def consolidate_memories(self) -> int:
        """Consolidates short-term conversation statements into long-term graph nodes."""
        logger.info("Dream Engine consolidating short-term memories...")
        chat_context = get_recent_context()
        if not chat_context:
            logger.info("Working memory empty, no records to consolidate.")
            return 0
            
        # Regex to scan for declarations (e.g. "Alice is a student")
        matches = re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\s+is\s+(?:a|an|the)\s+([a-zA-Z0-9_\s]+)\b', chat_context)
        consolidated_count = 0
        
        for name, role in matches:
            node_id = f"user_{name.lower()}"
            # Check if node already exists before adding
            node = self.kg.get_node(node_id)
            if not node:
                self.kg.add_node(node_id, "person", name, {"role": role.strip()})
                logger.info(f"Consolidated memory: Created person node '{name}' with role '{role.strip()}'")
                consolidated_count += 1
                
        return consolidated_count

    def optimize_database(self) -> bool:
        """Runs SQLite vacuum queries to compress space and releases file locks."""
        logger.info("Dream Engine executing database optimizations...")
        if not os.path.exists(self.db_path):
            logger.warning("Database file not found, skipping optimization.")
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            # Vacuum command to rebuild database file and reclaim free pages
            conn.execute("VACUUM")
            conn.close()
            logger.info("SQLite VACUUM optimization executed successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to optimize SQLite database: {e}")
            return False

    def start_dream_cycle(self) -> str:
        """Launches both memory sweeps and storage vacuuming."""
        logger.info("Starting DevBuddy Dream Cycle...")
        m_count = self.consolidate_memories()
        db_opt = self.optimize_database()
        
        status = "optimized" if db_opt else "unoptimized"
        result = f"Dream cycle complete. Consolidated {m_count} memories. Database {status}."
        logger.info(result)
        return result
