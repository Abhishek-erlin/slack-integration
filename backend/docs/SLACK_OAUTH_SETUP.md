# Slack OAuth Integration Setup Guide

This document provides comprehensive setup instructions for the Slack OAuth integration following the 3-layer architecture pattern.

## Architecture Overview

The Slack OAuth integration follows the established 3-layer architecture:

```
Client → Router Layer → Service Layer → Repository Layer → Database
```

### Layer Responsibilities

1. **Router Layer** (`routes/slack_routes.py`)
   - HTTP request handling and validation
   - API endpoint definitions
   - Response formatting

2. **Service Layer** (`services/slack_service.py`)
   - Business logic and OAuth flow orchestration
   - Slack API communication
   - Token management and validation

3. **Repository Layer** (`repository/slack_repository.py`)
   - Database operations and data persistence
   - Token encryption/decryption
   - Data access abstraction

## Prerequisites

1. **Slack App Configuration**
   - Create a Slack app at https://api.slack.com/apps
   - Configure OAuth & Permissions
   - Set redirect URL to your callback endpoint

2. **Environment Variables**
   - Copy `.env.example` to `.env`
   - Configure all required Slack OAuth variables

3. **Database Setup**
   - Run the migration script to create required tables
   - Ensure Supabase connection is configured

## Environment Configuration

### Required Environment Variables

```bash
# Slack OAuth Configuration
SLACK_CLIENT_ID=your-slack-client-id-here
SLACK_CLIENT_SECRET=your-slack-client-secret-here
SLACK_REDIRECT_URI=http://localhost:8000/api/v1/slack/oauth/callback

# Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Security
ENCRYPTION_KEY=your-32-byte-base64-encryption-key-here
```

### Generating Encryption Key

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Use this as ENCRYPTION_KEY
```

## Slack App Setup

### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name and select workspace

### 2. Configure OAuth & Permissions

1. Navigate to "OAuth & Permissions"
2. Add redirect URL: `http://localhost:8000/api/v1/slack/oauth/callback`
3. Add required scopes:
   - `chat:write` - Send messages
   - `channels:read` - Read public channels
   - `users:read` - Read user information
   - `groups:read` - Read private channels
   - `im:read` - Read direct messages
   - `mpim:read` - Read group direct messages

### 3. Get Credentials

1. Copy "Client ID" to `SLACK_CLIENT_ID`
2. Copy "Client Secret" to `SLACK_CLIENT_SECRET`

## Database Migration

Run the migration script to create the required table:

```sql
-- Execute migrations/001_create_user_slack_tokens.sql
-- This creates the user_slack_tokens table with proper indexes and constraints
```

## API Endpoints

### OAuth Flow

1. **Start OAuth Flow**
   ```
   GET /api/v1/slack/oauth/start?user_id={user_id}
   ```
   Returns OAuth URL for user to authorize

2. **OAuth Callback**
   ```
   GET /api/v1/slack/oauth/callback?code={code}&state={state}
   ```
   Handles Slack OAuth callback and stores tokens

### Message Operations

3. **Send Message**
   ```
   POST /api/v1/slack/send-message?user_id={user_id}
   Body: {"message": "Hello World", "channel_id": "optional"}
   ```

4. **Update Default Channel**
   ```
   PUT /api/v1/slack/channel?user_id={user_id}
   Body: {"channel_id": "C1234567890"}
   ```

### Integration Management

5. **Get Integration Status**
   ```
   GET /api/v1/slack/status?user_id={user_id}
   ```

6. **Disconnect Integration**
   ```
   DELETE /api/v1/slack/disconnect?user_id={user_id}
   ```

## Usage Examples

### Frontend Integration

```javascript
// Start OAuth flow
const startOAuth = async (userId) => {
  const response = await fetch(`/api/v1/slack/oauth/start?user_id=${userId}`);
  const data = await response.json();
  window.location.href = data.oauth_url;
};

// Send message
const sendMessage = async (userId, message) => {
  const response = await fetch(`/api/v1/slack/send-message?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  return response.json();
};
```

### Backend Notification Service

```python
from services.slack_service import SlackService

async def send_notification_to_all_users(message: str):
    slack_service = SlackService()
    
    # Get all active integrations
    integrations = await slack_service.repository.get_all_active_integrations()
    
    for integration in integrations:
        try:
            await slack_service.send_message(
                user_id=integration['user_id'],
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to send to user {integration['user_id']}: {e}")
```

## Security Considerations

1. **Token Encryption**
   - All access and refresh tokens are encrypted before storage
   - Uses Fernet symmetric encryption with base64 encoding

2. **CSRF Protection**
   - State parameter validates OAuth requests
   - Prevents cross-site request forgery attacks

3. **Environment Security**
   - Never commit `.env` files
   - Use secure key management in production
   - Rotate encryption keys regularly

## Error Handling

The integration includes comprehensive error handling:

- **OAuth Errors**: Invalid state, authorization failures
- **API Errors**: Slack API rate limits, token expiration
- **Database Errors**: Connection issues, constraint violations
- **Encryption Errors**: Key issues, decryption failures

## Testing

### Manual Testing

1. Start the application: `uvicorn main:app --reload`
2. Navigate to `/docs` for interactive API documentation
3. Test OAuth flow with a real Slack workspace
4. Verify message sending functionality

### Integration Testing

```python
import pytest
from services.slack_service import SlackService

@pytest.mark.asyncio
async def test_oauth_flow():
    service = SlackService()
    
    # Test OAuth URL generation
    response = await service.get_oauth_url("test-user-id")
    assert "slack.com/oauth/v2/authorize" in response.oauth_url
    assert response.state is not None
```

## Production Deployment

1. **Environment Variables**
   - Use secure secret management (AWS Secrets Manager, etc.)
   - Set production Slack app credentials
   - Configure production redirect URLs

2. **Database**
   - Use production Supabase instance
   - Enable Row Level Security (RLS)
   - Set up proper backup strategies

3. **Monitoring**
   - Log all OAuth flows and API calls
   - Monitor token expiration and refresh
   - Set up alerts for integration failures

## Troubleshooting

### Common Issues

1. **Invalid Redirect URI**
   - Ensure redirect URI in Slack app matches `SLACK_REDIRECT_URI`
   - Check for trailing slashes and protocol mismatches

2. **Token Decryption Errors**
   - Verify `ENCRYPTION_KEY` is consistent
   - Check for key rotation issues

3. **Slack API Errors**
   - Verify scopes are properly configured
   - Check for rate limiting issues
   - Ensure bot is added to channels

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues and questions:
1. Check the logs for detailed error messages
2. Verify environment configuration
3. Test with Slack API documentation
4. Review the 3-layer architecture implementation
