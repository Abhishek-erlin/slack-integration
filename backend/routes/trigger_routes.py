"""
Trigger API routes for FastAPI.
Following the 3-layer architecture pattern.
"""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from models.notification_models import (
    TriggerRequest,
    TriggerResponse,
    NotificationType,
    Priority
)
from services.trigger_service import NotificationTriggerService
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_notification_service():
    """Dependency for notification service."""
    return NotificationService()


def get_trigger_service():
    """Dependency for trigger service."""
    notification_service = get_notification_service()
    return NotificationTriggerService(notification_service)


@router.post("/send", response_model=TriggerResponse)
async def send_trigger_notification(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
    trigger_service: NotificationTriggerService = Depends(get_trigger_service)
):
    """
    Send a notification based on an event trigger.
    
    This endpoint accepts the three required parameters:
    - user_id: UUID of the user to notify
    - website_id: UUID of the website related to the event
    - channel_id: Optional Slack channel ID
    
    For high priority events, notifications are processed immediately.
    For normal/low priority events, notifications are processed in the background.
    
    Returns trigger response with notification status and ID.
    """
    try:
        logger.info(f"Received trigger request: {request.event_type} for user {request.user_id}")
        
        # Validate required parameters
        if not request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        if not request.website_id:
            raise HTTPException(status_code=400, detail="website_id is required")
        
        if not request.event_type:
            raise HTTPException(status_code=400, detail="event_type is required")
        
        # Check if event type is supported
        supported_events = trigger_service.get_supported_event_types()
        if request.event_type not in supported_events:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported event type: {request.event_type}. Supported types: {[e.value for e in supported_events]}"
            )
        
        # Determine if this should be processed immediately or in background
        # System alerts and high priority events are processed immediately
        if request.event_type == NotificationType.SYSTEM_ALERT:
            return await trigger_service.handle_event_trigger(
                user_id=request.user_id,
                website_id=request.website_id,
                event_type=request.event_type,
                channel_id=request.channel_id,
                context=request.context
            )
        
        # For other events, process in background for better performance
        background_tasks.add_task(
            trigger_service.handle_event_trigger,
            user_id=request.user_id,
            website_id=request.website_id,
            event_type=request.event_type,
            channel_id=request.channel_id,
            context=request.context
        )
        
        # Return immediate response for background processing
        return TriggerResponse(
            success=True,
            message="Event trigger queued for processing",
            event_type=request.event_type,
            delivery_status=None  # Will be updated when processed
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in send_trigger_notification endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process trigger: {str(e)}")


@router.get("/supported-events")
async def get_supported_events(
    trigger_service: NotificationTriggerService = Depends(get_trigger_service)
):
    """
    Get list of supported event types for triggers.
    
    Returns:
        List of supported event types with their configurations
    """
    try:
        supported_events = trigger_service.get_supported_event_types()
        
        return {
            "supported_events": [
                {
                    "event_type": event.value,
                    "name": event.value.replace("_", " ").title(),
                    "description": _get_event_description(event)
                }
                for event in supported_events
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in get_supported_events endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve supported events: {str(e)}")


@router.post("/test")
async def test_trigger(
    user_id: UUID,
    website_id: UUID,
    event_type: NotificationType,
    channel_id: str = None,
    trigger_service: NotificationTriggerService = Depends(get_trigger_service)
):
    """
    Test endpoint for trigger functionality.
    
    This endpoint allows testing trigger notifications with sample data.
    Useful for development and debugging purposes.
    """
    try:
        # Create test context based on event type
        test_context = _get_test_context(event_type)
        
        result = await trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=event_type,
            channel_id=channel_id,
            context=test_context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in test_trigger endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test trigger: {str(e)}")


@router.get("/health")
async def health_check(
    trigger_service: NotificationTriggerService = Depends(get_trigger_service)
):
    """
    Health check endpoint for trigger system.
    """
    try:
        supported_events = trigger_service.get_supported_event_types()
        
        return {
            "status": "healthy",
            "service": "notification-trigger-service",
            "components": {
                "trigger_service": "operational",
                "supported_events_count": len(supported_events)
            }
        }
    except Exception as e:
        logger.error(f"Trigger service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "notification-trigger-service",
            "error": str(e)
        }


def _get_event_description(event_type: NotificationType) -> str:
    """Get description for an event type."""
    descriptions = {
        NotificationType.AUDIT_COMPLETE: "Triggered when a website audit is completed",
        NotificationType.AI_VISIBILITY: "Triggered when AI visibility analysis is completed",
        NotificationType.COMPETITOR_ANALYSIS: "Triggered when competitor analysis is ready",
        NotificationType.SYSTEM_ALERT: "Triggered for system-wide alerts and important notifications"
    }
    return descriptions.get(event_type, "Event trigger notification")


def _get_test_context(event_type: NotificationType) -> dict:
    """Get test context data for different event types."""
    base_context = {
        "website_name": "example.com",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    if event_type == NotificationType.AUDIT_COMPLETE:
        return {
            **base_context,
            "audit_type": "technical",
            "score": 85,
            "issues_count": 3,
            "issues_summary": "Found 3 minor issues to review."
        }
    elif event_type == NotificationType.AI_VISIBILITY:
        return {
            **base_context,
            "visibility_score": 78,
            "insights_count": 12,
            "improvement_areas": ["content optimization", "keyword targeting"]
        }
    elif event_type == NotificationType.COMPETITOR_ANALYSIS:
        return {
            **base_context,
            "competitor_count": 5,
            "top_competitor": "competitor-site.com",
            "competitive_score": 82
        }
    elif event_type == NotificationType.SYSTEM_ALERT:
        return {
            **base_context,
            "alert_message": "System maintenance scheduled for tonight at 2 AM UTC"
        }
    
    return base_context
