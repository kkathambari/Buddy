import json
import redis
from core.logging import setup_logger
from core.config import get_config

logger = setup_logger("messaging")

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        config = get_config()
        # Default to localhost if not specified, which is fine for local dev
        # In production compose, it will be 'redis'
        redis_url = config.get("redis_url", "redis://localhost:6379/0")
        try:
            _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            _redis_client.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {redis_url}: {e}")
            _redis_client = None
    return _redis_client

def publish_ws_event(companion_id: str, message: str):
    """Publish a proactive message event to be sent over WebSocket."""
    client = get_redis_client()
    if client:
        payload = {
            "companion_id": companion_id,
            "message": message
        }
        client.publish("ws_events", json.dumps(payload))
        logger.info(f"Published ws_event to Redis for companion {companion_id}")
    else:
        logger.warning(f"Redis not connected. Failed to publish ws_event for companion {companion_id}")
