"""
Notification system models for request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID


class NotificationType(str, Enum):
    """Enum for notification types."""
    AUDIT_COMPLETE = "audit_complete"
    AI_VISIBILITY = "ai_visibility"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    SYSTEM_ALERT = "system_alert"


class DeliveryStatus(str, Enum):
    """Enum for notification delivery status."""
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class Priority(str, Enum):
    """Enum for notification priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationRequest(BaseModel):
    """Model for notification request."""
    user_id: UUID = Field(..., description="User ID to send notification to")
    channel_id: Optional[str] = Field(None, description="Slack channel ID or user Slack ID")
    notification_type: NotificationType = Field(..., description="Type of notification")
    message_content: str = Field(..., description="Message content to send")
    priority: Priority = Field(default=Priority.NORMAL, description="Priority level of notification")
    metadata: Optional[dict] = Field(None, description="Additional metadata for the notification")


class NotificationResponse(BaseModel):
    """Response model for notification operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    notification_id: Optional[UUID] = Field(None, description="ID of the notification if created")
    delivery_status: Optional[DeliveryStatus] = Field(None, description="Current delivery status")


class NotificationLogEntry(BaseModel):
    """Model representing a notification log entry in the database."""
    id: UUID = Field(..., description="Unique notification ID")
    user_id: UUID = Field(..., description="User ID the notification was sent to")
    notification_type: NotificationType = Field(..., description="Type of notification")
    message_content: str = Field(..., description="Message content that was sent")
    channel_id: Optional[str] = Field(None, description="Slack channel ID or user Slack ID")
    slack_message_id: Optional[str] = Field(None, description="Slack message ID if delivered")
    delivery_status: DeliveryStatus = Field(..., description="Current delivery status")
    priority: Priority = Field(default=Priority.NORMAL, description="Priority level of notification")
    metadata: Optional[dict] = Field(None, description="Additional metadata for the notification")
    created_at: datetime = Field(..., description="When the notification was created")
    sent_at: Optional[datetime] = Field(None, description="When the notification was sent")
    delivered_at: Optional[datetime] = Field(None, description="When the notification was delivered")
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")
    retry_count: Optional[int] = Field(0, description="Number of retry attempts")


class NotificationHistoryResponse(BaseModel):
    """Response model for notification history."""
    notifications: List[NotificationLogEntry] = Field(..., description="List of notification log entries")
    total_count: int = Field(..., description="Total count of notifications matching filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class TriggerRequest(BaseModel):
    """Model for trigger notification request."""
    user_id: UUID = Field(..., description="User ID to send notification to")
    website_id: UUID = Field(..., description="Website ID related to the event")
    channel_id: Optional[str] = Field(None, description="Slack channel ID where notification should be sent")
    event_type: NotificationType = Field(..., description="Type of event that triggered the notification")
    context: Optional[dict] = Field(None, description="Additional context data for message formatting")


class TriggerResponse(BaseModel):
    """Response model for trigger operations."""
    success: bool = Field(..., description="Whether the trigger was successful")
    message: str = Field(..., description="Status message")
    notification_id: Optional[UUID] = Field(None, description="ID of the notification if created")
    event_type: NotificationType = Field(..., description="Type of event that was triggered")
    delivery_status: Optional[DeliveryStatus] = Field(None, description="Current delivery status")
