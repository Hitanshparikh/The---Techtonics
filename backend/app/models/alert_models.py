from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class AlertStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AlertChannel(str, enum.Enum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"

class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    region = Column(String(100))  # Mumbai, Gujarat, etc.
    preferences = Column(JSON)  # Notification preferences
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("AlertSubscription", back_populates="contact")
    alerts = relationship("Alert", back_populates="contact")

class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    alert_type = Column(String(100), nullable=False)  # flood, tide, storm, etc.
    severity_threshold = Column(Float, default=0.7)
    channels = Column(JSON)  # List of preferred channels
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contact = relationship("Contact", back_populates="subscriptions")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    alert_type = Column(String(100), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(Enum(AlertChannel), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.PENDING)
    
    # Alert metadata
    risk_score = Column(Float)
    location_data = Column(JSON)  # lat, lng, region
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True))
    
    # Delivery tracking
    delivery_attempts = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Relationships
    contact = relationship("Contact", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity}, status={self.status})>"


