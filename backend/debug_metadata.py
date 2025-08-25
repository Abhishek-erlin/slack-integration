#!/usr/bin/env python3
"""
Debug script to check if trigger metadata is being saved correctly.
"""

import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

async def check_trigger_metadata():
    """Check recent notification logs for trigger metadata."""
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in environment variables")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Query recent notification logs with metadata
        result = supabase.table("notification_logs").select(
            "id, notification_type, delivery_status, metadata, created_at, website_id"
        ).order("created_at", desc=True).limit(10).execute()
        
        if not result.data:
            print("❌ No notification logs found")
            return
        
        print("🔍 Recent Notification Logs:")
        print("=" * 80)
        
        for log in result.data:
            print(f"ID: {log['id']}")
            print(f"Type: {log['notification_type']}")
            print(f"Status: {log['delivery_status']}")
            print(f"Website ID: {log.get('website_id', 'None')}")
            print(f"Created: {log['created_at']}")
            
            metadata = log.get('metadata')
            if metadata:
                print("✅ Metadata found:")
                for key, value in metadata.items():
                    print(f"  - {key}: {value}")
            else:
                print("❌ No metadata found")
            
            print("-" * 40)
        
        # Check specifically for trigger-related metadata
        trigger_logs = [log for log in result.data if log.get('metadata', {}).get('trigger_source') == 'automatic']
        
        if trigger_logs:
            print(f"\n🎯 Found {len(trigger_logs)} trigger-generated notifications with metadata!")
        else:
            print("\n⚠️  No trigger-generated notifications found in recent logs")
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")

if __name__ == "__main__":
    asyncio.run(check_trigger_metadata())
