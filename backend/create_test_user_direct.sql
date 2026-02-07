-- Test Kullanıcısı Oluşturma SQL
-- Email: test@kiro2.com
-- Şifre: Test123!

-- Users tablosunu kontrol et/oluştur
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'student',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Test kullanıcısını sil (eğer varsa)
DELETE FROM users WHERE email = 'test@kiro2.com';

-- Test kullanıcısını ekle
-- Şifre: Test123! (bcrypt hash)
-- Hash: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIrS.MjhuG
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active)
VALUES (
    'test@kiro2.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIrS.MjhuG',
    'Test',
    'User',
    'student',
    true
);

-- Doğrulama
SELECT id, email, first_name, last_name, role, is_active, created_at 
FROM users 
WHERE email = 'test@kiro2.com';
