import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
from fastapi import BackgroundTasks

from app.models.alert_models import Alert, Contact, AlertSubscription
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.sms_enabled = settings.SMS_ENABLED
        self.email_enabled = settings.EMAIL_ENABLED
        self.alert_threshold = settings.ALERT_THRESHOLD
        
    async def send_sms_alert(self, phone: str, message: str, alert_id: str) -> Dict[str, Any]:
        """Send SMS alert (mock implementation)"""
        try:
            # Mock SMS sending - replace with actual SMS API integration
            logger.info(f"[MOCK SMS] Sending to {phone}: {message}")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Mock success response
            return {
                "success": True,
                "message_id": f"sms_{alert_id}",
                "phone": phone,
                "status": "delivered",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone": phone,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_email_alert(self, email: str, subject: str, message: str, alert_id: str) -> Dict[str, Any]:
        """Send email alert (mock implementation)"""
        try:
            # Mock email sending - replace with actual SMTP integration
            logger.info(f"[MOCK EMAIL] Sending to {email}: {subject}")
            logger.info(f"[MOCK EMAIL] Content: {message}")
            
            # Simulate SMTP delay
            await asyncio.sleep(0.2)
            
            # Mock success response
            return {
                "success": True,
                "message_id": f"email_{alert_id}",
                "email": email,
                "status": "sent",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "email": email,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_bulk_sms(self, contacts: List[Contact], message: str, alert_type: str) -> List[Dict[str, Any]]:
        """Send bulk SMS alerts"""
        results = []
        
        for contact in contacts:
            if contact.phone:
                result = await self.send_sms_alert(contact.phone, message, f"bulk_{alert_type}")
                results.append({
                    "contact_id": contact.id,
                    "contact_name": contact.name,
                    "phone": contact.phone,
                    "result": result
                })
        
        return results
    
    async def send_bulk_emails(self, contacts: List[Contact], subject: str, message: str, alert_type: str) -> List[Dict[str, Any]]:
        """Send bulk email alerts"""
        results = []
        
        for contact in contacts:
            if contact.email:
                result = await self.send_email_alert(contact.email, subject, message, f"bulk_{alert_type}")
                results.append({
                    "contact_id": contact.id,
                    "contact_name": contact.name,
                    "email": contact.email,
                    "result": result
                })
        
        return results
    
    def create_alert_message(self, alert_type: str, severity: str, location: str, risk_score: float) -> str:
        """Create formatted alert message"""
        severity_emoji = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🟠",
            "critical": "🔴"
        }
        
        emoji = severity_emoji.get(severity.lower(), "⚪")
        
        message = f"{emoji} COASTAL THREAT ALERT {emoji}\n\n"
        message += f"Type: {alert_type.upper()}\n"
        message += f"Severity: {severity.upper()}\n"
        message += f"Location: {location}\n"
        message += f"Risk Score: {risk_score:.2f}\n\n"
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += "Please take necessary precautions and monitor the situation."
        
        return message
    
    def create_email_subject(self, alert_type: str, severity: str, location: str) -> str:
        """Create email subject line"""
        return f"[{severity.upper()}] Coastal Threat Alert - {alert_type.title()} in {location}"
    
    async def process_risk_alerts(self, risk_data: Dict[str, Any], background_tasks: BackgroundTasks) -> List[Dict[str, Any]]:
        """Process risk data and trigger alerts if threshold exceeded"""
        alerts_triggered = []
        
        risk_score = risk_data.get('risk_score', 0)
        location = risk_data.get('location', 'Unknown')
        alert_type = risk_data.get('alert_type', 'general')
        
        if risk_score >= self.alert_threshold:
            # Determine severity
            if risk_score >= 0.9:
                severity = "critical"
            elif risk_score >= 0.7:
                severity = "high"
            elif risk_score >= 0.5:
                severity = "medium"
            else:
                severity = "low"
            
            # Create alert message
            message = self.create_alert_message(alert_type, severity, location, risk_score)
            subject = self.create_email_subject(alert_type, severity, location)
            
            # Trigger alerts in background
            background_tasks.add_task(
                self._trigger_alerts_background,
                alert_type,
                severity,
                message,
                subject,
                risk_score,
                location
            )
            
            alerts_triggered.append({
                "alert_type": alert_type,
                "severity": severity,
                "risk_score": risk_score,
                "location": location,
                "message": message,
                "triggered_at": datetime.now().isoformat()
            })
        
        return alerts_triggered
    
    async def _trigger_alerts_background(self, alert_type: str, severity: str, message: str, 
                                       subject: str, risk_score: float, location: str):
        """Background task to trigger alerts"""
        try:
            # Get active subscriptions for this alert type
            # This would typically query the database
            # For now, we'll use mock data
            
            # Mock contacts for demonstration
            mock_contacts = [
                Contact(id="1", name="Emergency Response", phone="+919876543210", email="emergency@coastal.gov"),
                Contact(id="2", name="Coastal Patrol", phone="+919876543211", email="patrol@coastal.gov"),
                Contact(id="3", name="Weather Station", phone="+919876543212", email="weather@coastal.gov")
            ]
            
            # Send SMS alerts
            if self.sms_enabled:
                sms_results = await self.send_bulk_sms(mock_contacts, message, alert_type)
                logger.info(f"SMS alerts sent: {len(sms_results)}")
            
            # Send email alerts
            if self.email_enabled:
                email_results = await self.send_bulk_emails(mock_contacts, subject, message, alert_type)
                logger.info(f"Email alerts sent: {len(email_results)}")
            
            logger.info(f"Background alert processing completed for {alert_type}")
            
        except Exception as e:
            logger.error(f"Error in background alert processing: {e}")
    
    async def import_contacts_from_file(self, file_content: str, file_type: str) -> Dict[str, Any]:
        """Import contacts from uploaded file (CSV/Excel)"""
        try:
            import pandas as pd
            from io import StringIO
            
            if file_type == "csv":
                df = pd.read_csv(StringIO(file_content))
            elif file_type in ["xlsx", "xls"]:
                df = pd.read_excel(StringIO(file_content))
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Validate required columns
            required_columns = ['name']
            if not all(col in df.columns for col in required_columns):
                return {
                    "success": False,
                    "error": f"Missing required columns: {required_columns}"
                }
            
            # Process contacts
            contacts_processed = 0
            contacts_errors = []
            
            for _, row in df.iterrows():
                try:
                    contact_data = {
                        "name": row.get('name', 'Unknown'),
                        "phone": row.get('phone', ''),
                        "email": row.get('email', ''),
                        "region": row.get('region', ''),
                        "preferences": {
                            "sms_enabled": row.get('sms_enabled', True),
                            "email_enabled": row.get('email_enabled', True)
                        }
                    }
                    
                    # Validate contact data
                    if not contact_data["phone"] and not contact_data["email"]:
                        contacts_errors.append(f"Contact {contact_data['name']} has no phone or email")
                        continue
                    
                    # Here you would typically save to database
                    # For now, just count as processed
                    contacts_processed += 1
                    
                except Exception as e:
                    contacts_errors.append(f"Error processing row: {e}")
            
            return {
                "success": True,
                "contacts_processed": contacts_processed,
                "contacts_errors": contacts_errors,
                "total_rows": len(df)
            }
            
        except Exception as e:
            logger.error(f"Error importing contacts: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global notification service instance
notification_service = NotificationService()


