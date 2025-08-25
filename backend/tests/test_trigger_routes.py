"""
Tests for the Trigger API Routes.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
import json

from main import app
from models.notification_models import (
    NotificationType,
    DeliveryStatus,
    TriggerResponse
)


class TestTriggerRoutes:
    """Test cases for trigger API routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())
    
    @pytest.fixture
    def sample_website_id(self):
        """Sample website ID for testing."""
        return str(uuid4())
    
    @pytest.fixture
    def valid_trigger_request(self, sample_user_id, sample_website_id):
        """Valid trigger request payload."""
        return {
            "user_id": sample_user_id,
            "website_id": sample_website_id,
            "channel_id": "C1234567890",
            "event_type": "audit_complete",
            "context": {
                "audit_type": "technical",
                "website_name": "example.com",
                "score": 85,
                "issues_count": 3
            }
        }
    
    @patch('routes.trigger_routes.get_notification_service')
    @patch('routes.trigger_routes.get_trigger_service')
    def test_send_trigger_notification_success_immediate(self, mock_get_trigger_service, mock_get_notification_service, client, valid_trigger_request):
        """Test successful immediate trigger notification (system alert)."""
        # Arrange
        mock_service = Mock()
        mock_service.handle_event_trigger = AsyncMock(return_value=TriggerResponse(
            success=True,
            message="Event trigger processed successfully",
            notification_id=uuid4(),
            event_type=NotificationType.SYSTEM_ALERT,
            delivery_status=DeliveryStatus.DELIVERED
        ))
        mock_service.get_supported_event_types.return_value = [
            NotificationType.AUDIT_COMPLETE,
            NotificationType.SYSTEM_ALERT
        ]
        mock_get_trigger_service.return_value = mock_service
        
        # Modify request for system alert (immediate processing)
        valid_trigger_request["event_type"] = "system_alert"
        valid_trigger_request["context"] = {"alert_message": "Test alert"}
        
        # Act
        response = client.post("/api/v1/triggers/send", json=valid_trigger_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_type"] == "system_alert"
        assert data["delivery_status"] == "delivered"
        
        # Verify service was called
        mock_service.handle_event_trigger.assert_called_once()
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_send_trigger_notification_success_background(self, mock_get_service, client, valid_trigger_request):
        """Test successful background trigger notification."""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_event_types.return_value = [
            NotificationType.AUDIT_COMPLETE,
            NotificationType.AUDIT_STARTED
        ]
        mock_get_service.return_value = mock_service
        
        # Act
        response = client.post("/api/v1/triggers/send", json=valid_trigger_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_type"] == "audit_complete"
        assert data["message"] == "Event trigger queued for processing"
        assert data["delivery_status"] is None  # Background processing
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_send_trigger_notification_missing_user_id(self, mock_get_service, client, valid_trigger_request):
        """Test trigger notification with missing user_id."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Remove user_id
        del valid_trigger_request["user_id"]
        
        # Act
        response = client.post("/api/v1/triggers/send", json=valid_trigger_request)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_send_trigger_notification_missing_website_id(self, mock_get_service, client, valid_trigger_request):
        """Test trigger notification with missing website_id."""
        # Arrange
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Remove website_id
        del valid_trigger_request["website_id"]
        
        # Act
        response = client.post("/api/v1/triggers/send", json=valid_trigger_request)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_send_trigger_notification_unsupported_event_type(self, mock_get_service, client, valid_trigger_request):
        """Test trigger notification with unsupported event type."""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_event_types.return_value = [
            NotificationType.AUDIT_COMPLETE
        ]
        mock_get_service.return_value = mock_service
        
        # Use unsupported event type
        valid_trigger_request["event_type"] = "unsupported_event"
        
        # Act
        response = client.post("/api/v1/triggers/send", json=valid_trigger_request)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported event type" in data["detail"]
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_send_trigger_notification_service_exception(self, mock_get_service, client, valid_trigger_request):
        """Test trigger notification with service exception."""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_event_types.return_value = [NotificationType.AUDIT_COMPLETE]
        mock_service.handle_event_trigger = AsyncMock(side_effect=Exception("Service error"))
        mock_get_service.return_value = mock_service
        
        # Modify for immediate processing to trigger exception
        valid_trigger_request["event_type"] = "system_alert"
        
        # Act
        response = client.post("/api/v1/triggers/send", json=valid_trigger_request)
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to process trigger" in data["detail"]
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_get_supported_events_success(self, mock_get_service, client):
        """Test getting supported events successfully."""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_event_types.return_value = [
            NotificationType.AUDIT_COMPLETE,
            NotificationType.AUDIT_STARTED,
            NotificationType.INTEGRATION_STATUS,
            NotificationType.SYSTEM_ALERT
        ]
        mock_get_service.return_value = mock_service
        
        # Act
        response = client.get("/api/v1/triggers/supported-events")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "supported_events" in data
        assert len(data["supported_events"]) == 4
        
        # Check event structure
        event = data["supported_events"][0]
        assert "event_type" in event
        assert "name" in event
        assert "description" in event
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_get_supported_events_service_exception(self, mock_get_service, client):
        """Test getting supported events with service exception."""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_event_types.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service
        
        # Act
        response = client.get("/api/v1/triggers/supported-events")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to retrieve supported events" in data["detail"]
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_test_trigger_success(self, mock_get_service, client, sample_user_id, sample_website_id):
        """Test trigger test endpoint successfully."""
        # Arrange
        mock_service = Mock()
        mock_service.handle_event_trigger = AsyncMock(return_value=TriggerResponse(
            success=True,
            message="Test trigger processed successfully",
            notification_id=uuid4(),
            event_type=NotificationType.AUDIT_COMPLETE,
            delivery_status=DeliveryStatus.DELIVERED
        ))
        mock_get_service.return_value = mock_service
        
        # Act
        response = client.post(
            "/api/v1/triggers/test",
            params={
                "user_id": sample_user_id,
                "website_id": sample_website_id,
                "event_type": "audit_complete",
                "channel_id": "C1234567890"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_type"] == "audit_complete"
        
        # Verify service was called with test context
        mock_service.handle_event_trigger.assert_called_once()
        call_args = mock_service.handle_event_trigger.call_args
        assert call_args[1]["context"]["website_name"] == "example.com"
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_test_trigger_exception(self, mock_get_service, client, sample_user_id, sample_website_id):
        """Test trigger test endpoint with exception."""
        # Arrange
        mock_service = Mock()
        mock_service.handle_event_trigger = AsyncMock(side_effect=Exception("Test error"))
        mock_get_service.return_value = mock_service
        
        # Act
        response = client.post(
            "/api/v1/triggers/test",
            params={
                "user_id": sample_user_id,
                "website_id": sample_website_id,
                "event_type": "audit_complete"
            }
        )
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to test trigger" in data["detail"]
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_health_check_success(self, mock_get_service, client):
        """Test health check endpoint successfully."""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_event_types.return_value = [
            NotificationType.AUDIT_COMPLETE,
            NotificationType.SYSTEM_ALERT
        ]
        mock_get_service.return_value = mock_service
        
        # Act
        response = client.get("/api/v1/triggers/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-trigger-service"
        assert data["components"]["trigger_service"] == "operational"
        assert data["components"]["supported_events_count"] == 2
    
    @patch('routes.trigger_routes.get_trigger_service')
    def test_health_check_failure(self, mock_get_service, client):
        """Test health check endpoint with failure."""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_event_types.side_effect = Exception("Health check error")
        mock_get_service.return_value = mock_service
        
        # Act
        response = client.get("/api/v1/triggers/health")
        
        # Assert
        assert response.status_code == 200  # Health endpoint should always return 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
    
    def test_trigger_request_validation(self, client):
        """Test trigger request validation."""
        # Test with invalid UUID format
        invalid_request = {
            "user_id": "invalid-uuid",
            "website_id": str(uuid4()),
            "event_type": "audit_complete"
        }
        
        response = client.post("/api/v1/triggers/send", json=invalid_request)
        assert response.status_code == 422
    
    def test_trigger_request_optional_fields(self, client, sample_user_id, sample_website_id):
        """Test trigger request with optional fields."""
        # Test minimal valid request (without channel_id and context)
        minimal_request = {
            "user_id": sample_user_id,
            "website_id": sample_website_id,
            "event_type": "audit_complete"
        }
        
        with patch('routes.trigger_routes.get_trigger_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_supported_event_types.return_value = [NotificationType.AUDIT_COMPLETE]
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/v1/triggers/send", json=minimal_request)
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])
