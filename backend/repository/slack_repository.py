"""
Slack OAuth integration repository layer for database operations.
Following the 3-layer architecture pattern from Goosebump Crew.
"""
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from datetime import datetime
import logging
from cryptography.fernet import Fernet
import base64

from models.slack_models import SlackTokenData

logger = logging.getLogger(__name__)


class SlackRepository:
    """Repository class for Slack OAuth integration data access."""
    
    def __init__(self):
        """Initialize Supabase client and encryption."""
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # Initialize encryption for tokens
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a key if not provided (for development)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("No ENCRYPTION_KEY found, using generated key for development")
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.cipher_suite = Fernet(encryption_key)
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token before storing in database."""
        try:
            encrypted_token = self.cipher_suite.encrypt(token.encode())
            return base64.b64encode(encrypted_token).decode()
        except Exception as e:
            logger.error(f"Error encrypting token: {e}")
            raise
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token retrieved from database."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_token.encode())
            decrypted_token = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_token.decode()
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            raise
    
    async def save_tokens(self, token_data: SlackTokenData) -> bool:
        """
        Save or update Slack OAuth tokens for a user.
        
        Args:
            token_data: SlackTokenData object containing all token information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Encrypt sensitive tokens
            encrypted_access_token = self._encrypt_token(token_data.access_token)
            encrypted_refresh_token = None
            if token_data.refresh_token:
                encrypted_refresh_token = self._encrypt_token(token_data.refresh_token)
            
            # Prepare data for upsert
            upsert_data = {
                "user_id": token_data.user_id,
                "slack_user_id": token_data.slack_user_id,
                "team_id": token_data.team_id,
                "team_name": token_data.team_name,
                "bot_user_id": token_data.bot_user_id,
                "access_token": encrypted_access_token,
                "refresh_token": encrypted_refresh_token,
                "scope": token_data.scope,
                "channel_id": token_data.channel_id,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Check if record exists
            existing = self.supabase.table("user_slack_tokens").select("id").eq("user_id", token_data.user_id).execute()
            
            if existing.data:
                # Update existing record
                result = self.supabase.table("user_slack_tokens").update(upsert_data).eq("user_id", token_data.user_id).execute()
            else:
                # Insert new record
                upsert_data["created_at"] = datetime.utcnow().isoformat()
                result = self.supabase.table("user_slack_tokens").insert(upsert_data).execute()
            
            if result.data:
                logger.info(f"Successfully saved Slack tokens for user {token_data.user_id}")
                return True
            else:
                logger.error(f"Failed to save Slack tokens for user {token_data.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving Slack tokens: {e}")
            return False
    
    async def get_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve Slack OAuth tokens for a user.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dict containing decrypted token data or None if not found
        """
        try:
            result = self.supabase.table("user_slack_tokens").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                logger.info(f"No Slack tokens found for user {user_id}")
                return None
            
            token_record = result.data[0]
            
            # Decrypt tokens
            decrypted_data = {
                "id": token_record["id"],
                "user_id": token_record["user_id"],
                "slack_user_id": token_record["slack_user_id"],
                "team_id": token_record["team_id"],
                "team_name": token_record["team_name"],
                "bot_user_id": token_record["bot_user_id"],
                "access_token": self._decrypt_token(token_record["access_token"]),
                "scope": token_record["scope"],
                "channel_id": token_record["channel_id"],
                "created_at": token_record["created_at"],
                "updated_at": token_record["updated_at"]
            }
            
            # Decrypt refresh token if it exists
            if token_record["refresh_token"]:
                decrypted_data["refresh_token"] = self._decrypt_token(token_record["refresh_token"])
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error retrieving Slack tokens for user {user_id}: {e}")
            return None
    
    async def update_channel(self, user_id: str, channel_id: str) -> bool:
        """
        Update the default channel for a user's Slack integration.
        
        Args:
            user_id: Internal user ID
            channel_id: Slack channel ID to set as default
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.supabase.table("user_slack_tokens").update({
                "channel_id": channel_id,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"Successfully updated channel for user {user_id} to {channel_id}")
                return True
            else:
                logger.error(f"Failed to update channel for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating channel for user {user_id}: {e}")
            return False
    
    async def delete_tokens(self, user_id: str) -> bool:
        """
        Delete Slack OAuth tokens for a user (disconnect integration).
        
        Args:
            user_id: Internal user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.supabase.table("user_slack_tokens").delete().eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"Successfully deleted Slack tokens for user {user_id}")
                return True
            else:
                logger.error(f"Failed to delete Slack tokens for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting Slack tokens for user {user_id}: {e}")
            return False
    
    async def get_all_active_integrations(self) -> list[Dict[str, Any]]:
        """
        Get all users with active Slack integrations for notification purposes.
        
        Returns:
            List of user token data for active integrations
        """
        try:
            result = self.supabase.table("user_slack_tokens").select("*").execute()
            
            active_integrations = []
            for record in result.data:
                try:
                    # Decrypt tokens for each record
                    decrypted_data = {
                        "user_id": record["user_id"],
                        "slack_user_id": record["slack_user_id"],
                        "team_id": record["team_id"],
                        "team_name": record["team_name"],
                        "bot_user_id": record["bot_user_id"],
                        "access_token": self._decrypt_token(record["access_token"]),
                        "scope": record["scope"],
                        "channel_id": record["channel_id"]
                    }
                    
                    if record["refresh_token"]:
                        decrypted_data["refresh_token"] = self._decrypt_token(record["refresh_token"])
                    
                    active_integrations.append(decrypted_data)
                    
                except Exception as decrypt_error:
                    logger.error(f"Error decrypting tokens for user {record['user_id']}: {decrypt_error}")
                    continue
            
            logger.info(f"Retrieved {len(active_integrations)} active Slack integrations")
            return active_integrations
            
        except Exception as e:
            logger.error(f"Error retrieving active Slack integrations: {e}")
            return []
