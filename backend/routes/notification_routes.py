"""
Notification API routes for FastAPI.
Following the 3-layer architecture pattern.
"""
import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query, Path

from models.notification_models import (
    NotificationType,
    DeliveryStatus,
    Priority,
    NotificationRequest,
    NotificationResponse,
    NotificationHistoryResponse
)
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_notification_service():
    """Dependency for notification service."""
    return NotificationService()


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Send a notification to a user via Slack.
    
    For low and normal priority notifications, this will be processed in the background.
    For high and urgent priority notifications, this will be processed immediately.
    
    Returns notification status and ID.
    """
    try:
        # For high priority notifications, process immediately
        if request.priority in [Priority.HIGH, Priority.URGENT]:
            return await notification_service.send_notification(
                user_id=request.user_id,
                message_content=request.message_content,
                notification_type=request.notification_type,
                channel_id=request.channel_id,
                priority=request.priority,
                metadata=request.metadata
            )
        
        # For low/normal priority, process in background
        background_tasks.add_task(
            notification_service.send_notification,
            user_id=request.user_id,
            message_content=request.message_content,
            notification_type=request.notification_type,
            channel_id=request.channel_id,
            priority=request.priority,
            metadata=request.metadata
        )
        
        # Return immediate response for background processing
        return NotificationResponse(
            success=True,
            message="Notification queued for delivery",
            delivery_status=DeliveryStatus.QUEUED
        )
        
    except Exception as e:
        logger.error(f"Error in send_notification endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.get("/history/{user_id}", response_model=NotificationHistoryResponse)
async def get_notification_history(
    user_id: UUID = Path(..., description="User ID to get notifications for"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    delivery_status: Optional[DeliveryStatus] = Query(None, description="Filter by delivery status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get notification history for a user with pagination and filtering.
    """
    try:
        result = await notification_service.get_notification_history(
            user_id=user_id,
            notification_type=notification_type,
            delivery_status=delivery_status,
            page=page,
            page_size=page_size
        )
        
        return NotificationHistoryResponse(
            notifications=result["notifications"],
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"]
        )
        
    except Exception as e:
        logger.error(f"Error in get_notification_history endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notification history: {str(e)}")


@router.get("/health")
async def health_check(
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Health check endpoint for notification system.
    """
    try:
        # Simple health check - just verify service initialization
        return {
            "status": "healthy",
            "service": "notification-service",
            "components": {
                "notification_service": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "notification-service",
            "error": str(e)
        }
