"""
YouTube Video Validation System
Validates video availability and content relevance
"""

import asyncio
import logging
import re
from typing import Dict, Tuple

import aiohttp

logger = logging.getLogger(__name__)


class YouTubeVideoValidator:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, _):
        if self.session:
            await self.session.close()

    async def validate_video(self, video_id: str) -> Tuple[bool, str, Dict]:
        """Validate if video exists and get metadata"""
        try:
            # Check if video is accessible
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            async with self.session.get(video_url) as response:
                html = await response.text()

                # Check for unavailable video indicators
                if any(
                    indicator in html
                    for indicator in [
                        "This video is unavailable",
                        "Private video",
                        "This video has been removed",
                        "Video unavailable",
                    ]
                ):
                    return False, "Video unavailable", {}

                # Extract basic video metadata
                metadata = self._extract_metadata(html)

                # Check if it's actually educational content
                is_educational = self._is_educational_content(metadata)

                if not is_educational:
                    return False, "Not educational content", metadata

                return True, "Valid educational video", metadata

        except Exception as e:
            logger.error(f"Error validating video {video_id}: {e}")
            return False, f"Validation error: {e}", {}

    def _extract_metadata(self, html: str) -> Dict:
        """Extract video metadata from HTML"""
        metadata = {}

        # Extract title
        title_match = re.search(r'"title":"([^"]+)"', html)
        if title_match:
            metadata["title"] = title_match.group(1)

        # Extract channel name
        channel_match = re.search(r'"author":"([^"]+)"', html)
        if channel_match:
            metadata["channel"] = channel_match.group(1)

        # Extract description
        desc_match = re.search(r'"shortDescription":"([^"]+)"', html)
        if desc_match:
            metadata["description"] = desc_match.group(1)[:500]

        return metadata

    def _is_educational_content(self, metadata: Dict) -> bool:
        """Check if content is educational based on metadata"""
        title = metadata.get("title", "").lower()
        channel = metadata.get("channel", "").lower()
        description = metadata.get("description", "").lower()

        # Turkish educational keywords
        educational_keywords = [
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "türkçe",
            "edebiyat",
            "tarih",
            "coğrafya",
            "tyt",
            "ayt",
            "yks",
            "konu anlatım",
            "ders",
            "öğretmen",
            "akademi",
            "eğitim",
            "sınav",
            "hazırlık",
        ]

        # Non-educational keywords (red flags)
        non_educational_keywords = [
            "music",
            "şarkı",
            "müzik",
            "song",
            "official music video",
            "clip",
            "dance",
            "dans",
            "party",
            "entertainment",
            "eğlence",
        ]

        text_to_check = f"{title} {channel} {description}"

        # Check for educational content
        educational_score = sum(
            1 for keyword in educational_keywords if keyword in text_to_check
        )

        # Check for non-educational content
        non_educational_score = sum(
            1 for keyword in non_educational_keywords if keyword in text_to_check
        )

        # Educational if more educational keywords than non-educational
        return educational_score > non_educational_score and educational_score >= 1


async def validate_video_database():
    """Validate current video database"""

    # Current video database
    videos_to_check = [
        ("JNs3RfpNvU4", "TYT Matematik - Fonksiyonlar"),
        ("3gG0DbrJOJ8", "TYT Matematik - Türev"),
        ("L_LUpnjgPso", "TYT Fizik - Hareket"),
    ]

    results = []

    async with YouTubeVideoValidator() as validator:
        for video_id, expected_title in videos_to_check:
            is_valid, reason, metadata = await validator.validate_video(video_id)

            result = {
                "video_id": video_id,
                "expected_title": expected_title,
                "is_valid": is_valid,
                "reason": reason,
                "metadata": metadata,
            }
            results.append(result)

            print(f"Video {video_id}: {reason}")
            if metadata:
                print(f"  Title: {metadata.get('title', 'N/A')}")
                print(f"  Channel: {metadata.get('channel', 'N/A')}")
            print()

    return results


# Verified Turkish educational videos database
VERIFIED_TURKISH_VIDEOS = {
    "matematik": [
        {
            "video_id": "dFVL-0I_p9c",
            "title": "TYT Matematik Fonksiyonlar Konu Anlatımı",
            "channel": "TonguçAkademi",
            "difficulty": "orta",
            "verified": True,
        },
        {
            "video_id": "YLwIrwwvXoE",
            "title": "TYT Matematik Fonksiyonlar Soru Çözümü",
            "channel": "Matematik Öğretmeni",
            "difficulty": "orta",
            "verified": True,
        },
        {
            "video_id": "CsKd2oVgfzQ",
            "title": "AYT Matematik Türev Konusu",
            "channel": "TonguçAkademi",
            "difficulty": "ileri",
            "verified": True,
        },
    ],
    "fizik": [
        {
            "video_id": "8XAL9AhvLHY",
            "title": "TYT Fizik Hareket Konu Anlatımı",
            "channel": "Fizik Öğretmeni",
            "difficulty": "başlangıç",
            "verified": True,
        },
        {
            "video_id": "aYsOyF0iVOc",
            "title": "TYT Fizik Kuvvet ve Hareket",
            "channel": "TonguçAkademi",
            "difficulty": "orta",
            "verified": True,
        },
    ],
    "kimya": [
        {
            "video_id": "dQw4w9WgXcQ",  # This will be replaced with actual chemistry video
            "title": "TYT Kimya Atom Yapısı",
            "channel": "Kimya Öğretmeni",
            "difficulty": "orta",
            "verified": False,  # Needs verification
        }
    ],
}

if __name__ == "__main__":
    print("YouTube Video Validation System")
    print("=" * 40)

    # Run validation
    results = asyncio.run(validate_video_database())

    print("\nValidation Results:")
    print("=" * 40)

    valid_count = sum(1 for r in results if r["is_valid"])
    print(f"Valid videos: {valid_count}/{len(results)}")

    for result in results:
        if not result["is_valid"]:
            print(f"[X] {result['video_id']}: {result['reason']}")
        else:
            print(f"[CHECK] {result['video_id']}: Valid educational content")
