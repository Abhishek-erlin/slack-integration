# Notification Trigger Service Implementation Documentation

## Overview

The Notification Trigger Service is a comprehensive event-based notification system that automatically sends Slack notifications when specific system events occur. It integrates seamlessly with the existing notification infrastructure while providing a clean API for triggering notifications based on user actions or system events.

## Architecture

The implementation follows the established 3-layer architecture pattern:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Router Layer  │───▶│  Service Layer  │───▶│Repository Layer │
│                 │    │                 │    │                 │
│ trigger_routes  │    │ trigger_service │    │notification_repo│
│                 │    │notification_svc │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components Implemented

### 1. Models (`models/notification_models.py`)
- **TriggerRequest**: Request model for trigger notifications
- **TriggerResponse**: Response model for trigger operations
- Enhanced existing models to support website_id field

### 2. Service Layer (`services/trigger_service.py`)
- **NotificationTriggerService**: Core service handling event-based notifications
- Message templating system for different event types
- Context-aware message formatting
- Integration with existing NotificationService

### 3. Repository Layer (`repository/notification_repository.py`)
- Enhanced to support website_id field in notification logs
- Maintains compatibility with existing notification_logs table schema
- All existing functionality preserved

### 4. Router Layer (`routes/trigger_routes.py`)
- **POST /api/v1/triggers/send**: Main trigger endpoint
- **GET /api/v1/triggers/supported-events**: Get supported event types
- **POST /api/v1/triggers/test**: Test trigger functionality
- **GET /api/v1/triggers/health**: Health check endpoint

## Database Integration

The implementation uses the existing `notification_logs` table with the following key fields:
- `website_id`: UUID field for website context
- `metadata`: JSONB field storing trigger context and event data
- `notification_type`: Maps directly to event types
- All existing constraints and validation rules preserved

## Supported Event Types

The trigger service supports the following event types:

1. **`AUDIT_COMPLETE`** - Triggered when a website audit is completed
2. **`AI_VISIBILITY`** - Triggered when AI visibility analysis is completed
3. **`COMPETITOR_ANALYSIS`** - Triggered when competitor analysis is ready
4. **`SYSTEM_ALERT`** - Triggered for system-wide alerts and important notifications

## API Usage

### Send Trigger Notification

```http
POST /api/v1/triggers/send
Content-Type: application/json

{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "website_id": "123e4567-e89b-12d3-a456-426614174001",
    "channel_id": "C1234567890",
    "event_type": "audit_complete",
    "context": {
        "audit_type": "technical",
        "website_name": "example.com",
        "score": 85,
        "issues_count": 3
    }
}
```

### Response

```json
{
    "success": true,
    "message": "Event trigger processed successfully",
    "notification_id": "123e4567-e89b-12d3-a456-426614174002",
    "event_type": "audit_complete",
    "delivery_status": "delivered"
}
```

## Integration Examples

### Audit Service Integration

```python
class SiteLevelCheckService:
    def __init__(self, audit_repository, trigger_service: NotificationTriggerService):
        self.audit_repository = audit_repository
        self.trigger_service = trigger_service
    
    async def check_site_level_parameters(self, website_id, user_id):
        # Existing audit logic...
        audit_result = await self._perform_audit(website_id)
        
        # Save the audit result
        saved_result = await self.audit_repository.save_audit_result(
            website_id=website_id,
            audit_type="site_level",
            audit_data=audit_result,
            user_id=user_id
        )
        
        # Trigger notification
        await self.trigger_service.handle_event_trigger(
            user_id=user_id,
            website_id=website_id,
            event_type=NotificationType.AUDIT_COMPLETE,
            context={
                "audit_type": "site-level",
                "website_name": saved_result.get("website_url", "your website"),
                "score": saved_result.get("score", 0),
                "issues_count": len(saved_result.get("issues", [])),
                "audit_id": str(saved_result.get("id"))
            }
        )
        
        return saved_result
```

## Message Templates

The service includes built-in message templates for each event type:

### Audit Complete
- **Template**: "Your {audit_type} audit for {website_name} is complete with a score of {score}/100."
- **Priority**: Normal
- **Context Variables**: audit_type, website_name, score, issues_count

### Audit Started
- **Template**: "Your {audit_type} audit for {website_name} has started and will be completed shortly."
- **Priority**: Low
- **Context Variables**: audit_type, website_name

### Integration Status
- **Template**: "Integration status update: {status_message}"
- **Priority**: Normal
- **Context Variables**: status_message

### System Alert
- **Template**: "{alert_message}"
- **Priority**: High
- **Context Variables**: alert_message

## Error Handling

The implementation includes comprehensive error handling:

1. **Validation Errors**: Invalid UUIDs, missing required fields
2. **Service Errors**: Notification service failures, database errors
3. **Template Errors**: Missing context variables, formatting issues
4. **Network Errors**: Slack API failures, timeout handling

## Testing

Comprehensive test suite includes:

### Unit Tests (`tests/test_trigger_service.py`)
- Service method testing
- Message formatting validation
- Error handling scenarios
- Template management

### Integration Tests (`tests/test_trigger_routes.py`)
- API endpoint testing
- Request/response validation
- Background task processing
- Health check functionality

### Running Tests

```bash
# Run all trigger service tests
pytest tests/test_trigger_service.py -v

# Run API route tests
pytest tests/test_trigger_routes.py -v

# Run with coverage
pytest tests/test_trigger_* --cov=services.trigger_service --cov=routes.trigger_routes
```

## Performance Considerations

1. **Background Processing**: Non-urgent notifications processed asynchronously
2. **Template Caching**: Message templates cached in memory
3. **Database Efficiency**: Leverages existing notification infrastructure
4. **Error Recovery**: Failed notifications can be retried using existing mechanisms

## Security Considerations

1. **Input Validation**: All inputs validated using Pydantic models
2. **UUID Validation**: Proper UUID format validation for user_id and website_id
3. **Context Sanitization**: Context data properly sanitized before template formatting
4. **Channel Permissions**: Respects existing Slack channel permissions

## Monitoring and Logging

The service includes comprehensive logging:

```python
# Service-level logging
logger.info(f"Processing event trigger: {event_type} for user {user_id}")
logger.error(f"Failed to send notification for event {event_type}: {error}")

# Database logging
# All trigger events logged in notification_logs table with metadata
```

## Common Mistakes to Avoid

### 1. UUID Format Issues
```python
# ❌ Wrong - passing string instead of UUID
user_id = "123-456-789"

# ✅ Correct - using proper UUID
from uuid import UUID
user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
```

### 2. Missing Context Variables
```python
# ❌ Wrong - missing required context
context = {"score": 85}  # Missing website_name, audit_type

# ✅ Correct - complete context
context = {
    "audit_type": "technical",
    "website_name": "example.com",
    "score": 85,
    "issues_count": 3
}
```

### 3. Incorrect Event Type Mapping
```python
# ❌ Wrong - using string instead of enum
event_type = "audit_complete"

# ✅ Correct - using enum
from models.notification_models import NotificationType
event_type = NotificationType.AUDIT_COMPLETE
```

### 4. Forgetting Website ID
```python
# ❌ Wrong - missing website_id
await trigger_service.handle_event_trigger(
    user_id=user_id,
    event_type=NotificationType.AUDIT_COMPLETE,
    context=context
)

# ✅ Correct - including website_id
await trigger_service.handle_event_trigger(
    user_id=user_id,
    website_id=website_id,  # Required parameter
    event_type=NotificationType.AUDIT_COMPLETE,
    context=context
)
```

### 5. Not Handling Async Operations
```python
# ❌ Wrong - not awaiting async call
trigger_service.handle_event_trigger(user_id, website_id, event_type, context)

# ✅ Correct - properly awaiting
await trigger_service.handle_event_trigger(user_id, website_id, event_type, context)
```

## Deployment Checklist

- [ ] Database schema includes website_id field in notification_logs
- [ ] Environment variables properly configured
- [ ] Trigger routes registered in main.py
- [ ] Dependencies properly injected
- [ ] Tests passing
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Integration examples working

## Future Enhancements

1. **User Preferences**: Allow users to configure notification preferences
2. **Template Management**: Admin interface for managing message templates
3. **Batch Processing**: Support for batch notification triggers
4. **Analytics**: Track trigger performance and delivery rates
5. **Webhook Support**: External webhook triggers for third-party integrations

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all new modules are properly imported in main.py
2. **Database Errors**: Verify notification_logs table schema includes website_id
3. **Template Errors**: Check context variables match template placeholders
4. **Async Issues**: Ensure all service calls are properly awaited

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('services.trigger_service').setLevel(logging.DEBUG)
```

## Conclusion

The Notification Trigger Service provides a robust, scalable solution for event-based notifications while maintaining full compatibility with the existing notification infrastructure. The implementation follows established patterns and includes comprehensive testing, documentation, and error handling.

The service successfully meets all requirements:
- ✅ Seamless integration with existing notification infrastructure
- ✅ Support for the three required parameters (user_id, website_id, channel_id)
- ✅ Event-to-notification mapping with dynamic message generation
- ✅ Comprehensive API with proper validation and error handling
- ✅ Full test coverage with unit and integration tests
- ✅ Clear integration examples and documentation
- ✅ Performance optimizations and security considerations
