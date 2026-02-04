"""
Text-to-Speech API
Fallback TTS servisi için backend endpoint

Requirements: REQ-50.45 (Fallback TTS servisi)
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional
import logging
from io import BytesIO

# TTS kütüphaneleri
try:
    from gtts import gTTS  # Google Text-to-Speech

    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logging.warning("gTTS kütüphanesi yüklü değil. pip install gtts")

try:
    import pyttsx3  # Offline TTS

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 kütüphanesi yüklü değil. pip install pyttsx3")

router = APIRouter(prefix="/api/v1/tts", tags=["Text-to-Speech"])
logger = logging.getLogger(__name__)


class TTSRequest(BaseModel):
    """TTS İstek Modeli"""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Seslendirilecek metin"
    )
    language: str = Field(default="tr-TR", description="Dil kodu (tr-TR, en-US, vb.)")
    rate: float = Field(default=1.0, ge=0.5, le=2.0, description="Ses hızı (0.5-2.0)")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Ses tonu (0.5-2.0)")
    voice_gender: Optional[str] = Field(
        default=None, description="Ses cinsiyeti (male/female)"
    )


class TTSService:
    """
    Text-to-Speech Servisi

    Fallback mekanizması:
    1. Google TTS (gTTS) - Online, yüksek kalite
    2. pyttsx3 - Offline, orta kalite
    3. Hata durumunda uygun mesaj
    """

    @staticmethod
    def synthesize_with_gtts(text: str, language: str = "tr") -> BytesIO:
        """
        Google TTS ile ses sentezleme

        Args:
            text: Seslendirilecek metin
            language: Dil kodu (tr, en, vb.)

        Returns:
            BytesIO: MP3 audio stream
        """
        if not GTTS_AVAILABLE:
            raise ImportError("gTTS kütüphanesi yüklü değil")

        try:
            # Dil kodunu gTTS formatına çevir (tr-TR -> tr)
            lang_code = language.split("-")[0].lower()

            # TTS oluştur
            tts = gTTS(text=text, lang=lang_code, slow=False)

            # BytesIO'ya kaydet
            audio_stream = BytesIO()
            tts.write_to_fp(audio_stream)
            audio_stream.seek(0)

            logger.info(f"gTTS ile ses sentezlendi: {len(text)} karakter")
            return audio_stream

        except Exception as e:
            logger.error(f"gTTS hatası: {str(e)}")
            raise

    @staticmethod
    def synthesize_with_pyttsx3(
        text: str,
        rate: float = 1.0,
        pitch: float = 1.0,
        voice_gender: Optional[str] = None,
    ) -> BytesIO:
        """
        pyttsx3 ile offline ses sentezleme

        Args:
            text: Seslendirilecek metin
            rate: Ses hızı (0.5-2.0)
            pitch: Ses tonu (0.5-2.0)
            voice_gender: Ses cinsiyeti

        Returns:
            BytesIO: WAV audio stream
        """
        if not PYTTSX3_AVAILABLE:
            raise ImportError("pyttsx3 kütüphanesi yüklü değil")

        try:
            engine = pyttsx3.init()

            # Ses hızı ayarla (150 = normal, 75-300 arası)
            base_rate = 150
            engine.setProperty("rate", int(base_rate * rate))

            # Ses seviyesi
            engine.setProperty("volume", 1.0)

            # Türkçe ses seç (varsa)
            voices = engine.getProperty("voices")
            turkish_voice = None

            for voice in voices:
                if "turkish" in voice.name.lower() or "tr" in voice.languages:
                    if voice_gender:
                        if voice_gender.lower() in voice.name.lower():
                            turkish_voice = voice
                            break
                    else:
                        turkish_voice = voice
                        break

            if turkish_voice:
                engine.setProperty("voice", turkish_voice.id)

            # Geçici dosyaya kaydet
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            engine.save_to_file(text, temp_path)
            engine.runAndWait()

            # Dosyayı oku ve BytesIO'ya aktar
            with open(temp_path, "rb") as f:
                audio_stream = BytesIO(f.read())

            # Geçici dosyayı sil
            import os

            os.unlink(temp_path)

            audio_stream.seek(0)
            logger.info(f"pyttsx3 ile ses sentezlendi: {len(text)} karakter")
            return audio_stream

        except Exception as e:
            logger.error(f"pyttsx3 hatası: {str(e)}")
            raise


@router.post("/synthesize", response_class=Response)
async def synthesize_speech(request: TTSRequest):
    """
    Metin seslendir (Fallback TTS)

    REQ-50.45: Web Speech API kullanılamadığında fallback TTS servisi

    Args:
        request: TTS isteği (metin, dil, hız, ton)

    Returns:
        Audio stream (MP3 veya WAV)

    Raises:
        HTTPException: TTS servisleri kullanılamıyorsa
    """
    try:
        # Önce gTTS dene (online, yüksek kalite)
        if GTTS_AVAILABLE:
            try:
                audio_stream = TTSService.synthesize_with_gtts(
                    text=request.text, language=request.language
                )

                return Response(
                    content=audio_stream.read(),
                    media_type="audio/mpeg",
                    headers={
                        "Content-Disposition": "attachment; filename=speech.mp3",
                        "X-TTS-Engine": "gTTS",
                    },
                )
            except Exception as e:
                logger.warning(f"gTTS başarısız, pyttsx3'e geçiliyor: {str(e)}")

        # gTTS başarısız olursa pyttsx3 dene (offline)
        if PYTTSX3_AVAILABLE:
            try:
                audio_stream = TTSService.synthesize_with_pyttsx3(
                    text=request.text,
                    rate=request.rate,
                    pitch=request.pitch,
                    voice_gender=request.voice_gender,
                )

                return Response(
                    content=audio_stream.read(),
                    media_type="audio/wav",
                    headers={
                        "Content-Disposition": "attachment; filename=speech.wav",
                        "X-TTS-Engine": "pyttsx3",
                    },
                )
            except Exception as e:
                logger.error(f"pyttsx3 başarısız: {str(e)}")

        # Hiçbir TTS servisi kullanılamıyorsa
        raise HTTPException(
            status_code=503,
            detail="TTS servisleri şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS API hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ses sentezleme hatası: {str(e)}")


@router.get("/voices")
async def get_available_voices():
    """
    Kullanılabilir sesleri listele

    Returns:
        Mevcut TTS motorları ve sesler
    """
    voices = {"engines": [], "voices": []}

    if GTTS_AVAILABLE:
        voices["engines"].append(
            {
                "name": "gTTS",
                "type": "online",
                "quality": "high",
                "languages": [
                    "tr",
                    "en",
                    "de",
                    "fr",
                    "es",
                    "it",
                    "pt",
                    "ru",
                    "ar",
                    "zh",
                ],
            }
        )

    if PYTTSX3_AVAILABLE:
        try:
            engine = pyttsx3.init()
            available_voices = engine.getProperty("voices")

            voices["engines"].append(
                {"name": "pyttsx3", "type": "offline", "quality": "medium"}
            )

            for voice in available_voices:
                voices["voices"].append(
                    {
                        "id": voice.id,
                        "name": voice.name,
                        "languages": voice.languages,
                        "gender": voice.gender if hasattr(voice, "gender") else None,
                    }
                )
        except Exception as e:
            logger.error(f"pyttsx3 ses listesi alınamadı: {str(e)}")

    return voices


@router.get("/health")
async def tts_health_check():
    """
    TTS servisi sağlık kontrolü

    Returns:
        Servis durumu ve kullanılabilir motorlar
    """
    return {
        "status": "healthy" if (GTTS_AVAILABLE or PYTTSX3_AVAILABLE) else "degraded",
        "gtts_available": GTTS_AVAILABLE,
        "pyttsx3_available": PYTTSX3_AVAILABLE,
        "message": "TTS servisi çalışıyor"
        if (GTTS_AVAILABLE or PYTTSX3_AVAILABLE)
        else "TTS kütüphaneleri yüklü değil",
    }
