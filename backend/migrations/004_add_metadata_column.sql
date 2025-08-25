-- Migration: Add metadata column to notification_logs
-- Description: Adds JSONB metadata column to store trigger context and additional information

-- Add metadata column if it doesn't exist
ALTER TABLE notification_logs 
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Add index for metadata queries
CREATE INDEX IF NOT EXISTS idx_notification_logs_metadata ON notification_logs USING GIN (metadata);

-- Add comment for documentation
COMMENT ON COLUMN notification_logs.metadata IS 'JSONB metadata containing trigger context, event details, and additional information';
