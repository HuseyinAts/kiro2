import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def activate_users():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2')  # pragma: allowlist secret
    emails = ['test@kiro2.com', 'admin@kiro2.com', 'ogretmen@kiro2.com', 'veli@kiro2.com', 'ogrenci@kiro2.com']
    
    async with engine.begin() as conn:
        for email in emails:
            await conn.execute(text("UPDATE users SET is_active = TRUE, is_verified = TRUE WHERE email = :email"), {"email": email})
            print(f"Activated {email}")
            
    await engine.dispose()
    print("All demo users activated!")

try:
    asyncio.run(activate_users())
except Exception as e:
    print('Error:', e)
