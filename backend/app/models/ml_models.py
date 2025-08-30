from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class MLModel(Base):
    __tablename__ = "ml_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(100), nullable=False)  # 'risk_assessment', 'anomaly_detection', etc.
    
    # Model metadata
    file_path = Column(String(500))  # Path to saved model file
    parameters = Column(JSON)  # Model hyperparameters
    features = Column(JSON)  # List of feature names
    target_column = Column(String(100))  # Target variable name
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Training info
    training_data_size = Column(Integer)
    last_trained = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    predictions = relationship("Prediction", back_populates="model")
    
    def __repr__(self):
        return f"<MLModel(id={self.id}, name={self.name}, version={self.version})>"

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("ml_models.id"), nullable=False)
    coastal_data_id = Column(String, ForeignKey("coastal_data.id"), nullable=False)
    
    # Prediction results
    predicted_value = Column(Float, nullable=False)
    confidence_score = Column(Float)
    prediction_type = Column(String(100))  # 'risk_score', 'anomaly', 'forecast'
    
    # Input features used
    input_features = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    model = relationship("MLModel", back_populates="predictions")
    coastal_data = relationship("CoastalData", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, predicted_value={self.predicted_value}, confidence={self.confidence_score})>"


