"""
Notification service layer for business logic.
Following the 3-layer architecture pattern.
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from models.notification_models import (
    NotificationType,
    DeliveryStatus,
    Priority,
    NotificationRequest,
    NotificationResponse
)
from repository.notification_repository import NotificationRepository
from services.slack_service import SlackService

logger = logging.getLogger(__name__)


class NotificationService:
    """Service class for notification business logic."""
    
    def __init__(self):
        """Initialize notification service with repository and dependencies."""
        self.repository = NotificationRepository()
        self.slack_service = SlackService()
    
    async def send_notification(
        self,
        user_id: UUID,
        message_content: str,
        notification_type: NotificationType,
        channel_id: Optional[str] = None,
        priority: Priority = Priority.NORMAL,
        metadata: Optional[dict] = None
    ) -> NotificationResponse:
        """
        Send a notification to a user via Slack.
        
        Args:
            user_id: User ID to send notification to
            message_content: Message content to send
            notification_type: Type of notification
            channel_id: Slack channel ID or user Slack ID (optional)
            priority: Priority level (default: NORMAL)
            metadata: Optional additional metadata
            
        Returns:
            NotificationResponse with success status and details
        """
        try:
            # Check if user has Slack integration
            integration_status = await self.slack_service.get_integration_status(str(user_id))
            
            if not integration_status.get("connected", False):
                # Save failed notification log
                notification_id = await self.repository.save_notification_log(
                    user_id=user_id,
                    notification_type=notification_type,
                    message_content=message_content,
                    channel_id=channel_id,
                    priority=priority,
                    delivery_status=DeliveryStatus.FAILED,
                    metadata=metadata
                )
                
                return NotificationResponse(
                    success=False,
                    message="User does not have an active Slack integration",
                    notification_id=notification_id,
                    delivery_status=DeliveryStatus.FAILED
                )
            
            # Use provided channel_id or get default from integration
            target_channel = channel_id or integration_status.get("channel_id")
            
            if not target_channel:
                # Save failed notification log
                notification_id = await self.repository.save_notification_log(
                    user_id=user_id,
                    notification_type=notification_type,
                    message_content=message_content,
                    priority=priority,
                    delivery_status=DeliveryStatus.FAILED,
                    metadata=metadata
                )
                
                return NotificationResponse(
                    success=False,
                    message="No Slack channel available for notification",
                    notification_id=notification_id,
                    delivery_status=DeliveryStatus.FAILED
                )
            
            # Save notification log with SENDING status
            notification_id = await self.repository.save_notification_log(
                user_id=user_id,
                notification_type=notification_type,
                message_content=message_content,
                channel_id=target_channel,
                priority=priority,
                delivery_status=DeliveryStatus.SENDING,
                metadata=metadata
            )
            
            # Send message via Slack
            slack_response = await self.slack_service.send_message(
                user_id=str(user_id),
                message=message_content,
                channel_id=target_channel
            )
            
            if slack_response.success:
                # Update notification status to DELIVERED
                await self.repository.update_notification_status(
                    notification_id=notification_id,
                    delivery_status=DeliveryStatus.DELIVERED,
                    slack_message_id=getattr(slack_response, 'slack_message_id', None)
                )
                
                return NotificationResponse(
                    success=True,
                    message="Notification delivered successfully",
                    notification_id=notification_id,
                    delivery_status=DeliveryStatus.DELIVERED
                )
            else:
                # Update notification status to FAILED
                await self.repository.update_notification_status(
                    notification_id=notification_id,
                    delivery_status=DeliveryStatus.FAILED,
                    error_message=slack_response.message
                )
                
                return NotificationResponse(
                    success=False,
                    message=f"Failed to deliver notification: {slack_response.message}",
                    notification_id=notification_id,
                    delivery_status=DeliveryStatus.FAILED
                )
        
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            
            # Try to save notification log with FAILED status if we haven't already
            try:
                if not locals().get('notification_id'):
                    notification_id = await self.repository.save_notification_log(
                        user_id=user_id,
                        channel_id=channel_id,
                        notification_type=notification_type,
                        message_content=message_content,
                        priority=priority,
                        delivery_status=DeliveryStatus.FAILED
                    )
                else:
                    await self.repository.update_notification_status(
                        notification_id=notification_id,
                        delivery_status=DeliveryStatus.FAILED,
                        error_message=str(e)
                    )
            except Exception as inner_e:
                logger.error(f"Error saving failed notification: {inner_e}")
            
            return NotificationResponse(
                success=False,
                message=f"Error sending notification: {str(e)}",
                notification_id=locals().get('notification_id'),
                delivery_status=DeliveryStatus.FAILED
            )
    
    async def get_notification_history(
        self,
        user_id: Optional[UUID] = None,
        notification_type: Optional[NotificationType] = None,
        delivery_status: Optional[DeliveryStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get notification history with pagination and filtering.
        
        Args:
            user_id: Optional filter by user ID
            notification_type: Optional filter by notification type
            delivery_status: Optional filter by delivery status
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Dict containing notifications, total count, and pagination info
        """
        try:
            return await self.repository.get_notification_history(
                user_id=user_id,
                notification_type=notification_type,
                delivery_status=delivery_status,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            logger.error(f"Error retrieving notification history: {e}")
            return {
                "notifications": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size
            }
