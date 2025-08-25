"""
Simplified tests for the Notification Trigger Service that avoid database dependencies.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from services.trigger_service import NotificationTriggerService
from models.notification_models import (
    NotificationType,
    Priority,
    DeliveryStatus,
    NotificationResponse,
    TriggerResponse
)


class TestTriggerServiceSimple:
    """Simplified test cases for NotificationTriggerService."""
    
    @pytest.fixture
    def mock_notification_service(self):
        """Create a mock notification service."""
        mock_service = Mock()
        mock_service.send_notification = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def trigger_service(self, mock_notification_service):
        """Create a trigger service instance with mocked dependencies."""
        return NotificationTriggerService(mock_notification_service)
    
    @pytest.mark.asyncio
    async def test_audit_complete_trigger(self, trigger_service, mock_notification_service):
        """Test audit complete trigger with proper mocking."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=True,
            message="Notification sent successfully",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        
        user_id = uuid4()
        website_id = uuid4()
        context = {
            "audit_type": "technical",
            "website_name": "example.com",
            "score": 85,
            "issues_count": 3
        }
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.AUDIT_COMPLETE,
            context=context
        )
        
        # Assert
        assert result.success is True
        assert result.event_type == NotificationType.AUDIT_COMPLETE
        assert result.delivery_status == DeliveryStatus.DELIVERED
        
        # Verify notification service was called with correct parameters
        mock_notification_service.send_notification.assert_called_once()
        call_args = mock_notification_service.send_notification.call_args
        assert call_args[1]['user_id'] == user_id
        assert call_args[1]['website_id'] == website_id
        assert call_args[1]['notification_type'] == NotificationType.AUDIT_COMPLETE
        assert "technical audit for example.com is complete with a score of 85/100" in call_args[1]['message_content']
    
    @pytest.mark.asyncio
    async def test_system_alert_trigger(self, trigger_service, mock_notification_service):
        """Test system alert trigger."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=True,
            message="Alert sent successfully",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        
        user_id = uuid4()
        website_id = uuid4()
        context = {"alert_message": "System maintenance scheduled"}
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.SYSTEM_ALERT,
            context=context
        )
        
        # Assert
        assert result.success is True
        assert result.event_type == NotificationType.SYSTEM_ALERT
        
        # Verify high priority was set
        call_args = mock_notification_service.send_notification.call_args
        assert call_args[1]['priority'] == Priority.HIGH
        assert "System maintenance scheduled" in call_args[1]['message_content']
    
    @pytest.mark.asyncio
    async def test_notification_service_failure(self, trigger_service, mock_notification_service):
        """Test handling of notification service failure."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=False,
            message="Failed to send notification",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.FAILED
        )
        
        user_id = uuid4()
        website_id = uuid4()
        context = {"website_name": "example.com"}
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.AUDIT_COMPLETE,
            context=context
        )
        
        # Assert
        assert result.success is False
        assert result.delivery_status == DeliveryStatus.FAILED
        assert "Failed to send notification" in result.message
    
    def test_message_formatting(self, trigger_service):
        """Test message formatting functionality."""
        template_config = {
            "template": "Your {audit_type} audit for {website_name} is complete with a score of {score}/100.",
            "fallback": "Your audit is complete."
        }
        
        context = {
            "audit_type": "technical",
            "website_name": "example.com",
            "score": 85
        }
        
        result = trigger_service._format_message(template_config, context)
        expected = "Your technical audit for example.com is complete with a score of 85/100. Found 0 issues to review."
        
        assert "technical audit for example.com is complete with a score of 85/100" in result
    
    def test_supported_event_types(self, trigger_service):
        """Test getting supported event types."""
        supported_events = trigger_service.get_supported_event_types()
        
        assert NotificationType.AUDIT_COMPLETE in supported_events
        assert NotificationType.AI_VISIBILITY in supported_events
        assert NotificationType.COMPETITOR_ANALYSIS in supported_events
        assert NotificationType.SYSTEM_ALERT in supported_events
        assert len(supported_events) == 4
    
    def test_template_update(self, trigger_service):
        """Test updating message templates."""
        new_template = "Custom template for {event_type}"
        
        result = trigger_service.update_message_template(
            event_type=NotificationType.AUDIT_COMPLETE,
            template=new_template,
            fallback="Custom fallback",
            priority=Priority.HIGH
        )
        
        assert result is True
        
        # Verify the template was updated
        template_config = trigger_service.message_templates[NotificationType.AUDIT_COMPLETE]
        assert template_config["template"] == new_template
        assert template_config["fallback"] == "Custom fallback"
        assert template_config["priority"] == Priority.HIGH


def test_trigger_service_initialization():
    """Test that trigger service initializes correctly."""
    mock_notification_service = Mock()
    trigger_service = NotificationTriggerService(mock_notification_service)
    
    assert trigger_service.notification_service == mock_notification_service
    assert len(trigger_service.message_templates) == 4
    assert NotificationType.AUDIT_COMPLETE in trigger_service.message_templates


if __name__ == "__main__":
    pytest.main([__file__])
