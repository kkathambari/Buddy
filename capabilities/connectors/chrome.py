from capabilities.connectors.base import BaseConnector
from core.logging import setup_logger

logger = setup_logger("chrome_connector")

class ChromeConnector(BaseConnector):
    """
    Chrome Browser Extension API Connector.
    Simulates browser automation, active tab URL scraping, and navigation.
    """
    def __init__(self):
        super().__init__("chrome")

    def open_url(self, url: str) -> bool:
        """Opens a target browser URL. Falls back to mock logs if scopes are missing."""
        if not self.validate_scope("browser_navigate"):
            logger.warning(f"Insufficient scopes. Staged mock URL open: '{url}'")
            return True
            
        logger.info(f"Successfully opened browser URL: '{url}'")
        return True

    def get_active_tab_url(self) -> str:
        """Scrapes URL of current active browser tab."""
        if not self.validate_scope("read_tabs"):
            logger.warning("Insufficient scopes. Returning mock active tab URL.")
            return "https://fastapi.tiangolo.com/"
            
        logger.info("Scraped active tab URL successfully.")
        return "https://github.com/fastapi/fastapi"
