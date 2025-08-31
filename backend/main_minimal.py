from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import data  # Import only data routes to avoid ML dependencies
from app.core.database import init_db, create_tables
# Import only essential models
from app.models import data_models
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

@app.get("/")
async def root():
    return {"message": "Coastal Threat Alert System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
