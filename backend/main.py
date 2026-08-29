import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, sync, chat
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

@app.on_event("startup")
async def validate_configuration_on_startup():
    validate_production_configuration()

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

# Include sub-routers
app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(chat.router)

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
    authorization = websocket.headers.get("authorization", "")
    companion_id = websocket.query_params.get("companion_id", "")
    if not authorization.startswith("Bearer ") or not companion_id:
        await websocket.close(code=1008, reason="Authentication and companion_id are required.")
        return
    user = identity_service.verify_token(authorization.removeprefix("Bearer ").strip())
    if not user or not user_owns_companion(user.get("uid", ""), companion_id):
        await websocket.close(code=1008, reason="Unauthorized companion access.")
        return
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any incoming messages from a connected client
            data = await websocket.receive_text()
            # Connection groups are intentionally omitted for now: do not echo
            # arbitrary client messages across other users' companion channels.
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
