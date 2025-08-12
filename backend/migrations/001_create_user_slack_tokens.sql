-- Migration: Create user_slack_tokens table for Slack OAuth integration
-- Following the 3-layer architecture pattern from Goosebump Crew

-- Create the user_slack_tokens table
CREATE TABLE IF NOT EXISTS user_slack_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    slack_user_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    bot_user_id VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    scope TEXT NOT NULL,
    channel_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_slack_tokens_user_id ON user_slack_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_user_slack_tokens_team_id ON user_slack_tokens(team_id);
CREATE INDEX IF NOT EXISTS idx_user_slack_tokens_slack_user_id ON user_slack_tokens(slack_user_id);

-- Create unique constraint to prevent duplicate integrations per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_slack_tokens_unique_user ON user_slack_tokens(user_id);

-- Add updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_user_slack_tokens_updated_at 
    BEFORE UPDATE ON user_slack_tokens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE user_slack_tokens IS 'Stores Slack OAuth tokens and integration data for users';
COMMENT ON COLUMN user_slack_tokens.user_id IS 'Internal user ID from the main user system';
COMMENT ON COLUMN user_slack_tokens.slack_user_id IS 'Slack user ID from OAuth response';
COMMENT ON COLUMN user_slack_tokens.team_id IS 'Slack workspace/team ID';
COMMENT ON COLUMN user_slack_tokens.team_name IS 'Slack workspace/team name';
COMMENT ON COLUMN user_slack_tokens.bot_user_id IS 'Bot user ID for the Slack app';
COMMENT ON COLUMN user_slack_tokens.access_token IS 'Encrypted Slack access token';
COMMENT ON COLUMN user_slack_tokens.refresh_token IS 'Encrypted Slack refresh token (if provided)';
COMMENT ON COLUMN user_slack_tokens.scope IS 'OAuth scopes granted by the user';
COMMENT ON COLUMN user_slack_tokens.channel_id IS 'Default channel ID for notifications';
