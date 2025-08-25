#!/usr/bin/env python3
"""
Test script to verify trigger metadata is being saved correctly.
Run this to debug metadata issues.
"""

import asyncio
import os
import sys
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.notification_models import NotificationType, Priority, DeliveryStatus
from services.trigger_service import NotificationTriggerService
from services.notification_service import NotificationService
from repository.notification_repository import NotificationRepository

class MockSlackService:
    """Mock Slack service for testing."""
    
    async def get_integration_status(self, user_id: str):
        return {
            "connected": True,
            "channel_id": "C1234567890"
        }
    
    async def send_message(self, user_id: str, message: str, channel_id: str):
        print(f"📤 Mock Slack: Sending message to {channel_id}")
        print(f"   Message: {message}")
        return MagicMock(success=True, slack_message_id="msg_123")

class MockNotificationRepository:
    """Mock repository that captures metadata for inspection."""
    
    def __init__(self):
        self.saved_logs = []
        self.status_updates = []
    
    async def save_notification_log(self, **kwargs):
        notification_id = uuid4()
        log_entry = {
            "notification_id": notification_id,
            **kwargs
        }
        self.saved_logs.append(log_entry)
        
        print(f"💾 Repository: Saving notification log")
        print(f"   ID: {notification_id}")
        print(f"   Type: {kwargs.get('notification_type')}")
        print(f"   Website ID: {kwargs.get('website_id')}")
        
        metadata = kwargs.get('metadata')
        if metadata:
            print(f"   ✅ Metadata saved:")
            for key, value in metadata.items():
                print(f"      - {key}: {value}")
        else:
            print(f"   ❌ No metadata provided")
        
        return notification_id
    
    async def update_notification_status(self, notification_id, delivery_status, **kwargs):
        update_entry = {
            "notification_id": notification_id,
            "delivery_status": delivery_status,
            **kwargs
        }
        self.status_updates.append(update_entry)
        
        print(f"🔄 Repository: Updating notification status")
        print(f"   ID: {notification_id}")
        print(f"   Status: {delivery_status}")
        print(f"   Note: Metadata column is NOT modified during status updates")
        
        return True

async def test_trigger_metadata_flow():
    """Test the complete trigger metadata flow."""
    
    print("🧪 Testing Trigger Metadata Flow")
    print("=" * 50)
    
    # Setup mocks
    mock_repo = MockNotificationRepository()
    mock_slack = MockSlackService()
    
    # Create services
    notification_service = NotificationService(
        repository=mock_repo,
        slack_service=mock_slack
    )
    
    trigger_service = NotificationTriggerService(notification_service)
    
    # Test data
    user_id = uuid4()
    website_id = uuid4()
    context = {
        "website_name": "example.com",
        "visibility_score": 85,
        "insights_count": 12
    }
    
    print(f"\n📋 Test Parameters:")
    print(f"   User ID: {user_id}")
    print(f"   Website ID: {website_id}")
    print(f"   Event Type: AI_VISIBILITY")
    print(f"   Context: {context}")
    
    print(f"\n🚀 Triggering AI Visibility notification...")
    
    # Trigger the notification
    result = await trigger_service.handle_event_trigger(
        user_id=user_id,
        website_id=website_id,
        event_type=NotificationType.AI_VISIBILITY,
        context=context,
        channel_id="C1234567890"
    )
    
    print(f"\n📊 Results:")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    print(f"   Notification ID: {result.notification_id}")
    print(f"   Delivery Status: {result.delivery_status}")
    
    print(f"\n🔍 Repository Inspection:")
    print(f"   Saved logs: {len(mock_repo.saved_logs)}")
    print(f"   Status updates: {len(mock_repo.status_updates)}")
    
    if mock_repo.saved_logs:
        saved_log = mock_repo.saved_logs[0]
        metadata = saved_log.get('metadata')
        
        if metadata:
            print(f"\n✅ SUCCESS: Metadata was saved!")
            print(f"   Trigger source: {metadata.get('trigger_source')}")
            print(f"   Event type: {metadata.get('event_type')}")
            print(f"   Website ID: {metadata.get('website_id')}")
            print(f"   Event context: {metadata.get('event_context')}")
            print(f"   Template used: {metadata.get('template_used')}")
        else:
            print(f"\n❌ PROBLEM: No metadata found in saved log!")
    
    print(f"\n💡 Key Points:")
    print(f"   1. Metadata is saved during initial save_notification_log() call")
    print(f"   2. Status updates do NOT modify the metadata column")
    print(f"   3. Metadata should persist even after status changes to DELIVERED")
    
    return result

async def test_metadata_structure():
    """Test the metadata structure created by trigger service."""
    
    print(f"\n🔬 Testing Metadata Structure")
    print("=" * 30)
    
    # Create trigger service
    mock_notification_service = AsyncMock()
    trigger_service = NotificationTriggerService(mock_notification_service)
    
    # Test context
    context = {
        "website_name": "test-site.com",
        "competitor_count": 5,
        "top_competitor": "rival.com"
    }
    
    # Get the template config (this is what creates metadata)
    template_config = trigger_service.message_templates.get(NotificationType.COMPETITOR_ANALYSIS)
    
    if template_config:
        print(f"✅ Template found for COMPETITOR_ANALYSIS")
        print(f"   Template: {template_config['template']}")
        print(f"   Priority: {template_config['priority']}")
    
    # This is the metadata structure that should be created
    expected_metadata = {
        "trigger_source": "automatic",
        "event_type": NotificationType.COMPETITOR_ANALYSIS.value,
        "website_id": str(uuid4()),
        "event_context": context,
        "template_used": template_config.get("template", "fallback") if template_config else "fallback"
    }
    
    print(f"\n📋 Expected Metadata Structure:")
    for key, value in expected_metadata.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    print("🔧 Trigger Metadata Debug Tool")
    print("This will help identify why metadata might not be appearing")
    print()
    
    asyncio.run(test_trigger_metadata_flow())
    asyncio.run(test_metadata_structure())
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Run this script to see if metadata is being created")
    print(f"   2. Check your database query - make sure you're selecting the 'metadata' column")
    print(f"   3. Verify your Supabase table has a 'metadata' JSONB column")
    print(f"   4. Check if there are any database constraints preventing JSONB storage")
