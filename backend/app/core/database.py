from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import aiosqlite
from .config import settings
import os

# Create SQLite database file path
DB_PATH = "./coastal_threats.db"

# Create async engine for SQLite
engine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    echo=settings.DEBUG,
    future=True
)

# Create sync engine for migrations and table creation
sync_engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=settings.DEBUG
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Sync session factory for SMS operations
SyncSessionLocal = sessionmaker(bind=sync_engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

async def get_db():
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """Dependency to get sync database session"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_tables():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def test_db_connection():
    """Test database connection"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def init_db():
    """Initialize database with tables (sync version for startup)"""
    Base.metadata.create_all(bind=sync_engine)
