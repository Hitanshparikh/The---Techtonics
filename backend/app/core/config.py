from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./coastal_threats.db"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    API_KEY: str = "your-api-key-change-in-production"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Coastal Threat Alert System"
    
    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "data/uploads"
    ALLOWED_EXTENSIONS: list = [".csv", ".xlsx", ".xls"]
    
    # ML Model
    MODEL_PATH: str = "data/models"
    RETRAIN_THRESHOLD: int = 1000  # Retrain after 1000 new records
    
    # Notifications
    SMS_ENABLED: bool = True
    EMAIL_ENABLED: bool = True
    ALERT_THRESHOLD: float = 0.7  # Risk score threshold for alerts
    
    # Redis (for future use)
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # External APIs
    WEATHER_API_KEY: Optional[str] = None
    SMS_API_KEY: Optional[str] = None
    EMAIL_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MODEL_PATH, exist_ok=True)


