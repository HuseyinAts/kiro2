import sys, asyncio
sys.path.insert(0, 'C:/Users/husey/kiro2/backend')
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2')
AsyncSess = sessionmaker(engine, class_=AsyncSession)

async def t():
    async with AsyncSess() as s:
        print('bind:', s.bind)
        print('type:', type(s))
        has_sync = hasattr(s, 'bind') and s.bind is not None and hasattr(s.bind, 'sync_engine')
        print('hasattr(db.bind, sync_engine):', has_sync)
        # Bu kosul False ise refresh token HICBIR ZAMAN kaydedilmiyor!

asyncio.run(t())
