-- Task 48.6: API Key Management Migration
-- Adds api_keys table for scoped third-party integrations
-- Author: Claude
-- Date: 2025-10-27

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- API Key information
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Permissions and scopes
    scopes JSON,
    allowed_ips JSON,
    rate_limit INTEGER NOT NULL DEFAULT 1000,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoke_reason VARCHAR(200),

    -- Usage tracking
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_ip VARCHAR(45),

    -- Security
    created_from_ip VARCHAR(45),

    -- System fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_api_key_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_key_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_key_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_key_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_key_revoked ON api_keys(revoked);
CREATE INDEX IF NOT EXISTS idx_api_key_expires ON api_keys(expires_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_api_key_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER api_key_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_api_key_updated_at();

-- Add comments for documentation
COMMENT ON TABLE api_keys IS 'API keys for third-party integrations (Task 48.6)';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the API key for secure storage';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 8 characters for identification (e.g., kiro2_prod_1a2b3c4d)';
COMMENT ON COLUMN api_keys.scopes IS 'JSON array of permission scopes (read:exam, write:content, etc.)';
COMMENT ON COLUMN api_keys.allowed_ips IS 'JSON array of whitelisted IP addresses (optional)';
COMMENT ON COLUMN api_keys.rate_limit IS 'Maximum requests per hour (default: 1000)';
COMMENT ON COLUMN api_keys.usage_count IS 'Total number of times this key was used';

-- Grant permissions (adjust for your database user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO app_user;
