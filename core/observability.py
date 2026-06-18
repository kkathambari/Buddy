import os
from typing import Any, Dict
from core.logging import setup_logger

logger = setup_logger("observability")

def init_error_tracking() -> None:
    """
    Initializes Sentry error tracking if SENTRY_DSN is configured.
    Otherwise falls back to logging error traces to the file logger.
    """
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
            logger.info("Sentry error tracking initialized successfully.")
        except ImportError:
            logger.warning("sentry-sdk is not installed. Error tracking will log to standard logs.")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
    else:
        logger.info("Sentry DSN not found. Falling back to local logging.")

def log_error_to_tracker(exception: Exception, context: Dict[str, Any] = None) -> None:
    """Logs an exception to Sentry or standard local log files with context."""
    logger.error(f"Observed error: {exception}. Context: {context or {}}", exc_info=exception)
    
    # Try Sentry if initialized
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            with sentry_sdk.configure_scope() as scope:
                if context:
                    for k, v in context.items():
                        scope.set_extra(k, v)
            sentry_sdk.capture_exception(exception)
        except Exception:
            pass

def emit_analytics_event(event_name: str, payload: Dict[str, Any] = None) -> None:
    """Emits a structured analytics event to track capability usages and user flows."""
    payload = payload or {}
    # Structure the event exactly for production log shippers (e.g. Logstash, fluentd)
    analytics_payload = {
        "event_type": "analytics",
        "event_name": event_name,
        "payload": payload
    }
    # Log at INFO level utilizing the JSON format option
    logger.info(f"Analytics event emitted: {analytics_payload}")
