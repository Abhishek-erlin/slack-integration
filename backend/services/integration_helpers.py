"""
Integration helpers for notification system.
These helpers make it easy to send notifications from other parts of the application.
"""
import logging
from typing import Optional
from uuid import UUID

from models.notification_models import NotificationType, Priority
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class NotificationHelper:
    """Helper class for sending notifications from other parts of the application."""
    
    def __init__(self):
        """Initialize notification helper with notification service."""
        self.notification_service = NotificationService()
    
    async def send_audit_complete_notification(
        self,
        user_id: UUID,
        channel_id: Optional[str] = None,
        website_url: str = "",
        audit_type: str = "site-level",
        score: Optional[int] = None,
        issues_count: Optional[int] = 0
    ):
        """
        Send a notification when an audit is completed.
        
        Args:
            user_id: User ID to send notification to
            channel_id: Optional Slack channel ID override
            website_url: URL of the website that was audited
            audit_type: Type of audit (site-level, product-template, etc.)
            score: Optional audit score
            issues_count: Number of issues found
            
        Returns:
            Result of notification sending
        """
        try:
            # Format message based on audit results
            score_text = f" with score {score}/100" if score is not None else ""
            issues_text = f"{issues_count} issues found" if issues_count > 0 else "No issues found"
            
            message = (
                f"🔍 Audit Complete: {audit_type} audit for {website_url}{score_text}. "
                f"{issues_text}. View results in dashboard."
            )
            
            # Create metadata
            metadata = {
                "website_url": website_url,
                "audit_type": audit_type,
                "score": score,
                "issues_count": issues_count
            }
            
            # Send notification
            return await self.notification_service.send_notification(
                user_id=user_id,
                message_content=message,
                notification_type=NotificationType.AUDIT_COMPLETE,
                channel_id=channel_id,
                priority=Priority.NORMAL,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error sending audit complete notification: {e}")
            return None
    
    async def send_audit_started_notification(
        self,
        user_id: UUID,
        channel_id: Optional[str] = None,
        website_url: str = "",
        audit_type: str = "site-level"
    ):
        """
        Send a notification when an audit is started.
        
        Args:
            user_id: User ID to send notification to
            channel_id: Optional Slack channel ID override
            website_url: URL of the website being audited
            audit_type: Type of audit (site-level, product-template, etc.)
            
        Returns:
            Result of notification sending
        """
        try:
            message = f"🚀 Audit Started: {audit_type} audit for {website_url} is now running. Results will be available soon."
            
            # Create metadata
            metadata = {
                "website_url": website_url,
                "audit_type": audit_type
            }
            
            # Send notification
            return await self.notification_service.send_notification(
                user_id=user_id,
                message_content=message,
                notification_type=NotificationType.AUDIT_STARTED,
                channel_id=channel_id,
                priority=Priority.LOW,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error sending audit started notification: {e}")
            return None
    
    async def send_integration_status_notification(
        self,
        user_id: UUID,
        channel_id: Optional[str] = None,
        integration_name: str = "Slack",
        status: str = "connected",
        details: str = ""
    ):
        """
        Send a notification about integration status changes.
        
        Args:
            user_id: User ID to send notification to
            channel_id: Optional Slack channel ID override
            integration_name: Name of the integration
            status: Status of the integration (connected, disconnected, error)
            details: Additional details about the status change
            
        Returns:
            Result of notification sending
        """
        try:
            # Format message based on status
            emoji = "✅" if status == "connected" else "❌"
            details_text = f": {details}" if details else ""
            
            message = f"{emoji} Integration Update: {integration_name} integration {status}{details_text}"
            
            # Create metadata
            metadata = {
                "integration_name": integration_name,
                "status": status,
                "details": details
            }
            
            # Send notification
            return await self.notification_service.send_notification(
                user_id=user_id,
                message_content=message,
                notification_type=NotificationType.INTEGRATION_STATUS,
                channel_id=channel_id,
                priority=Priority.NORMAL,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error sending integration status notification: {e}")
            return None
    
    async def send_system_alert(
        self,
        user_id: UUID,
        channel_id: Optional[str] = None,
        alert_title: str = "System Alert",
        alert_message: str = "",
        priority: Priority = Priority.HIGH,
        alert_details: Optional[dict] = None
    ):
        """
        Send a system alert notification.
        
        Args:
            user_id: User ID to send notification to
            channel_id: Optional Slack channel ID override
            alert_title: Title of the alert
            alert_message: Alert message details
            priority: Priority level of the alert
            alert_details: Optional additional details about the alert
            
        Returns:
            Result of notification sending
        """
        try:
            message = f"⚠️ {alert_title}: {alert_message}"
            
            # Create metadata
            metadata = {
                "alert_title": alert_title,
                "alert_type": "system_alert"
            }
            
            # Add additional details if provided
            if alert_details:
                metadata.update(alert_details)
            
            # Send notification
            return await self.notification_service.send_notification(
                user_id=user_id,
                message_content=message,
                notification_type=NotificationType.SYSTEM_ALERT,
                channel_id=channel_id,
                priority=priority,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error sending system alert notification: {e}")
            return None
