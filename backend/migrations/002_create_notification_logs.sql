-- Migration: Create notification_logs table
-- Description: Creates a table to store notification logs for the notification system

-- Create notification_logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    channel_id TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    message_content TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    delivery_status TEXT NOT NULL DEFAULT 'queued',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_notification_logs_user_id ON notification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_notification_type ON notification_logs(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_logs_delivery_status ON notification_logs(delivery_status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON notification_logs(created_at);

-- Add comments for documentation
COMMENT ON TABLE notification_logs IS 'Stores logs of all notifications sent through the system';
COMMENT ON COLUMN notification_logs.id IS 'Unique identifier for the notification log';
COMMENT ON COLUMN notification_logs.user_id IS 'User ID the notification was sent to';
COMMENT ON COLUMN notification_logs.channel_id IS 'Slack channel ID or user Slack ID';
COMMENT ON COLUMN notification_logs.notification_type IS 'Type of notification (audit_complete, audit_started, integration_status, system_alert)';
COMMENT ON COLUMN notification_logs.message_content IS 'Message content that was sent';
COMMENT ON COLUMN notification_logs.priority IS 'Priority level (low, normal, high, urgent)';
COMMENT ON COLUMN notification_logs.delivery_status IS 'Current delivery status (queued, sending, delivered, failed, retrying)';
COMMENT ON COLUMN notification_logs.created_at IS 'When the notification was created';
COMMENT ON COLUMN notification_logs.updated_at IS 'When the notification was last updated';
COMMENT ON COLUMN notification_logs.delivered_at IS 'When the notification was delivered';
COMMENT ON COLUMN notification_logs.error_message IS 'Error message if delivery failed';
COMMENT ON COLUMN notification_logs.retry_count IS 'Number of retry attempts for failed notifications';

-- Add foreign key constraint to user_slack_tokens
ALTER TABLE notification_logs
ADD CONSTRAINT fk_notification_logs_user_slack_tokens
FOREIGN KEY (user_id)
REFERENCES user_slack_tokens(user_id)
ON DELETE CASCADE;
