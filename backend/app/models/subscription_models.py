from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class PhoneSubscription(Base):
    __tablename__ = "phone_subscriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), nullable=False, unique=True)
    name = Column(String(100))
    is_active = Column(Boolean, default=True)
    welcome_sent = Column(Boolean, default=False)
    
    # Subscription preferences
    receive_alerts = Column(Boolean, default=True)
    alert_types = Column(Text)  # JSON string of preferred alert types
    
    # Timestamps
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_sent = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PhoneSubscription(phone={self.phone_number}, name={self.name}, active={self.is_active})>"

class SmsLog(Base):
    __tablename__ = "sms_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(50))  # 'welcome', 'alert', 'notification'
    status = Column(String(20))  # 'sent', 'failed', 'delivered'
    provider_message_id = Column(String(100))
    error_message = Column(Text)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<SmsLog(phone={self.phone_number}, type={self.message_type}, status={self.status})>"
