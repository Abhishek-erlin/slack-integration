# Slack Integration Backend: Use Case Implementation Guide

This document provides a comprehensive guide to implementing a Slack integration backend service using the 3-layer architecture pattern. It covers the core functionality, components, and implementation details needed to replicate this integration in other projects.

## 1. Overview

The Slack integration backend enables applications to connect with Slack workspaces through OAuth, send notifications to users via Slack channels, and manage notification delivery with proper tracking and error handling. The system follows a clean 3-layer architecture with separation of concerns between routes, services, and repositories.

### Core Features

- **OAuth Integration**: Complete Slack OAuth flow with CSRF protection
- **Notification System**: Event-based notification delivery to Slack channels
- **Message Templates**: Dynamic message formatting with fallbacks
- **Delivery Tracking**: Comprehensive logging of notification delivery status
- **Channel Management**: Default channel configuration for users
- **Error Handling**: Robust error handling and reporting

## 2. Architecture

The backend follows a 3-layer architecture pattern:

1. **Router Layer (API/Controller)**: FastAPI routes handling HTTP requests
2. **Service Layer (Business Logic)**: Core business logic and orchestration
3. **Repository Layer (Data Access)**: Database operations and persistence

### Key Components

```
├── routes/
│   ├── slack_routes.py        # Slack OAuth and messaging endpoints
│   ├── notification_routes.py  # Notification management endpoints
│   └── trigger_routes.py       # Event trigger endpoints
├── services/
│   ├── slack_service.py        # Slack OAuth and messaging logic
│   ├── notification_service.py  # Notification delivery logic
│   └── trigger_service.py      # Event trigger handling logic
├── repository/
│   ├── slack_repository.py     # Slack token storage and retrieval
│   └── notification_repository.py # Notification logs persistence
└── models/
    ├── slack_models.py         # Slack-related data models
    └── notification_models.py  # Notification system data models
```

## 3. OAuth Integration Implementation

### OAuth Flow

1. **Initiation**: User requests OAuth connection to Slack
2. **Authorization**: User is redirected to Slack for authorization
3. **Callback**: Slack redirects back with authorization code
4. **Token Exchange**: Backend exchanges code for access tokens
5. **Storage**: Tokens are securely stored for future use
6. **Confirmation**: User is redirected to confirmation page

### Key Implementation Details

#### State Management for CSRF Protection

The system uses a secure random token for state management to prevent CSRF attacks:

```python
# Generate secure random state
state = secrets.token_urlsafe(32)

# Store state with user ID and timestamp
SlackService._shared_state_storage[state] = {
    "user_id": user_id,
    "timestamp": time.time()
}
```

#### OAuth URL Generation

```python
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
```

#### Token Exchange

```python
async def _exchange_code_for_tokens(self, code: str) -> Optional[Dict[str, Any]]:
    """Exchange authorization code for access tokens via Slack API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )
            
            data = response.json()
            
            if not data.get("ok", False):
                logger.error(f"Slack API error: {data.get('error')}")
                return None
                
            return data
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {e}")
        return None
```

#### Token Storage

Tokens are stored in a database with the user ID as the key:

```python
# Store tokens in database
await self.repository.save_tokens(
    user_id=user_id,
    access_token=token_data["access_token"],
    team_id=token_data["team"]["id"],
    team_name=token_data["team"]["name"],
    slack_user_id=token_data["authed_user"]["id"],
    scope=token_data.get("scope", "")
)
```

## 4. Notification System

### Notification Flow

1. **Trigger**: An event triggers a notification (e.g., audit completion)
2. **Context**: Event context is gathered for message formatting
3. **Template**: Appropriate message template is selected and formatted
4. **Delivery**: Message is sent to Slack via the Slack API
5. **Tracking**: Delivery status is tracked and logged
6. **Reporting**: Success/failure is reported back to the caller

### Key Implementation Details

#### Event Types

The system supports multiple notification types:

```python
class NotificationType(str, Enum):
    """Enum for notification types."""
    AUDIT_COMPLETE = "audit_complete"
    AI_VISIBILITY = "ai_visibility"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    SYSTEM_ALERT = "system_alert"
```

#### Message Templates

Templates are defined with fallbacks for each notification type:

```python
self.message_templates = {
    NotificationType.AUDIT_COMPLETE: {
        "template": "Your {audit_type} audit for {website_name} is complete with a score of {score}/100.",
        "fallback": "Your audit is complete. Check your dashboard for details.",
        "priority": Priority.NORMAL
    },
    NotificationType.AI_VISIBILITY: {
        "template": "🤖 AI Visibility analysis for {website_name} is complete! Your visibility score is {visibility_score}/100 with {insights_count} insights available.",
        "fallback": "Your AI visibility analysis is ready! Check your dashboard for insights.",
        "priority": Priority.NORMAL
    },
    # Additional templates...
}
```

#### Message Formatting

Templates are dynamically formatted with context data:

```python
def _format_message(self, template_config: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Format a message template using context variables."""
    try:
        template = template_config.get("template", "")
        formatted_message = template.format(**context)
        
        # Add additional formatting for common patterns
        if "issues_summary" not in context and "issues_count" in context:
            issues_count = context.get("issues_count", 0)
            if issues_count > 0:
                formatted_message += f" Found {issues_count} issue{'s' if issues_count != 1 else ''} to review."
            else:
                formatted_message += " No issues found - great job!"
        
        return formatted_message
        
    except KeyError as e:
        # Fall back to the fallback message
        fallback = template_config.get("fallback", "Notification update available")
        
        # Try to add basic context to fallback if available
        if "website_name" in context:
            fallback += f" for {context['website_name']}"
        
        return fallback
```

#### Notification Delivery

The notification service handles delivery to Slack:

```python
async def send_notification(
    self,
    user_id: UUID,
    message_content: str,
    notification_type: NotificationType,
    channel_id: Optional[str] = None,
    priority: Priority = Priority.NORMAL,
    metadata: Optional[dict] = None,
    website_id: Optional[UUID] = None
) -> NotificationResponse:
    """Send a notification to a user via Slack."""
    try:
        # Check if user has Slack integration
        integration_status = await self.slack_service.get_integration_status(str(user_id))
        
        if not integration_status.get("connected", False):
            # Save failed notification log
            notification_id = await self.repository.save_notification_log(
                user_id=user_id,
                notification_type=notification_type,
                message_content=message_content,
                channel_id=channel_id,
                priority=priority,
                delivery_status=DeliveryStatus.FAILED,
                metadata=metadata,
                website_id=website_id
            )
            
            return NotificationResponse(
                success=False,
                message="User does not have an active Slack integration",
                notification_id=notification_id,
                delivery_status=DeliveryStatus.FAILED
            )
        
        # Use provided channel_id or get default from integration
        target_channel = channel_id or integration_status.get("channel_id")
        
        # Send message to Slack
        slack_response = await self.slack_service.send_message(
            user_id=str(user_id),
            message=message_content,
            channel_id=target_channel
        )
        
        # Update notification status based on delivery result
        if slack_response.success:
            # Update notification status to DELIVERED
            await self.repository.update_notification_status(
                notification_id=notification_id,
                delivery_status=DeliveryStatus.DELIVERED,
                slack_message_id=getattr(slack_response, 'slack_message_id', None)
            )
            
            return NotificationResponse(
                success=True,
                message="Notification delivered successfully",
                notification_id=notification_id,
                delivery_status=DeliveryStatus.DELIVERED
            )
        else:
            # Update notification status to FAILED
            await self.repository.update_notification_status(
                notification_id=notification_id,
                delivery_status=DeliveryStatus.FAILED,
                error_message=slack_response.message
            )
            
            return NotificationResponse(
                success=False,
                message=f"Failed to deliver notification: {slack_response.message}",
                notification_id=notification_id,
                delivery_status=DeliveryStatus.FAILED
            )
    except Exception as e:
        # Error handling...
```

## 5. Trigger Service

The trigger service acts as a higher-level abstraction for sending notifications based on specific events:

### Event Trigger Flow

1. **Event Occurs**: A system event occurs (e.g., audit completion)
2. **Trigger Call**: The trigger service is called with event details
3. **Context Processing**: Event context is processed for message formatting
4. **Template Selection**: Appropriate message template is selected
5. **Notification**: Notification service is called to deliver the message
6. **Response**: Success/failure is reported back to the caller

### Key Implementation Details

#### Event Trigger Handling

```python
async def handle_event_trigger(
    self,
    user_id: UUID,
    website_id: UUID,
    event_type: NotificationType,
    channel_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> TriggerResponse:
    """Handle an event trigger and send appropriate notification."""
    try:
        # Get message template configuration for this event type
        template_config = self.message_templates.get(event_type)
        if not template_config:
            return TriggerResponse(
                success=False,
                message=f"No template configuration found for event type: {event_type}",
                event_type=event_type,
                delivery_status=DeliveryStatus.FAILED
            )
        
        # Format the message using context data
        message_content = self._format_message(template_config, context or {})
        priority = template_config.get("priority", Priority.NORMAL)
        
        # Prepare metadata with trigger information
        metadata = {
            "trigger_source": "event",
            "event_type": event_type,
            "website_id": str(website_id),
            "event_context": context,
            "template_used": template_config.get("template")
        }
        
        # Send notification via notification service
        notification_result = await self.notification_service.send_notification(
            user_id=user_id,
            message_content=message_content,
            notification_type=event_type,
            channel_id=channel_id,
            priority=priority,
            metadata=metadata,
            website_id=website_id
        )
        
        if notification_result.success:
            return TriggerResponse(
                success=True,
                message="Event trigger processed successfully",
                notification_id=notification_result.notification_id,
                event_type=event_type,
                delivery_status=notification_result.delivery_status
            )
        else:
            return TriggerResponse(
                success=False,
                message=f"Failed to send notification: {notification_result.message}",
                notification_id=notification_result.notification_id,
                event_type=event_type,
                delivery_status=notification_result.delivery_status
            )
    except Exception as e:
        # Error handling...
```

## 6. API Endpoints

### Slack OAuth Endpoints

- `GET /api/v1/slack/oauth/start`: Start OAuth flow
- `GET /api/v1/slack/oauth/callback`: Handle OAuth callback
- `GET /api/v1/slack/status`: Get integration status
- `DELETE /api/v1/slack/disconnect`: Disconnect integration
- `GET /api/v1/slack/health`: Health check endpoint

### Notification Endpoints

- `POST /api/v1/notifications/send`: Send notification
- `GET /api/v1/notifications/history`: Get notification history

### Trigger Endpoints

- `POST /api/v1/triggers/send`: Send event-based notification
- `GET /api/v1/triggers/supported-events`: Get supported event types
- `POST /api/v1/triggers/test`: Test notification trigger

## 7. Database Schema

### Slack Integration Table

```sql
CREATE TABLE slack_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    access_token TEXT NOT NULL,
    team_id TEXT NOT NULL,
    team_name TEXT NOT NULL,
    slack_user_id TEXT NOT NULL,
    channel_id TEXT,
    scope TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Notification Logs Table

```sql
CREATE TABLE notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    website_id UUID,
    notification_type TEXT NOT NULL,
    message_content TEXT NOT NULL,
    channel_id TEXT,
    slack_message_id TEXT,
    delivery_status TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    CONSTRAINT chk_notification_type CHECK (
        notification_type IN (
            'audit_complete', 
            'ai_visibility', 
            'competitor_analysis', 
            'system_alert'
        )
    ),
    CONSTRAINT chk_delivery_status CHECK (
        delivery_status IN (
            'queued', 
            'sending', 
            'delivered', 
            'failed', 
            'retrying'
        )
    ),
    CONSTRAINT chk_priority CHECK (
        priority IN (
            'low', 
            'normal', 
            'high', 
            'urgent'
        )
    )
);

CREATE INDEX idx_notification_logs_user_id ON notification_logs(user_id);
CREATE INDEX idx_notification_logs_website_id ON notification_logs(website_id);
CREATE INDEX idx_notification_logs_type ON notification_logs(notification_type);
CREATE INDEX idx_notification_logs_status ON notification_logs(delivery_status);
```

## 8. Security Considerations

### Token Storage

- Access tokens are stored in a secure database
- Tokens are never exposed in logs or responses
- Database should have proper access controls

### CSRF Protection

- State parameter is used to prevent CSRF attacks
- State is validated on callback
- States expire after 10 minutes

### Error Handling

- Errors are logged but not exposed to clients
- Generic error messages are returned to users
- Detailed logs are available for debugging

## 9. Implementation Steps

1. **Set up environment**:
   - Configure required environment variables
   - Set up database with proper schema

2. **Implement OAuth flow**:
   - Create OAuth start endpoint
   - Implement callback handling
   - Set up token storage

3. **Create notification system**:
   - Implement notification models
   - Create notification service
   - Set up notification repository

4. **Build trigger service**:
   - Define event types
   - Create message templates
   - Implement trigger handling

5. **Set up API endpoints**:
   - Create FastAPI routers
   - Implement dependency injection
   - Add error handling

6. **Add monitoring and logging**:
   - Configure comprehensive logging
   - Add health check endpoints
   - Implement status reporting

## 10. Testing

### OAuth Flow Testing

- Test OAuth URL generation
- Test callback handling with valid/invalid states
- Test token exchange with mock Slack API

### Notification Testing

- Test message template formatting
- Test notification delivery with mock Slack API
- Test error handling and fallbacks

### Integration Testing

- Test end-to-end OAuth flow
- Test end-to-end notification delivery
- Test with actual Slack API (in staging environment)

## 11. Common Issues and Solutions

### OAuth Redirect Issues

**Problem**: OAuth redirect fails or returns to wrong URL
**Solution**: Ensure redirect_uri exactly matches the one registered with Slack

### Token Storage Issues

**Problem**: Tokens not persisting between requests
**Solution**: Check database connection and transaction handling

### Message Formatting Errors

**Problem**: Template formatting fails with KeyError
**Solution**: Ensure all required context variables are provided or use fallback

### Channel Selection Issues

**Problem**: Messages sent to wrong channel
**Solution**: Verify channel_id priority and default channel configuration

## 12. Extending the System

### Adding New Notification Types

1. Add new enum value to `NotificationType`
2. Add template to `message_templates` in `TriggerService`
3. Update database constraint if necessary

### Supporting Additional Platforms

1. Create new service for platform (e.g., `TeamsService`)
2. Implement similar methods as `SlackService`
3. Update `NotificationService` to support multiple platforms

### Implementing Webhooks

1. Create webhook endpoints in a new router
2. Implement webhook verification
3. Process incoming webhook events

## 13. Production Considerations

### Scaling

- Use async operations for better concurrency
- Implement rate limiting for Slack API calls
- Consider message queuing for high-volume scenarios

### Monitoring

- Log all API calls and responses
- Track notification delivery rates and failures
- Set up alerts for persistent failures

### Maintenance

- Regularly rotate and refresh tokens if needed
- Monitor for Slack API changes
- Update message templates based on user feedback

## 14. Required Environment Variables

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
SLACK_REDIRECT_URI=your_slack_redirect_uri
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 15. Conclusion

This Slack integration backend provides a robust foundation for adding Slack notifications to any application. By following the 3-layer architecture pattern and implementing proper error handling and security measures, the system ensures reliable delivery of notifications while maintaining clean separation of concerns.

The modular design allows for easy extension to support additional notification types or even additional messaging platforms in the future.
