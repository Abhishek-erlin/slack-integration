"""
Test script for notification system.
This script tests the end-to-end flow of sending notifications.
"""
import asyncio
import sys
import os
import logging
from uuid import UUID
import json
from datetime import datetime

# Add parent directory to path to import from project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.notification_models import NotificationType, Priority
from services.notification_service import NotificationService
from repository.notification_repository import NotificationRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_test_notification(user_id: str, channel_id: str):
    """Send a test notification."""
    try:
        notification_service = NotificationService()
        
        # Create test metadata
        metadata = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "test_script"
        }
        
        # Send a test notification
        response = await notification_service.send_notification(
            user_id=UUID(user_id),
            message_content="This is a test notification from the notification system",
            notification_type=NotificationType.SYSTEM_ALERT,
            channel_id=channel_id,
            priority=Priority.NORMAL,
            metadata=metadata
        )
        
        logging.info(f"Notification response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error sending test notification: {e}")
        return None


async def test_notification_history(user_id: str):
    """Test retrieving notification history."""
    logger.info(f"Testing notification history for user {user_id}")
    
    service = NotificationService()
    
    # Get notification history
    history = await service.get_notification_history(
        user_id=UUID(user_id),
        page=1,
        page_size=10
    )
    
    # Log the history
    logger.info(f"Found {history['total_count']} notifications")
    
    # Print each notification in a readable format
    for notification in history['notifications']:
        logger.info(f"Notification {notification.id}:")
        logger.info(f"  Type: {notification.notification_type}")
        logger.info(f"  Status: {notification.delivery_status}")
        logger.info(f"  Created: {notification.created_at}")
        logger.info(f"  Message: {notification.message_content[:50]}...")
    
    return history


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test notification system")
    parser.add_argument("--user-id", required=True, help="User ID to send notification to")
    parser.add_argument("--channel-id", required=True, help="Slack channel ID to send notification to")
    
    args = parser.parse_args()
    
    # Test sending a notification
    await send_test_notification(args.user_id, args.channel_id)
    
    # Test getting notification history
    await test_notification_history(args.user_id)
    await asyncio.sleep(2)
    
    # Test retrieving notification history
    history_result = await test_notification_history(args.user_id)


if __name__ == "__main__":
    asyncio.run(main())
