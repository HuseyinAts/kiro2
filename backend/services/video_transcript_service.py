"""
Video Transkript Servisi
Teknofest 2025 Eğitim Eylemci Platformu

Task 72.3: Video Transkript
- Auto-generated transcripts
- Manual transcript editing
- Searchable transcripts

Requirements: REQ-14.1, REQ-14.2
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.video_solution import (
    TranscriptStatus,
    VideoSolution,
    VideoTranscript,
)

logger = logging.getLogger(__name__)


# ============================================================================
# TASK 72.3: Video Transcript Service
# ============================================================================


class VideoTranscriptService:
    """Video transkript servisi"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_auto_transcript(
        self, video_id: str, video_path: Path, language: str = "tr"
    ) -> Tuple[bool, Optional[str], Optional[VideoTranscript]]:
        """
        Otomatik transkript oluştur (TASK 72.3: Auto-generated transcripts)

        Bu fonksiyon gerçek implementasyonda Whisper AI veya Google Speech-to-Text
        gibi bir servis kullanmalı. Şimdilik placeholder implementation.

        Args:
            video_id: Video ID
            video_path: Video dosya yolu
            language: Dil kodu

        Returns:
            tuple: (başarılı mı, hata mesajı, VideoTranscript)
        """
        try:
            # Placeholder: Gerçek implementasyonda Whisper AI kullanılacak
            # import whisper
            # model = whisper.load_model("base")
            # result = model.transcribe(str(video_path), language=language)

            # Şimdilik mock data
            mock_segments = [
                {
                    "start": 0.0,
                    "end": 5.2,
                    "text": "Merhaba arkadaşlar, bugün matematik sorusunu çözeceğiz.",
                },
                {"start": 5.2, "end": 10.5, "text": "Bu soru fonksiyonlar konusundan."},
                {
                    "start": 10.5,
                    "end": 18.3,
                    "text": "Öncelikle verilen fonksiyonu analiz edelim.",
                },
            ]

            full_text = " ".join(seg["text"] for seg in mock_segments)

            # Transkript kaydı oluştur
            transcript = VideoTranscript(
                video_id=video_id,
                language=language,
                full_text=full_text,
                timestamped_segments={"segments": mock_segments},
                transcript_status=TranscriptStatus.AUTO_GENERATED,
                auto_generated_by="Whisper AI (Mock)",
                auto_generation_confidence=0.95,
                auto_generated_at=datetime.utcnow(),
                word_count=len(full_text.split()),
                average_words_per_minute=150.0,
                readability_score=75.0,
            )

            self.db.add(transcript)

            # Video kaydını güncelle
            result = await self.db.execute(
                select(VideoSolution).where(VideoSolution.id == video_id)
            )
            video = result.scalar_one_or_none()

            if video:
                video.has_transcript = True

            await self.db.commit()
            await self.db.refresh(transcript)

            logger.info(f"Auto transcript generated for video: {video_id}")
            return True, None, transcript

        except Exception as e:
            logger.error(f"Auto transcript generation error: {e}")
            await self.db.rollback()
            return False, f"Transkript oluşturma hatası: {str(e)}", None

    async def update_transcript(
        self,
        transcript_id: str,
        user_id: str,
        full_text: Optional[str] = None,
        timestamped_segments: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[str], Optional[VideoTranscript]]:
        """
        Transkripti manuel olarak düzenle (TASK 72.3: Manual transcript editing)

        Args:
            transcript_id: Transkript ID
            user_id: Düzenleyen kullanıcı ID
            full_text: Yeni tam metin
            timestamped_segments: Yeni zaman damgalı segmentler

        Returns:
            tuple: (başarılı mı, hata mesajı, VideoTranscript)
        """
        try:
            result = await self.db.execute(
                select(VideoTranscript).where(VideoTranscript.id == transcript_id)
            )
            transcript = result.scalar_one_or_none()

            if not transcript:
                return False, "Transkript bulunamadı", None

            # Güncelleme
            if full_text is not None:
                transcript.full_text = full_text
                transcript.word_count = len(full_text.split())

            if timestamped_segments is not None:
                transcript.timestamped_segments = timestamped_segments

            # Manuel düzenleme bilgilerini güncelle
            transcript.transcript_status = TranscriptStatus.MANUALLY_EDITED
            transcript.manually_edited_by = user_id
            transcript.manually_edited_at = datetime.utcnow()
            transcript.edit_count += 1

            await self.db.commit()
            await self.db.refresh(transcript)

            logger.info(f"Transcript manually edited: {transcript_id} by {user_id}")
            return True, None, transcript

        except Exception as e:
            logger.error(f"Transcript update error: {e}")
            await self.db.rollback()
            return False, f"Transkript güncelleme hatası: {str(e)}", None

    async def search_transcripts(
        self, query: str, video_id: Optional[str] = None, language: str = "tr"
    ) -> List[Dict]:
        """
        Transkriptlerde arama yap (TASK 72.3: Searchable transcripts)

        Args:
            query: Arama sorgusu
            video_id: Belirli bir video ile sınırla (opsiyonel)
            language: Dil filtresi

        Returns:
            list: Eşleşen transkriptler ve segmentler
        """
        try:
            # Query oluştur
            stmt = select(VideoTranscript).where(
                VideoTranscript.language == language, VideoTranscript.is_active == True
            )

            if video_id:
                stmt = stmt.where(VideoTranscript.video_id == video_id)

            # Full-text search (basit implementasyon)
            # Gerçek implementasyonda PostgreSQL full-text search veya Elasticsearch kullanılmalı
            stmt = stmt.where(VideoTranscript.full_text.ilike(f"%{query}%"))

            result = await self.db.execute(stmt)
            transcripts = result.scalars().all()

            # Sonuçları formatla
            search_results = []
            for transcript in transcripts:
                # Eşleşen segmentleri bul
                matching_segments = []
                for segment in transcript.timestamped_segments.get("segments", []):
                    if query.lower() in segment["text"].lower():
                        matching_segments.append(
                            {
                                "start": segment["start"],
                                "end": segment["end"],
                                "text": segment["text"],
                                "highlight": self._highlight_text(
                                    segment["text"], query
                                ),
                            }
                        )

                if matching_segments:
                    search_results.append(
                        {
                            "transcript_id": transcript.id,
                            "video_id": transcript.video_id,
                            "language": transcript.language,
                            "matching_segments": matching_segments,
                            "total_matches": len(matching_segments),
                        }
                    )

            logger.info(f"Transcript search: '{query}' - {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Transcript search error: {e}")
            return []

    @staticmethod
    def _highlight_text(text: str, query: str) -> str:
        """Metinde arama terimini vurgula"""
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(lambda m: f"**{m.group()}**", text)

    async def extract_keywords(
        self, transcript_id: str
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Transkriptten anahtar kelimeleri çıkar

        Args:
            transcript_id: Transkript ID

        Returns:
            tuple: (başarılı mı, hata mesajı, anahtar kelimeler)
        """
        try:
            result = await self.db.execute(
                select(VideoTranscript).where(VideoTranscript.id == transcript_id)
            )
            transcript = result.scalar_one_or_none()

            if not transcript:
                return False, "Transkript bulunamadı", None

            # Basit keyword extraction (gerçek implementasyonda NLP kullanılmalı)
            # Türkçe stopwords filtrele
            stopwords = {
                "bir",
                "bu",
                "ve",
                "için",
                "ile",
                "de",
                "da",
                "mi",
                "mı",
                "mu",
                "mü",
                "ne",
                "ki",
                "gibi",
                "daha",
                "çok",
                "en",
                "şu",
                "o",
                "ben",
                "sen",
            }

            words = transcript.full_text.lower().split()
            keywords = [
                word for word in words if len(word) > 3 and word not in stopwords
            ]

            # Frekans analizi
            from collections import Counter

            word_freq = Counter(keywords)
            top_keywords = [word for word, _ in word_freq.most_common(10)]

            # Transkripti güncelle
            transcript.keywords = top_keywords
            await self.db.commit()

            logger.info(f"Keywords extracted for transcript: {transcript_id}")
            return True, None, top_keywords

        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            await self.db.rollback()
            return False, f"Anahtar kelime çıkarma hatası: {str(e)}", None
