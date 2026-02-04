"""
Video Solution Upload Tests
Task 72.1: Video yükleme testi
"""

import pytest
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from models.video_solution import VideoFormat, VideoProcessingStatus
from services.video_solution_service import VideoValidator, VideoConfig


class TestVideoValidator:
    """Video validation testleri"""

    @pytest.mark.asyncio
    async def test_validate_upload_success(self):
        """Başarılı video upload validasyonu"""
        # Mock file
        file_content = b"fake video content"
        file = UploadFile(filename="test_video.mp4", file=BytesIO(file_content))

        # Mock database
        db = AsyncMock(spec=AsyncSession)

        # Mock question exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id="question-123")
        db.execute = AsyncMock(return_value=mock_result)

        # Test validation
        is_valid, error_msg, metadata = await VideoValidator.validate_upload(
            file=file, question_id="question-123", db=db
        )

        assert is_valid is True
        assert error_msg is None
        assert metadata is not None
        assert metadata["original_filename"] == "test_video.mp4"
        assert metadata["format"] == VideoFormat.MP4

    @pytest.mark.asyncio
    async def test_validate_upload_invalid_format(self):
        """Geçersiz format validasyonu"""
        # Mock file with invalid format
        file_content = b"fake content"
        file = UploadFile(filename="test_video.txt", file=BytesIO(file_content))

        db = AsyncMock(spec=AsyncSession)

        # Test validation
        is_valid, error_msg, metadata = await VideoValidator.validate_upload(
            file=file, question_id="question-123", db=db
        )

        assert is_valid is False
        assert "Desteklenmeyen video formatı" in error_msg

    @pytest.mark.asyncio
    async def test_validate_upload_file_too_large(self):
        """Çok büyük dosya validasyonu"""
        # Mock large file
        large_content = b"x" * (VideoConfig.MAX_FILE_SIZE_BYTES + 1000)
        file = UploadFile(filename="large_video.mp4", file=BytesIO(large_content))

        db = AsyncMock(spec=AsyncSession)

        # Mock question exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id="question-123")
        db.execute = AsyncMock(return_value=mock_result)

        # Test validation
        is_valid, error_msg, metadata = await VideoValidator.validate_upload(
            file=file, question_id="question-123", db=db
        )

        assert is_valid is False
        assert "Dosya çok büyük" in error_msg

    @pytest.mark.asyncio
    async def test_validate_upload_empty_file(self):
        """Boş dosya validasyonu"""
        # Mock empty file
        file = UploadFile(filename="empty_video.mp4", file=BytesIO(b""))

        db = AsyncMock(spec=AsyncSession)

        # Test validation
        is_valid, error_msg, metadata = await VideoValidator.validate_upload(
            file=file, question_id="question-123", db=db
        )

        assert is_valid is False
        assert "Dosya boş" in error_msg

    @pytest.mark.asyncio
    async def test_validate_upload_question_not_found(self):
        """Soru bulunamadı validasyonu"""
        # Mock file
        file_content = b"fake video content"
        file = UploadFile(filename="test_video.mp4", file=BytesIO(file_content))

        # Mock database - question not found
        db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        # Test validation
        is_valid, error_msg, metadata = await VideoValidator.validate_upload(
            file=file, question_id="nonexistent-question", db=db
        )

        assert is_valid is False
        assert "Soru bulunamadı" in error_msg


class TestVideoConfig:
    """Video configuration testleri"""

    def test_max_file_size(self):
        """Maximum dosya boyutu kontrolü"""
        assert VideoConfig.MAX_FILE_SIZE_MB == 500
        assert VideoConfig.MAX_FILE_SIZE_BYTES == 500 * 1024 * 1024

    def test_supported_formats(self):
        """Desteklenen formatlar kontrolü"""
        assert VideoFormat.MP4 in VideoConfig.SUPPORTED_FORMATS
        assert VideoFormat.WEBM in VideoConfig.SUPPORTED_FORMATS
        assert VideoFormat.AVI in VideoConfig.SUPPORTED_FORMATS
        assert VideoFormat.MOV in VideoConfig.SUPPORTED_FORMATS
        assert VideoFormat.MKV in VideoConfig.SUPPORTED_FORMATS

    def test_resolution_requirements(self):
        """Çözünürlük gereksinimleri kontrolü"""
        assert VideoConfig.MIN_RESOLUTION_WIDTH == 640
        assert VideoConfig.MIN_RESOLUTION_HEIGHT == 480

    def test_duration_requirements(self):
        """Süre gereksinimleri kontrolü"""
        assert VideoConfig.MIN_DURATION_SECONDS == 10
        assert VideoConfig.MAX_DURATION_SECONDS == 3600


@pytest.mark.asyncio
async def test_video_upload_integration():
    """Video upload entegrasyon testi"""
    # Bu test gerçek ffmpeg gerektirir, bu yüzden skip edilebilir
    pytest.skip("Integration test - requires ffmpeg")
