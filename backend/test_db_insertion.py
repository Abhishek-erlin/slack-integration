#!/usr/bin/env python3
"""
Test database insertion with new notification types.
This will help identify if the issue is with database constraints.
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.notification_models import NotificationType, Priority, DeliveryStatus
from repository.notification_repository import NotificationRepository

async def test_database_insertion():
    """Test inserting each notification type into the database."""
    
    print("🔍 Testing Database Insertion for New Notification Types")
    print("=" * 60)
    
    # Initialize repository
    try:
        repo = NotificationRepository()
        print("✅ Repository initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize repository: {e}")
        return
    
    # Test data
    user_id = uuid4()
    website_id = uuid4()
    
    # Test each notification type
    test_cases = [
        {
            'type': NotificationType.AUDIT_COMPLETE,
            'message': 'Test audit complete notification',
            'metadata': {
                'trigger_source': 'test',
                'event_type': 'audit_complete',
                'website_id': str(website_id),
                'event_context': {'score': 85}
            }
        },
        {
            'type': NotificationType.AI_VISIBILITY,
            'message': 'Test AI visibility notification',
            'metadata': {
                'trigger_source': 'test',
                'event_type': 'ai_visibility',
                'website_id': str(website_id),
                'event_context': {'visibility_score': 78, 'insights_count': 12}
            }
        },
        {
            'type': NotificationType.COMPETITOR_ANALYSIS,
            'message': 'Test competitor analysis notification',
            'metadata': {
                'trigger_source': 'test',
                'event_type': 'competitor_analysis',
                'website_id': str(website_id),
                'event_context': {'competitor_count': 5}
            }
        },
        {
            'type': NotificationType.SYSTEM_ALERT,
            'message': 'Test system alert notification',
            'metadata': {
                'trigger_source': 'test',
                'event_type': 'system_alert',
                'website_id': str(website_id),
                'event_context': {'alert_message': 'Test alert'}
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['type'].name}")
        print(f"   Type value: '{test_case['type'].value}'")
        
        try:
            # Attempt to save notification log
            notification_id = await repo.save_notification_log(
                user_id=user_id,
                notification_type=test_case['type'],
                message_content=test_case['message'],
                channel_id="C1234567890",
                priority=Priority.NORMAL,
                delivery_status=DeliveryStatus.QUEUED,
                metadata=test_case['metadata'],
                website_id=website_id
            )
            
            if notification_id:
                print(f"   ✅ SUCCESS: Saved with ID {notification_id}")
                results.append({
                    'type': test_case['type'].name,
                    'success': True,
                    'notification_id': notification_id,
                    'error': None
                })
            else:
                print(f"   ❌ FAILED: save_notification_log returned None")
                results.append({
                    'type': test_case['type'].name,
                    'success': False,
                    'notification_id': None,
                    'error': 'save_notification_log returned None'
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                'type': test_case['type'].name,
                'success': False,
                'notification_id': None,
                'error': str(e)
            })
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print("=" * 30)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print(f"\n🚨 FAILED INSERTIONS:")
        for result in failed:
            print(f"   - {result['type']}: {result['error']}")
        
        print(f"\n💡 LIKELY CAUSES:")
        print(f"   1. Database constraint rejecting new notification types")
        print(f"   2. Missing 'metadata' or 'website_id' columns in database")
        print(f"   3. CHECK constraint limiting notification_type values")
        print(f"   4. ENUM type that doesn't include new values")
        
        print(f"\n🔧 SOLUTIONS:")
        print(f"   1. Run the migration: migrations/003_update_notification_types.sql")
        print(f"   2. Check database schema with: \\d notification_logs")
        print(f"   3. Check constraints with: \\d+ notification_logs")
    else:
        print(f"\n🎉 All notification types saved successfully!")
        print(f"   The database is properly configured for new notification types.")

if __name__ == "__main__":
    asyncio.run(test_database_insertion())
