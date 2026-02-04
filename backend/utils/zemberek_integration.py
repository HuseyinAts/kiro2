"""
Zemberek-NLP Entegrasyon Utilities
"""

import asyncio
import logging
import os
import signal
import subprocess
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ZemberekServer:
    """
    Zemberek-NLP server yönetimi
    """

    def __init__(self, port: int = 6789):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.server_url = f"http://localhost:{port}"
        self.jar_path = self._find_zemberek_jar()

    def _find_zemberek_jar(self) -> Optional[str]:
        """Zemberek JAR dosyasını bul"""
        possible_paths = [
            "zemberek-full.jar",
            "lib/zemberek-full.jar",
            "/opt/zemberek/zemberek-full.jar",
            os.path.expanduser("~/zemberek/zemberek-full.jar"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        logger.warning("Zemberek JAR dosyası bulunamadı")
        return None

    async def start_server(self) -> bool:
        """
        Zemberek server'ı başlat

        Returns:
            bool: Server başarıyla başlatıldı mı
        """
        try:
            if not self.jar_path:
                logger.error("Zemberek JAR dosyası bulunamadı")
                return False

            # Server zaten çalışıyor mu kontrol et
            if await self._is_server_running():
                logger.info("Zemberek server zaten çalışıyor")
                return True

            # Server'ı başlat
            cmd = [
                "java",
                "-Xmx4G",  # 4GB heap
                "-jar",
                self.jar_path,
                "--server",
                "--port",
                str(self.port),
            ]

            logger.info(f"Zemberek server başlatılıyor: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            # Server'ın başlamasını bekle
            for i in range(30):  # 30 saniye bekle
                await asyncio.sleep(1)
                if await self._is_server_running():
                    logger.info("Zemberek server başarıyla başlatıldı")
                    return True

            logger.error("Zemberek server başlatılamadı")
            await self.stop_server()
            return False

        except Exception as e:
            logger.error(f"Zemberek server başlatma hatası: {e}")
            return False

    async def stop_server(self):
        """Zemberek server'ı durdur"""
        try:
            if self.process:
                if os.name == "nt":  # Windows
                    self.process.terminate()
                else:  # Unix/Linux
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

                # Process'in bitmesini bekle
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if os.name == "nt":
                        self.process.kill()
                    else:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)

                self.process = None
                logger.info("Zemberek server durduruldu")

        except Exception as e:
            logger.error(f"Zemberek server durdurma hatası: {e}")

    async def _is_server_running(self) -> bool:
        """Server çalışıyor mu kontrol et"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_server()
        return self

    async def __aexit__(self, exc_type, exc_val, _):
        """Async context manager exit"""
        await self.stop_server()


class ZemberekClient:
    """
    Zemberek API client
    """

    def __init__(self, server_url: str = "http://localhost:6789"):
        self.server_url = server_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, _):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def analyze_morphology(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Kelimenin morfolojik analizini yap

        Args:
            word: Analiz edilecek kelime

        Returns:
            Dict: Morfolojik analiz sonucu
        """
        try:
            if not self.session:
                return None

            payload = {"word": word}

            async with self.session.post(
                f"{self.server_url}/morphology/analyze", json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Zemberek API hatası: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Zemberek morphology API hatası: {e}")
            return None

    async def normalize_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Metni normalize et

        Args:
            text: Normalize edilecek metin

        Returns:
            Dict: Normalizasyon sonucu
        """
        try:
            if not self.session:
                return None

            payload = {"text": text}

            async with self.session.post(
                f"{self.server_url}/normalization/normalize", json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(
                        f"Zemberek normalization API hatası: {response.status}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Zemberek normalization API hatası: {e}")
            return None

    async def tokenize(self, text: str) -> Optional[List[str]]:
        """
        Metni tokenize et

        Args:
            text: Tokenize edilecek metin

        Returns:
            List[str]: Token listesi
        """
        try:
            if not self.session:
                return None

            payload = {"text": text}

            async with self.session.post(
                f"{self.server_url}/tokenization/tokenize", json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("tokens", [])
                else:
                    logger.warning(
                        f"Zemberek tokenization API hatası: {response.status}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Zemberek tokenization API hatası: {e}")
            return None

    async def spell_check(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Yazım kontrolü yap

        Args:
            word: Kontrol edilecek kelime

        Returns:
            Dict: Yazım kontrolü sonucu
        """
        try:
            if not self.session:
                return None

            payload = {"word": word}

            async with self.session.post(
                f"{self.server_url}/spelling/check", json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(
                        f"Zemberek spell check API hatası: {response.status}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Zemberek spell check API hatası: {e}")
            return None

    async def health_check(self) -> bool:
        """
        Server sağlık kontrolü

        Returns:
            bool: Server sağlıklı mı
        """
        try:
            if not self.session:
                return False

            async with self.session.get(f"{self.server_url}/health") as response:
                return response.status == 200

        except Exception:
            return False


# Utility functions
async def setup_zemberek_environment():
    """
    Zemberek ortamını hazırla
    """
    try:
        # Zemberek JAR dosyasının varlığını kontrol et
        server = ZemberekServer()

        if not server.jar_path:
            logger.warning(
                """
            Zemberek JAR dosyası bulunamadı!
            
            Kurulum için:
            1. https://github.com/ahmetaa/zemberek-nlp/releases adresinden son sürümü indirin
            2. zemberek-full.jar dosyasını proje kök dizinine koyun
            3. Veya ZEMBEREK_JAR_PATH environment variable'ını ayarlayın
            """
            )
            return False

        # Test için server'ı başlat ve durdur
        async with server:
            logger.info("Zemberek ortamı başarıyla hazırlandı")
            return True

    except Exception as e:
        logger.error(f"Zemberek ortam hazırlama hatası: {e}")
        return False


async def test_zemberek_integration():
    """
    Zemberek entegrasyonunu test et
    """
    try:
        async with ZemberekServer() as server:
            async with ZemberekClient() as client:
                # Health check
                if not await client.health_check():
                    logger.error("Zemberek server sağlık kontrolü başarısız")
                    return False

                # Morphology test
                test_word = "kitaplarımızdan"
                morphology_result = await client.analyze_morphology(test_word)

                if morphology_result:
                    logger.info(
                        f"Morphology test başarılı: {test_word} -> {morphology_result}"
                    )
                else:
                    logger.warning("Morphology test başarısız")

                # Normalization test
                test_text = "merhaba  dünya!  nasılsın?"
                normalization_result = await client.normalize_text(test_text)

                if normalization_result:
                    logger.info(f"Normalization test başarılı: {normalization_result}")
                else:
                    logger.warning("Normalization test başarısız")

                return True

    except Exception as e:
        logger.error(f"Zemberek entegrasyon testi hatası: {e}")
        return False


# Global instances
zemberek_server = ZemberekServer()
zemberek_client = ZemberekClient()
