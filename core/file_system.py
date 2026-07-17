import os
import json
from typing import List, Dict, Any
from core.logging import setup_logger
from shared.storage import safe_load, safe_save

logger = setup_logger("file_system")
INDEX_FILE = "data/file_index.json"

class SmartFileSystem:
    """
    Smart File System.
    Builds a localized file index and exposes high-speed fuzzy search APIs.
    """
    def __init__(self, index_path: str = INDEX_FILE):
        self.index_path = index_path

    def reindex_workspace(self, project_path: str) -> None:
        """Indexes files in workspace folder recursively and writes metadata index."""
        logger.info(f"Indexing files under project path: '{project_path}'")
        indexed_files = []
        try:
            if os.path.exists(project_path):
                for root, dirs, files in os.walk(project_path):
                    # Skip common build/node_modules/git directories for performance
                    dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "build", "dist", "__pycache__"]]
                    for f in files:
                        fpath = os.path.join(root, f)
                        try:
                            fsize = os.path.getsize(fpath)
                        except OSError:
                            fsize = 0
                        indexed_files.append({
                            "name": f,
                            "path": fpath,
                            "size": fsize
                        })
            # Save index cache
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            safe_save(self.index_path, {"files": indexed_files})
            logger.info(f"Reindexing complete. Cached {len(indexed_files)} files in index.")
        except Exception as e:
            logger.error(f"Failed to compile workspace file index: {e}")

    def fuzzy_search_files(self, query: str) -> List[str]:
        """Fuzzy search matching against cached file names. Returns list of absolute paths."""
        query_clean = query.lower()
        if not os.path.exists(self.index_path):
            logger.warning("No file index found. Workspace must be reindexed first.")
            return []
            
        data = safe_load(self.index_path, {"files": []})
        matches = []
        for item in data.get("files", []):
            fname = item["name"].lower()
            fpath = item["path"].lower()
            if query_clean in fname:
                matches.append(item["path"])
                
        # Limit to top 20 matches
        return matches[:20]
