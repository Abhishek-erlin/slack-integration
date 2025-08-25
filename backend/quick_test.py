#!/usr/bin/env python3
"""
Quick test to verify new notification types work after migration.
"""

import asyncio
import sys
import os
from uuid import uuid4

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.notification_models import NotificationType
from services.trigger_service import NotificationTriggerService
from services.notification_service import NotificationService

async def test_new_notification_types():
    """Test that new notification types can be saved to database."""
    
    print("🧪 Testing New Notification Types After Migration")
    print("=" * 50)
    
    # Initialize services
    notification_service = NotificationService()
    trigger_service = NotificationTriggerService(notification_service)
    
    # Test data
    user_id = uuid4()
    website_id = uuid4()
    
    # Test AI_VISIBILITY
    print("\n📊 Testing AI_VISIBILITY...")
    try:
        result = await trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.AI_VISIBILITY,
            context={
                "website_name": "test-site.com",
                "visibility_score": 78,
                "insights_count": 12
            },
            channel_id="C1234567890"
        )
        
        if result.success:
            print(f"   ✅ SUCCESS: {result.message}")
            print(f"   📝 Notification ID: {result.notification_id}")
        else:
            print(f"   ❌ FAILED: {result.message}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test COMPETITOR_ANALYSIS
    print("\n🔍 Testing COMPETITOR_ANALYSIS...")
    try:
        result = await trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.COMPETITOR_ANALYSIS,
            context={
                "website_name": "test-site.com",
                "competitor_count": 5,
                "top_competitor": "rival.com"
            },
            channel_id="C1234567890"
        )
        
        if result.success:
            print(f"   ✅ SUCCESS: {result.message}")
            print(f"   📝 Notification ID: {result.notification_id}")
        else:
            print(f"   ❌ FAILED: {result.message}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print(f"\n💡 If you see SUCCESS messages above, the database constraint issue is fixed!")
    print(f"   If you see FAILED messages, check the error details for next steps.")

if __name__ == "__main__":
    asyncio.run(test_new_notification_types())
