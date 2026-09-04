import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, sync, chat, dashboard, companions, memory, goals
from core.logging import setup_logger
from core.config import get_config
from typing import List
from backend.routers.auth import identity_service
from backend.services.ownership import user_owns_companion
from backend.configuration import validate_production_configuration
import os

logger = setup_logger("fastapi_main")

app = FastAPI(
    title="Forge AI Backend",
    description="Clean Architecture REST & WebSockets Backend for DevBuddy (Forge AI)",
    version="1.0.0"
)

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.limiter import limiter

@app.on_event("startup")
async def validate_configuration_on_startup():
    validate_production_configuration()
    
    # 14.9 Register planner observability
    from brain.planner import global_planner
    import json
    def _on_plan_updated(companion_id, plan):
        try:
            from backend.messaging import publish_ws_event
            publish_ws_event(companion_id, json.dumps({
                "type": "plan_update",
                "companion_id": companion_id,
                "plan": plan.to_dict()
            }))
        except Exception as e:
            logger.error(f"Failed to publish plan update: {e}")
            
    global_planner.on_plan_update = _on_plan_updated
    
    # 15.4 Subscribe to Redis for worker events
    import threading
    def _redis_subscriber():
        from backend.messaging import get_redis_client
        client = get_redis_client()
        if not client:
            return
        pubsub = client.pubsub()
        pubsub.subscribe("ws_events")
        logger.info("Subscribed to Redis ws_events channel")
        loop = asyncio.get_event_loop()
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    comp_id = data.get("companion_id")
                    msg_text = data.get("message")
                    
                    if comp_id and msg_text:
                        # Try parsing message to see if it's already a JSON event (like plan_update)
                        try:
                            json_obj = json.loads(msg_text)
                            payload_str = msg_text
                        except Exception:
                            # It's a raw string (proactive message)
                            payload_str = json.dumps({
                                "type": "proactive_message",
                                "message": msg_text
                            })
                            
                        asyncio.run_coroutine_threadsafe(
                            manager.send_to_companion(comp_id, payload_str),
                            loop
                        )
                except Exception as e:
                    logger.error(f"Error processing Redis ws_event: {e}")

    threading.Thread(target=_redis_subscriber, daemon=True).start()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from core.exceptions import GatewayException
@app.exception_handler(GatewayException)
async def gateway_exception_handler(request: Request, exc: GatewayException):
    logger.error(f"Gateway Error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Service unavailable: AI Provider is currently offline. Please try again later."}
    )

# Request Size Limit Middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1_000_000: # 1MB limit
        return JSONResponse(status_code=413, content={"detail": "Payload too large"})
    return await call_next(request)

# Request Latency Middleware
@app.middleware("http")
async def track_latency(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["X-Process-Time-Sec"] = f"{duration:.4f}"
    logger.info(f"API latency: {request.method} {request.url.path} handled in {duration:.4f}s")
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("BUDDY_CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from asgi_correlation_id import CorrelationIdMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

app.add_middleware(CorrelationIdMiddleware)

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

# Include sub-routers
app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(memory.router)
app.include_router(goals.router)
app.include_router(companions.router, prefix="/api")

# WebSocket Connection Manager
class ConnectionManager:
    """Manages active WebSockets connections to broadcast events in real-time."""
    def __init__(self):
        self.active_connections = {} # companion_id -> List[WebSocket]
        self.all_connections = []

    async def connect(self, websocket: WebSocket, companion_id: str):
        await websocket.accept()
        if companion_id not in self.active_connections:
            self.active_connections[companion_id] = []
        self.active_connections[companion_id].append(websocket)
        self.all_connections.append(websocket)
        logger.info(f"New client connected ({companion_id}). Active: {len(self.all_connections)}")

    def disconnect(self, websocket: WebSocket, companion_id: str = None):
        if websocket in self.all_connections:
            self.all_connections.remove(websocket)
        if companion_id and companion_id in self.active_connections:
            if websocket in self.active_connections[companion_id]:
                self.active_connections[companion_id].remove(websocket)
        logger.info(f"Client disconnected. Active: {len(self.all_connections)}")

    async def broadcast(self, message: str):
        for connection in self.all_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send websocket message: {e}")
                
    async def send_to_companion(self, companion_id: str, message: str):
        if companion_id in self.active_connections:
            for connection in self.active_connections[companion_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send to companion {companion_id}: {e}")

manager = ConnectionManager()

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Wait for the first message to be the auth payload
        auth_msg_raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        import json
        auth_msg = json.loads(auth_msg_raw)
        
        if auth_msg.get("type") != "auth" or not auth_msg.get("token") or not auth_msg.get("companion_id"):
            await websocket.close(code=1008, reason="Valid auth payload required as first message.")
            return
            
        token = auth_msg["token"]
        companion_id = auth_msg["companion_id"]
        
        user = identity_service.verify_token(token)
        if not user or not user_owns_companion(user.get("uid", ""), companion_id):
            await websocket.close(code=1008, reason="Unauthorized companion access.")
            return
            
        await manager.connect(websocket, companion_id)
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="WebSocket connection or authentication failed.")
        return

    try:
        # Proactive task is now handled by Redis pub/sub in startup
        
        message_timestamps = []
        loop = asyncio.get_event_loop()
        while True:
            # Wait for any incoming messages from a connected client
            data = await websocket.receive_text()
            
            # Prevent OOM DoS
            if len(data) > 5 * 1024 * 1024:
                await websocket.close(code=1009, reason="Payload too large")
                return
            
            # Simple in-memory token bucket for this connection (60 msgs/min)
            now = time.time()
            message_timestamps = [ts for ts in message_timestamps if now - ts < 60]
            if len(message_timestamps) >= 60:
                await websocket.send_text('{"type": "stream_error", "error": "Rate limit exceeded."}')
                continue
            message_timestamps.append(now)
            
            import json
            try:
                msg_payload = json.loads(data)
            except Exception:
                await websocket.send_text(data)
                continue

            if msg_payload.get("type") == "chat":
                user_input = msg_payload.get("message", "")
                image_data = msg_payload.get("image", None)
                
                if image_data and not str(image_data).startswith("data:image/"):
                    await websocket.send_text('{"type": "stream_error", "error": "Invalid image format."}')
                    continue
                    
                thread_id = msg_payload.get("thread_id", companion_id)
                
                from backend.repositories.factory import get_companion_repository, get_memory_repository
                comp_repo = get_companion_repository()
                mem_repo = get_memory_repository()
                
                if thread_id != companion_id:
                    threads = mem_repo.get_threads(companion_id)
                    if thread_id not in [t["id"] for t in threads]:
                        await websocket.send_text('{"type": "stream_error", "error": "Unauthorized thread access."}')
                        continue
                
                soul = comp_repo.get(companion_id) or {}
                stats = soul.get("stats", {})
                energy = soul.get("energy", 100)
                
                # Retrieve and append user message
                history = mem_repo.get(thread_id) or []
                history.append({"sender": "user", "message": user_input, "timestamp": time.time()})
                mem_repo.save(thread_id, history)
                
                queue = asyncio.Queue()
                
                def run_generator():
                    try:
                        from brain.conversation import stream_process_chat
                        full_res = ""
                        for chunk in stream_process_chat(user_input, stats, energy, companion_id, user.get("uid"), image_data):
                            full_res += chunk
                            asyncio.run_coroutine_threadsafe(queue.put({"type": "stream_chunk", "chunk": chunk}), loop)
                        
                        # Append and save bot message with the latest history from DB
                        latest_history = mem_repo.get(thread_id) or []
                        latest_history.append({"sender": companion_id, "message": full_res, "timestamp": time.time()})
                        mem_repo.save(thread_id, latest_history)
                        
                        from core.automation import parse_and_execute_actions, generate_action_token
                        _, action = parse_and_execute_actions(full_res)
                        action_token = None
                        plan_details = None
                        
                        if action:
                            import re
                            if action.lower().startswith("[plan:"):
                                match = re.search(r'\[PLAN:\s*(.+?)\]', action, flags=re.IGNORECASE)
                                if match:
                                    goal = match.group(1)
                                    from brain.planner import global_planner
                                    plan_obj = global_planner.create_plan(companion_id, goal)
                                    plan_details = plan_obj.to_dict()
                                    
                            action_token = generate_action_token(action, companion_id)
                        
                        asyncio.run_coroutine_threadsafe(queue.put({
                            "type": "stream_complete", 
                            "action": action, 
                            "token": action_token,
                            "plan_details": plan_details
                        }), loop)
                    except Exception as e:
                        asyncio.run_coroutine_threadsafe(queue.put({"type": "stream_error", "error": str(e)}), loop)

                import threading
                threading.Thread(target=run_generator, daemon=True).start()
                
                while True:
                    item = await queue.get()
                    if item["type"] == "stream_complete":
                        await websocket.send_json(item)
                        break
                    elif item["type"] == "stream_error":
                        await websocket.send_json(item)
                        break
                    else:
                        await websocket.send_json(item)
            else:
                await websocket.send_text(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, companion_id if 'companion_id' in locals() else None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, companion_id if 'companion_id' in locals() else None)

@app.get("/health")
def health_check():
    """Exposes a detailed health check validating dependencies and settings."""
    cfg = get_config()
    db_configured = bool(cfg.get("firebase_url"))
    auth_configured = bool(cfg.get("firebase_api_key"))
    ai_provider = cfg.get("ai_provider", "ollama")
    repo_type = cfg.get("repository_type", "sqlite")
    
    postgres_status = "unknown"
    redis_status = "unknown"
    
    # Check postgres if active
    if repo_type == "postgres":
        try:
            from backend.db import engine
            from sqlalchemy import text
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            postgres_status = "connected"
        except Exception as e:
            postgres_status = f"error: {e}"
            
    # Check redis
    try:
        from backend.messaging import get_redis_client
        client = get_redis_client()
        if client and client.ping():
            redis_status = "connected"
        else:
            redis_status = "disconnected"
    except Exception as e:
        redis_status = f"error: {e}"
    
    return {
        "status": "healthy" if postgres_status in ["connected", "unknown"] else "unhealthy",
        "service": "Buddy API",
        "checks": {
            "firebase_database": "configured" if db_configured else "default_mock",
            "firebase_authentication": "configured" if auth_configured else "default_mock",
            "ai_gateway_provider": ai_provider,
            "postgres": postgres_status,
            "redis": redis_status,
            "repository": repo_type
        }
    }
