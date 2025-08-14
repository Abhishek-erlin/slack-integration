"""
Unit tests for notification system.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from models.notification_models import (
    NotificationType,
    DeliveryStatus,
    Priority,
    NotificationRequest,
    NotificationResponse
)
from services.notification_service import NotificationService
from repository.notification_repository import NotificationRepository


@pytest.fixture
def mock_notification_repository():
    """Mock notification repository for testing."""
    repository = AsyncMock(spec=NotificationRepository)
    
    # Mock save_notification_log
    repository.save_notification_log.return_value = uuid.uuid4()
    
    # Mock update_notification_status
    repository.update_notification_status.return_value = True
    
    # Mock get_notification_history
    repository.get_notification_history.return_value = {
        "notifications": [],
        "total_count": 0,
        "page": 1,
        "page_size": 20
    }
    
    return repository


@pytest.fixture
def mock_slack_service():
    """Mock slack service for testing."""
    slack_service = AsyncMock()
    
    # Mock get_integration_status
    slack_service.get_integration_status.return_value = {
        "connected": True,
        "team_name": "Test Team",
        "slack_user_id": "U12345",
        "channel_id": "C12345"
    }
    
    # Mock send_message
    slack_service.send_message.return_value = MagicMock(
        success=True,
        message="Message sent successfully",
        slack_message_id="1234567890.123456"
    )
    
    return slack_service


@pytest.mark.asyncio
async def test_send_notification_success(mock_notification_repository, mock_slack_service):
    """Test successful notification sending."""
    # Arrange
    with patch('services.notification_service.NotificationRepository', return_value=mock_notification_repository), \
         patch('services.notification_service.SlackService', return_value=mock_slack_service):
        
        service = NotificationService()
        user_id = uuid.uuid4()
        channel_id = "C12345"
        message = "Test notification"
        notification_type = NotificationType.SYSTEM_ALERT
        metadata = {"test": "data"}
        
        # Act
        response = await service.send_notification(
            user_id=user_id,
            message_content=message,
            notification_type=notification_type,
            channel_id=channel_id,
            metadata=metadata
        )
        
        # Assert
        assert response.success is True
        assert response.delivery_status == DeliveryStatus.DELIVERED
        mock_notification_repository.save_notification_log.assert_called_once()
        mock_notification_repository.update_notification_status.assert_called_with(
            notification_id=mock_notification_repository.save_notification_log.return_value,
            delivery_status=DeliveryStatus.DELIVERED,
            slack_message_id=mock_slack_service.send_message.return_value.slack_message_id
        )
        mock_slack_service.send_message.assert_called_once_with(
            user_id=str(user_id),
            message=message,
            channel_id=channel_id
        )


@pytest.mark.asyncio
async def test_send_notification_no_integration(mock_notification_repository, mock_slack_service):
    """Test notification sending with no Slack integration."""
    # Arrange
    mock_slack_service.get_integration_status.return_value = {
        "connected": False,
        "message": "No Slack integration found"
    }
    
    with patch('services.notification_service.NotificationRepository', return_value=mock_notification_repository), \
         patch('services.notification_service.SlackService', return_value=mock_slack_service):
        
        service = NotificationService()
        user_id = uuid.uuid4()
        channel_id = "C12345"
        message = "Test notification"
        notification_type = NotificationType.SYSTEM_ALERT
        metadata = {"test": "data"}
        
        # Act
        response = await service.send_notification(
            user_id=user_id,
            message_content=message,
            notification_type=notification_type,
            channel_id=channel_id,
            metadata=metadata
        )
        
        # Assert
        assert response.success is False
        assert response.delivery_status == DeliveryStatus.FAILED
        mock_notification_repository.save_notification_log.assert_called_once_with(
            user_id=user_id,
            notification_type=notification_type,
            message_content=message,
            channel_id=channel_id,
            priority=Priority.NORMAL,
            delivery_status=DeliveryStatus.FAILED,
            metadata=metadata
        )
        mock_slack_service.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_notification_slack_failure(mock_notification_repository, mock_slack_service):
    """Test notification sending with Slack API failure."""
    # Arrange
    mock_slack_service.send_message.return_value = MagicMock(
        success=False,
        message="Failed to send message: channel_not_found"
    )
    
    with patch('services.notification_service.NotificationRepository', return_value=mock_notification_repository), \
         patch('services.notification_service.SlackService', return_value=mock_slack_service):
        
        service = NotificationService()
        user_id = uuid.uuid4()
        channel_id = "C12345"
        message = "Test notification"
        notification_type = NotificationType.SYSTEM_ALERT
        metadata = {"test": "data"}
        
        # Act
        response = await service.send_notification(
            user_id=user_id,
            message_content=message,
            notification_type=notification_type,
            channel_id=channel_id,
            metadata=metadata
        )
        
        # Assert
        assert response.success is False
        assert response.delivery_status == DeliveryStatus.FAILED
        mock_notification_repository.update_notification_status.assert_called_with(
            notification_id=mock_notification_repository.save_notification_log.return_value,
            delivery_status=DeliveryStatus.FAILED,
            error_message="Failed to send message: channel_not_found"
        )


@pytest.mark.asyncio
async def test_get_notification_history(mock_notification_repository):
    """Test retrieving notification history."""
    # Arrange
    mock_notification_repository.get_notification_history.return_value = {
        "notifications": [
            MagicMock(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                channel_id="C12345",
                notification_type=NotificationType.SYSTEM_ALERT,
                message_content="Test notification",
                priority=Priority.NORMAL,
                delivery_status=DeliveryStatus.DELIVERED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                delivered_at=datetime.utcnow(),
                error_message=None
            )
        ],
        "total_count": 1,
        "page": 1,
        "page_size": 20
    }
    
    with patch('services.notification_service.NotificationRepository', return_value=mock_notification_repository):
        service = NotificationService()
        user_id = uuid.uuid4()
        
        # Act
        result = await service.get_notification_history(user_id=user_id)
        
        # Assert
        assert result["total_count"] == 1
        assert len(result["notifications"]) == 1
        mock_notification_repository.get_notification_history.assert_called_once_with(
            user_id=user_id,
            notification_type=None,
            delivery_status=None,
            page=1,
            page_size=20
        )
