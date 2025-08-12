"""
Slack OAuth integration Pydantic models for request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SlackOAuthStartResponse(BaseModel):
    """Response model for OAuth start endpoint."""
    oauth_url: str = Field(..., description="Slack OAuth authorization URL")
    state: str = Field(..., description="CSRF protection state parameter")


class SlackOAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback endpoint."""
    code: str = Field(..., description="Authorization code from Slack")
    state: str = Field(..., description="State parameter for CSRF validation")


class SlackMessageRequest(BaseModel):
    """Request model for sending Slack messages."""
    message: str = Field(..., description="Message text to send")
    channel_id: Optional[str] = Field(None, description="Optional channel ID override")


class SlackMessageResponse(BaseModel):
    """Response model for message sending."""
    success: bool = Field(..., description="Whether message was sent successfully")
    message: str = Field(..., description="Status message")
    slack_message_id: Optional[str] = Field(None, description="Slack message ID if successful")


class SlackTokenData(BaseModel):
    """Model for Slack token data from OAuth response."""
    user_id: str = Field(..., description="Internal user ID")
    slack_user_id: str = Field(..., description="Slack user ID")
    team_id: str = Field(..., description="Slack team/workspace ID")
    team_name: str = Field(..., description="Slack team/workspace name")
    bot_user_id: str = Field(..., description="Bot user ID")
    access_token: str = Field(..., description="Slack access token")
    refresh_token: Optional[str] = Field(None, description="Slack refresh token")
    scope: str = Field(..., description="Granted OAuth scopes")
    channel_id: Optional[str] = Field(None, description="Default channel ID")


class SlackIntegrationResponse(BaseModel):
    """Response model for Slack integration status."""
    success: bool = Field(..., description="Whether integration was successful")
    message: str = Field(..., description="Status message")
    team_name: Optional[str] = Field(None, description="Connected Slack workspace name")
    user_id: str = Field(..., description="Internal user ID")


class SlackChannelUpdateRequest(BaseModel):
    """Request model for updating default channel."""
    channel_id: str = Field(..., description="Slack channel ID to set as default")


class SlackErrorResponse(BaseModel):
    """Response model for Slack API errors."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Slack API error code")
