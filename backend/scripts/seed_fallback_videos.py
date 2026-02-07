"""
Seed Fallback Videos
P0 Fix #3: Add example videos to database for fallback system

This script populates the fallback_videos table with high-quality
Turkish educational videos for when live search fails.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_async_session_context
from database.learning_path_repository import learning_path_repository

# Example high-quality Turkish educational videos
FALLBACK_VIDEOS = [
    # Matematik
    {
        "subject": "matematik",
        "topic": "türev",
        "video_id": "FALLBACK_MAT_TUREV_001",
        "title": "Türev - Temel Kavramlar ve Örnekler",
        "description": "Türev konusuna giriş ve temel örnekler",
        "url": "https://www.youtube.com/watch?v=example1",
        "thumbnail_url": "https://i.ytimg.com/vi/example1/hqdefault.jpg",
        "duration": "15:30",
        "duration_minutes": 15,
        "channel_name": "Matematik Akademi",
        "channel_id": "UC_matematik_akademi",
        "turkish_score": 1.0,
        "relevance_score": 0.95,
        "quality_score": 0.9,
        "final_score": 0.95,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["matematik", "türev", "kalkülüs", "YKS"],
    },
    {
        "subject": "matematik",
        "topic": "integral",
        "video_id": "FALLBACK_MAT_INTEGRAL_001",
        "title": "İntegral - Belirli ve Belirsiz İntegral",
        "description": "İntegral konusuna giriş ve örnekler",
        "url": "https://www.youtube.com/watch?v=example2",
        "thumbnail_url": "https://i.ytimg.com/vi/example2/hqdefault.jpg",
        "duration": "18:45",
        "duration_minutes": 18,
        "channel_name": "Matematik Akademi",
        "channel_id": "UC_matematik_akademi",
        "turkish_score": 1.0,
        "relevance_score": 0.95,
        "quality_score": 0.9,
        "final_score": 0.95,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["matematik", "integral", "kalkülüs", "YKS"],
    },
    {
        "subject": "matematik",
        "topic": None,  # General matematik
        "video_id": "FALLBACK_MAT_GENEL_001",
        "title": "Matematik - Genel Tekrar ve İpuçları",
        "description": "YKS için matematik genel tekrar",
        "url": "https://www.youtube.com/watch?v=example3",
        "thumbnail_url": "https://i.ytimg.com/vi/example3/hqdefault.jpg",
        "duration": "25:00",
        "duration_minutes": 25,
        "channel_name": "YKS Hazırlık",
        "channel_id": "UC_yks_hazirlik",
        "turkish_score": 1.0,
        "relevance_score": 0.85,
        "quality_score": 0.9,
        "final_score": 0.88,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["matematik", "YKS", "genel tekrar"],
    },
    # Fizik
    {
        "subject": "fizik",
        "topic": "hareket",
        "video_id": "FALLBACK_FIZ_HAREKET_001",
        "title": "Hareket - Newton Yasaları ve Kinematik",
        "description": "Hareket konusuna giriş ve temel kavramlar",
        "url": "https://www.youtube.com/watch?v=example4",
        "thumbnail_url": "https://i.ytimg.com/vi/example4/hqdefault.jpg",
        "duration": "20:15",
        "duration_minutes": 20,
        "channel_name": "Fizik Dünyası",
        "channel_id": "UC_fizik_dunyasi",
        "turkish_score": 1.0,
        "relevance_score": 0.95,
        "quality_score": 0.92,
        "final_score": 0.96,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["fizik", "hareket", "Newton", "YKS"],
    },
    {
        "subject": "fizik",
        "topic": "elektrik",
        "video_id": "FALLBACK_FIZ_ELEKTRIK_001",
        "title": "Elektrik - Akım ve Devreler",
        "description": "Elektrik konusuna giriş ve devre analizı",
        "url": "https://www.youtube.com/watch?v=example5",
        "thumbnail_url": "https://i.ytimg.com/vi/example5/hqdefault.jpg",
        "duration": "22:30",
        "duration_minutes": 22,
        "channel_name": "Fizik Dünyası",
        "channel_id": "UC_fizik_dunyasi",
        "turkish_score": 1.0,
        "relevance_score": 0.94,
        "quality_score": 0.91,
        "final_score": 0.95,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["fizik", "elektrik", "devre", "YKS"],
    },
    {
        "subject": "fizik",
        "topic": None,  # General fizik
        "video_id": "FALLBACK_FIZ_GENEL_001",
        "title": "Fizik - YKS Sınav Taktikleri",
        "description": "YKS için fizik sınav stratejileri",
        "url": "https://www.youtube.com/watch?v=example6",
        "thumbnail_url": "https://i.ytimg.com/vi/example6/hqdefault.jpg",
        "duration": "30:00",
        "duration_minutes": 30,
        "channel_name": "YKS Hazırlık",
        "channel_id": "UC_yks_hazirlik",
        "turkish_score": 1.0,
        "relevance_score": 0.88,
        "quality_score": 0.90,
        "final_score": 0.89,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["fizik", "YKS", "sınav taktikleri"],
    },
    # Kimya
    {
        "subject": "kimya",
        "topic": "atom",
        "video_id": "FALLBACK_KIM_ATOM_001",
        "title": "Atom - Atomun Yapısı ve Periyodik Sistem",
        "description": "Atom konusuna giriş ve periyodik cetvel",
        "url": "https://www.youtube.com/watch?v=example7",
        "thumbnail_url": "https://i.ytimg.com/vi/example7/hqdefault.jpg",
        "duration": "17:45",
        "duration_minutes": 17,
        "channel_name": "Kimya Lab",
        "channel_id": "UC_kimya_lab",
        "turkish_score": 1.0,
        "relevance_score": 0.96,
        "quality_score": 0.93,
        "final_score": 0.96,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["kimya", "atom", "periyodik sistem", "YKS"],
    },
    {
        "subject": "kimya",
        "topic": "reaksiyon",
        "video_id": "FALLBACK_KIM_REAKSIYON_001",
        "title": "Kimyasal Reaksiyonlar - Denklem Denkleştirme",
        "description": "Kimyasal reaksiyonlar ve denklem denkleştirme",
        "url": "https://www.youtube.com/watch?v=example8",
        "thumbnail_url": "https://i.ytimg.com/vi/example8/hqdefault.jpg",
        "duration": "19:20",
        "duration_minutes": 19,
        "channel_name": "Kimya Lab",
        "channel_id": "UC_kimya_lab",
        "turkish_score": 1.0,
        "relevance_score": 0.94,
        "quality_score": 0.92,
        "final_score": 0.95,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["kimya", "reaksiyon", "denklem", "YKS"],
    },
    {
        "subject": "kimya",
        "topic": None,  # General kimya
        "video_id": "FALLBACK_KIM_GENEL_001",
        "title": "Kimya - YKS Hazırlık Stratejileri",
        "description": "YKS için kimya çalışma yöntemleri",
        "url": "https://www.youtube.com/watch?v=example9",
        "thumbnail_url": "https://i.ytimg.com/vi/example9/hqdefault.jpg",
        "duration": "28:15",
        "duration_minutes": 28,
        "channel_name": "YKS Hazırlık",
        "channel_id": "UC_yks_hazirlik",
        "turkish_score": 1.0,
        "relevance_score": 0.87,
        "quality_score": 0.90,
        "final_score": 0.89,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["kimya", "YKS", "çalışma yöntemleri"],
    },
    # Biyoloji
    {
        "subject": "biyoloji",
        "topic": None,
        "video_id": "FALLBACK_BIO_GENEL_001",
        "title": "Biyoloji - Hücre Biyolojisi Temelleri",
        "description": "Hücre yapısı ve fonksiyonları",
        "url": "https://www.youtube.com/watch?v=example10",
        "thumbnail_url": "https://i.ytimg.com/vi/example10/hqdefault.jpg",
        "duration": "24:00",
        "duration_minutes": 24,
        "channel_name": "Biyoloji Dünyası",
        "channel_id": "UC_biyoloji_dunyasi",
        "turkish_score": 1.0,
        "relevance_score": 0.92,
        "quality_score": 0.91,
        "final_score": 0.94,
        "is_accessible": True,
        "is_embeddable": True,
        "is_turkish": True,
        "is_example": True,
        "tags": ["biyoloji", "hücre", "YKS"],
    },
]


async def seed_fallback_videos():
    """Seed fallback videos to database"""
    print("🌱 Seeding fallback videos to database...")

    async with get_async_session_context() as session:
        try:
            count = await learning_path_repository.batch_create_fallback_videos(
                session, FALLBACK_VIDEOS
            )
            print(f"✅ Successfully seeded {count} fallback videos!")
            print("📊 Subjects covered: matematik, fizik, kimya, biyoloji")
            print(f"📹 Total videos: {len(FALLBACK_VIDEOS)}")
            return count
        except Exception as e:
            print(f"❌ Error seeding fallback videos: {e}")
            raise


async def verify_fallback_videos():
    """Verify fallback videos were seeded correctly"""
    print("\n🔍 Verifying fallback videos...")

    async with get_async_session_context() as session:
        subjects = ["matematik", "fizik", "kimya", "biyoloji"]

        for subject in subjects:
            videos = await learning_path_repository.get_fallback_videos(
                session, subject, None, 10
            )
            print(f"  {subject}: {len(videos)} videos")

        print("✅ Verification complete!")


async def main():
    """Main function"""
    print("=" * 60)
    print("FALLBACK VIDEO SEEDER - P0 FIX #3")
    print("=" * 60)

    try:
        # Seed videos
        count = await seed_fallback_videos()

        # Verify
        await verify_fallback_videos()

        print("\n" + "=" * 60)
        print(f"✅ SUCCESS: {count} fallback videos seeded!")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ FAILED: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    asyncio.run(main())
