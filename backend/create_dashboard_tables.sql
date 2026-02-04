-- Dashboard Tables Migration
-- Created: 2025-11-17
-- Purpose: Add student_goals and notifications tables for dashboard service

-- Create student_goals table
CREATE TABLE IF NOT EXISTS student_goals (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    goal_type VARCHAR(20) NOT NULL,  -- 'gunluk', 'haftalik', 'aylik'
    target_value FLOAT NOT NULL,
    current_value FLOAT DEFAULT 0,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'aktif',  -- 'aktif', 'tamamlandi', 'iptal'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(20) NOT NULL,  -- 'basari', 'uyari', 'bilgi', 'hata'
    is_read BOOLEAN DEFAULT 0,
    action_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_student_goals_user ON student_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_student_goals_status ON student_goals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);
