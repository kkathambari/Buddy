import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, sync, chat, dashboard, companions, memory
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
app.include_router(companions.router, prefix="/api")

# WebSocket Connection Manager
class ConnectionManager:
    """Manages active WebSockets connections to broadcast events in real-time."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        logger.info(f"Broadcasting event: {message}")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send websocket message: {e}")

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
            
        manager.active_connections.append(websocket)
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="WebSocket connection or authentication failed.")
        return

    try:
        message_timestamps = []
        loop = asyncio.get_event_loop()
        while True:
            # Wait for any incoming messages from a connected client
            data = await websocket.receive_text()
            
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
                        for chunk in stream_process_chat(user_input, stats, energy, companion_id, user.get("uid")):
                            full_res += chunk
                            asyncio.run_coroutine_threadsafe(queue.put({"type": "stream_chunk", "chunk": chunk}), loop)
                        
                        # Append and save bot message with the latest history from DB
                        latest_history = mem_repo.get(thread_id) or []
                        latest_history.append({"sender": companion_id, "message": full_res, "timestamp": time.time()})
                        mem_repo.save(thread_id, latest_history)
                        
                        from core.automation import parse_and_execute_actions, generate_action_token
                        _, action = parse_and_execute_actions(full_res)
                        action_token = None
                        if action:
                            action_token = generate_action_token(action)
                        
                        asyncio.run_coroutine_threadsafe(queue.put({
                            "type": "stream_complete", 
                            "action": action, 
                            "token": action_token
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
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/health")
def health_check():
    """Exposes a detailed health check validating Firebase and AI settings."""
    cfg = get_config()
    db_configured = bool(cfg.get("firebase_url"))
    auth_configured = bool(cfg.get("firebase_api_key"))
    ai_provider = cfg.get("ai_provider", "ollama")
    
    return {
        "status": "healthy",
        "service": "Forge AI Backend",
        "checks": {
            "firebase_database": "configured" if db_configured else "default_mock",
            "firebase_authentication": "configured" if auth_configured else "default_mock",
            "ai_gateway_provider": ai_provider
        }
    }
