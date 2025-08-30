from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import json
from typing import List

from app.core.config import settings
from app.core.database import engine, Base
from app.routes import data, alerts, ml, upload
from app.services.websocket_manager import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Coastal Threat Alert System...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")
    
    # Set WebSocket manager for routes
    from app.routes.data import set_websocket_manager
    set_websocket_manager(manager)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="AI Coastal Threat Alert System",
    description="A comprehensive system for monitoring coastal threats using AI/ML",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data.router, prefix="/api/v1", tags=["data"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(ml.router, prefix="/api/v1", tags=["ml"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                if message.get("type") == "subscribe":
                    # Handle subscription to topics
                    topics = message.get("topics", [])
                    await manager.subscribe(websocket, topics)
                    logger.info(f"Client subscribed to topics: {topics}")
                    
                elif message.get("type") == "ping":
                    # Handle ping/pong for keeping connection alive
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
                else:
                    # Echo back for unknown message types
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "data": message
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "coastal-threat-alert-system"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Coastal Threat Alert System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


