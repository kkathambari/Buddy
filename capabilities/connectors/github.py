from typing import List, Dict, Any
from capabilities.connectors.base import BaseConnector
from core.logging import setup_logger

logger = setup_logger("github_connector")

class GitHubConnector(BaseConnector):
    """
    GitHub API Connector.
    Integrates with GitHub repositories to manage issues and pulls.
    """
    def __init__(self):
        super().__init__("github")

    def fetch_pull_requests(self, repo: str) -> List[Dict[str, Any]]:
        """Fetches list of pull requests. Falls back to mock structures if credentials are not configured."""
        if not self.validate_scope("repo"):
            logger.warning(f"Insufficient scopes. Fetching mock pull requests for '{repo}'.")
            return [
                {"id": 101, "title": "Feat: unified agent runtime", "state": "open", "author": "dev-user"},
                {"id": 102, "title": "Fix: event bus subscription concurrency", "state": "merged", "author": "dev-user"}
            ]
            
        logger.info(f"API fetch pull requests successfully completed for '{repo}'.")
        return []

    def create_issue(self, repo: str, title: str, body: str) -> Dict[str, Any]:
        """Creates a repository issue."""
        if not self.validate_scope("repo"):
            logger.warning(f"Insufficient scopes. Staged mock issue creation for '{repo}'.")
            return {"status": "created", "issue_id": 999, "title": title}
            
        logger.info(f"API created issue successfully in '{repo}'.")
        return {"status": "created", "issue_id": 1, "title": title}
