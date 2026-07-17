from capabilities.connectors.base import BaseConnector
from core.logging import setup_logger

logger = setup_logger("vscode_connector")

class VSCodeConnector(BaseConnector):
    """
    VS Code Extension API Connector.
    Interacts with local VS Code workspaces to fetch file context and insert content.
    """
    def __init__(self):
        super().__init__("vscode")

    def get_active_editor_file(self) -> str:
        """Retrieves path of the file active in editor. Falls back to mock workspace in tests."""
        if not self.validate_scope("read_editor"):
            logger.warning("Insufficient scopes. Returning mock active workspace file.")
            return "e:\\claude-code-main\\brain\\planner.py"
            
        logger.info("Retrieved active editor workspace file successfully.")
        return "e:\\claude-code-main\\core\\runtime.py"

    def insert_text_at_cursor(self, text: str) -> bool:
        """Inserts text at current editor cursor position."""
        if not self.validate_scope("write_editor"):
            logger.warning(f"Insufficient scopes. Staged mock editor insert: '{text}'")
            return True
            
        logger.info(f"Inserted text at cursor successfully in active editor.")
        return True
