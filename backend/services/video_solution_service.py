"""
Video Çözüm Sistemi Servisi
Teknofest 2025 Eğitim Eylemci Platformu

Task 72.1: Video Yükleme
- Video upload, format validation, compression
- Format validation
- Compression optimization

Requirements: REQ-14.1, REQ-14.2, REQ-14.3
"""

import asyncio
import hashlib
import logging
import mimetypes
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.video_solution import (
    VideoFormat,
    VideoProcessingStatus,
    VideoSolution,
    is_valid_video_format,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


class VideoConfig:
    """Video yükleme konfigürasyonu"""

    # Dosya boyutu limitleri
    MAX_FILE_SIZE_MB = 500  # 500 MB
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    # Desteklenen formatlar
    SUPPORTED_FORMATS = {
        VideoFormat.MP4,
        VideoFormat.WEBM,
        VideoFormat.AVI,
        VideoFormat.MOV,
        VideoFormat.MKV,
    }

    # Video kalite gereksinimleri
    MIN_RESOLUTION_WIDTH = 640  # Minimum 640px genişlik
    MIN_RESOLUTION_HEIGHT = 480  # Minimum 480px yükseklik
    MIN_DURATION_SECONDS = 10  # Minimum 10 saniye
    MAX_DURATION_SECONDS = 3600  # Maximum 1 saat

    # Compression ayarları
    TARGET_BITRATE_KBPS = 2000  # 2 Mbps hedef bitrate
    TARGET_CODEC = "libx264"  # H.264 codec
    TARGET_AUDIO_CODEC = "aac"
    TARGET_AUDIO_BITRATE_KBPS = 128

    # Depolama
    UPLOAD_DIR = Path("uploads/videos")
    PROCESSED_DIR = Path("uploads/videos/processed")
    THUMBNAIL_DIR = Path("uploads/thumbnails")

    @classmethod
    def ensure_directories(cls):
        """Gerekli dizinleri oluştur"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        cls.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Video Validation
# ============================================================================


class VideoValidator:
    """Video format ve içerik validasyonu"""

    @staticmethod
    async def validate_upload(
        file: UploadFile, question_id: str, db: AsyncSession
    ) -> tuple[bool, str | None, dict | None]:
        """
        Yüklenen videoyu valide et

        Args:
            file: Yüklenen dosya
            question_id: İlişkili soru ID
            db: Database session

        Returns:
            tuple: (geçerli mi, hata mesajı, metadata)
        """
        errors = []
        metadata = {}

        # 1. Dosya adı kontrolü
        if not file.filename:
            return False, "Dosya adı bulunamadı", None

        metadata["original_filename"] = file.filename

        # 2. Format kontrolü (REQ-14.1)
        is_valid, video_format = is_valid_video_format(file.filename)
        if not is_valid:
            errors.append(
                f"Desteklenmeyen video formatı: {file.filename.split('.')[-1]}"
            )
        else:
            metadata["format"] = video_format

        # 3. MIME type kontrolü
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type and not mime_type.startswith("video/"):
            errors.append(f"Geçersiz MIME type: {mime_type}")
        metadata["mime_type"] = mime_type

        # 4. Dosya boyutu kontrolü
        file.file.seek(0, 2)  # Dosya sonuna git
        file_size = file.file.tell()
        file.file.seek(0)  # Başa dön

        if file_size == 0:
            errors.append("Dosya boş")
        elif file_size > VideoConfig.MAX_FILE_SIZE_BYTES:
            errors.append(
                f"Dosya çok büyük: {file_size / (1024 * 1024):.2f} MB "
                f"(Maximum: {VideoConfig.MAX_FILE_SIZE_MB} MB)"
            )

        metadata["file_size_bytes"] = file_size
        metadata["file_size_mb"] = file_size / (1024 * 1024)

        # 5. Soru varlığı kontrolü
        from models.question_bank import QuestionBankItem

        result = await db.execute(
            select(QuestionBankItem).where(QuestionBankItem.id == question_id)
        )
        question = result.scalar_one_or_none()

        if not question:
            errors.append(f"Soru bulunamadı: {question_id}")

        if errors:
            return False, "; ".join(errors), metadata

        return True, None, metadata

    @staticmethod
    async def validate_video_properties(
        video_path: Path,
    ) -> tuple[bool, str | None, dict | None]:
        """
        Video özelliklerini ffprobe ile kontrol et (REQ-14.2)

        Args:
            video_path: Video dosya yolu

        Returns:
            tuple: (geçerli mi, hata mesajı, video özellikleri)
        """
        try:
            # ffprobe ile video bilgilerini al
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return False, f"ffprobe hatası: {stderr.decode()}", None

            import json

            probe_data = json.loads(stdout.decode())

            # Video stream bul
            video_stream = next(
                (
                    s
                    for s in probe_data.get("streams", [])
                    if s["codec_type"] == "video"
                ),
                None,
            )

            if not video_stream:
                return False, "Video stream bulunamadı", None

            # Özellikleri çıkar
            properties = {
                "duration": float(probe_data["format"].get("duration", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "codec": video_stream.get("codec_name"),
                "fps": (
                    lambda r: int(r.split("/")[0]) / int(r.split("/")[1])
                    if "/" in r and int(r.split("/")[1]) != 0
                    else float(r)
                    if r
                    else 0
                )(video_stream.get("r_frame_rate", "0/1")),
                "bitrate": int(probe_data["format"].get("bit_rate", 0)),
            }

            # Validasyon kontrolleri
            errors = []

            if properties["duration"] < VideoConfig.MIN_DURATION_SECONDS:
                errors.append(
                    f"Video çok kısa: {properties['duration']:.1f}s "
                    f"(Minimum: {VideoConfig.MIN_DURATION_SECONDS}s)"
                )

            if properties["duration"] > VideoConfig.MAX_DURATION_SECONDS:
                errors.append(
                    f"Video çok uzun: {properties['duration']:.1f}s "
                    f"(Maximum: {VideoConfig.MAX_DURATION_SECONDS}s)"
                )

            if properties["width"] < VideoConfig.MIN_RESOLUTION_WIDTH:
                errors.append(
                    f"Çözünürlük çok düşük: {properties['width']}x{properties['height']} "
                    f"(Minimum: {VideoConfig.MIN_RESOLUTION_WIDTH}x{VideoConfig.MIN_RESOLUTION_HEIGHT})"
                )

            if errors:
                return False, "; ".join(errors), properties

            return True, None, properties

        except Exception as e:
            logger.error(f"Video properties validation error: {e}")
            return False, f"Video analiz hatası: {e!s}", None


# ============================================================================
# Video Processing
# ============================================================================


class VideoProcessor:
    """Video işleme ve optimizasyon"""

    @staticmethod
    async def compress_video(
        input_path: Path,
        output_path: Path,
        target_bitrate_kbps: int = VideoConfig.TARGET_BITRATE_KBPS,
    ) -> tuple[bool, str | None, dict | None]:
        """
        Videoyu sıkıştır (TASK 72.1: Compression optimization)

        Args:
            input_path: Girdi video yolu
            output_path: Çıktı video yolu
            target_bitrate_kbps: Hedef bitrate (kbps)

        Returns:
            tuple: (başarılı mı, hata mesajı, compression stats)
        """
        try:
            # ffmpeg ile video sıkıştırma
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-c:v",
                VideoConfig.TARGET_CODEC,
                "-b:v",
                f"{target_bitrate_kbps}k",
                "-c:a",
                VideoConfig.TARGET_AUDIO_CODEC,
                "-b:a",
                f"{VideoConfig.TARGET_AUDIO_BITRATE_KBPS}k",
                "-movflags",
                "+faststart",  # Web streaming için optimize et
                "-y",  # Üzerine yaz
                str(output_path),
            ]

            logger.info(f"Compressing video: {input_path} -> {output_path}")

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"ffmpeg compression error: {error_msg}")
                return False, f"Sıkıştırma hatası: {error_msg}", None

            # Dosya boyutlarını karşılaştır
            original_size = input_path.stat().st_size
            compressed_size = output_path.stat().st_size

            compression_ratio = (
                original_size / compressed_size if compressed_size > 0 else 0
            )
            size_reduction_percent = (
                (original_size - compressed_size) / original_size
            ) * 100

            stats = {
                "original_size_bytes": original_size,
                "compressed_size_bytes": compressed_size,
                "compression_ratio": compression_ratio,
                "size_reduction_percent": size_reduction_percent,
            }

            logger.info(
                f"Compression successful: {original_size / (1024 * 1024):.2f} MB -> "
                f"{compressed_size / (1024 * 1024):.2f} MB "
                f"({size_reduction_percent:.1f}% reduction)"
            )

            return True, None, stats

        except Exception as e:
            logger.error(f"Video compression error: {e}")
            return False, f"Sıkıştırma hatası: {e!s}", None

    @staticmethod
    async def generate_thumbnail(
        video_path: Path, output_path: Path, timestamp_seconds: float = 5.0
    ) -> tuple[bool, str | None]:
        """
        Video thumbnail oluştur (REQ-14.3)

        Args:
            video_path: Video dosya yolu
            output_path: Thumbnail çıktı yolu
            timestamp_seconds: Thumbnail alınacak zaman (saniye)

        Returns:
            tuple: (başarılı mı, hata mesajı)
        """
        try:
            cmd = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-ss",
                str(timestamp_seconds),
                "-vframes",
                "1",
                "-vf",
                "scale=640:-1",  # 640px genişlik, yükseklik otomatik
                "-y",
                str(output_path),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Thumbnail generation error: {error_msg}")
                return False, f"Thumbnail oluşturma hatası: {error_msg}"

            logger.info(f"Thumbnail generated: {output_path}")
            return True, None

        except Exception as e:
            logger.error(f"Thumbnail generation error: {e}")
            return False, f"Thumbnail oluşturma hatası: {e!s}"


# ============================================================================
# Video Upload Service
# ============================================================================


class VideoSolutionService:
    """Video çözüm yükleme ve yönetim servisi"""

    def __init__(self, db: AsyncSession):
        self.db = db
        VideoConfig.ensure_directories()

    async def upload_video(
        self,
        file: UploadFile,
        question_id: str,
        user_id: str,
        title: str,
        description: str | None = None,
        solution_method: str | None = None,
    ) -> tuple[bool, str | None, VideoSolution | None]:
        """
        Video yükle ve işle (TASK 72.1)

        Args:
            file: Yüklenen video dosyası
            question_id: İlişkili soru ID
            user_id: Yükleyen kullanıcı ID
            title: Video başlığı
            description: Video açıklaması
            solution_method: Çözüm yöntemi

        Returns:
            tuple: (başarılı mı, hata mesajı, VideoSolution)
        """
        try:
            # 1. Validasyon (REQ-14.1)
            is_valid, error_msg, metadata = await VideoValidator.validate_upload(
                file, question_id, self.db
            )

            if not is_valid:
                return False, error_msg, None

            # 2. Dosyayı geçici olarak kaydet
            file_hash = hashlib.sha256(
                f"{user_id}{question_id}{datetime.now(UTC).isoformat()}".encode()
            ).hexdigest()[:16]
            original_ext = file.filename.split(".")[-1]
            temp_filename = f"{file_hash}_original.{original_ext}"
            temp_path = VideoConfig.UPLOAD_DIR / temp_filename

            async with aiofiles.open(temp_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            logger.info(f"Video uploaded to temp: {temp_path}")

            # 3. Video özelliklerini kontrol et (REQ-14.2)
            (
                is_valid,
                error_msg,
                video_props,
            ) = await VideoValidator.validate_video_properties(temp_path)

            if not is_valid:
                temp_path.unlink()  # Geçersiz dosyayı sil
                return False, error_msg, None

            # 4. Database kaydı oluştur
            video_solution = VideoSolution(
                question_id=question_id,
                uploaded_by=user_id,
                title=title,
                description=description,
                solution_method=solution_method,
                # Upload bilgileri
                original_filename=file.filename,
                original_format=metadata["format"],
                original_size_bytes=metadata["file_size_bytes"],
                original_duration_seconds=video_props["duration"],
                original_url=str(temp_path),
                # Validation sonuçları
                is_format_valid=True,
                validation_errors=None,
                # Processing durumu
                processing_status=VideoProcessingStatus.VALIDATING,
                processing_started_at=datetime.now(UTC),
            )

            self.db.add(video_solution)
            await self.db.commit()
            await self.db.refresh(video_solution)

            logger.info(f"Video solution created: {video_solution.id}")

            # 5. Arka planda işleme başlat
            asyncio.create_task(self._process_video_async(video_solution.id, temp_path))

            return True, None, video_solution

        except Exception as e:
            logger.error(f"Video upload error: {e}")
            await self.db.rollback()
            return False, f"Video yükleme hatası: {e!s}", None

    async def _process_video_async(self, video_id: str, temp_path: Path):
        """
        Videoyu arka planda işle

        Args:
            video_id: Video solution ID
            temp_path: Geçici video dosya yolu
        """
        try:
            # Video kaydını al
            result = await self.db.execute(
                select(VideoSolution).where(VideoSolution.id == video_id)
            )
            video = result.scalar_one_or_none()

            if not video:
                logger.error(f"Video not found: {video_id}")
                return

            # 1. Sıkıştırma (TASK 72.1: Compression optimization)
            video.processing_status = VideoProcessingStatus.COMPRESSING
            await self.db.commit()

            compressed_filename = f"{video_id}_compressed.mp4"
            compressed_path = VideoConfig.PROCESSED_DIR / compressed_filename

            success, error_msg, compression_stats = await VideoProcessor.compress_video(
                temp_path, compressed_path
            )

            if not success:
                video.processing_status = VideoProcessingStatus.FAILED
                video.processing_error = error_msg
                await self.db.commit()
                return

            # Compression bilgilerini güncelle
            video.compressed_size_bytes = compression_stats["compressed_size_bytes"]
            video.compression_ratio = compression_stats["compression_ratio"]
            video.cdn_url = str(compressed_path)  # CDN entegrasyonu sonra eklenecek

            # 2. Thumbnail oluştur (REQ-14.3)
            video.processing_status = VideoProcessingStatus.GENERATING_THUMBNAILS
            await self.db.commit()

            thumbnail_filename = f"{video_id}_thumb.jpg"
            thumbnail_path = VideoConfig.THUMBNAIL_DIR / thumbnail_filename

            success, error_msg = await VideoProcessor.generate_thumbnail(
                compressed_path, thumbnail_path
            )

            if success:
                video.thumbnail_url = str(thumbnail_path)
                video.thumbnail_generated_at = datetime.now(UTC)

            # 3. İşlem tamamlandı
            video.processing_status = VideoProcessingStatus.READY
            video.processing_completed_at = datetime.now(UTC)
            await self.db.commit()

            # Geçici dosyayı sil
            if temp_path.exists():
                temp_path.unlink()

            logger.info(f"Video processing completed: {video_id}")

        except Exception as e:
            logger.error(f"Video processing error: {e}")

            # Hata durumunu kaydet
            try:
                result = await self.db.execute(
                    select(VideoSolution).where(VideoSolution.id == video_id)
                )
                video = result.scalar_one_or_none()

                if video:
                    video.processing_status = VideoProcessingStatus.FAILED
                    video.processing_error = str(e)
                    await self.db.commit()
            except Exception as db_err:
                logger.debug(f"Failed to update video status: {db_err}")


# ============================================================================
# TASK 72.2: Video Streaming Service
# ============================================================================


class VideoStreamingService:
    """
    Video streaming servisi
    - HLS/DASH streaming
    - Adaptive bitrate
    - CDN integration

    Requirements: REQ-14.4, REQ-14.5
    """

    @staticmethod
    async def generate_hls_playlist(
        video_path: Path, output_dir: Path, qualities: list = None
    ) -> tuple[bool, str | None, dict | None]:
        """
        HLS playlist oluştur (TASK 72.2: HLS streaming)

        Args:
            video_path: Video dosya yolu
            output_dir: Çıktı dizini
            qualities: Kalite seviyeleri [(width, height, bitrate_kbps), ...]

        Returns:
            tuple: (başarılı mı, hata mesajı, playlist bilgileri)
        """
        if qualities is None:
            # Default adaptive bitrate qualities
            qualities = [
                (640, 360, 800),  # 360p
                (854, 480, 1400),  # 480p
                (1280, 720, 2800),  # 720p
                (1920, 1080, 5000),  # 1080p
            ]

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Master playlist dosyası
            master_playlist = output_dir / "master.m3u8"
            variant_playlists = []

            # Her kalite için variant oluştur
            for width, height, bitrate_kbps in qualities:
                variant_name = f"{height}p"
                variant_dir = output_dir / variant_name
                variant_dir.mkdir(exist_ok=True)

                # ffmpeg ile HLS segmentleri oluştur
                cmd = [
                    "ffmpeg",
                    "-i",
                    str(video_path),
                    "-vf",
                    f"scale={width}:{height}",
                    "-c:v",
                    "libx264",
                    "-b:v",
                    f"{bitrate_kbps}k",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-hls_time",
                    "6",  # 6 saniyelik segmentler
                    "-hls_list_size",
                    "0",  # Tüm segmentleri listele
                    "-hls_segment_filename",
                    str(variant_dir / "segment_%03d.ts"),
                    "-f",
                    "hls",
                    str(variant_dir / "playlist.m3u8"),
                ]

                logger.info(
                    f"Generating HLS variant: {variant_name} ({bitrate_kbps}kbps)"
                )

                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode()
                    logger.error(
                        f"HLS generation error for {variant_name}: {error_msg}"
                    )
                    continue

                variant_playlists.append(
                    {
                        "quality": variant_name,
                        "width": width,
                        "height": height,
                        "bitrate_kbps": bitrate_kbps,
                        "playlist_path": str(variant_dir / "playlist.m3u8"),
                    }
                )

                logger.info(f"HLS variant generated: {variant_name}")

            if not variant_playlists:
                return False, "HLS variant oluşturulamadı", None

            # Master playlist oluştur
            with open(master_playlist, "w") as f:
                f.write("#EXTM3U\n")
                f.write("#EXT-X-VERSION:3\n\n")

                for variant in variant_playlists:
                    f.write(
                        f"#EXT-X-STREAM-INF:BANDWIDTH={variant['bitrate_kbps'] * 1000},"
                        f"RESOLUTION={variant['width']}x{variant['height']}\n"
                    )
                    f.write(f"{variant['quality']}/playlist.m3u8\n\n")

            result = {
                "master_playlist": str(master_playlist),
                "variants": variant_playlists,
                "total_variants": len(variant_playlists),
            }

            logger.info(f"HLS master playlist created: {master_playlist}")
            return True, None, result

        except Exception as e:
            logger.error(f"HLS generation error: {e}")
            return False, f"HLS oluşturma hatası: {e!s}", None

    @staticmethod
    async def generate_dash_manifest(
        video_path: Path, output_dir: Path
    ) -> tuple[bool, str | None, str | None]:
        """
        DASH manifest oluştur (TASK 72.2: DASH streaming)

        Args:
            video_path: Video dosya yolu
            output_dir: Çıktı dizini

        Returns:
            tuple: (başarılı mı, hata mesajı, manifest yolu)
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = output_dir / "manifest.mpd"

            # ffmpeg ile DASH segmentleri oluştur
            cmd = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-b:v:0",
                "800k",  # 360p
                "-b:v:1",
                "1400k",  # 480p
                "-b:v:2",
                "2800k",  # 720p
                "-s:v:0",
                "640x360",
                "-s:v:1",
                "854x480",
                "-s:v:2",
                "1280x720",
                "-map",
                "0:v",
                "-map",
                "0:v",
                "-map",
                "0:v",
                "-map",
                "0:a",
                "-f",
                "dash",
                "-seg_duration",
                "6",
                "-use_template",
                "1",
                "-use_timeline",
                "1",
                "-init_seg_name",
                "init-$RepresentationID$.m4s",
                "-media_seg_name",
                "chunk-$RepresentationID$-$Number%05d$.m4s",
                str(manifest_path),
            ]

            logger.info(f"Generating DASH manifest: {manifest_path}")

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"DASH generation error: {error_msg}")
                return False, f"DASH oluşturma hatası: {error_msg}", None

            logger.info(f"DASH manifest created: {manifest_path}")
            return True, None, str(manifest_path)

        except Exception as e:
            logger.error(f"DASH generation error: {e}")
            return False, f"DASH oluşturma hatası: {e!s}", None

    @staticmethod
    async def upload_to_cdn(
        local_path: Path, cdn_config: dict
    ) -> tuple[bool, str | None, str | None]:
        """
        CDN'e yükle (TASK 72.2: CDN integration)

        Args:
            local_path: Yerel dosya yolu
            cdn_config: CDN konfigürasyonu

        Returns:
            tuple: (başarılı mı, hata mesajı, CDN URL)
        """
        # Bu fonksiyon CDN provider'a göre implement edilecek
        # Örnek: AWS S3, Cloudflare, Azure CDN, vb.

        # Şimdilik placeholder implementation
        logger.info(f"CDN upload placeholder: {local_path}")

        # Gerçek implementasyonda:
        # 1. CDN provider SDK kullan
        # 2. Dosyayı yükle
        # 3. CDN URL'ini al
        # 4. Cache invalidation yap (gerekirse)

        # Placeholder CDN URL
        cdn_url = f"https://cdn.example.com/videos/{local_path.name}"

        return True, None, cdn_url


class VideoAnalyticsService:
    """
    Video izleme analitiği servisi (REQ-14.4)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_view(
        self,
        video_id: str,
        user_id: str | None,
        session_id: str,
        watch_duration_seconds: float,
        completion_percentage: float,
        device_info: dict | None = None,
    ) -> bool:
        """
        Video izleme kaydı oluştur (REQ-14.4: İzlenme sayısı)

        Args:
            video_id: Video ID
            user_id: Kullanıcı ID (opsiyonel)
            session_id: Session ID
            watch_duration_seconds: İzleme süresi
            completion_percentage: Tamamlanma yüzdesi
            device_info: Cihaz bilgileri

        Returns:
            bool: Başarılı mı
        """
        try:
            from datetime import datetime

            from models.video_solution import VideoAnalytics, VideoSolution

            # Video analytics kaydı oluştur
            analytics = VideoAnalytics(
                video_id=video_id,
                user_id=user_id,
                session_id=session_id,
                started_at=datetime.now(UTC),
                watch_duration_seconds=watch_duration_seconds,
                completion_percentage=completion_percentage,
                device_type=device_info.get("device_type") if device_info else None,
                browser=device_info.get("browser") if device_info else None,
                os=device_info.get("os") if device_info else None,
            )

            self.db.add(analytics)

            # Video total views güncelle
            result = await self.db.execute(
                select(VideoSolution).where(VideoSolution.id == video_id)
            )
            video = result.scalar_one_or_none()

            if video:
                video.total_views += 1
                video.total_watch_time_seconds += watch_duration_seconds

                # Average completion rate güncelle
                total_analytics = await self.db.execute(
                    select(VideoAnalytics).where(VideoAnalytics.video_id == video_id)
                )
                all_analytics = total_analytics.scalars().all()

                if all_analytics:
                    avg_completion = sum(
                        a.completion_percentage for a in all_analytics
                    ) / len(all_analytics)
                    video.average_completion_rate = avg_completion / 100.0

            await self.db.commit()

            logger.info(
                f"Video view tracked: {video_id} - {watch_duration_seconds}s ({completion_percentage}%)"
            )
            return True

        except Exception as e:
            logger.error(f"Video analytics tracking error: {e}")
            await self.db.rollback()
            return False
