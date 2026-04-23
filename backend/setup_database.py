#!/usr/bin/env python3
"""
YKS Hazırlık Platformu - Veritabanı Kurulum ve Test Scripti
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import uuid
from datetime import UTC, datetime

import asyncpg
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models_unified import (
    Base,
    Kullanici,
    KullaniciRolu,
    OgrenmeProfili,
    Soru,
    SoruZorluk,
)

# Database configuration (Port 5434 - KIRO2 Standard)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5434/turkiye_sinav_db"
ASYNC_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5434/turkiye_sinav_db"
)


async def create_database():
    """Create database if not exists"""
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="postgres",
            password="postgres",
            database="postgres",
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", "turkiye_sinav_db"
        )

        if not exists:
            # Create database
            await conn.execute("CREATE DATABASE turkiye_sinav_db")
            print("[OK] Veritabani olusturuldu: turkiye_sinav_db")
        else:
            print("[OK] Veritabani zaten mevcut: turkiye_sinav_db")

        await conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Veritabanı oluşturma hatası: {e}")
        return False


async def create_tables():
    """Create all tables using SQLAlchemy"""
    try:
        # Use sync engine for table creation
        engine = create_engine(DATABASE_URL.replace("+asyncpg", ""))

        # Drop all existing tables (for clean start)
        Base.metadata.drop_all(bind=engine)
        print("[DEL] Eski tablolar temizlendi")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("[OK] Tüm tablolar oluşturuldu")

        engine.dispose()
        return True

    except Exception as e:
        print(f"[ERROR] Tablo oluşturma hatası: {e}")
        return False


async def insert_test_data():
    """Insert test data"""
    try:
        engine = create_async_engine(ASYNC_DATABASE_URL)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Create test users
            ogrenci1 = Kullanici(
                id=uuid.uuid4(),
                ad="Ali",
                soyad="Yılmaz",
                email="ali@test.com",
                telefon="5551234567",
                rol=KullaniciRolu.OGRENCI,
                parola_hash="hash123",
                sinif=11,
                okul="Atatürk Lisesi",
                alan="Sayısal",
                hedef_universite="Boğaziçi Üniversitesi",
                hedef_bolum="Bilgisayar Mühendisliği",
                aktif=True,
                kayit_tarihi=datetime.now(UTC),
            )

            ogrenci2 = Kullanici(
                id=uuid.uuid4(),
                ad="Ayşe",
                soyad="Demir",
                email="ayse@test.com",
                telefon="5559876543",
                rol=KullaniciRolu.OGRENCI,
                parola_hash="hash456",
                sinif=12,
                okul="Cumhuriyet Lisesi",
                alan="Eşit Ağırlık",
                hedef_universite="ODTÜ",
                hedef_bolum="İşletme",
                aktif=True,
                kayit_tarihi=datetime.now(UTC),
            )

            ogretmen = Kullanici(
                id=uuid.uuid4(),
                ad="Mehmet",
                soyad="Öğretmen",
                email="mehmet@test.com",
                telefon="5555555555",
                rol=KullaniciRolu.OGRETMEN,
                parola_hash="hash789",
                okul="Atatürk Lisesi",
                aktif=True,
                kayit_tarihi=datetime.now(UTC),
            )

            # Add users to session
            session.add(ogrenci1)
            session.add(ogrenci2)
            session.add(ogretmen)

            # Create learning profiles
            profil1 = OgrenmeProfili(
                id=uuid.uuid4(),
                kullanici_id=ogrenci1.id,
                vark_visual=0.8,
                vark_auditory=0.3,
                vark_reading=0.6,
                vark_kinesthetic=0.4,
                felder_active_reflective=0.3,
                felder_sensing_intuitive=-0.2,
                felder_visual_verbal=0.5,
                felder_sequential_global=-0.1,
                hibrit_kod="V-AIVS",
                dominant_vark="visual",
                dominant_felder="visual_verbal",
                guven_seviyesi=0.85,
                tespit_sayisi=3,
                grup_calismasi_tercihi=0.7,
                ogretmene_saygi_seviyesi=0.9,
                aile_katilim_derecesi=0.6,
                akran_rekabet_egilimi=0.5,
                ilk_tespit_tarihi=datetime.now(UTC),
            )

            session.add(profil1)

            # Create test questions
            sorular = [
                Soru(
                    id=uuid.uuid4(),
                    kod="TYT-MAT-001",
                    metin="Bir sayının 3 katının 5 fazlası 26 ise, bu sayı kaçtır?",
                    secenekler={"A": "5", "B": "6", "C": "7", "D": "8", "E": "9"},
                    dogru_cevap="C",
                    sinav_tipi="TYT",
                    konu="Matematik",
                    alt_konu="Denklemler",
                    kazanim="Birinci dereceden bir bilinmeyenli denklemleri çözer",
                    irt_discrimination=1.2,
                    irt_difficulty=-0.5,
                    irt_guessing=0.2,
                    zorluk=SoruZorluk.KOLAY,
                    kelime_sayisi=12,
                    aktif=True,
                ),
                Soru(
                    id=uuid.uuid4(),
                    kod="TYT-MAT-002",
                    metin="x² - 5x + 6 = 0 denkleminin kökleri çarpımı kaçtır?",
                    secenekler={"A": "2", "B": "3", "C": "5", "D": "6", "E": "10"},
                    dogru_cevap="D",
                    sinav_tipi="TYT",
                    konu="Matematik",
                    alt_konu="İkinci Dereceden Denklemler",
                    kazanim="İkinci dereceden denklemlerin köklerini bulur",
                    irt_discrimination=1.5,
                    irt_difficulty=0.3,
                    irt_guessing=0.2,
                    zorluk=SoruZorluk.ORTA,
                    kelime_sayisi=10,
                    aktif=True,
                ),
                Soru(
                    id=uuid.uuid4(),
                    kod="TYT-TUR-001",
                    metin="Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?",
                    secenekler={
                        "A": "Yarınki toplantıya katılacak mısınız?",
                        "B": "Bu günkü gazetede önemli haberler var.",
                        "C": "Dünkü maçı izlediniz mi?",
                        "D": "Önceki hafta tatildeydik.",
                        "E": "Sonraki durakta ineceğim.",
                    },
                    dogru_cevap="B",
                    sinav_tipi="TYT",
                    konu="Türkçe",
                    alt_konu="Yazım Kuralları",
                    kazanim="Yazım kurallarını uygular",
                    irt_discrimination=1.0,
                    irt_difficulty=-0.8,
                    irt_guessing=0.2,
                    zorluk=SoruZorluk.COK_KOLAY,
                    kelime_sayisi=15,
                    morfoloji_skoru=0.3,
                    aktif=True,
                ),
            ]

            for soru in sorular:
                session.add(soru)

            # Commit all data
            await session.commit()
            print("[OK] Test verileri eklendi")

            # Verify data
            from sqlalchemy import select

            # Count users
            result = await session.execute(select(Kullanici))
            users = result.scalars().all()
            print(f"   - {len(users)} kullanıcı")

            # Count questions
            result = await session.execute(select(Soru))
            questions = result.scalars().all()
            print(f"   - {len(questions)} soru")

            # Count profiles
            result = await session.execute(select(OgrenmeProfili))
            profiles = result.scalars().all()
            print(f"   - {len(profiles)} öğrenme profili")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"[ERROR] Test verisi ekleme hatası: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_queries():
    """Test database queries"""
    try:
        engine = create_async_engine(ASYNC_DATABASE_URL)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            from sqlalchemy import select

            print("\n[STATS] Veritabani Sorgu Testleri:")

            # Test 1: Get all students
            result = await session.execute(
                select(Kullanici).where(Kullanici.rol == KullaniciRolu.OGRENCI)
            )
            students = result.scalars().all()
            print(f"[OK] Öğrenci sayısı: {len(students)}")
            for student in students:
                print(f"   - {student.ad} {student.soyad} ({student.sinif}. sınıf)")

            # Test 2: Get questions by difficulty
            result = await session.execute(
                select(Soru).where(Soru.zorluk == SoruZorluk.KOLAY)
            )
            easy_questions = result.scalars().all()
            print(f"[OK] Kolay soru sayısı: {len(easy_questions)}")

            # Test 3: Get learning profile
            result = await session.execute(select(OgrenmeProfili))
            profiles = result.scalars().all()
            if profiles:
                profile = profiles[0]
                print(f"[OK] Öğrenme profili: {profile.hibrit_kod}")
                print(f"   - VARK Dominant: {profile.dominant_vark}")
                print(f"   - Güven seviyesi: {profile.guven_seviyesi}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"[ERROR] Sorgu testi hatası: {e}")
        return False


async def main():
    """Main setup function"""
    print("=" * 60)
    print("YKS HAZIRLIK PLATFORMU - VERITABANI KURULUMU")
    print("=" * 60)

    # Step 1: Create database
    if not await create_database():
        print(
            "\n[ERROR] Veritabanı oluşturulamadı. PostgreSQL'in çalıştığından emin olun."
        )
        print("   docker-compose up -d postgres")
        return

    # Step 2: Create tables
    if not await create_tables():
        print("\n[ERROR] Tablolar oluşturulamadı.")
        return

    # Step 3: Insert test data
    if not await insert_test_data():
        print("\n[ERROR] Test verileri eklenemedi.")
        return

    # Step 4: Test queries
    if not await test_queries():
        print("\n[ERROR] Sorgular test edilemedi.")
        return

    print("\n" + "=" * 60)
    print("[OK] VERİTABANI KURULUMU BAŞARIYLA TAMAMLANDI!")
    print("=" * 60)

    print("\n[INFO] Veritabani Bilgileri:")
    print("   - Host: localhost")
    print("   - Port: 5432")
    print("   - Database: turkiye_sinav_db")
    print("   - User: postgres")
    print("   - Password: postgres")

    print("\n[NEXT] Sonraki Adimlar:")
    print("1. Backend'i başlatın: uvicorn main:app --reload")
    print("2. API Docs: http://localhost:8000/docs")
    print("3. Frontend'i başlatın: npm run dev")


if __name__ == "__main__":
    asyncio.run(main())
