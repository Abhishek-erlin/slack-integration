"""
Notification trigger service for event-based notifications.
Following the 3-layer architecture pattern.
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from models.notification_models import (
    NotificationType,
    Priority,
    TriggerResponse,
    DeliveryStatus
)
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class NotificationTriggerService:
    """Service class for handling event-based notification triggers."""
    
    def __init__(self, notification_service: NotificationService):
        """
        Initialize trigger service with notification service dependency.
        
        Args:
            notification_service: NotificationService instance for sending notifications
        """
        self.notification_service = notification_service
        
        # Message templates for different event types
        self.message_templates = {
            NotificationType.AUDIT_COMPLETE: {
                "template": "Your {audit_type} audit for {website_name} is complete with a score of {score}/100.",
                "fallback": "Your audit is complete. Check your dashboard for details.",
                "priority": Priority.NORMAL
            },
            NotificationType.AI_VISIBILITY: {
                "template": "🤖 AI Visibility analysis for {website_name} is complete! Your visibility score is {visibility_score}/100 with {insights_count} insights available.",
                "fallback": "Your AI visibility analysis is ready! Check your dashboard for insights.",
                "priority": Priority.NORMAL
            },
            NotificationType.COMPETITOR_ANALYSIS: {
                "template": "🔍 See who your competitors are! Our analysis for {website_name} is ready!! We analyzed {competitor_count} competitors and found valuable insights.",
                "fallback": "Your competitor analysis is complete! Discover who your competitors are.",
                "priority": Priority.NORMAL
            },
            NotificationType.SYSTEM_ALERT: {
                "template": "{alert_message}",
                "fallback": "System alert: Please check your dashboard for details.",
                "priority": Priority.HIGH
            }
        }
    
    async def handle_event_trigger(
        self,
        user_id: UUID,
        website_id: UUID,
        event_type: NotificationType,
        channel_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> TriggerResponse:
        """
        Handle an event trigger and send appropriate notification.
        
        Args:
            user_id: User ID to send notification to
            website_id: Website ID related to the event
            event_type: Type of event that triggered the notification
            channel_id: Optional Slack channel ID where notification should be sent
            context: Optional context data for message formatting
            
        Returns:
            TriggerResponse with success status and details
        """
        try:
            logger.info(f"Processing event trigger: {event_type} for user {user_id}, website {website_id}")
            
            # Get message template configuration for this event type
            template_config = self.message_templates.get(event_type)
            if not template_config:
                logger.warning(f"No template configuration found for event type: {event_type}")
                return TriggerResponse(
                    success=False,
                    message=f"No template configuration found for event type: {event_type}",
                    event_type=event_type,
                    delivery_status=DeliveryStatus.FAILED
                )
            
            # Format the message using context data
            message_content = self._format_message(template_config, context or {})
            priority = template_config.get("priority", Priority.NORMAL)
            
            # Prepare metadata with trigger information
            metadata = {
                "trigger_source": "automatic",
                "event_type": event_type.value,
                "website_id": str(website_id),
                "event_context": context or {},
                "template_used": template_config.get("template", "fallback")
            }
            
            # Send the notification using existing notification service
            notification_result = await self.notification_service.send_notification(
                user_id=user_id,
                message_content=message_content,
                notification_type=event_type,
                channel_id=channel_id,
                priority=priority,
                metadata=metadata,
                website_id=website_id
            )
            
            if notification_result.success:
                logger.info(f"Successfully triggered notification {notification_result.notification_id} for event {event_type}")
                return TriggerResponse(
                    success=True,
                    message="Event trigger processed successfully",
                    notification_id=notification_result.notification_id,
                    event_type=event_type,
                    delivery_status=notification_result.delivery_status
                )
            else:
                logger.error(f"Failed to send notification for event {event_type}: {notification_result.message}")
                return TriggerResponse(
                    success=False,
                    message=f"Failed to send notification: {notification_result.message}",
                    notification_id=notification_result.notification_id,
                    event_type=event_type,
                    delivery_status=notification_result.delivery_status
                )
                
        except Exception as e:
            logger.error(f"Error processing event trigger {event_type}: {str(e)}")
            return TriggerResponse(
                success=False,
                message=f"Error processing event trigger: {str(e)}",
                event_type=event_type,
                delivery_status=DeliveryStatus.FAILED
            )
    
    def _format_message(self, template_config: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Format a message template using context variables.
        
        Args:
            template_config: Template configuration with template and fallback
            context: Context data for formatting
            
        Returns:
            Formatted message string
        """
        try:
            template = template_config.get("template", "")
            formatted_message = template.format(**context)
            
            # Add additional formatting for common patterns
            if "issues_summary" not in context and "issues_count" in context:
                issues_count = context.get("issues_count", 0)
                if issues_count > 0:
                    formatted_message += f" Found {issues_count} issue{'s' if issues_count != 1 else ''} to review."
                else:
                    formatted_message += " No issues found - great job!"
            
            return formatted_message
            
        except KeyError as e:
            logger.warning(f"Missing context key in template formatting: {e}")
            # Fall back to the fallback message
            fallback = template_config.get("fallback", "Notification update available")
            
            # Try to add basic context to fallback if available
            if "website_name" in context:
                fallback += f" for {context['website_name']}"
            
            return fallback
        except Exception as e:
            logger.error(f"Error formatting message template: {e}")
            return template_config.get("fallback", "Notification update available")
    
    def get_supported_event_types(self) -> list:
        """
        Get list of supported event types.
        
        Returns:
            List of supported NotificationType values
        """
        return list(self.message_templates.keys())
    
    def update_message_template(
        self, 
        event_type: NotificationType, 
        template: str, 
        fallback: str = None, 
        priority: Priority = None
    ) -> bool:
        """
        Update message template for a specific event type.
        
        Args:
            event_type: Event type to update template for
            template: New message template
            fallback: Optional fallback message
            priority: Optional priority level
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            if event_type not in self.message_templates:
                self.message_templates[event_type] = {}
            
            self.message_templates[event_type]["template"] = template
            
            if fallback:
                self.message_templates[event_type]["fallback"] = fallback
                
            if priority:
                self.message_templates[event_type]["priority"] = priority
                
            logger.info(f"Updated message template for event type: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating message template: {e}")
            return False
