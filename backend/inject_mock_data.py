import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2"
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.begin() as conn:
        print("Inserting mock user...")
        user_id = str(uuid.uuid4())
        # Make sure users table exists and columns match
        # Let's check table exists first
        try:
            await conn.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, full_name, is_active)
                    VALUES (:id, :email, 'hashed', 'Mock User', true)
                    ON CONFLICT DO NOTHING
                """),
                {"id": user_id, "email": f"mock_{user_id}@example.com"}
            )
        except Exception as e:
            print("Could not insert user, it might be due to schema. Error:", e)
            return

        print("Inserting mock data into chat_sessions, chat_messages, image_uploads...")
        total_sessions = 10000
        batch_size = 500
        
        for i in range(0, total_sessions, batch_size):
            sessions = []
            messages = []
            images = []
            
            for _ in range(batch_size):
                session_id = str(uuid.uuid4())
                sessions.append({
                    "id": session_id,
                    "user_id": user_id,
                    "title": "Mock Session",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                })
                
                for j in range(8):
                    messages.append({
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "role": "user" if j % 2 == 0 else "assistant",
                        "content": f"Mock message {j} for seq_scan tests",
                        "created_at": datetime.now(timezone.utc)
                    })
                    
                for k in range(2):
                    images.append({
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "user_id": user_id,
                        "filename": f"mock_img_{k}.jpg",
                        "file_path": "/mock/path/img.jpg",
                        "ocr_text": "Mock OCR TEXT "*20,
                        "processing_status": "COMPLETED"
                    })
            try:
                await conn.execute(
                    text("""
                        INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at, is_active)
                        VALUES (:id, :user_id, :title, :created_at, :updated_at, :is_active)
                    """),
                    sessions
                )
                
                await conn.execute(
                    text("""
                        INSERT INTO chat_messages (id, session_id, role, content, created_at)
                        VALUES (:id, :session_id, :role, :content, :created_at)
                    """),
                    messages
                )
                
                await conn.execute(
                    text("""
                        INSERT INTO image_uploads (id, session_id, user_id, filename, file_path, ocr_text, processing_status)
                        VALUES (:id, :session_id, :user_id, :filename, :file_path, :ocr_text, :processing_status)
                    """),
                    images
                )
            except Exception as e:
                print(f"Batch failed at {i}:", e)
                break
                
            print(f"Inserted batch up to {i + batch_size} sessions")
            
    print("Mock data injection completed.")

if __name__ == "__main__":
    asyncio.run(main())
