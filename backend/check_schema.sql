-- Check if notification_logs table has metadata column
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'notification_logs' 
  AND table_schema = 'public'
ORDER BY ordinal_position;

-- If metadata column is missing, add it:
-- ALTER TABLE notification_logs ADD COLUMN metadata JSONB;

-- Check recent notifications with metadata
SELECT 
    id,
    notification_type,
    delivery_status,
    website_id,
    metadata,
    created_at
FROM notification_logs 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 10;
