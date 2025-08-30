from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_type = Column(String(50), nullable=False)  # 'api' or 'file'
    source_url = Column(String(500))  # For API sources
    file_path = Column(String(500))   # For file uploads
    schema = Column(JSON)  # Dynamic schema information
    total_records = Column(Integer, default=0)
    status = Column(String(50), default='active')  # active, inactive, processing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    coastal_data = relationship("CoastalData", back_populates="dataset")

class CoastalData(Base):
    __tablename__ = "coastal_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Dynamic data fields stored as JSON
    data_fields = Column(JSON, nullable=False)
    
    # Computed fields
    risk_score = Column(Float)
    anomaly_detected = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    dataset = relationship("Dataset", back_populates="coastal_data")
    predictions = relationship("Prediction", back_populates="coastal_data")
    
    def __repr__(self):
        return f"<CoastalData(id={self.id}, timestamp={self.timestamp}, risk_score={self.risk_score})>"


