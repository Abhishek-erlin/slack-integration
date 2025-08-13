"""
Slack OAuth integration service layer for business logic.
Following the 3-layer architecture pattern from Goosebump Crew.
"""
import os
import secrets
import httpx
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from models.slack_models import (
    SlackOAuthStartResponse, 
    SlackTokenData, 
    SlackMessageResponse,
    SlackIntegrationResponse,
    SlackErrorResponse
)
from repository.slack_repository import SlackRepository

logger = logging.getLogger(__name__)


class SlackService:
    """Service class for Slack OAuth integration business logic."""
    
    def __init__(self):
        """Initialize Slack service with configuration and repository."""
        self.client_id = os.getenv("SLACK_CLIENT_ID")
        self.client_secret = os.getenv("SLACK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SLACK_REDIRECT_URI")
        self.base_url = "https://slack.com/api"
        
        # Validate required environment variables
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing required Slack OAuth environment variables")
        
        self.repository = SlackRepository()
        
        # Use class-level state storage to persist across instances
        if not hasattr(SlackService, '_shared_state_storage'):
            SlackService._shared_state_storage: Dict[str, Dict[str, any]] = {}
    
    async def get_oauth_url(self, user_id: str) -> SlackOAuthStartResponse:
        """
        Generate Slack OAuth authorization URL with CSRF protection.
        
        Args:
            user_id: Internal user ID for state tracking
            
        Returns:
            SlackOAuthStartResponse with OAuth URL and state
        """
        try:
            # Generate secure random state for CSRF protection
            state = secrets.token_urlsafe(32)
            
            # Store state linked to user_id with timestamp for TTL
            import time
            SlackService._shared_state_storage[state] = {
                "user_id": user_id,
                "timestamp": time.time()
            }
            
            # Define OAuth scopes
            scopes = [
                "chat:write",
                "channels:read",
                "users:read",
                "groups:read",
                "im:read",
                "mpim:read"
            ]
            
            # Build OAuth URL
            oauth_params = {
                "client_id": self.client_id,
                "scope": ",".join(scopes),
                "redirect_uri": self.redirect_uri,
                "state": state,
                "response_type": "code"
            }
            
            oauth_url = f"https://slack.com/oauth/v2/authorize?{urlencode(oauth_params)}"
            
            logger.info(f"Generated OAuth URL for user {user_id}")
            
            return SlackOAuthStartResponse(
                oauth_url=oauth_url,
                state=state
            )
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL for user {user_id}: {e}")
            raise
    
    async def handle_oauth_callback(self, code: str, state: str) -> SlackIntegrationResponse:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from Slack
            state: State parameter for CSRF validation
            
        Returns:
            SlackIntegrationResponse with integration status
        """
        try:
            # Validate state for CSRF protection
            import time
            current_time = time.time()
            
            # Clean up expired states (older than 10 minutes)
            expired_states = [
                s for s, data in SlackService._shared_state_storage.items() 
                if current_time - data["timestamp"] > 600
            ]
            for expired_state in expired_states:
                del SlackService._shared_state_storage[expired_state]
            
            if state not in SlackService._shared_state_storage:
                logger.error(f"Invalid state parameter: {state}")
                return SlackIntegrationResponse(
                    success=False,
                    message="Invalid state parameter. Please try again.",
                    user_id=""
                )
            
            user_id = SlackService._shared_state_storage[state]["user_id"]
            
            # Exchange code for tokens
            token_data = await self._exchange_code_for_tokens(code)
            if not token_data:
                return SlackIntegrationResponse(
                    success=False,
                    message="Failed to exchange authorization code for tokens.",
                    user_id=user_id
                )
            
            # Add user_id to token data
            token_data["user_id"] = user_id
            
            # Create SlackTokenData object
            slack_token_data = SlackTokenData(**token_data)
            
            # Save tokens to database
            save_success = await self.repository.save_tokens(slack_token_data)
            if not save_success:
                return SlackIntegrationResponse(
                    success=False,
                    message="Failed to save integration data.",
                    user_id=user_id
                )
            
            # Clean up state
            del SlackService._shared_state_storage[state]
            
            logger.info(f"Successfully completed OAuth integration for user {user_id}")
            
            return SlackIntegrationResponse(
                success=True,
                message="Successfully connected to Slack!",
                team_name=token_data.get("team_name"),
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return SlackIntegrationResponse(
                success=False,
                message="An error occurred during integration.",
                user_id=""
            )
    
    async def _exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access tokens via Slack API.
        
        Args:
            code: Authorization code from Slack
            
        Returns:
            Dict containing token data or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/oauth.v2.access",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": self.redirect_uri
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Slack API error: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                
                if not data.get("ok"):
                    logger.error(f"Slack OAuth error: {data.get('error')}")
                    return None
                
                # Extract token information
                token_data = {
                    "slack_user_id": data["authed_user"]["id"],
                    "team_id": data["team"]["id"],
                    "team_name": data["team"]["name"],
                    "bot_user_id": data["bot_user_id"],
                    "access_token": data["access_token"],
                    "refresh_token": data.get("refresh_token"),
                    "scope": data["scope"]
                }
                
                logger.info(f"Successfully exchanged code for tokens for team {data['team']['name']}")
                return token_data
                
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            return None
    
    async def send_message(self, user_id: str, message: str, channel_id: Optional[str] = None) -> SlackMessageResponse:
        """
        Send a message to Slack using stored user tokens.
        
        Args:
            user_id: Internal user ID
            message: Message text to send
            channel_id: Optional channel ID override
            
        Returns:
            SlackMessageResponse with send status
        """
        try:
            # Get user's Slack tokens
            token_data = await self.repository.get_tokens(user_id)
            if not token_data:
                return SlackMessageResponse(
                    success=False,
                    message="No Slack integration found. Please connect your Slack workspace first."
                )
            
            # Use provided channel_id or fall back to stored default
            target_channel = channel_id or token_data.get("channel_id")
            if not target_channel:
                return SlackMessageResponse(
                    success=False,
                    message="No channel specified. Please set a default channel or provide one."
                )
            
            # Send message via Slack API
            slack_response = await self._send_slack_message(
                token_data["access_token"],
                target_channel,
                message
            )
            
            if slack_response.get("ok"):
                logger.info(f"Successfully sent message for user {user_id}")
                return SlackMessageResponse(
                    success=True,
                    message="Message sent successfully!",
                    slack_message_id=slack_response.get("ts")
                )
            else:
                error = slack_response.get("error", "Unknown error")
                logger.error(f"Slack API error for user {user_id}: {error}")
                
                # Handle token expiration
                if error == "invalid_auth":
                    return SlackMessageResponse(
                        success=False,
                        message="Slack integration expired. Please reconnect your workspace."
                    )
                
                return SlackMessageResponse(
                    success=False,
                    message=f"Failed to send message: {error}"
                )
                
        except Exception as e:
            logger.error(f"Error sending message for user {user_id}: {e}")
            return SlackMessageResponse(
                success=False,
                message="An error occurred while sending the message."
            )
    
    async def _send_slack_message(self, access_token: str, channel: str, message: str) -> Dict[str, Any]:
        """
        Send message via Slack chat.postMessage API.
        
        Args:
            access_token: Slack access token
            channel: Channel ID to send message to
            message: Message text
            
        Returns:
            Dict containing Slack API response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat.postMessage",
                    json={
                        "channel": channel,
                        "text": message
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error calling Slack API: {e}")
            return {"ok": False, "error": "api_error"}
    
    async def update_default_channel(self, user_id: str, channel_id: str) -> bool:
        """
        Update the default channel for a user's Slack integration.
        
        Args:
            user_id: Internal user ID
            channel_id: Slack channel ID to set as default
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return await self.repository.update_channel(user_id, channel_id)
        except Exception as e:
            logger.error(f"Error updating default channel for user {user_id}: {e}")
            return False
    
    async def disconnect_integration(self, user_id: str) -> bool:
        """
        Disconnect Slack integration for a user.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return await self.repository.delete_tokens(user_id)
        except Exception as e:
            logger.error(f"Error disconnecting Slack integration for user {user_id}: {e}")
            return False
    
    async def get_integration_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get Slack integration status for a user.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dict containing integration status information
        """
        try:
            token_data = await self.repository.get_tokens(user_id)
            
            if not token_data:
                return {
                    "connected": False,
                    "message": "No Slack integration found"
                }
            
            return {
                "connected": True,
                "team_name": token_data.get("team_name"),
                "slack_user_id": token_data.get("slack_user_id"),
                "channel_id": token_data.get("channel_id"),
                "connected_at": token_data.get("created_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting integration status for user {user_id}: {e}")
            return {
                "connected": False,
                "message": "Error checking integration status"
            }
