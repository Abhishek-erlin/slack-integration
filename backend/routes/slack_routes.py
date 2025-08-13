"""
Slack OAuth integration routes layer for API endpoints.
Following the 3-layer architecture pattern from Goosebump Crew.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
import logging
from typing import Optional

from models.slack_models import (
    SlackOAuthStartResponse,
    SlackOAuthCallbackRequest,
    SlackMessageRequest,
    SlackMessageResponse,
    SlackIntegrationResponse,
    SlackChannelUpdateRequest,
    SlackErrorResponse
)
from services.slack_service import SlackService

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

# Dependency to get SlackService instance
def get_slack_service() -> SlackService:
    """Dependency injection for SlackService."""
    return SlackService()


@router.get("/oauth/start", response_model=SlackOAuthStartResponse)
async def start_oauth(
    user_id: str = Query(..., description="Internal user ID"),
    slack_service: SlackService = Depends(get_slack_service)
):
    """
    Start Slack OAuth flow by generating authorization URL.
    
    Args:
        user_id: Internal user ID for state tracking
        slack_service: Injected SlackService instance
        
    Returns:
        SlackOAuthStartResponse with OAuth URL and state
    """
    try:
        logger.info(f"Starting OAuth flow for user {user_id}")
        
        oauth_response = await slack_service.get_oauth_url(user_id)
        
        return oauth_response
        
    except Exception as e:
        logger.error(f"Error starting OAuth for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate OAuth URL"
        )


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Slack"),
    state: str = Query(..., description="State parameter for CSRF validation"),
    error: Optional[str] = Query(None, description="Error from Slack OAuth"),
    slack_service: SlackService = Depends(get_slack_service)
):
    """
    Handle Slack OAuth callback and redirect user to frontend.
    
    Args:
        code: Authorization code from Slack
        state: State parameter for CSRF validation
        error: Optional error parameter from Slack
        slack_service: Injected SlackService instance
        
    Returns:
        RedirectResponse to frontend with success/error status
    """
    try:
        # Check for OAuth errors from Slack
        if error:
            logger.error(f"OAuth error from Slack: {error}")
            return RedirectResponse(
                url=f"http://localhost:3000/test-oauth?success=false&error={error}",
                status_code=302
            )
        
        logger.info(f"Processing OAuth callback with state {state}")
        
        # Handle the OAuth callback
        integration_response = await slack_service.handle_oauth_callback(code, state)
        
        if integration_response.success:
            logger.info(f"OAuth integration successful for user {integration_response.user_id}")
            return RedirectResponse(
                url=f"http://localhost:3000/test-oauth?success=true&user_id={integration_response.user_id}&message=Integration successful",
                status_code=302
            )
        else:
            logger.error(f"OAuth integration failed: {integration_response.message}")
            return RedirectResponse(
                url=f"http://localhost:3000/test-oauth?success=false&error=integration_failed&message={integration_response.message}",
                status_code=302
            )
        
    except Exception as e:
        logger.error(f"Error processing OAuth callback: {e}")
        return RedirectResponse(
            url=f"http://localhost:3000/test-oauth?success=false&error=server_error&message=Failed to complete OAuth integration",
            status_code=302
        )


@router.post("/send-message", response_model=SlackMessageResponse)
async def send_message(
    message_request: SlackMessageRequest,
    user_id: str = Query(..., description="Internal user ID"),
    slack_service: SlackService = Depends(get_slack_service)
):
    """
    Send a message to Slack using stored user integration.
    
    Args:
        message_request: SlackMessageRequest with message details
        user_id: Internal user ID
        slack_service: Injected SlackService instance
        
    Returns:
        SlackMessageResponse with send status
    """
    try:
        logger.info(f"Sending message for user {user_id}")
        
        message_response = await slack_service.send_message(
            user_id=user_id,
            message=message_request.message,
            channel_id=message_request.channel_id
        )
        
        return message_response
        
    except Exception as e:
        logger.error(f"Error sending message for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send message"
        )


@router.put("/channel")
async def update_default_channel(
    channel_request: SlackChannelUpdateRequest,
    user_id: str = Query(..., description="Internal user ID"),
    slack_service: SlackService = Depends(get_slack_service)
):
    """
    Update the default channel for a user's Slack integration.
    
    Args:
        channel_request: SlackChannelUpdateRequest with channel ID
        user_id: Internal user ID
        slack_service: Injected SlackService instance
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Updating default channel for user {user_id}")
        
        success = await slack_service.update_default_channel(
            user_id=user_id,
            channel_id=channel_request.channel_id
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update default channel"
            )
        
        return {"message": "Default channel updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update default channel"
        )


@router.get("/status")
async def get_integration_status(
    user_id: str = Query(..., description="Internal user ID"),
    slack_service: SlackService = Depends(get_slack_service)
):
    """
    Get Slack integration status for a user.
    
    Args:
        user_id: Internal user ID
        slack_service: Injected SlackService instance
        
    Returns:
        Integration status information
    """
    try:
        logger.info(f"Getting integration status for user {user_id}")
        
        status = await slack_service.get_integration_status(user_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting integration status for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get integration status"
        )


@router.delete("/disconnect")
async def disconnect_integration(
    user_id: str = Query(..., description="Internal user ID"),
    slack_service: SlackService = Depends(get_slack_service)
):
    """
    Disconnect Slack integration for a user.
    
    Args:
        user_id: Internal user ID
        slack_service: Injected SlackService instance
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Disconnecting Slack integration for user {user_id}")
        
        success = await slack_service.disconnect_integration(user_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to disconnect integration"
            )
        
        return {"message": "Slack integration disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting integration for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect integration"
        )


# Health check endpoint for Slack integration
@router.get("/health")
async def health_check():
    """Health check endpoint for Slack integration."""
    return {"status": "healthy", "service": "slack-integration"}
