-- Migration: Update notification types
-- Description: Updates notification_logs table to support new notification types (ai_visibility, competitor_analysis)

-- First, check if there's an enum type and drop it if exists
DROP TYPE IF EXISTS notification_type_enum CASCADE;

-- Drop any existing constraints on notification_type
ALTER TABLE notification_logs DROP CONSTRAINT IF EXISTS chk_notification_type;
ALTER TABLE notification_logs DROP CONSTRAINT IF EXISTS notification_logs_notification_type_check;

-- Ensure the column is TEXT type (not enum)
ALTER TABLE notification_logs ALTER COLUMN notification_type TYPE TEXT;

-- Add new constraint with updated notification types
ALTER TABLE notification_logs 
ADD CONSTRAINT chk_notification_type CHECK (
    notification_type IN (
        'audit_complete',
        'ai_visibility', 
        'competitor_analysis',
        'system_alert'
    )
);

-- Add metadata column if it doesn't exist
ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Add website_id column if it doesn't exist  
ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS website_id UUID;

-- Create index for metadata queries
CREATE INDEX IF NOT EXISTS idx_notification_logs_metadata ON notification_logs USING GIN (metadata);

-- Create index for website_id
CREATE INDEX IF NOT EXISTS idx_notification_logs_website_id ON notification_logs(website_id);

-- Update comments to reflect new notification types
COMMENT ON COLUMN notification_logs.notification_type IS 'Type of notification (audit_complete, ai_visibility, competitor_analysis, system_alert)';
COMMENT ON COLUMN notification_logs.metadata IS 'JSONB metadata containing trigger context, event details, and additional information';
COMMENT ON COLUMN notification_logs.website_id IS 'Website ID related to the notification (optional)';
