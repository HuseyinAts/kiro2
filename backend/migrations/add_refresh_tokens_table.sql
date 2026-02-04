-- Task 48.4: JWT Refresh Token Database Migration
-- Adds refresh_tokens table for dual-token authentication system
-- Author: Claude
-- Date: 2025-10-27

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::VARCHAR,
    user_id VARCHAR NOT NULL,

    -- Token information
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    jti VARCHAR(255) UNIQUE NOT NULL,

    -- Device and session tracking
    device_id VARCHAR(255),
    device_name VARCHAR(200),
    device_type VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),

    -- Expiration and status
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoke_reason VARCHAR(200),

    -- Usage tracking
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER NOT NULL DEFAULT 0,

    -- System fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_refresh_token_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_refresh_token_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_token_jti ON refresh_tokens(jti);
CREATE INDEX IF NOT EXISTS idx_refresh_token_expires ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_token_revoked ON refresh_tokens(revoked);
CREATE INDEX IF NOT EXISTS idx_refresh_token_user_device ON refresh_tokens(user_id, device_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_refresh_token_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_token_updated_at
    BEFORE UPDATE ON refresh_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_refresh_token_updated_at();

-- Add comments for documentation
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for dual-token authentication (Task 48.4)';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA-256 hash of the refresh token for secure storage';
COMMENT ON COLUMN refresh_tokens.jti IS 'JWT ID from token payload for blacklisting';
COMMENT ON COLUMN refresh_tokens.device_id IS 'Unique device identifier for session tracking';
COMMENT ON COLUMN refresh_tokens.expires_at IS 'Token expiration timestamp (typically 7 days)';
COMMENT ON COLUMN refresh_tokens.revoked IS 'Token revocation status for logout/security';
COMMENT ON COLUMN refresh_tokens.usage_count IS 'Number of times this refresh token was used';

-- Grant permissions (adjust for your database user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON refresh_tokens TO app_user;

-- Cleanup script (optional - for maintenance)
-- Delete expired tokens older than 30 days
-- DELETE FROM refresh_tokens WHERE expires_at < NOW() - INTERVAL '30 days';
