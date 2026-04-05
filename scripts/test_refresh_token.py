import sys, asyncio, hashlib, traceback
sys.path.insert(0, 'C:/Users/husey/kiro2/backend')
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session as SyncSession

engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2')
AsyncSess = sessionmaker(engine, class_=AsyncSession)

async def t():
    async with AsyncSess() as db:
        print("db.bind:", db.bind)
        print("sync_engine:", db.bind.sync_engine)

        # RefreshToken modelini import et
        try:
            from models.database import RefreshToken
            print("RefreshToken import: OK, tablo:", RefreshToken.__tablename__)
            cols = [c.name for c in RefreshToken.__table__.columns]
            print("Kolonlar:", cols)
        except Exception as e:
            print("RefreshToken import HATA:", e)
            traceback.print_exc()
            return

        # Sync session yarat
        sync_db = SyncSession(bind=db.bind.sync_engine)
        try:
            token_hash = hashlib.sha256(b"test_token").hexdigest()
            from datetime import datetime, UTC, timedelta
            db_token = RefreshToken(
                user_id="00000000-0000-0000-0000-000000000001",
                token_hash=token_hash,
                jti="test-jti-123",
                device_id=None,
                device_name=None,
                device_type="desktop",
                ip_address="127.0.0.1",
                user_agent="test",
                expires_at=datetime.now(UTC) + timedelta(days=7),
                revoked=False,
            )
            sync_db.add(db_token)
            sync_db.commit()
            print("BASARILI: refresh token kaydedildi!")
            # Temizle
            sync_db.delete(db_token)
            sync_db.commit()
        except Exception as e:
            print("HATA:", type(e).__name__, str(e))
            traceback.print_exc()
            sync_db.rollback()
        finally:
            sync_db.close()

asyncio.run(t())
