import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./coastal_threats.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Coastal Threat Alert System"
    VERSION: str = "1.0.0"
    
    # File Upload
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".csv", ".xlsx", ".xls"]
    
    # ML Model
    MODEL_PATH: str = "./data/models"
    MODEL_UPDATE_INTERVAL: int = 3600  # 1 hour
    
    # Notifications
    SMS_ENABLED: bool = True
    EMAIL_ENABLED: bool = True
    ALERT_THRESHOLD: float = 0.7
    
    # Redis (for future use)
    REDIS_URL: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.MODEL_PATH).mkdir(parents=True, exist_ok=True)

settings = Settings()
