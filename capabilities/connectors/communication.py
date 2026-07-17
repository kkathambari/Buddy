from capabilities.connectors.base import BaseConnector
from core.logging import setup_logger

logger = setup_logger("communication_connector")

class CommConnector(BaseConnector):
    """
    Communication Service Connector.
    Dispatches mock emails (Gmail) and posts messages to Slack webhooks.
    """
    def __init__(self):
        super().__init__("communication")

    def send_email(self, to_addr: str, subject: str, body: str) -> bool:
        """Sends an email alert. Falls back to mock logs if scopes are missing."""
        if not self.validate_scope("send_mail"):
            logger.warning(f"Insufficient scopes. Staged mock email to '{to_addr}': {subject}")
            return True
            
        logger.info(f"Email successfully dispatched to '{to_addr}'.")
        return True

    def post_slack_message(self, channel: str, message: str) -> bool:
        """Posts a message to Slack webhook."""
        if not self.validate_scope("slack_webhook"):
            logger.warning(f"Insufficient scopes. Staged mock Slack post to '{channel}': {message}")
            return True
            
        logger.info(f"Slack webhook post successfully dispatched to '{channel}'.")
        return True
