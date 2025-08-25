"""
Tests for the Notification Trigger Service.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID

from services.trigger_service import NotificationTriggerService
from services.notification_service import NotificationService
from models.notification_models import (
    NotificationType,
    Priority,
    DeliveryStatus,
    NotificationResponse,
    TriggerResponse
)


class TestNotificationTriggerService:
    """Test cases for NotificationTriggerService."""
    
    @pytest.fixture
    def mock_notification_service(self):
        """Create a mock notification service."""
        mock_service = Mock(spec=NotificationService)
        mock_service.send_notification = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def trigger_service(self, mock_notification_service):
        """Create a trigger service instance with mocked dependencies."""
        return NotificationTriggerService(mock_notification_service)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid4()
    
    @pytest.fixture
    def sample_website_id(self):
        """Sample website ID for testing."""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_handle_audit_complete_trigger_success(
        self, trigger_service, mock_notification_service, sample_user_id, sample_website_id
    ):
        """Test successful audit complete trigger."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=True,
            message="Notification sent successfully",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        
        context = {
            "audit_type": "technical",
            "website_name": "example.com",
            "score": 85,
            "issues_count": 3
        }
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=sample_user_id,
            website_id=sample_website_id,
            event_type=NotificationType.AUDIT_COMPLETE,
            context=context
        )
        
        # Assert
        assert result.success is True
        assert result.event_type == NotificationType.AUDIT_COMPLETE
        assert result.delivery_status == DeliveryStatus.DELIVERED
        assert result.notification_id is not None
        
        # Verify notification service was called correctly
        mock_notification_service.send_notification.assert_called_once()
        call_args = mock_notification_service.send_notification.call_args
        assert call_args[1]['user_id'] == sample_user_id
        assert call_args[1]['website_id'] == sample_website_id
        assert call_args[1]['notification_type'] == NotificationType.AUDIT_COMPLETE
        assert "technical audit for example.com is complete with a score of 85/100" in call_args[1]['message_content']
    
    @pytest.mark.asyncio
    async def test_handle_ai_visibility_trigger_success(
        self, trigger_service, mock_notification_service, sample_user_id, sample_website_id
    ):
        """Test successful AI visibility trigger."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=True,
            message="Notification sent successfully",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        
        context = {
            "website_name": "example.com",
            "visibility_score": 78,
            "insights_count": 12
        }
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=sample_user_id,
            website_id=sample_website_id,
            event_type=NotificationType.AI_VISIBILITY,
            context=context
        )
        
        # Assert
        assert result.success is True
        assert result.event_type == NotificationType.AI_VISIBILITY
        
        # Verify message content
        call_args = mock_notification_service.send_notification.call_args
        assert "AI Visibility analysis for example.com is complete" in call_args[1]['message_content']
        assert "visibility score is 78/100" in call_args[1]['message_content']
        assert call_args[1]['priority'] == Priority.NORMAL
    
    @pytest.mark.asyncio
    async def test_handle_competitor_analysis_trigger_success(
        self, trigger_service, mock_notification_service, sample_user_id, sample_website_id
    ):
        """Test successful competitor analysis trigger."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=True,
            message="Notification sent successfully",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        
        context = {
            "website_name": "example.com",
            "competitor_count": 5,
            "top_competitor": "competitor-site.com"
        }
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=sample_user_id,
            website_id=sample_website_id,
            event_type=NotificationType.COMPETITOR_ANALYSIS,
            context=context
        )
        
        # Assert
        assert result.success is True
        assert result.event_type == NotificationType.COMPETITOR_ANALYSIS
        
        # Verify message content
        call_args = mock_notification_service.send_notification.call_args
        assert "See who your competitors are! Our analysis for example.com is ready!!" in call_args[1]['message_content']
        assert "analyzed 5 competitors" in call_args[1]['message_content']
        assert call_args[1]['priority'] == Priority.NORMAL
    
    @pytest.mark.asyncio
    async def test_handle_system_alert_trigger_success(
        self, trigger_service, mock_notification_service, sample_user_id, sample_website_id
    ):
        """Test successful system alert trigger."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=True,
            message="Notification sent successfully",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        
        context = {
            "alert_message": "System maintenance scheduled for tonight"
        }
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=sample_user_id,
            website_id=sample_website_id,
            event_type=NotificationType.SYSTEM_ALERT,
            context=context
        )
        
        # Assert
        assert result.success is True
        assert result.event_type == NotificationType.SYSTEM_ALERT
        
        # Verify message content and priority
        call_args = mock_notification_service.send_notification.call_args
        assert "System maintenance scheduled for tonight" in call_args[1]['message_content']
        assert call_args[1]['priority'] == Priority.HIGH
    
    @pytest.mark.asyncio
    async def test_handle_trigger_with_channel_id(
        self, trigger_service, mock_notification_service, sample_user_id, sample_website_id
    ):
        """Test trigger with specific channel ID."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=True,
            message="Notification sent successfully",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        
        channel_id = "C1234567890"
        context = {"website_name": "example.com"}
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=sample_user_id,
            website_id=sample_website_id,
            event_type=NotificationType.INTEGRATION_STATUS,
            channel_id=channel_id,
            context=context
        )
        
        # Assert
        assert result.success is True
        
        # Verify channel_id was passed correctly
        call_args = mock_notification_service.send_notification.call_args
        assert call_args[1]['channel_id'] == channel_id
    
    @pytest.mark.asyncio
    async def test_handle_trigger_notification_service_failure(
        self, trigger_service, mock_notification_service, sample_user_id, sample_website_id
    ):
        """Test handling of notification service failure."""
        # Arrange
        mock_notification_service.send_notification.return_value = NotificationResponse(
            success=False,
            message="Failed to send notification",
            notification_id=uuid4(),
            delivery_status=DeliveryStatus.FAILED
        )
        
        context = {"website_name": "example.com"}
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=sample_user_id,
            website_id=sample_website_id,
            event_type=NotificationType.AUDIT_COMPLETE,
            context=context
        )
        
        # Assert
        assert result.success is False
        assert result.event_type == NotificationType.AUDIT_COMPLETE
        assert result.delivery_status == DeliveryStatus.FAILED
        assert "Failed to send notification" in result.message
    
    @pytest.mark.asyncio
    async def test_handle_trigger_exception(
        self, trigger_service, mock_notification_service, sample_user_id, sample_website_id
    ):
        """Test handling of exceptions during trigger processing."""
        # Arrange
        mock_notification_service.send_notification.side_effect = Exception("Database connection failed")
        
        context = {"website_name": "example.com"}
        
        # Act
        result = await trigger_service.handle_event_trigger(
            user_id=sample_user_id,
            website_id=sample_website_id,
            event_type=NotificationType.AUDIT_COMPLETE,
            context=context
        )
        
        # Assert
        assert result.success is False
        assert result.event_type == NotificationType.AUDIT_COMPLETE
        assert result.delivery_status == DeliveryStatus.FAILED
        assert "Error processing event trigger" in result.message
    
    def test_format_message_with_complete_context(self, trigger_service):
        """Test message formatting with complete context."""
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
        
        assert result == "Your technical audit for example.com is complete with a score of 85/100."
    
    def test_format_message_with_missing_context_key(self, trigger_service):
        """Test message formatting with missing context key."""
        template_config = {
            "template": "Your {audit_type} audit for {website_name} is complete.",
            "fallback": "Your audit is complete."
        }
        
        context = {
            "audit_type": "technical"
            # Missing website_name
        }
        
        result = trigger_service._format_message(template_config, context)
        
        assert result == "Your audit is complete."
    
    def test_format_message_with_issues_count(self, trigger_service):
        """Test message formatting with issues count enhancement."""
        template_config = {
            "template": "Your {audit_type} audit for {website_name} is complete with a score of {score}/100.",
            "fallback": "Your audit is complete."
        }
        
        context = {
            "audit_type": "technical",
            "website_name": "example.com",
            "score": 85,
            "issues_count": 3
        }
        
        result = trigger_service._format_message(template_config, context)
        
        assert "Found 3 issues to review" in result
    
    def test_format_message_with_zero_issues(self, trigger_service):
        """Test message formatting with zero issues."""
        template_config = {
            "template": "Your {audit_type} audit for {website_name} is complete with a score of {score}/100.",
            "fallback": "Your audit is complete."
        }
        
        context = {
            "audit_type": "technical",
            "website_name": "example.com",
            "score": 95,
            "issues_count": 0
        }
        
        result = trigger_service._format_message(template_config, context)
        
        assert "No issues found - great job!" in result
    
    def test_get_supported_event_types(self, trigger_service):
        """Test getting supported event types."""
        supported_events = trigger_service.get_supported_event_types()
        
        assert NotificationType.AUDIT_COMPLETE in supported_events
        assert NotificationType.AI_VISIBILITY in supported_events
        assert NotificationType.COMPETITOR_ANALYSIS in supported_events
        assert NotificationType.SYSTEM_ALERT in supported_events
        assert len(supported_events) == 4
    
    def test_update_message_template(self, trigger_service):
        """Test updating message template."""
        new_template = "Custom template for {event_type}"
        new_fallback = "Custom fallback message"
        
        result = trigger_service.update_message_template(
            event_type=NotificationType.AUDIT_COMPLETE,
            template=new_template,
            fallback=new_fallback,
            priority=Priority.HIGH
        )
        
        assert result is True
        
        # Verify the template was updated
        template_config = trigger_service.message_templates[NotificationType.AUDIT_COMPLETE]
        assert template_config["template"] == new_template
        assert template_config["fallback"] == new_fallback
        assert template_config["priority"] == Priority.HIGH


class TestTriggerServiceIntegration:
    """Integration tests for trigger service with real dependencies."""
    
    @pytest.mark.asyncio
    async def test_trigger_service_with_real_notification_service(self):
        """Test trigger service with real notification service (mocked at lower level)."""
        with patch('services.notification_service.NotificationService') as mock_ns_class:
            # Setup mock notification service
            mock_ns_instance = Mock()
            mock_ns_instance.send_notification = AsyncMock(return_value=NotificationResponse(
                success=True,
                message="Success",
                notification_id=uuid4(),
                delivery_status=DeliveryStatus.DELIVERED
            ))
            mock_ns_class.return_value = mock_ns_instance
            
            # Create trigger service
            trigger_service = NotificationTriggerService(mock_ns_instance)
            
            # Test trigger
            result = await trigger_service.handle_event_trigger(
                user_id=uuid4(),
                website_id=uuid4(),
                event_type=NotificationType.AUDIT_COMPLETE,
                context={"website_name": "test.com", "score": 90}
            )
            
            assert result.success is True
            assert result.event_type == NotificationType.AUDIT_COMPLETE


if __name__ == "__main__":
    pytest.main([__file__])
