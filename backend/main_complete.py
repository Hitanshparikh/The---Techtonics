from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import data  # Import only data routes to avoid ML dependencies
from app.core.database import init_db, create_tables, get_db
from app.models import data_models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import asyncio
import json
from typing import List
from datetime import datetime, timedelta

# Initialize database tables
init_db()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Coastal Threat Alert System",
    description="A comprehensive system for monitoring coastal threats and sending alerts",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API versioning
app.include_router(data.router, prefix="/api/v1", tags=["data"])

# Add missing alerts routes
@app.get("/api/v1/alerts/history")
async def get_alert_history(limit: int = 10):
    """Get alert history - mock implementation"""
    try:
        # Mock alert history data
        mock_alerts = []
        for i in range(min(limit, 5)):
            alert_time = datetime.utcnow() - timedelta(hours=i*6)
            mock_alerts.append({
                "id": f"alert-{i+1}",
                "type": "coastal_warning" if i % 2 == 0 else "storm_alert",
                "severity": "high" if i < 2 else "medium",
                "message": f"Coastal threat detected at {alert_time.strftime('%H:%M')}",
                "location": ["Miami Beach", "Charleston Harbor", "San Francisco Bay"][i % 3],
                "timestamp": alert_time.isoformat(),
                "status": "resolved" if i > 2 else "active"
            })
        
        return {
            "alerts": mock_alerts,
            "total": len(mock_alerts),
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alert history: {str(e)}")

@app.post("/api/v1/alerts/send")
async def send_alert(alert_data: dict):
    """Send alert - mock implementation"""
    try:
        # Mock alert sending
        alert = {
            "id": f"alert-{datetime.utcnow().timestamp()}",
            "message": alert_data.get("message", "Emergency coastal alert"),
            "severity": alert_data.get("severity", "medium"),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        
        # Broadcast to WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "new_alert",
            "data": alert
        }))
        
        return {"success": True, "alert": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending alert: {str(e)}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(30)  # Send update every 30 seconds
            
            # Send real-time data update
            update_data = {
                "type": "data_update",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            await manager.send_personal_message(
                json.dumps(update_data), 
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "Coastal Threat Alert System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Add static file handling for missing logo
@app.get("/logo192.png")
async def get_logo():
    return JSONResponse(
        content={"message": "Logo not found"},
        status_code=404
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
