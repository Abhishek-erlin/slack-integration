#!/usr/bin/env python3
"""
Simple test to verify notification types are working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.notification_models import NotificationType

def test_notification_types():
    """Test that all notification types are accessible."""
    
    print("🔍 Testing Notification Types")
    print("=" * 40)
    
    # Test each notification type
    types_to_test = [
        ('AUDIT_COMPLETE', 'audit_complete'),
        ('AI_VISIBILITY', 'ai_visibility'),
        ('COMPETITOR_ANALYSIS', 'competitor_analysis'),
        ('SYSTEM_ALERT', 'system_alert')
    ]
    
    for enum_name, expected_value in types_to_test:
        try:
            notification_type = getattr(NotificationType, enum_name)
            actual_value = notification_type.value
            
            if actual_value == expected_value:
                print(f"✅ {enum_name}: {actual_value}")
            else:
                print(f"❌ {enum_name}: Expected '{expected_value}', got '{actual_value}'")
                
        except AttributeError:
            print(f"❌ {enum_name}: Not found in NotificationType enum")
    
    # Test old types that should NOT exist
    old_types = ['AUDIT_STARTED', 'INTEGRATION_STATUS']
    
    print(f"\n🚫 Testing Old Types (should not exist):")
    for old_type in old_types:
        try:
            getattr(NotificationType, old_type)
            print(f"❌ {old_type}: Still exists (should be removed)")
        except AttributeError:
            print(f"✅ {old_type}: Correctly removed")
    
    # Test creating notification with each type
    print(f"\n🧪 Testing Notification Type Values:")
    for enum_name, expected_value in types_to_test:
        try:
            notification_type = getattr(NotificationType, enum_name)
            print(f"   {enum_name}.value = '{notification_type.value}'")
        except AttributeError:
            print(f"   {enum_name}: ERROR - Not accessible")

if __name__ == "__main__":
    test_notification_types()
