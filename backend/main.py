from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.routes import data, alerts, ml, upload, sms
from app.services.websocket_manager import ConnectionManager
from app.core.database import init_db, create_tables
# Import models to register them with SQLAlchemy
from app.models import data_models, alert_models, ml_models, subscription_models
import asyncio

# Initialize database tables
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="AI Coastal Threat Alert System",
    description="Real-time coastal threat monitoring and risk assessment",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
manager = ConnectionManager()

# Include routers
app.include_router(data.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(ml.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(sms.router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for testing
            await manager.send_personal_message(f"Message: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {
        "message": "AI Coastal Threat Alert System API",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "coastal-threat-alert-system"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
