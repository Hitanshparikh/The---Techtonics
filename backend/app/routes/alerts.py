from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.services.notification_service import notification_service
from app.models.alert_models import Alert, Contact, AlertSubscription

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/alerts/send")
async def send_alert(
    background_tasks: BackgroundTasks,
    message: str = Form(...),
    alert_type: str = Form(...),
    severity: str = Form("medium"),
    channels: List[str] = Form(["sms", "email"]),
    region: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Send manual alert to all subscribed contacts"""
    try:
        # Validate inputs
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        valid_severities = ["low", "medium", "high", "critical"]
        if severity not in valid_severities:
            raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {valid_severities}")
        
        valid_channels = ["sms", "email", "push"]
        if not all(channel in valid_channels for channel in channels):
            raise HTTPException(status_code=400, detail=f"Invalid channels. Must be one of: {valid_channels}")
        
        # Mock contacts for demonstration
        # In production, this would query the database for subscribed contacts
        mock_contacts = [
            {"id": "1", "name": "Emergency Response", "phone": "+919876543210", "email": "emergency@coastal.gov", "region": "Mumbai"},
            {"id": "2", "name": "Coastal Patrol", "phone": "+919876543211", "email": "patrol@coastal.gov", "region": "Gujarat"},
            {"id": "3", "name": "Weather Station", "phone": "+919876543212", "email": "weather@coastal.gov", "region": "Chennai"},
            {"id": "4", "name": "Local Authority", "phone": "+919876543213", "email": "authority@coastal.gov", "region": "Mumbai"}
        ]
        
        # Filter by region if specified
        if region:
            mock_contacts = [c for c in mock_contacts if c.get('region') == region]
        
        # Send alerts in background
        background_tasks.add_task(
            send_bulk_alerts_background,
            mock_contacts,
            message,
            alert_type,
            severity,
            channels
        )
        
        return {
            "message": "Alert sent successfully",
            "alert_type": alert_type,
            "severity": severity,
            "channels": channels,
            "recipients_count": len(mock_contacts),
            "region": region,
            "status": "sending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending alert: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/alerts/contacts/import")
async def import_contacts(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import contacts from CSV/Excel file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read file content
        file_content = await file.read()
        
        # Determine file type
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == "csv":
            file_type = "csv"
            content_str = file_content.decode('utf-8')
        elif file_extension in ["xlsx", "xls"]:
            file_type = file_extension
            content_str = file_content.decode('latin-1')  # Excel files might have special characters
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or Excel files.")
        
        # Process contacts in background
        background_tasks.add_task(
            process_contacts_import_background,
            content_str,
            file_type
        )
        
        return {
            "message": "Contact import started",
            "filename": file.filename,
            "file_type": file_type,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/contacts")
async def list_contacts(
    db: AsyncSession = Depends(get_db),
    region: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List all contacts with optional filtering"""
    try:
        # Mock contacts for demonstration
        mock_contacts = [
            {
                "id": "1",
                "name": "Emergency Response",
                "phone": "+919876543210",
                "email": "emergency@coastal.gov",
                "region": "Mumbai",
                "is_active": True,
                "created_at": "2024-01-01T10:00:00"
            },
            {
                "id": "2",
                "name": "Coastal Patrol",
                "phone": "+919876543211",
                "email": "patrol@coastal.gov",
                "region": "Gujarat",
                "is_active": True,
                "created_at": "2024-01-01T11:00:00"
            },
            {
                "id": "3",
                "name": "Weather Station",
                "phone": "+919876543212",
                "email": "weather@coastal.gov",
                "region": "Mumbai",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00"
            }
        ]
        
        # Apply filters
        if region:
            mock_contacts = [c for c in mock_contacts if c.get("region") == region]
        
        # Apply pagination
        total_count = len(mock_contacts)
        paginated_contacts = mock_contacts[offset:offset + limit]
        
        return {
            "contacts": paginated_contacts,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/alerts/contacts")
async def create_contact(
    name: str = Form(...),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contact"""
    try:
        # Validate inputs
        if not name.strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        
        if not phone and not email:
            raise HTTPException(status_code=400, detail="Either phone or email must be provided")
        
        # In production, this would save to database
        # For now, return success response
        
        return {
            "message": "Contact created successfully",
            "contact": {
                "id": "new_contact_id",
                "name": name,
                "phone": phone,
                "email": email,
                "region": region,
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/history")
async def get_alert_history(
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    alert_type: Optional[str] = None
):
    """Get alert history"""
    try:
        # Mock alert history for demonstration
        mock_alerts = [
            {
                "id": "1",
                "alert_type": "flood_warning",
                "severity": "high",
                "message": "High tide levels detected in Mumbai region",
                "channel": "sms",
                "status": "sent",
                "risk_score": 0.8,
                "location": "Mumbai",
                "triggered_at": "2024-01-01T10:00:00",
                "sent_at": "2024-01-01T10:01:00"
            },
            {
                "id": "2",
                "alert_type": "storm_alert",
                "severity": "critical",
                "message": "Severe storm approaching Gujarat coast",
                "channel": "email",
                "status": "sent",
                "risk_score": 0.95,
                "location": "Gujarat",
                "triggered_at": "2024-01-01T09:30:00",
                "sent_at": "2024-01-01T09:31:00"
            },
            {
                "id": "3",
                "alert_type": "tide_monitoring",
                "severity": "medium",
                "message": "Unusual tide patterns detected",
                "channel": "sms",
                "status": "failed",
                "risk_score": 0.6,
                "location": "Mumbai",
                "triggered_at": "2024-01-01T08:45:00",
                "sent_at": None
            }
        ]
        
        # Apply filters
        if status:
            mock_alerts = [a for a in mock_alerts if a["status"] == status]
        
        if alert_type:
            mock_alerts = [a for a in mock_alerts if a["alert_type"] == alert_type]
        
        # Sort by triggered_at (newest first)
        sorted_alerts = sorted(mock_alerts, key=lambda x: x["triggered_at"], reverse=True)
        
        # Apply pagination
        total_count = len(sorted_alerts)
        paginated_alerts = sorted_alerts[offset:offset + limit]
        
        return {
            "alerts": paginated_alerts,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/statistics")
async def get_alert_statistics(db: AsyncSession = Depends(get_db)):
    """Get alert statistics and metrics"""
    try:
        # Mock statistics for demonstration
        stats = {
            "total_alerts": 150,
            "alerts_today": 12,
            "alerts_this_week": 45,
            "alerts_this_month": 150,
            "success_rate": 0.92,
            "by_severity": {
                "low": 25,
                "medium": 60,
                "high": 45,
                "critical": 20
            },
            "by_channel": {
                "sms": 80,
                "email": 60,
                "push": 10
            },
            "by_type": {
                "flood_warning": 40,
                "storm_alert": 35,
                "tide_monitoring": 45,
                "anomaly_detection": 30
            },
            "by_region": {
                "Mumbai": 80,
                "Gujarat": 70
            },
            "average_response_time": "2.5 minutes"
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/alerts/test")
async def test_alert_system(
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Send test alert to verify system functionality"""
    try:
        if not phone and not email:
            raise HTTPException(status_code=400, detail="Either phone or email must be provided")
        
        test_message = "🧪 TEST ALERT - This is a test message to verify the alert system is working correctly. No action required."
        
        results = []
        
        # Send test SMS
        if phone:
            sms_result = await notification_service.send_sms_alert(phone, test_message, "test_alert")
            results.append({"channel": "sms", "result": sms_result})
        
        # Send test email
        if email:
            email_result = await notification_service.send_email_alert(
                email, 
                "Test Alert - Coastal Threat System", 
                test_message, 
                "test_alert"
            )
            results.append({"channel": "email", "result": email_result})
        
        return {
            "message": "Test alerts sent successfully",
            "test_message": test_message,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def send_bulk_alerts_background(
    contacts: List[Dict[str, str]],
    message: str,
    alert_type: str,
    severity: str,
    channels: List[str]
):
    """Background task to send bulk alerts"""
    try:
        logger.info(f"Starting background alert sending for {len(contacts)} contacts")
        
        # Send SMS alerts (includes WhatsApp)
        if "sms" in channels:
            sms_results = await notification_service.send_bulk_sms(contacts, message)
            logger.info(f"SMS/WhatsApp alerts sent: {len(sms_results)}")
            for result in sms_results:
                if result['result'].get('success'):
                    method = result['result'].get('method', 'SMS')
                    logger.info(f"Alert sent via {method} to {result['contact']['name']}")
                else:
                    logger.error(f"Failed to send to {result['contact']['name']}: {result['result'].get('error')}")
        
        # Send email alerts
        if "email" in channels:
            email_results = await notification_service.send_bulk_emails(
                contacts, 
                f"[{severity.upper()}] {alert_type.replace('_', ' ').title()} Alert", 
                message
            )
            logger.info(f"Email alerts sent: {len(email_results)}")
        
        logger.info("Background alert sending completed")
        
    except Exception as e:
        logger.error(f"Error in background alert sending: {e}")

async def process_contacts_import_background(content: str, file_type: str):
    """Background task to process contacts import"""
    try:
        logger.info(f"Starting background contacts import processing")
        
        # Process contacts
        result = await notification_service.import_contacts_from_file(content, file_type)
        
        if result["success"]:
            logger.info(f"Contacts import completed successfully. Processed: {result['contacts_processed']}")
        else:
            logger.error(f"Contacts import failed: {result['error']}")
        
    except Exception as e:
        logger.error(f"Error in background contacts import processing: {e}")


