"""
Notification repository layer for database operations.
Following the 3-layer architecture pattern.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from supabase import create_client, Client
import os

from models.notification_models import DeliveryStatus, NotificationType, Priority, NotificationLogEntry

logger = logging.getLogger(__name__)


class NotificationRepository:
    """Repository class for notification data access."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    async def save_notification_log(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        message_content: str,
        channel_id: Optional[str] = None,
        priority: Priority = Priority.NORMAL,
        delivery_status: DeliveryStatus = DeliveryStatus.QUEUED,
        metadata: Optional[dict] = None,
        website_id: Optional[UUID] = None
    ) -> Optional[UUID]:
        """
        Save a new notification log entry.
        
        Args:
            user_id: User ID the notification is for
            notification_type: Type of notification
            message_content: Message content
            channel_id: Optional Slack channel ID or user Slack ID
            priority: Priority level (default: NORMAL)
            delivery_status: Initial delivery status (default: QUEUED)
            metadata: Optional additional metadata
            website_id: Optional website ID related to the notification
            
        Returns:
            UUID of the created notification log or None if failed
        """
        try:
            notification_id = uuid4()
            now = datetime.utcnow().isoformat()
            
            notification_data = {
                "id": str(notification_id),
                "user_id": str(user_id),
                "notification_type": notification_type.value,
                "message_content": message_content,
                "channel_id": channel_id,
                "priority": priority.value,
                "delivery_status": delivery_status.value,
                "created_at": now,
                "metadata": metadata,
                "website_id": str(website_id) if website_id else None
            }
            
            result = self.supabase.table("notification_logs").insert(notification_data).execute()
            
            if result.data:
                logger.info(f"Successfully saved notification log with ID {notification_id}")
                return notification_id
            else:
                logger.error("Failed to save notification log")
                return None
                
        except Exception as e:
            logger.error(f"Error saving notification log: {e}")
            return None
    
    async def update_notification_status(
        self,
        notification_id: UUID,
        delivery_status: DeliveryStatus,
        slack_message_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the delivery status of a notification.
        
        Args:
            notification_id: ID of the notification to update
            delivery_status: New delivery status
            slack_message_id: Optional Slack message ID if delivered
            error_message: Optional error message if delivery failed
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            update_data = {
                "delivery_status": delivery_status.value
            }
            
            if delivery_status == DeliveryStatus.SENDING:
                update_data["sent_at"] = datetime.utcnow().isoformat()
                
            if delivery_status == DeliveryStatus.DELIVERED:
                update_data["delivered_at"] = datetime.utcnow().isoformat()
                
            if slack_message_id:
                update_data["slack_message_id"] = slack_message_id
                
            if error_message:
                update_data["error_message"] = error_message
                
            result = self.supabase.table("notification_logs").update(update_data).eq("id", str(notification_id)).execute()
            
            if result.data:
                logger.info(f"Successfully updated notification {notification_id} status to {delivery_status.value}")
                return True
            else:
                logger.error(f"Failed to update notification {notification_id} status")
                return False
                
        except Exception as e:
            logger.error(f"Error updating notification status: {e}")
            return False
    
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
            # Start building the query
            query = self.supabase.table("notification_logs").select("*")
            
            # Apply filters if provided
            if user_id:
                query = query.eq("user_id", str(user_id))
                
            if notification_type:
                query = query.eq("notification_type", notification_type.value)
                
            if delivery_status:
                query = query.eq("delivery_status", delivery_status.value)
            
            # Get total count for pagination
            count_result = query.execute()
            total_count = len(count_result.data)
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)
            
            # Execute the query
            result = query.execute()
            
            # Convert to NotificationLogEntry objects
            notifications = []
            for item in result.data:
                try:
                    notifications.append(NotificationLogEntry(
                        id=UUID(item["id"]),
                        user_id=UUID(item["user_id"]),
                        channel_id=item["channel_id"],
                        notification_type=NotificationType(item["notification_type"]),
                        message_content=item["message_content"],
                        priority=Priority(item["priority"]),
                        delivery_status=DeliveryStatus(item["delivery_status"]),
                        created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
                        delivered_at=datetime.fromisoformat(item["delivered_at"].replace("Z", "+00:00")) if item.get("delivered_at") else None,
                        error_message=item.get("error_message")
                    ))
                except Exception as e:
                    logger.error(f"Error parsing notification log entry: {e}")
                    continue
            
            return {
                "notifications": notifications,
                "total_count": total_count,
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Error retrieving notification history: {e}")
            return {
                "notifications": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size
            }
    
    async def get_failed_notifications(
        self,
        max_retries: int = 3,
        limit: int = 50
    ) -> List[NotificationLogEntry]:
        """
        Get failed notifications for retry processing.
        
        Args:
            max_retries: Maximum number of retries to consider
            limit: Maximum number of notifications to return
            
        Returns:
            List of failed notification log entries
        """
        try:
            # Get notifications with FAILED status that have been retried less than max_retries times
            query = self.supabase.table("notification_logs") \
                .select("*") \
                .eq("delivery_status", DeliveryStatus.FAILED.value) \
                .lt("retry_count", max_retries) \
                .order("updated_at", desc=False) \
                .limit(limit)
            
            result = query.execute()
            
            # Convert to NotificationLogEntry objects
            notifications = []
            for item in result.data:
                try:
                    notifications.append(NotificationLogEntry(
                        id=UUID(item["id"]),
                        user_id=UUID(item["user_id"]),
                        channel_id=item["channel_id"],
                        notification_type=NotificationType(item["notification_type"]),
                        message_content=item["message_content"],
                        priority=Priority(item["priority"]),
                        delivery_status=DeliveryStatus(item["delivery_status"]),
                        created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
                        delivered_at=None,
                        error_message=item.get("error_message")
                    ))
                except Exception as e:
                    logger.error(f"Error parsing failed notification log entry: {e}")
                    continue
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error retrieving failed notifications: {e}")
            return []
