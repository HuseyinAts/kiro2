"""Create chat_sessions and chat_messages tables."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

SQL_SESSIONS = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    title VARCHAR(255),
    subject_type VARCHAR(20) DEFAULT 'general',
    status VARCHAR(20) DEFAULT 'active',
    context JSONB DEFAULT '{}'::jsonb,
    meta_data JSONB DEFAULT '{}'::jsonb,
    model_name VARCHAR(100) DEFAULT 'qwen3:8b',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2000,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ
)
"""

SQL_MESSAGES = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    session_id VARCHAR NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    image_id VARCHAR,
    model VARCHAR(100),
    tokens_used INTEGER,
    cost FLOAT,
    response_time_ms INTEGER,
    confidence_score FLOAT,
    relevance_score FLOAT,
    user_rating INTEGER,
    is_helpful BOOLEAN,
    feedback_comment TEXT,
    meta_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
"""

async def main():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"
    )
    async with engine.begin() as conn:
        await conn.execute(text(SQL_SESSIONS))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_created ON chat_sessions(created_at)"))
        await conn.execute(text(SQL_MESSAGES))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at)"))

    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename LIKE 'chat%' ORDER BY tablename"))
        for row in r:
            print(f"OK {row[0]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
