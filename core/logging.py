import logging
import os
import sys
import json
from datetime import datetime

LOGS_DIR = "logs"
LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"

class JsonFormatter(logging.Formatter):
    """Formats log records as structured JSON objects."""
    def format(self, record):
        from asgi_correlation_id.context import correlation_id
        
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "line_number": record.lineno,
            "request_id": correlation_id.get() if correlation_id.get() else None
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logger(name: str, use_json: bool = False) -> logging.Logger:
    """
    Configures a standard logger instance.
    Writes INFO and above logs to a persistent file and prints them to console.
    Optionally outputs structured JSON format.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    os.makedirs(LOGS_DIR, exist_ok=True)

    # Resolve Formatter
    formatter = JsonFormatter() if (use_json or os.environ.get("LOG_FORMAT_JSON") == "1") else logging.Formatter(LOG_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOGS_DIR, f"forge_ai_{today_str}.log")
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

sys_logger = setup_logger("forge_ai")
