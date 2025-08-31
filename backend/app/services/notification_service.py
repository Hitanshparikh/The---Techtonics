import asyncio
import pandas as pd
import requests
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from twilio.rest import Client
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.models.subscription_models import PhoneSubscription, SmsLog
from app.core.database import get_db, engine
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.sms_enabled = True
        self.email_enabled = True
        
        # Twilio configuration
        self.twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        # Initialize Twilio client if credentials are provided
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
            self.real_sms_enabled = True
            logger.info("Twilio SMS service initialized")
        else:
            self.twilio_client = None
            self.real_sms_enabled = False
            logger.warning("Twilio credentials not found - using mock SMS")
    
    def get_db_session(self) -> Session:
        """Get database session"""
        from app.core.database import sync_engine
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=sync_engine)
        return SessionLocal()
        
    async def save_sms_log(self, phone: str, message: str, message_type: str, 
                          status: str, provider_message_id: str = None, error_message: str = None):
        """Save SMS log to database"""
        try:
            db = self.get_db_session()
            sms_log = SmsLog(
                phone_number=phone,
                message=message,
                message_type=message_type,
                status=status,
                provider_message_id=provider_message_id,
                error_message=error_message,
                delivered_at=datetime.now() if status == 'sent' else None
            )
            db.add(sms_log)
            db.commit()
            db.refresh(sms_log)
            db.close()
            return sms_log.id
        except Exception as e:
            logger.error(f"Failed to save SMS log: {e}")
            if 'db' in locals():
                db.close()
            return None
        
    async def send_sms_alert(self, phone: str, message: str, message_type: str = "alert") -> Dict[str, Any]:
        """Send real SMS alert using Twilio"""
        try:
            if self.real_sms_enabled and self.twilio_client:
                # Send real SMS via Twilio
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_phone_number,
                    to=phone
                )
                
                # Save to database
                log_id = await self.save_sms_log(
                    phone=phone,
                    message=message,
                    message_type=message_type,
                    status="sent",
                    provider_message_id=message_obj.sid
                )
                
                logger.info(f"Real SMS sent to {phone}: {message[:50]}...")
                return {
                    "success": True,
                    "message_id": message_obj.sid,
                    "log_id": log_id,
                    "delivered_at": datetime.now().isoformat(),
                    "provider": "twilio"
                }
            else:
                # Mock SMS for development
                await asyncio.sleep(1)
                
                # Save to database as mock
                log_id = await self.save_sms_log(
                    phone=phone,
                    message=message,
                    message_type=message_type,
                    status="sent",
                    provider_message_id=f"mock_{datetime.now().timestamp()}"
                )
                
                logger.info(f"Mock SMS sent to {phone}: {message[:50]}...")
                return {
                    "success": True,
                    "message_id": f"mock_sms_{datetime.now().timestamp()}",
                    "log_id": log_id,
                    "delivered_at": datetime.now().isoformat(),
                    "provider": "mock"
                }
                
        except Exception as e:
            # Save error to database
            await self.save_sms_log(
                phone=phone,
                message=message,
                message_type=message_type,
                status="failed",
                error_message=str(e)
            )
            
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio" if self.real_sms_enabled else "mock"
            }
    
    async def subscribe_phone_number(self, phone: str, name: str = None) -> Dict[str, Any]:
        """Subscribe a phone number for SMS alerts"""
        try:
            db = self.get_db_session()
            
            # Check if phone number already exists
            existing = db.query(PhoneSubscription).filter(
                PhoneSubscription.phone_number == phone
            ).first()
            
            if existing:
                if existing.is_active:
                    db.close()
                    return {
                        "success": False,
                        "error": "Phone number already subscribed",
                        "subscription_id": existing.id
                    }
                else:
                    # Reactivate existing subscription
                    existing.is_active = True
                    existing.name = name if name else existing.name
                    existing.updated_at = datetime.now()
                    db.commit()
                    subscription_id = existing.id
            else:
                # Create new subscription
                subscription = PhoneSubscription(
                    phone_number=phone,
                    name=name,
                    is_active=True,
                    receive_alerts=True
                )
                db.add(subscription)
                db.commit()
                db.refresh(subscription)
                subscription_id = subscription.id
            
            db.close()
            
            # Send welcome message
            welcome_result = await self.send_welcome_message(phone, name)
            
            logger.info(f"Phone number {phone} subscribed successfully")
            return {
                "success": True,
                "subscription_id": subscription_id,
                "welcome_sent": welcome_result.get("success", False),
                "message": "Successfully subscribed to SMS alerts"
            }
            
        except Exception as e:
            if 'db' in locals():
                db.close()
            logger.error(f"Failed to subscribe phone number {phone}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_welcome_message(self, phone: str, name: str = None) -> Dict[str, Any]:
        """Send welcome SMS to new subscriber"""
        try:
            name_part = f" {name}" if name else ""
            welcome_message = (
                f"Welcome{name_part}! 🌊 You're now subscribed to Coastal Threat Alerts. "
                f"You'll receive important notifications about coastal risks, weather alerts, "
                f"and emergency situations in your area. Reply STOP to unsubscribe."
            )
            
            result = await self.send_sms_alert(phone, welcome_message, "welcome")
            
            if result.get("success"):
                # Mark welcome as sent in database
                db = self.get_db_session()
                subscription = db.query(PhoneSubscription).filter(
                    PhoneSubscription.phone_number == phone
                ).first()
                if subscription:
                    subscription.welcome_sent = True
                    subscription.last_message_sent = datetime.now()
                    db.commit()
                db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send welcome message to {phone}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_active_subscribers(self) -> List[Dict[str, Any]]:
        """Get all active phone subscribers"""
        try:
            db = self.get_db_session()
            subscribers = db.query(PhoneSubscription).filter(
                PhoneSubscription.is_active == True,
                PhoneSubscription.receive_alerts == True
            ).all()
            
            result = []
            for sub in subscribers:
                result.append({
                    "id": sub.id,
                    "phone": sub.phone_number,
                    "name": sub.name,
                    "subscribed_at": sub.subscribed_at.isoformat() if sub.subscribed_at else None
                })
            
            db.close()
            return result
            
        except Exception as e:
            if 'db' in locals():
                db.close()
            logger.error(f"Failed to get active subscribers: {e}")
            return []
    
    async def unsubscribe_phone_number(self, phone: str) -> Dict[str, Any]:
        """Unsubscribe a phone number"""
        try:
            db = self.get_db_session()
            subscription = db.query(PhoneSubscription).filter(
                PhoneSubscription.phone_number == phone
            ).first()
            
            if subscription:
                subscription.is_active = False
                subscription.updated_at = datetime.now()
                db.commit()
                db.close()
                
                # Send confirmation message
                await self.send_sms_alert(
                    phone, 
                    "You have been unsubscribed from Coastal Threat Alerts. Thank you for using our service.",
                    "unsubscribe"
                )
                
                return {
                    "success": True,
                    "message": "Successfully unsubscribed"
                }
            else:
                db.close()
                return {
                    "success": False,
                    "error": "Phone number not found"
                }
                
        except Exception as e:
            if 'db' in locals():
                db.close()
            logger.error(f"Failed to unsubscribe phone number {phone}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def send_email_alert(self, email: str, subject: str, message: str) -> Dict[str, Any]:
        """Send email alert (mock implementation)"""
        try:
            # Simulate email sending delay
            await asyncio.sleep(2)
            
            logger.info(f"Email sent to {email}: {subject}")
            return {
                "success": True,
                "message_id": f"email_{datetime.now().timestamp()}",
                "delivered_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def send_bulk_sms(self, contacts: List[Dict[str, str]], message: str) -> List[Dict[str, Any]]:
        """Send bulk SMS alerts to contacts"""
        results = []
        for contact in contacts:
            if contact.get('phone'):
                result = await self.send_sms_alert(contact['phone'], message, "alert")
                result['method'] = 'SMS'
                results.append({
                    "contact": contact,
                    "result": result
                })
        return results

    async def send_bulk_sms_to_subscribers(self, message: str, message_type: str = "alert") -> Dict[str, Any]:
        """Send SMS to all active subscribers"""
        try:
            subscribers = await self.get_active_subscribers()
            results = []
            success_count = 0
            failure_count = 0
            
            for subscriber in subscribers:
                result = await self.send_sms_alert(
                    subscriber['phone'], 
                    message, 
                    message_type
                )
                
                if result.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
                    
                results.append({
                    "subscriber": subscriber,
                    "result": result
                })
            
            return {
                "success": True,
                "total_sent": len(subscribers),
                "success_count": success_count,
                "failure_count": failure_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Failed to send bulk SMS to subscribers: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
    async def send_bulk_emails(self, contacts: List[Dict[str, str]], subject: str, message: str) -> List[Dict[str, Any]]:
        """Send bulk email alerts"""
        results = []
        for contact in contacts:
            if contact.get('email'):
                result = await self.send_email_alert(contact['email'], subject, message)
                results.append({
                    "contact": contact,
                    "result": result
                })
        return results
        
    def create_alert_message(self, alert_type: str, location: str, risk_score: float) -> str:
        """Create formatted alert message"""
        risk_percentage = int(risk_score * 100)
        
        if risk_score > 0.9:
            severity = "CRITICAL"
            action = "IMMEDIATE EVACUATION REQUIRED"
        elif risk_score > 0.8:
            severity = "HIGH"
            action = "EVACUATION ADVISED"
        elif risk_score > 0.7:
            severity = "MODERATE"
            action = "MONITOR CLOSELY"
        else:
            severity = "LOW"
            action = "CONTINUE MONITORING"
            
        return f"🚨 {severity} ALERT: {alert_type} detected in {location}. Risk Level: {risk_percentage}%. {action}. Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
    def create_email_subject(self, alert_type: str, severity: str) -> str:
        """Create email subject line"""
        return f"[{severity}] Coastal Threat Alert: {alert_type}"
        
    async def process_risk_alerts(self, data: Dict[str, Any], contacts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Process risk alerts and send notifications"""
        results = []
        
        if data.get('risk_score', 0) > 0.7:  # High risk threshold
            alert_type = "High Risk Condition"
            location = data.get('location', 'Unknown')
            risk_score = data.get('risk_score', 0)
            
            # Create alert message
            message = self.create_alert_message(alert_type, location, risk_score)
            subject = self.create_email_subject(alert_type, "HIGH")
            
            # Send SMS alerts to subscribers
            subscriber_results = await self.send_bulk_sms_to_subscribers(message, "alert")
            results.append({
                "type": "subscriber_sms",
                "result": subscriber_results
            })
            
            # Send SMS alerts to provided contacts
            if self.sms_enabled and contacts:
                sms_results = await self.send_bulk_sms(contacts, message)
                results.append({
                    "type": "contact_sms",
                    "result": sms_results
                })
                
            # Send email alerts
            if self.email_enabled and contacts:
                email_results = await self.send_bulk_emails(contacts, subject, message)
                results.append({
                    "type": "email",
                    "result": email_results
                })
                
        return results
        
    async def import_contacts_from_file(self, file_path: str) -> List[Dict[str, str]]:
        """Import contacts from CSV/Excel file"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
                
            contacts = []
            for _, row in df.iterrows():
                contact = {}
                if 'name' in df.columns:
                    contact['name'] = str(row['name'])
                if 'email' in df.columns:
                    contact['email'] = str(row['email'])
                if 'phone' in df.columns:
                    contact['phone'] = str(row['phone'])
                    
                if contact.get('email') or contact.get('phone'):
                    contacts.append(contact)
                    
            logger.info(f"Imported {len(contacts)} contacts from {file_path}")
            return contacts
            
        except Exception as e:
            logger.error(f"Failed to import contacts: {e}")
            return []

# Global instance
notification_service = NotificationService()