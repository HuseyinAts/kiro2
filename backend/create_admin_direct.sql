-- Create admin user directly
-- Password: admin123 (bcrypt hash)

DELETE FROM users WHERE email = 'admin@turkiyesinav.com';

INSERT INTO users (
    id,
    email,
    username,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_verified,
    created_at,
    updated_at
) VALUES (
    'admin-001',
    'admin@turkiyesinav.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYn0H6Z6qWu',
    'Platform',
    'Yöneticisi',
    'admin',
    1,
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Verify
SELECT id, email, username, role FROM users WHERE email = 'admin@turkiyesinav.com';
