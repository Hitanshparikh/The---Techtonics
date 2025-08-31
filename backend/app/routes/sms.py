from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, validator
import re
from app.core.database import get_sync_db
from app.services.notification_service import notification_service
from app.models.subscription_models import PhoneSubscription, SmsLog

router = APIRouter(prefix="/api/v1/sms", tags=["SMS Subscriptions"])

class PhoneSubscriptionRequest(BaseModel):
    phone_number: str
    name: Optional[str] = None
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove spaces and special characters
        phone = re.sub(r'[^\d+]', '', v)
        
        # Basic phone number validation
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValueError('Invalid phone number format')
        
        # Ensure it starts with + for international format
        if not phone.startswith('+'):
            # Add default country code if not provided (adjust as needed)
            phone = '+1' + phone  # Default to US, change as needed
            
        return phone

class PhoneSubscriptionResponse(BaseModel):
    success: bool
    message: str
    subscription_id: Optional[str] = None
    welcome_sent: Optional[bool] = None

class UnsubscribeRequest(BaseModel):
    phone_number: str

class BulkSMSRequest(BaseModel):
    message: str
    message_type: Optional[str] = "notification"

@router.post("/subscribe", response_model=PhoneSubscriptionResponse)
async def subscribe_phone_number(
    request: PhoneSubscriptionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_sync_db)
):
    """Subscribe a phone number for SMS alerts"""
    try:
        result = await notification_service.subscribe_phone_number(
            phone=request.phone_number,
            name=request.name
        )
        
        if result.get("success"):
            return PhoneSubscriptionResponse(
                success=True,
                message=result.get("message", "Successfully subscribed"),
                subscription_id=result.get("subscription_id"),
                welcome_sent=result.get("welcome_sent", False)
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to subscribe phone number")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unsubscribe")
async def unsubscribe_phone_number(
    request: UnsubscribeRequest,
    db: Session = Depends(get_sync_db)
):
    """Unsubscribe a phone number from SMS alerts"""
    try:
        result = await notification_service.unsubscribe_phone_number(request.phone_number)
        
        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message", "Successfully unsubscribed")
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Phone number not found")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscribers")
async def get_active_subscribers(db: Session = Depends(get_sync_db)):
    """Get list of active SMS subscribers"""
    try:
        subscribers = await notification_service.get_active_subscribers()
        return {
            "success": True,
            "count": len(subscribers),
            "subscribers": subscribers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-bulk")
async def send_bulk_sms(
    request: BulkSMSRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_sync_db)
):
    """Send SMS to all active subscribers"""
    try:
        # Send SMS in background
        background_tasks.add_task(
            notification_service.send_bulk_sms_to_subscribers,
            request.message,
            request.message_type
        )
        
        # Get subscriber count for immediate response
        subscribers = await notification_service.get_active_subscribers()
        
        return {
            "success": True,
            "message": "Bulk SMS sending initiated",
            "target_subscribers": len(subscribers),
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_sms_logs(
    phone_number: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_sync_db)
):
    """Get SMS logs, optionally filtered by phone number"""
    try:
        query = db.query(SmsLog)
        
        if phone_number:
            query = query.filter(SmsLog.phone_number == phone_number)
            
        logs = query.order_by(SmsLog.sent_at.desc()).limit(limit).all()
        
        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "phone_number": log.phone_number,
                "message": log.message[:100] + "..." if len(log.message) > 100 else log.message,
                "message_type": log.message_type,
                "status": log.status,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "delivered_at": log.delivered_at.isoformat() if log.delivered_at else None,
                "error_message": log.error_message
            })
            
        return {
            "success": True,
            "count": len(result),
            "logs": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_sms_stats(db: Session = Depends(get_sync_db)):
    """Get SMS statistics"""
    try:
        # Get subscriber stats
        total_subscribers = db.query(PhoneSubscription).count()
        active_subscribers = db.query(PhoneSubscription).filter(
            PhoneSubscription.is_active == True
        ).count()
        
        # Get SMS stats
        total_sms = db.query(SmsLog).count()
        successful_sms = db.query(SmsLog).filter(SmsLog.status == 'sent').count()
        failed_sms = db.query(SmsLog).filter(SmsLog.status == 'failed').count()
        
        return {
            "success": True,
            "subscribers": {
                "total": total_subscribers,
                "active": active_subscribers,
                "inactive": total_subscribers - active_subscribers
            },
            "sms": {
                "total_sent": total_sms,
                "successful": successful_sms,
                "failed": failed_sms,
                "success_rate": round((successful_sms / total_sms * 100), 2) if total_sms > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
